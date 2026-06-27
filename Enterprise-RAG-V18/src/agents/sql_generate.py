# src/agents/sql_generate.py
import logging
import json
from langchain_core.prompts import PromptTemplate
from src.agents.state import AgentState
from src.llm.gateway import llm_gateway
from src.llm.model_router import TaskType
from src.cache.redis_cache import redis_cache
from src.db.postgres import fetch_rows

logger = logging.getLogger(__name__)

async def _get_schema_context() -> str:
    # Feature G: SQL Schema Introspection Cache
    # Cache TTL 1 hour
    cached = await redis_cache.get(tier=3, content="db_schema_introspection")
    if cached and isinstance(cached, str):
        return cached
        
    try:
        sql = """
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            ORDER BY table_name, ordinal_position
        """
        rows = await fetch_rows(sql)
        
        schema_dict = {}
        for row in rows:
            t = row['table_name']
            c = row['column_name']
            dt = row['data_type']
            if t not in schema_dict:
                schema_dict[t] = []
            schema_dict[t].append(f"{c} ({dt})")
            
        schema_str = ""
        for t, cols in schema_dict.items():
            schema_str += f"Table: {t}\nColumns: {', '.join(cols)}\n\n"
            
        await redis_cache.set(tier=3, content="db_schema_introspection", value=schema_str)
        return schema_str
    except Exception as e:
        logger.error(f"Failed to introspect schema: {e}")
        return "Schema introspection failed."

async def sql_generate_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    
    # Check Redis L3 Cache for SQL String
    cached = await redis_cache.get(tier=3, content=query)
    if cached and isinstance(cached, dict) and "sql" in cached:
        logger.info("L3 Cache hit for SQL generation.")
        state["sql_query"] = cached["sql"]
        return state
        
    logger.info("Generating SQL query.")
    
    schema_context = await _get_schema_context()
    
    try:
        llm = llm_gateway.get_llm(task=TaskType.SQL_GENERATION, temperature=0.0)
        
        prompt = PromptTemplate.from_template(
            """You are a PostgreSQL expert. Write a SQL query to answer the user's question.
You MUST ONLY write SELECT statements. NEVER use DROP, INSERT, UPDATE, DELETE, or TRUNCATE.

Here is the database schema:
{schema}

Question: {query}

Output strictly valid JSON with a single key "sql" containing the query.
Example: {{"sql": "SELECT * FROM users;"}}"""
        )
        
        chain = prompt | llm
        res = await chain.ainvoke({"schema": schema_context, "query": query})
        
        try:
            parsed = json.loads(res.content)
            sql_query = parsed.get("sql", "")
        except Exception:
            sql_query = res.content.strip().strip("```sql").strip("```").strip()
            
        state["sql_query"] = sql_query
        
        # Save to L3 Cache
        await redis_cache.set(tier=3, content=query, value={"sql": sql_query})
        
        return state
    except Exception as e:
        logger.error(f"SQL Generate error: {e}")
        state["error"] = f"SQLGenerate: {str(e)}"
        state["sql_query"] = ""
        return state
