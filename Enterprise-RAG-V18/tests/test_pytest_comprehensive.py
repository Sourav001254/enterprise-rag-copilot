import pytest
import hashlib
from src.agents.rrf import compute_rrf
from src.retrieval.base import Document
from src.cache.redis_cache import redis_cache
from src.security.pipeline import run_input_pipeline
from src.agents.intent_router import intent_router_node
from src.agents.state import AgentState

@pytest.mark.asyncio
async def test_cache_key_hashing():
    seed = "query_string"
    hashed = redis_cache._hash_key(seed)
    assert hashed == hashlib.sha256(seed.encode("utf-8")).hexdigest()

def test_rrf_scoring():
    d1 = Document(id="docA", content="First document", score=0.9)
    d2 = Document(id="docB", content="Second document", score=0.8)
    
    list_dense = [d1, d2]
    list_sparse = [d2, d1]
    
    fused = compute_rrf([list_dense, list_sparse], k=60)
    assert len(fused) == 2
    # docB gets rank 2 in dense (score 1/62) + rank 1 in sparse (score 1/61)
    # docA gets rank 1 in dense (score 1/61) + rank 2 in sparse (score 1/62)
    # So they should be tied exactly!
    assert fused[0].score == pytest.approx(fused[1].score)

@pytest.mark.asyncio
async def test_sql_validator_pipeline():
    claims = {"sub": "user", "roles": []}
    safe_res = await run_input_pipeline("Show me the logs", claims)
    assert safe_res.safe is True

    unsafe_res = await run_input_pipeline("DROP TABLE users;", claims)
    assert unsafe_res.safe is False
    assert "Injection" in unsafe_res.reason

@pytest.mark.asyncio
async def test_graph_integration_mock(mocker):
    # Mock LLM gateway
    mock_llm = mocker.AsyncMock()
    mock_llm.ainvoke.return_value.content = '{"intent": "rag", "complexity": "simple"}'
    mocker.patch("src.llm.gateway.llm_gateway.get_llm", return_value=mock_llm)
    
    state = AgentState(query="What is a pod?", intent="", complexity="")
    new_state = await intent_router_node(state)
    
    assert new_state["intent"] == "rag"
    assert new_state["complexity"] == "simple"
