import pytest
from src.agents.state import AgentState
from src.agents.self_rag_reflect import self_rag_reflect_node
from src.llm.gateway import llm_gateway
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_self_rag_reflect():
    state = AgentState(query="test", answer="good answer", self_rag_attempts=0)
    
    with patch("src.llm.gateway.llm_gateway.get_llm") as mock_get:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value.content = '{"score": 0.9}'
        mock_get.return_value = mock_llm
        
        new_state = await self_rag_reflect_node(state)
        assert new_state["self_rag_score"] == 0.9
        assert new_state["self_rag_attempts"] == 1
