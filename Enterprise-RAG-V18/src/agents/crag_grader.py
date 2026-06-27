# src/agents/crag_grader.py
import logging
from datetime import datetime, timezone
import json
from langchain_core.prompts import PromptTemplate
from src.agents.state import AgentState
from src.llm.gateway import llm_gateway
from src.llm.model_router import TaskType
from configs.settings import settings

logger = logging.getLogger(__name__)

async def crag_grader_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    docs = state.get("reranked_docs", [])
    retrieval_attempts = state.get("retrieval_attempts", 0)
    
    state["retrieval_attempts"] = retrieval_attempts + 1
    
    if not docs:
        logger.warning("No docs to grade.")
        state["crag_score"] = 0.0
        state["web_search_used"] = True
        state["context_sufficient"] = False
        return state
        
    logger.info(f"Grading {len(docs)} docs for relevance. Attempt: {state['retrieval_attempts']}")
    
    from configs.prompts import BATCH_CRAG_GRADER_PROMPT
    llm = llm_gateway.get_llm(task=TaskType.JSON_STRUCTURED, temperature=0.0)
    prompt = PromptTemplate.from_template(BATCH_CRAG_GRADER_PROMPT)
    chain = prompt | llm
    
    max_score = 0.0
    now = datetime.now(timezone.utc)
    
    docs_str = "\n".join([f"[{i+1}] {doc.content}" for i, doc in enumerate(docs)])
    
    try:
        res = await chain.ainvoke({"query": query, "docs_str": docs_str})
        parsed = json.loads(res.content)
        
        for i, doc in enumerate(docs):
            idx_str = str(i + 1)
            score = float(parsed.get(idx_str, 0.0))
            
            # Feature B: Document Freshness Scoring
            created_at_str = doc.metadata.get("created_at")
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                    if (now - created_at).days > 30:
                        logger.debug(f"Penalizing doc {doc.id} for age > 30 days")
                        score *= 0.8
                except Exception:
                    pass
                    
            if score > max_score:
                max_score = score
    except Exception as e:
        logger.error(f"Error in batch grading docs: {e}")
            
    logger.info("CRAG grading loop completed successfully.")
    state["crag_score"] = max_score
    
    if max_score >= settings.CRAG_SCORE_THRESHOLD:
        logger.info(f"Context is sufficient (score: {max_score})")
        state["context_sufficient"] = True
        state["web_search_used"] = False
    else:
        logger.info(f"Context is insufficient (score: {max_score})")
        state["context_sufficient"] = False
        if state["retrieval_attempts"] >= settings.RETRIEVAL_MAX_ATTEMPTS:
            logger.info("Max retrieval attempts reached, falling back to Tavily.")
            state["web_search_used"] = True
        else:
            state["web_search_used"] = False # will route to rewriter
            
    return state
