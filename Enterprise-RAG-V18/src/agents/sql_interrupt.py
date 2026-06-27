# src/agents/sql_interrupt.py
import logging
from langgraph.types import interrupt
from src.agents.state import AgentState

logger = logging.getLogger(__name__)

async def sql_interrupt_node(state: AgentState) -> AgentState:
    sql = state.get("sql_query", "")
    
    if not sql or state.get("error"):
        return state
        
    logger.info("Interrupting execution for SQL approval.")
    
    # We call interrupt, returning the SQL query to the human.
    # The human will resume the graph via POST /sql/approve, providing the approved status.
    response = interrupt({
        "action": "approve_sql",
        "sql_query": sql,
        "message": "Please approve the execution of this SQL query."
    })
    
    # The response is what the human provides when resuming
    approved = response.get("approved", False)
    
    if not approved:
        logger.warning("SQL execution rejected by human.")
        state["sql_approved"] = False
        state["error"] = "SQL execution rejected by human."
    else:
        logger.info("SQL execution approved by human.")
        state["sql_approved"] = True
        
    return state
