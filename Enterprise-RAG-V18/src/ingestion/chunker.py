# src/ingestion/chunker.py
import logging
from typing import List
import json
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.retrieval.base import Document
from src.llm.gateway import llm_gateway
from src.llm.model_router import TaskType
from langchain_core.prompts import PromptTemplate
from prometheus_client import Gauge
from configs.settings import settings

logger = logging.getLogger(__name__)

chunk_rejection_gauge = Gauge(
    "rag_chunk_rejection_rate",
    "Rate of chunks rejected by the ingestion quality gate"
)

class DocumentChunker:
    def __init__(self):
        self.embeddings = llm_gateway.get_embeddings()
        
    def chunk(self, documents: List[Document]) -> List[Document]:
        logger.info(f"Chunking {len(documents)} documents using {settings.CHUNKING_STRATEGY} strategy.")
        
        try:
            if settings.CHUNKING_STRATEGY == "semantic":
                splitter = SemanticChunker(self.embeddings, breakpoint_threshold_type="percentile")
            else:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=settings.CHUNK_SIZE, 
                    chunk_overlap=settings.CHUNK_OVERLAP
                )
                
            chunks = []
            for doc in documents:
                # SemanticChunker creates text strings usually
                texts = splitter.split_text(doc.content)
                for i, text in enumerate(texts):
                    chunks.append(Document(
                        id=f"{doc.id}_c{i}",
                        content=text,
                        metadata={**doc.metadata, "chunk_index": i, "parent_id": doc.id}
                    ))
            
            logger.info(f"Created {len(chunks)} chunks.")
            return chunks
        except Exception as e:
            logger.error(f"Semantic chunking failed, falling back to recursive: {e}")
            # Fallback
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE, 
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            chunks = []
            for doc in documents:
                texts = splitter.split_text(doc.content)
                for i, text in enumerate(texts):
                    chunks.append(Document(
                        id=f"{doc.id}_c{i}",
                        content=text,
                        metadata={**doc.metadata, "chunk_index": i, "parent_id": doc.id}
                    ))
            return chunks

    async def apply_quality_gate(self, chunks: List[Document]) -> List[Document]:
        """Feature E: Ingestion Quality Gate"""
        logger.info(f"Applying quality gate to {len(chunks)} chunks.")
        llm = llm_gateway.get_llm(task=TaskType.JSON_STRUCTURED, temperature=0.0)
        
        prompt = PromptTemplate.from_template(
            """Evaluate the quality of these text chunks for a Kubernetes knowledge base.
Is each coherent, informative, and free of excessive boilerplate?
Give a score between 0.0 and 1.0 for each index.

Chunks:
{chunks_str}

Output strictly valid JSON mapping index to score: {{"1": 0.0, "2": 0.0}}"""
        )
        
        chain = prompt | llm
        
        passed_chunks = []
        rejected = 0
        
        # Filter too-short chunks immediately
        valid_chunks = [c for c in chunks if len(c.content.split()) >= 10]
        rejected += (len(chunks) - len(valid_chunks))
        
        if not valid_chunks:
            return []
            
        chunks_str = "\n".join([f"[{i+1}] {c.content}" for i, c in enumerate(valid_chunks)])
        
        try:
            res = await chain.ainvoke({"chunks_str": chunks_str})
            parsed = json.loads(res.content)
            
            for i, chunk in enumerate(valid_chunks):
                score = float(parsed.get(str(i+1), 0.0))
                if score >= 0.3:
                    passed_chunks.append(chunk)
                else:
                    rejected += 1
        except Exception as e:
            logger.error(f"Error in batch quality gate: {e}")
            passed_chunks.extend(valid_chunks) # pass on failure
                
        rejection_rate = rejected / len(chunks) if chunks else 0.0
        logger.info(f"Quality gate passed {len(passed_chunks)} chunks, rejected {rejected}. Rejection rate: {rejection_rate:.2f}")
        chunk_rejection_gauge.set(rejection_rate)
        return passed_chunks

document_chunker = DocumentChunker()
