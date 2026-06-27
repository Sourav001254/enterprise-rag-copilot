# src/api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class QueryRequest(BaseModel):
    query: str = Field(..., max_length=1000)
    session_id: str = Field(default_factory=lambda: "default_session")
    
class SourceItem(BaseModel):
    url: str
    title: str
    score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []
    tokens_used: int = 0
    latency_ms: int = 0
    degraded: bool = False
    intent: str = "rag"

class SQLApproveRequest(BaseModel):
    session_id: str
    approved: bool

class UploadResponse(BaseModel):
    status: str
    documents_processed: int
    chunks_created: int
