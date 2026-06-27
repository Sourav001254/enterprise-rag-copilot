# src/llm/semantic_cache.py
import logging

logger = logging.getLogger(__name__)

class SemanticCache:
    def __init__(self):
        self._initialized = False

    def init_cache(self):
        if self._initialized:
            return
            
        logger.info("GPTCache semantic caching is currently disabled in this environment.")
        self._initialized = True

semantic_cache = SemanticCache()
