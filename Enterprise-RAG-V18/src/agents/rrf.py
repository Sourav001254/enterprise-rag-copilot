# src/agents/rrf.py
import logging
from typing import List
from src.agents.state import AgentState
from src.retrieval.base import Document
from configs.settings import settings

logger = logging.getLogger(__name__)

def compute_rrf(doc_lists: List[List[Document]], k: int = 60) -> List[Document]:
    """Compute Reciprocal Rank Fusion across multiple ranked lists."""
    rrf_score = {}
    doc_map = {}
    
    for doc_list in doc_lists:
        for rank, doc in enumerate(doc_list, start=1):
            if doc.id not in rrf_score:
                rrf_score[doc.id] = 0.0
                doc_map[doc.id] = doc
            rrf_score[doc.id] += 1.0 / (k + rank)
            
    # Sort by RRF score
    sorted_docs = sorted(rrf_score.items(), key=lambda x: x[1], reverse=True)
    
    result = []
    for doc_id, score in sorted_docs:
        doc = doc_map[doc_id].model_copy()
        doc.score = score
        result.append(doc)
        
    return result

async def rrf_node(state: AgentState) -> AgentState:
    dense_docs = state.get("dense_docs", [])
    sparse_docs = state.get("sparse_docs", [])
    
    logger.info(f"Running RRF on {len(dense_docs)} dense and {len(sparse_docs)} sparse documents.")
    
    fused_docs = compute_rrf([dense_docs, sparse_docs], k=60)
    top_docs = fused_docs[:settings.RETRIEVER_TOP_K]
    
    state["retrieved_docs"] = top_docs
    state["rrf_scores"] = {d.id: d.score for d in top_docs}
    
    return state
