# src/ingestion/pipeline.py
import logging
import uuid
from typing import Optional
from qdrant_client.http.models import PointStruct
from src.ingestion.loaders import DocumentLoader
from src.ingestion.deduplicator import deduplicator
from src.ingestion.chunker import document_chunker
from src.ingestion.embedder import batch_embedder
from src.retrieval.qdrant_client import qdrant_manager
from src.retrieval.bm25_index import bm25_index
from src.security.prompt_shield import prompt_shield

logger = logging.getLogger(__name__)

class IngestionPipeline:
    @staticmethod
    async def run(directory_path: str) -> dict:
        logger.info(f"Starting ingestion pipeline for directory: {directory_path}")
        
        # 1. Load
        raw_docs = DocumentLoader.load_directory(directory_path)
        if not raw_docs:
            return {"status": "error", "message": "No documents found."}
            
        # 2. Clean
        for doc in raw_docs:
            doc.content = prompt_shield.clean(doc.content)
            
        # 3. Dedup
        unique_docs = await deduplicator.get_unique_documents(raw_docs)
        if not unique_docs:
            return {"status": "success", "message": "No new documents to process.", "documents_processed": 0, "chunks_created": 0}
            
        # 4. Semantic Chunk
        chunks = document_chunker.chunk(unique_docs)
        
        # Feature E: Quality Gate
        chunks = await document_chunker.apply_quality_gate(chunks)
        
        if not chunks:
            return {"status": "error", "message": "All chunks rejected by quality gate."}
            
        # 5 & 6. Embed (Dense + Sparse)
        dense_vectors, sparse_vectors = await batch_embedder.embed_documents(chunks)
        
        # 7. Upsert to Qdrant
        points = []
        for i, chunk in enumerate(chunks):
            # Qdrant expects points formatted for named vectors
            vector_data = {
                "dense": dense_vectors[i]
            }
            if sparse_vectors[i]:
                # Qdrant sparse vector format
                indices = [int(k) for k in sparse_vectors[i].keys()]
                values = [float(v) for v in sparse_vectors[i].values()]
                vector_data["sparse"] = {"indices": indices, "values": values}
                
            points.append(PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.id)),
                vector=vector_data,
                payload={"content": chunk.content, **chunk.metadata}
            ))
            
        await qdrant_manager.upsert(points)
        
        # 8. Rebuild BM25 Index
        # We explicitly load the index if it exists, so we don't drop existing chunks if the pipeline restarted
        if not bm25_index.documents:
            bm25_index.load_index("bm25_index.json")
            
        existing_docs = bm25_index.documents
        bm25_index.build_index(existing_docs + chunks, save_path="bm25_index.json")
        
        # 9. Log
        await deduplicator.log_processed_documents(unique_docs, chunks_per_doc=len(chunks)//len(unique_docs) if unique_docs else 1)
        
        logger.info("Ingestion pipeline completed successfully.")
        return {
            "status": "success",
            "documents_processed": len(unique_docs),
            "chunks_created": len(chunks)
        }
