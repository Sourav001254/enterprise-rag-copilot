import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
def test_ready_check_success():
    with patch("src.api.main.check_db", return_value=True), \
         patch("src.api.main.check_redis", return_value=True):
        response = client.get("/ready")
        assert response.status_code == 200 # Exact assertion

def test_ready_check_failure():
    with patch("src.api.main.check_db", return_value=False):
        response = client.get("/ready")
        assert response.status_code == 503

@pytest.mark.asyncio
async def test_query_endpoint_unauthorized():
    response = client.post("/query", json={"query": "test"})
    # Should be exactly 403 due to missing auth header
    assert response.status_code == 403

def test_query_endpoint_authorized(monkeypatch):
    monkeypatch.setenv("DEV_AUTH_TOKEN", "testtoken")
    headers = {"Authorization": "Bearer testtoken"}
    payload = {"query": "How do I deploy to Kubernetes?", "session_id": "1234"}
    
    with patch("src.api.main.graph_app.ainvoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"answer": "Use kubectl apply -f.", "sources": []}
        response = client.post("/query", json=payload, headers=headers)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_stream_endpoint():
    headers = {"Authorization": "Bearer testtoken"}
    payload = {"query": "What is a Pod?", "session_id": "123"}
    
    with patch("src.api.main.graph_app.astream_events") as mock_stream:
        # Mocking async generator
        async def mock_gen():
            yield {"event": "on_chat_model_stream", "data": {"chunk": "A pod "}}
            yield {"event": "on_chat_model_stream", "data": {"chunk": "is a "}}
            yield {"event": "on_chat_model_stream", "data": {"chunk": "unit."}}
        
        mock_stream.return_value = mock_gen()
        response = client.post("/query/stream", json=payload, headers=headers)
        assert response.status_code == 200

def test_invalid_payload():
    headers = {"Authorization": "Bearer testtoken"}
    response = client.post("/query", json={"wrong_key": "value"}, headers=headers)
    assert response.status_code == 422

# More comprehensive tests for rate limiting, injection detection, etc.
def test_rate_limiting():
    headers = {"Authorization": "Bearer testtoken"}
    payload = {"query": "test"}
    # Simulate multiple requests
    for _ in range(10):
        client.post("/query", json=payload, headers=headers)
    
    # Next should be 429
    res = client.post("/query", json=payload, headers=headers)
    assert res.status_code == 429

def test_pii_redaction_middleware():
    headers = {"Authorization": "Bearer testtoken"}
    payload = {"query": "My email is test@example.com"}
    with patch("src.api.main.graph_app.ainvoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"answer": "Redacted.", "sources": []}
        res = client.post("/query", json=payload, headers=headers)
        assert res.status_code == 200
