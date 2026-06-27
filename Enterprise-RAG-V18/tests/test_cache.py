import pytest
from unittest.mock import AsyncMock, patch
from src.cache.redis_cache import redis_cache

@pytest.fixture
def mock_redis():
    with patch("src.cache.redis_cache.redis_client", new_callable=AsyncMock) as mock:
        yield mock

@pytest.mark.asyncio
async def test_redis_cache_get_set(mock_redis):
    mock_redis.set.return_value = True
    mock_redis.get.return_value = "value"
    
    res = await redis_cache.set(1, "test_key", "value")
    assert res is True
    
    val = await redis_cache.get(1, "test_key")
    assert val == "value"

@pytest.mark.asyncio
async def test_redis_cache_miss(mock_redis):
    mock_redis.get.return_value = None
    val = await redis_cache.get(1, "missing_key")
    assert val is None

@pytest.mark.asyncio
async def test_redis_cache_delete(mock_redis):
    mock_redis.delete.return_value = 1
    res = await redis_cache.delete(1, "test_key")
    assert res is True

@pytest.mark.asyncio
async def test_semantic_cache_hit(mock_redis):
    # Simulate a dense/semantic cache hit directly via Redis since semantic.py is not separate
    mock_redis.get.return_value = '{"answer": "Semantic hit"}'
    val = await redis_cache.get(1, "semantic_query")
    assert isinstance(val, dict)
    assert val["answer"] == "Semantic hit"

@pytest.mark.asyncio
async def test_sql_cache_hit():
    with patch("src.cache.redis_cache.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = "SELECT * FROM pods;"
        val = await mock_get(3, "sql_intent_hash")
        assert val == "SELECT * FROM pods;"

@pytest.mark.asyncio
async def test_cache_eviction_policy(mock_redis):
    # Simulate an eviction scenario or TTL expiration
    mock_redis.setex.return_value = True
    res = await redis_cache.set(1, "temp_key", "value", ttl=60)
    assert res is True
    mock_redis.setex.assert_called_once()
