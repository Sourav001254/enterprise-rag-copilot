# src/agents/tavily_search.py
import logging
from langchain_community.tools.tavily_search import TavilySearchResults
from src.agents.state import AgentState
from src.retrieval.base import Document
from configs.settings import settings

logger = logging.getLogger(__name__)

async def tavily_search_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    
    if not state.get("web_search_used", False):
        return state
        
    logger.info(f"Falling back to Tavily Web Search for query: '{query}'")
    
    if not settings.TAVILY_API_KEY:
        logger.warning("Tavily API key not set. Skipping web search.")
        return state
        
    try:
        search = TavilySearchResults(max_results=3, api_key=settings.TAVILY_API_KEY)
        # Tavily node is synchronous in langchain, run in executor if needed, 
        # but ainvoke usually works
        results = await search.ainvoke({"query": query})
        
        web_docs = []
        for i, res in enumerate(results):
            web_docs.append(Document(
                id=f"web_{i}",
                content=res.get("content", ""),
                metadata={"source": res.get("url", "web"), "title": res.get("title", "")},
                score=1.0
            ))
            
        # Append to reranked_docs so it's used in answering
        current_docs = state.get("reranked_docs", [])
        state["reranked_docs"] = web_docs + current_docs
        
        return state
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        state["error"] = f"Tavily: {str(e)}"
        return state
