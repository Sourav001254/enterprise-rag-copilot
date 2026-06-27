# src/agents/hybrid_retrieval.py
import logging
import asyncio
import hashlib
from src.agents.state import AgentState
from src.retrieval.qdrant_client import qdrant_manager
from src.retrieval.bm25_index import bm25_index
from configs.settings import settings

logger = logging.getLogger(__name__)

async def hybrid_retrieval_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    query_vector = state.get("query_vector")
    hyde_vectors = state.get("hyde_vectors", [])
    
    if not query_vector:
        logger.warning("No query vector found, skipping retrieval.")
        state["retrieved_docs"] = []
        return state

    logger.info(f"Running hybrid retrieval for query: '{query}'")
    
    try:
        # Start sparse search (BM25 fallback for sparse)
        sparse_task = bm25_index.search(query, top_k=settings.RETRIEVER_TOP_K)
        
        # Start dense search(es)
        dense_tasks = []
        # Use query vector
        dense_tasks.append(qdrant_manager.async_search(query_vector, None, settings.RETRIEVER_TOP_K))
        # Use HyDE vectors
        for hv in hyde_vectors:
            dense_tasks.append(qdrant_manager.async_search(hv, None, settings.RETRIEVER_TOP_K))
            
        results = await asyncio.gather(sparse_task, *dense_tasks, return_exceptions=True)
        
        sparse_res = results[0]
        if isinstance(sparse_res, Exception):
            logger.error(f"Sparse retrieval task failed: {sparse_res}")
            sparse_res = []
            
        all_dense = []
        for res in results[1:]:
            if isinstance(res, Exception):
                logger.error(f"Dense retrieval task failed: {res}")
            else:
                all_dense.extend(res)
                
        logger.info(f"Hybrid retrieval found {len(all_dense)} dense and {len(sparse_res)} sparse documents.")
        state["sparse_docs"] = sparse_res
        state["dense_docs"] = all_dense
        
        return state
    except Exception as e:
        logger.error(f"Hybrid retrieval error: {e}")
        state["error"] = f"HybridRetrieval: {str(e)}"
        state["retrieved_docs"] = []
        return state
