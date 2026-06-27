# src/agents/sql_validate.py
import logging
import sqlglot
from sqlglot import exp
from src.agents.state import AgentState

logger = logging.getLogger(__name__)

ALLOWED_TABLES = {
    "query_logs", "sessions", "users", "token_budgets", 
    "sql_approvals", "eval_results", "document_metadata"
}

def _check_subquery_depth(node, current_depth: int = 0) -> int:
    max_depth = current_depth
    if isinstance(node, exp.Select):
        max_depth = current_depth + 1
        
    for k, v in node.args.items():
        if isinstance(v, list):
            for child in v:
                if isinstance(child, exp.Expression):
                    max_depth = max(max_depth, _check_subquery_depth(child, current_depth + (1 if isinstance(node, exp.Select) else 0)))
        elif isinstance(v, exp.Expression):
            max_depth = max(max_depth, _check_subquery_depth(v, current_depth + (1 if isinstance(node, exp.Select) else 0)))
            
    return max_depth

async def sql_validate_node(state: AgentState) -> AgentState:
    sql = state.get("sql_query", "")
    
    if not sql:
        logger.warning("No SQL to validate.")
        state["error"] = "SQLValidate: Empty query"
        return state
        
    logger.info(f"Validating SQL: {sql}")
    
    try:
        parsed = sqlglot.parse_one(sql, read="postgres")
        
        # 1. Reject non-SELECT
        if not isinstance(parsed, exp.Select):
            raise ValueError("Only SELECT statements are allowed.")
            
        # 2. Check table allowlist
        for table in parsed.find_all(exp.Table):
            table_name = table.name.lower()
            if table_name not in ALLOWED_TABLES:
                raise ValueError(f"Table '{table_name}' is not in allowlist.")
                
        # 3. Check subquery depth (> 3 rejected)
        depth = _check_subquery_depth(parsed)
        if depth > 3:
            raise ValueError(f"Subquery depth {depth} exceeds maximum of 3.")
            
        logger.info("SQL Validation passed.")
        return state
        
    except Exception as e:
        logger.error(f"SQL Validation failed: {e}")
        state["error"] = f"SQLValidate: {str(e)}"
        return state
