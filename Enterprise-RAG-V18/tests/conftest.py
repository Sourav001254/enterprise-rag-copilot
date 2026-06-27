# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_redis():
    with patch("src.cache.redis_cache.redis_cache.get", new_callable=AsyncMock) as mock_get:
        with patch("src.cache.redis_cache.redis_cache.set", new_callable=AsyncMock) as mock_set:
            mock_get.return_value = None
            mock_set.return_value = True
            yield {"get": mock_get, "set": mock_set}

@pytest.fixture
def mock_postgres():
    with patch("src.db.postgres.execute_query", new_callable=AsyncMock) as mock_exec:
        with patch("src.db.postgres.fetch_rows", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []
            yield {"execute": mock_exec, "fetch": mock_fetch}

@pytest.fixture
def mock_llm_gateway():
    with patch("src.llm.gateway.llm_gateway.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '{"intent": "rag", "complexity": "simple"}'
        mock_get_llm.return_value = mock_llm
        yield mock_get_llm
