import pytest
from src.llm.semantic_cache import semantic_cache

def test_semantic_cache_init():
    assert semantic_cache._initialized is False
    semantic_cache.init_cache()
    assert semantic_cache._initialized is True
    
    # Repeated call should not change state but just return
    semantic_cache.init_cache()
    assert semantic_cache._initialized is True
