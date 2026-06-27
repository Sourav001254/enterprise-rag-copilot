# src/agents/hyde.py
import logging
import asyncio
from langchain_core.prompts import PromptTemplate
from src.agents.state import AgentState
from src.llm.gateway import llm_gateway
from src.llm.model_router import TaskType
from configs.settings import settings

logger = logging.getLogger(__name__)

async def _generate_single_hyde(query: str, llm) -> str:
    prompt = PromptTemplate.from_template(
        "Write a hypothetical, plausible, and highly technical Kubernetes SRE answer to the following question. "
        "Do not include pleasantries. Just the technical explanation.\n\nQuestion: {query}"
    )
    chain = prompt | llm
    res = await chain.ainvoke({"query": query})
    return res.content

async def hyde_node(state: AgentState) -> AgentState:
    if state.get("complexity") == "simple":
        logger.info("Query complexity is simple. Skipping HyDE.")
        state["hyde_queries"] = []
        return state

    query = state.get("query", "")
    logger.info(f"Generating {settings.HYDE_NUM_QUERIES} HyDE queries for: '{query}'")
    
    try:
        llm = llm_gateway.get_llm(task=TaskType.FAST, temperature=0.7)
        
        tasks = [_generate_single_hyde(query, llm) for _ in range(settings.HYDE_NUM_QUERIES)]
        hypothetical_answers = await asyncio.gather(*tasks, return_exceptions=True)
        
        hyde_queries = []
        for ans in hypothetical_answers:
            if isinstance(ans, Exception):
                logger.warning(f"HyDE generation failed for one instance: {ans}")
            else:
                hyde_queries.append(ans)
                
        state["hyde_queries"] = hyde_queries
        return state
    except Exception as e:
        logger.error(f"HyDE error: {e}")
        state["error"] = f"HyDE: {str(e)}"
        state["hyde_queries"] = []
        return state
