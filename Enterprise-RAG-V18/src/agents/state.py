# src/agents/state.py
from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from src.retrieval.base import Document

class AgentState(TypedDict):
    query: str
    original_query: str
    session_id: str
    user_id: str
    intent: str                      # "rag", "sql", "hybrid", "chitchat", "out_of_scope"
    complexity: str                  # "simple", "complex", "multi-hop"
    chat_history: List[BaseMessage]
    dense_docs: List[Document]
    sparse_docs: List[Document]
    retrieved_docs: List[Document]
    reranked_docs: List[Document]
    hyde_queries: List[str]          # 3 hypothetical answers
    rrf_scores: Dict[str, float]
    crag_score: float                # relevance score 0–1
    context_sufficient: bool
    retrieval_attempts: int          # cap at 3
    sql_query: str
    sql_approved: bool
    sql_result: Any
    self_rag_score: float            # quality score 0–1
    self_rag_attempts: int           # cap at 2
    answer: str
    sources: List[Dict]
    web_search_used: bool
    tokens_used: int
    prompt_tokens: Optional[int]
    latency_ms: int
    error: Optional[str]
    
    # Store vectors
    query_vector: List[float]
    hyde_vectors: List[List[float]]
