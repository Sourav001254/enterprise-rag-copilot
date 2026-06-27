# src/agents/rewriter.py
import logging
from langchain_core.prompts import PromptTemplate
from src.agents.state import AgentState
from src.llm.gateway import llm_gateway
from src.llm.model_router import TaskType

logger = logging.getLogger(__name__)

async def rewriter_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    original_query = state.get("original_query", query)
    
    logger.info(f"Rewriting query: '{query}'")
    
    try:
        llm = llm_gateway.get_llm(task=TaskType.GENERATION, temperature=0.8)
        
        prompt = PromptTemplate.from_template(
            """You are a search query rewriter.
The original query did not return sufficient context from the vector database.
Rewrite the query to be more effective for semantic search, using different keywords or breaking down complex terms.

Original Query: {original}
Current Query: {current}

Output ONLY the new query string, without quotes or explanation."""
        )
        
        chain = prompt | llm
        res = await chain.ainvoke({"original": original_query, "current": query})
        
        new_query = res.content.strip().strip('"').strip("'")
        logger.info(f"Rewrote query to: '{new_query}'")
        
        state["query"] = new_query
        return state
    except Exception as e:
        logger.error(f"Rewriter error: {e}")
        state["error"] = f"Rewriter: {str(e)}"
        return state
