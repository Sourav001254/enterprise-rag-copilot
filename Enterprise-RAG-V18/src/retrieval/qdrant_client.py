# src/retrieval/qdrant_client.py
import logging
from typing import List, Optional, Tuple, Dict
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance, VectorParams, Models, PointStruct, 
    QueryRequest
)
from tenacity import retry, wait_exponential, stop_after_attempt
from configs.settings import settings
from src.retrieval.base import Document

logger = logging.getLogger(__name__)

class QdrantManager:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        try:
            kwargs = {"url": settings.QDRANT_URL}
            if settings.QDRANT_API_KEY:
                kwargs["api_key"] = settings.QDRANT_API_KEY
            self.client = AsyncQdrantClient(**kwargs)
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            self.client = None

    async def setup_collection(self):
        if not self.client:
            return
            
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)
            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "dense": VectorParams(size=1536, distance=Distance.COSINE),
                        # SPLADE/Sparse vectors don't need size/distance in the same way in newer Qdrant, 
                        # but we define sparse_vectors config here for full hybrid.
                    },
                    sparse_vectors_config={
                        "sparse": Models.SparseVectorParams()
                    }
                )
                logger.info("Collection created.")
        except Exception as e:
            logger.error(f"Error setting up Qdrant collection: {e}")

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    async def async_search(
        self, 
        query_vector: List[float], 
        sparse_vector: Optional[Dict[str, float]], 
        top_k: int = 20
    ) -> List[Document]:
        if not self.client:
            logger.warning("Qdrant client not initialized.")
            return []
            
        try:
            # Prepare search requests for hybrid search if sparse vector is available
            requests = []
            
            # Dense search request
            requests.append(
                QueryRequest(
                    query=query_vector,
                    using="dense",
                    limit=top_k,
                    with_payload=True
                )
            )
            
            # Sparse search request
            if sparse_vector:
                indices = []
                values = []
                for k, v in sparse_vector.items():
                    indices.append(int(k))
                    values.append(float(v))
                    
                requests.append(
                    QueryRequest(
                        query=Models.SparseVector(
                            indices=indices,
                            values=values
                        ),
                        using="sparse",
                        limit=top_k,
                        with_payload=True
                    )
                )

            # In newer Qdrant clients, we can use search_batch for multiple queries
            # or prefetch for true hybrid. For simplicity and broad compatibility, 
            # we'll execute batch search using query_batch_points:
            results = await self.client.query_batch_points(
                collection_name=self.collection_name,
                requests=requests
            )
            
            docs = []
            # results is a list of lists of ScoredPoint
            for batch_result in results:
                for hit in batch_result:
                    payload = hit.payload or {}
                    docs.append(Document(
                        id=str(hit.id),
                        content=payload.get("content", ""),
                        metadata=payload,
                        score=hit.score
                    ))
                    
            return docs
            
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            raise

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
    async def upsert(self, points: List[PointStruct]):
        if not self.client:
            return
        await self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

qdrant_manager = QdrantManager()
