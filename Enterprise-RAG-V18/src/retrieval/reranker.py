# src/retrieval/reranker.py
import logging
from typing import List
from flashrank import Ranker, RerankRequest
import aiohttp
from configs.settings import settings
from src.retrieval.base import Document
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self):
        self.flashrank_ranker = None
        if not settings.VOYAGE_API_KEY:
            try:
                self.flashrank_ranker = Ranker()
            except Exception as e:
                logger.error(f"Failed to load FlashRank: {e}")

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    async def _rerank_voyage(self, query: str, docs: List[Document], top_k: int) -> List[Document]:
        url = "https://api.voyageai.com/v1/rerank"
        headers = {
            "Authorization": f"Bearer {settings.VOYAGE_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "query": query,
            "documents": [doc.content for doc in docs],
            "model": "rerank-lite-1",
            "top_k": top_k
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                result = await response.json()
                
                reranked = []
                for item in result["data"]:
                    idx = item["index"]
                    doc = docs[idx].model_copy()
                    doc.score = item["relevance_score"]
                    reranked.append(doc)
                return reranked

    async def _rerank_flashrank(self, query: str, docs: List[Document], top_k: int) -> List[Document]:
        if not self.flashrank_ranker:
            logger.warning("FlashRank not initialized, returning original docs.")
            return docs[:top_k]
            
        passages = [
            {"id": doc.id, "text": doc.content, "meta": doc.metadata} 
            for doc in docs
        ]
        
        rerankrequest = RerankRequest(query=query, passages=passages)
        results = self.flashrank_ranker.rerank(rerankrequest)
        
        reranked = []
        for i, res in enumerate(results[:top_k]):
            # Flashrank returns dictionaries
            original_doc = next((d for d in docs if str(d.id) == str(res['id'])), docs[i])
            doc = original_doc.model_copy()
            doc.score = res.get('score', 0.0)
            reranked.append(doc)
            
        return reranked

    async def rerank(self, query: str, docs: List[Document], top_k: int = 5) -> List[Document]:
        if not docs:
            return []
            
        logger.info(f"Reranking {len(docs)} documents for query: '{query}'")
        try:
            if settings.VOYAGE_API_KEY:
                return await self._rerank_voyage(query, docs, top_k)
            else:
                return await self._rerank_flashrank(query, docs, top_k)
        except Exception as e:
            logger.error(f"Reranking failed: {e}. Returning unranked top_k.")
            return docs[:top_k]

reranker = Reranker()
