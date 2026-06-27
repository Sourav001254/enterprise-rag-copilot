# src/ingestion/loaders.py
import logging
import os
from typing import List
from langchain_community.document_loaders import UnstructuredFileLoader, DirectoryLoader
from src.retrieval.base import Document

logger = logging.getLogger(__name__)

class DocumentLoader:
    @staticmethod
    def load_directory(directory_path: str, glob_pattern: str = "**/*.*") -> List[Document]:
        """Load PDFs, MDs, HTML, TXT files using Unstructured."""
        if not os.path.exists(directory_path):
            logger.error(f"Directory {directory_path} does not exist.")
            return []
            
        logger.info(f"Loading documents from {directory_path} with pattern {glob_pattern}")
        try:
            # We use UnstructuredLoader under the hood via DirectoryLoader
            loader = DirectoryLoader(
                directory_path, 
                glob=glob_pattern,
                show_progress=True,
                use_multithreading=True
            )
            raw_docs = loader.load()
            
            # Convert to our schema
            documents = []
            for i, d in enumerate(raw_docs):
                documents.append(Document(
                    id=f"doc_{i}",
                    content=d.page_content,
                    metadata=d.metadata
                ))
            
            logger.info(f"Loaded {len(documents)} raw documents.")
            return documents
        except Exception as e:
            logger.error(f"Error loading directory: {e}")
            return []
