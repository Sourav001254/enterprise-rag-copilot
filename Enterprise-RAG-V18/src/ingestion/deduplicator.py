# src/ingestion/deduplicator.py
import logging
import hashlib
from typing import List
from src.retrieval.base import Document
from src.db.postgres import fetch_rows, execute_query

logger = logging.getLogger(__name__)

class Deduplicator:
    @staticmethod
    async def get_unique_documents(documents: List[Document]) -> List[Document]:
        logger.info(f"Deduplicating {len(documents)} documents against Postgres.")
        
        unique_docs = []
        hashes = []
        
        for doc in documents:
            content_hash = hashlib.sha256(doc.content.encode('utf-8')).hexdigest()
            doc.metadata["content_hash"] = content_hash
            hashes.append(content_hash)
            
        if not hashes:
            return []
            
        # Check DB in a single batch
        sql = "SELECT content_hash FROM document_metadata WHERE content_hash = ANY($1::text[])"
        rows = await fetch_rows(sql, hashes)
        existing_hashes = {row["content_hash"] for row in rows}
        
        for doc in documents:
            if doc.metadata["content_hash"] not in existing_hashes:
                unique_docs.append(doc)
                
        logger.info(f"Found {len(unique_docs)} unique documents out of {len(documents)}.")
        return unique_docs
        
    @staticmethod
    async def log_processed_documents(documents: List[Document], chunks_per_doc: int = 1):
        for doc in documents:
            try:
                content_hash = doc.metadata.get("content_hash")
                source = doc.metadata.get("source", "unknown")
                
                sql = """
                    INSERT INTO document_metadata (content_hash, source, chunk_count)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (content_hash) DO NOTHING
                """
                await execute_query(sql, content_hash, source, chunks_per_doc)
            except Exception as e:
                logger.error(f"Failed to log document metadata to DB: {e}")

deduplicator = Deduplicator()
