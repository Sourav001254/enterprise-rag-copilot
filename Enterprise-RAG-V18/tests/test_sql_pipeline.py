import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.agents.state import AgentState
from src.agents.sql_generate import sql_generate_node
from src.agents.sql_execute import sql_execute_node

@pytest.mark.asyncio
async def test_sql_generate():
    state = AgentState(query="Show me tokens", intent="sql")
    with patch("src.llm.gateway.llm_gateway.get_llm") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="SELECT * FROM tokens;")
        mock_get_llm.return_value = mock_llm
        
        new_state = await sql_generate_node(state)
        assert "sql_query" in new_state
        assert new_state["sql_query"] == "SELECT * FROM tokens;"

@pytest.mark.asyncio
async def test_sql_execute():
    state = AgentState(sql_query="SELECT 1;", intent="sql")
    with patch("src.db.postgres.execute_query", new_callable=AsyncMock) as mock_exec, \
         patch("src.db.postgres.fetch_rows", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [{"col": 1}]
        
        # Test requires logic to be implemented, but we verify the state mutation
        # Depending on how sql_execute_node handles db interactions
        new_state = await sql_execute_node(state)
        assert "db_results" in new_state
        assert new_state["db_results"] == [{"col": 1}]
