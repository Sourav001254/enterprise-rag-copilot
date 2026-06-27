# src/ingestion/embedder.py
import logging
import asyncio
from typing import List, Dict, Tuple
from fastembed import SparseTextEmbedding
from src.retrieval.base import Document
from src.llm.gateway import llm_gateway
from src.cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)

class BatchEmbedder:
    def __init__(self):
        self.embeddings = llm_gateway.get_embeddings()
        try:
            # SPLADE model for sparse vectors
            self.sparse_model = SparseTextEmbedding(model_name="prithvida/Splade_PP_en_v1")
        except Exception as e:
            logger.error(f"Failed to load SparseTextEmbedding: {e}")
            self.sparse_model = None

    async def _embed_dense_batch(self, texts: List[str]) -> List[List[float]]:
        # Fast path checking cache
        results = [None] * len(texts)
        missing_indices = []
        missing_texts = []
        
        for i, text in enumerate(texts):
            cached = await redis_cache.get(tier=1, content=text)
            if cached:
                results[i] = cached
            else:
                missing_indices.append(i)
                missing_texts.append(text)
                
        if missing_texts:
            logger.debug(f"Embedding {len(missing_texts)} missing items from API")
            new_embeddings = await self.embeddings.aembed_documents(missing_texts)
            
            for idx, emb, text in zip(missing_indices, new_embeddings, missing_texts):
                results[idx] = emb
                await redis_cache.set(tier=1, content=text, value=emb)
                
        return results
        
    def _embed_sparse_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        if not self.sparse_model:
            return [{}] * len(texts)
            
        # fastembed is synchronous generator
        sparse_results = list(self.sparse_model.embed(texts))
        
        formatted_sparse = []
        for res in sparse_results:
            # res has .indices and .values
            indices = res.indices.tolist()
            values = res.values.tolist()
            # Convert to dictionary of str -> float
            sparse_dict = {str(k): float(v) for k, v in zip(indices, values)}
            formatted_sparse.append(sparse_dict)
            
        return formatted_sparse

    async def embed_documents(self, documents: List[Document], batch_size: int = 100) -> Tuple[List[List[float]], List[Dict[str, float]]]:
        logger.info(f"Embedding {len(documents)} documents (batch size {batch_size})...")
        
        all_dense = []
        all_sparse = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            texts = [doc.content for doc in batch]
            
            # Run dense and sparse in parallel
            dense_task = self._embed_dense_batch(texts)
            # Sparse is sync but wrapped fast enough or run in executor
            sparse_task = asyncio.to_thread(self._embed_sparse_batch, texts)
            
            dense_res, sparse_res = await asyncio.gather(dense_task, sparse_task)
            
            all_dense.extend(dense_res)
            all_sparse.extend(sparse_res)
            
            logger.info(f"Embedded batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
        return all_dense, all_sparse

batch_embedder = BatchEmbedder()
