# src/agents/reranker.py
import logging
from src.agents.state import AgentState
from src.retrieval.reranker import reranker
from configs.settings import settings

logger = logging.getLogger(__name__)

async def rerank_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    docs = state.get("retrieved_docs", [])
    
    if not docs:
        state["reranked_docs"] = []
        return state
        
    logger.info(f"Reranking top {len(docs)} docs for query: '{query}'")
    try:
        reranked = await reranker.rerank(query, docs, top_k=settings.RERANKER_TOP_K)
        state["reranked_docs"] = reranked
        return state
    except Exception as e:
        logger.error(f"Rerank node error: {e}")
        state["error"] = f"Reranker: {str(e)}"
        # Fallback to just taking the top K without reranking
        state["reranked_docs"] = docs[:settings.RERANKER_TOP_K]
        return state
