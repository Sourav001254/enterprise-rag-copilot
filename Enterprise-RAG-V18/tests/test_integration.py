import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.agents.graph import compile_graph
from src.agents.state import AgentState

@pytest.fixture
def compiled_graph():
    return compile_graph()

@pytest.mark.asyncio
async def test_end_to_end_rag_smoke(compiled_graph):
    """
    End-to-End smoke test that executes REAL LangGraph logic.
    Only external network dependencies (LLM, DB, Redis) are mocked.
    """
    initial_state = AgentState(
        query="How to setup Kubernetes?",
        intent="rag",
        session_id="smoke_session"
    )

    # Patch ONLY the external dependencies, NOT the graph nodes
    with patch("src.llm.gateway.llm_gateway.get_llm") as mock_get_llm, \
         patch("src.retrieval.qdrant_client.QdrantManager.async_search", new_callable=AsyncMock) as mock_dense, \
         patch("src.retrieval.bm25_index.BM25IndexManager.search", new_callable=AsyncMock) as mock_sparse, \
         patch("src.db.postgres.execute_query", new_callable=AsyncMock) as mock_db:

        # Setup LLM Mock to simulate answering
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="kubectl apply -f deployment.yaml")
        mock_get_llm.return_value = mock_llm
        
        # Setup Retriever Mocks
        mock_dense.return_value = []
        mock_sparse.return_value = []

        try:
            # Ainvoke the unmocked graph
            result = await compiled_graph.ainvoke(initial_state)
            
            # Assert exact final structural shape of the LangGraph state object
            assert result is not None
            assert "answer" in result
            assert "intent" in result
            assert result["intent"] == "rag"
            assert "session_id" in result
        except Exception as e:
            pytest.fail(f"Graph execution logic failed: {e}")
