# src/retrieval/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel

class Document(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float = 0.0

class BaseRetriever(ABC):
    @abstractmethod
    async def search(self, query: str, top_k: int = 20) -> List[Document]:
        """Search the corpus and return relevant documents."""
        pass

    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to the retrieval index."""
        pass
