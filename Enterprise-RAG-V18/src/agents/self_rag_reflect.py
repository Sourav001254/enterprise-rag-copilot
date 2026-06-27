# src/agents/self_rag_reflect.py
import logging
import json
from langchain_core.prompts import PromptTemplate
from src.agents.state import AgentState
from src.llm.gateway import llm_gateway
from src.llm.model_router import TaskType
from configs.settings import settings

logger = logging.getLogger(__name__)

async def self_rag_reflect_node(state: AgentState) -> AgentState:
    answer = state.get("answer", "")
    query = state.get("original_query", state.get("query", ""))
    attempts = state.get("self_rag_attempts", 0)
    
    state["self_rag_attempts"] = attempts + 1
    
    if not answer or state.get("error"):
        state["self_rag_score"] = 0.0
        return state
        
    logger.info(f"Reflecting on answer quality. Attempt: {state['self_rag_attempts']}")
    
    try:
        llm = llm_gateway.get_llm(task=TaskType.JSON_STRUCTURED, temperature=0.0)
        
        prompt = PromptTemplate.from_template(
            """You are a strict evaluator. Assess the quality of the given answer to the user's question.
Check for accuracy, relevance, and presence of hallucination markers [unverified].
Score the answer between 0.0 and 1.0. A score < 0.8 means the answer needs to be regenerated.

Question: {query}
Answer: {answer}

Output strictly valid JSON: {{"score": 0.0}}"""
        )
        
        chain = prompt | llm
        res = await chain.ainvoke({"query": query, "answer": answer})
        
        try:
            parsed = json.loads(res.content)
            score = float(parsed.get("score", 0.0))
        except Exception:
            score = 0.5
            
        logger.info(f"Self-RAG Score: {score}")
        state["self_rag_score"] = score
        
        return state
    except Exception as e:
        logger.error(f"Self RAG error: {e}")
        state["error"] = f"SelfRAG: {str(e)}"
        state["self_rag_score"] = 1.0 # bypass on error to avoid infinite loops
        return state
