# src/agents/sql_execute.py
import logging
import json
from src.agents.state import AgentState
from src.db.postgres import fetch_rows
from src.cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)

async def sql_execute_node(state: AgentState) -> AgentState:
    if not state.get("sql_approved", False):
        logger.warning("SQL not approved, skipping execution.")
        state["sql_result"] = []
        return state
        
    sql = state.get("sql_query", "")
    
    # Check L4 cache for result
    cached = await redis_cache.get(tier=4, content=sql)
    if cached:
        logger.info("L4 Cache hit for SQL result.")
        state["sql_result"] = cached
        return state
        
    logger.info(f"Executing SQL: {sql}")
    
    try:
        # fetch_rows uses asyncpg connection pool with 30s timeout configured in pool
        rows = await fetch_rows(sql)
        
        # Convert to list of dicts for JSON serialization
        result = []
        for r in rows:
            result.append(dict(r))
            
        state["sql_result"] = result
        
        # Save to L4 cache
        await redis_cache.set(tier=4, content=sql, value=result)
        
        return state
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        state["error"] = f"SQLExecute: {str(e)}"
        state["sql_result"] = []
        return state
