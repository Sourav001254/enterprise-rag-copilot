import pytest
from unittest.mock import patch, AsyncMock
from src.agents.state import AgentState
from src.agents.hybrid_retrieval import hybrid_retrieval_node
from src.agents.rrf import rrf_node
from src.retrieval.base import Document

@pytest.mark.asyncio
async def test_hybrid_retrieval():
    state = AgentState(query="test", query_vector=[0.1]*1536)
    
    with patch("src.retrieval.qdrant_client.QdrantRetriever.retrieve", new_callable=AsyncMock) as mock_dense, \
         patch("src.retrieval.bm25_index.BM25Retriever.retrieve", new_callable=AsyncMock) as mock_sparse:
        
        mock_dense.return_value = [Document(id="1", content="dense res")]
        mock_sparse.return_value = [Document(id="2", content="sparse res")]
        
        new_state = await hybrid_retrieval_node(state)
        assert "dense_docs" in new_state
        assert "sparse_docs" in new_state
        assert len(new_state["dense_docs"]) == 1

@pytest.mark.asyncio
async def test_rrf():
    state = AgentState(
        dense_docs=[Document(id="1", content="test1")], 
        sparse_docs=[Document(id="2", content="test2")]
    )
    
    new_state = await rrf_node(state)
    assert "retrieved_docs" in new_state
    # RRF should combine both sources
    assert len(new_state["retrieved_docs"]) > 0
