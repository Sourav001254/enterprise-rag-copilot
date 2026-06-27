# src/agents/embed_query.py
import logging
import asyncio
from typing import List
from src.agents.state import AgentState
from src.llm.gateway import llm_gateway
from src.cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)

async def _get_embedding(text: str, embeddings_model) -> List[float]:
    # Check L1 cache
    cached = await redis_cache.get(1, text)
    if cached and isinstance(cached, list):
        return cached
        
    vector = await embeddings_model.aembed_query(text)
    await redis_cache.set(1, text, vector)
    return vector

async def embed_query_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    hyde_queries = state.get("hyde_queries", [])
    
    logger.info("Embedding query and HyDE variations.")
    try:
        embeddings_model = llm_gateway.get_embeddings()
        
        # Parallel embedding
        tasks = [_get_embedding(query, embeddings_model)]
        for hq in hyde_queries:
            tasks.append(_get_embedding(hq, embeddings_model))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        if isinstance(results[0], Exception):
            raise results[0]
            
        state["query_vector"] = results[0]
        
        hyde_vectors = []
        for r in results[1:]:
            if not isinstance(r, Exception):
                hyde_vectors.append(r)
                
        state["hyde_vectors"] = hyde_vectors
        return state
    except Exception as e:
        logger.error(f"EmbedQuery error: {e}")
        state["error"] = f"EmbedQuery: {str(e)}"
        state["query_vector"] = []
        state["hyde_vectors"] = []
        return state
