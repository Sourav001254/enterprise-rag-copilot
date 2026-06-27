# src/agents/intent_router.py
import logging
import json
from langchain_core.prompts import PromptTemplate
from src.agents.state import AgentState
from src.cache.redis_cache import redis_cache
from src.llm.gateway import llm_gateway
from src.llm.model_router import TaskType

logger = logging.getLogger(__name__)

async def intent_router_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    logger.info(f"Routing intent for query: '{query}'")
    
    try:
        # Check Redis L2 Cache
        cached = await redis_cache.get(2, query)
        if cached and isinstance(cached, dict):
            logger.info(f"Intent cache hit: {cached}")
            state["intent"] = cached.get("intent", "rag")
            state["complexity"] = cached.get("complexity", "simple")
            return state

        llm = llm_gateway.get_llm(task=TaskType.JSON_STRUCTURED, temperature=0.0)
        
        from configs.prompts import INTENT_ROUTER_PROMPT
        prompt = PromptTemplate.from_template(INTENT_ROUTER_PROMPT)
        
        chain = prompt | llm
        result = await chain.ainvoke({"query": query})
        
        try:
            parsed = json.loads(result.content)
            intent = parsed.get("intent", "rag")
            complexity = parsed.get("complexity", "simple")
        except Exception:
            intent = "rag"
            complexity = "complex"
            
        state["intent"] = intent
        state["complexity"] = complexity
        
        # Save to L2 cache
        await redis_cache.set(2, query, {"intent": intent, "complexity": complexity})
        
        return state
    except Exception as e:
        logger.error(f"Intent router error: {e}")
        state["error"] = f"IntentRouter: {str(e)}"
        state["intent"] = "rag" # safe fallback
        state["complexity"] = "complex"
        return state
