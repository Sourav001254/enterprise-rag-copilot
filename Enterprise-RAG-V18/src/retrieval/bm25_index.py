# src/retrieval/bm25_index.py
import json
import logging
from typing import List
from rank_bm25 import BM25Okapi
import nltk
from src.retrieval.base import Document

logger = logging.getLogger(__name__)

class BM25IndexManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BM25IndexManager, cls).__new__(cls)
            cls._instance.bm25 = None
            cls._instance.documents = []
            try:
                nltk.download('punkt', quiet=True)
            except Exception as e:
                logger.warning(f"Could not download NLTK punkt: {e}")
        return cls._instance

    def load_index(self, path: str = "bm25_index.json") -> bool:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.documents = [Document(**doc) for doc in data['documents']]
                
            tokenized_corpus = [nltk.word_tokenize(doc.content.lower()) for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_corpus)
            logger.info(f"BM25 index loaded with {len(self.documents)} documents.")
            return True
        except FileNotFoundError:
            logger.warning(f"BM25 index file not found at {path}. Initializing empty index.")
            self.documents = []
            self.bm25 = None
            return False
        except Exception as e:
            logger.error(f"Error loading BM25 index: {e}. Initializing empty index.")
            self.documents = []
            self.bm25 = None
            return False

    def build_index(self, documents: List[Document], save_path: str = "bm25_index.json"):
        self.documents = documents
        tokenized_corpus = [nltk.word_tokenize(doc.content.lower()) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "documents": [doc.model_dump() for doc in self.documents]
                }, f)
            logger.info(f"BM25 index built and saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save BM25 index to {save_path}: {e}")

    async def search(self, query: str, top_k: int = 20) -> List[Document]:
        if not self.bm25:
            logger.warning("BM25 index not initialized. Returning empty.")
            return []
            
        tokenized_query = nltk.word_tokenize(query.lower())
        doc_scores = self.bm25.get_scores(tokenized_query)
        
        # Get top_k indices
        top_n = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
        
        results = []
        for i in top_n:
            if doc_scores[i] > 0:
                doc = self.documents[i].model_copy()
                doc.score = float(doc_scores[i])
                results.append(doc)
                
        return results

bm25_index = BM25IndexManager()
