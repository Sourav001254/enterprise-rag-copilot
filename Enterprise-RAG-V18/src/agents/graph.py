# src/agents/graph.py
import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END
from src.agents.state import AgentState
from src.agents.intent_router import intent_router_node
from src.agents.hyde import hyde_node
from src.agents.embed_query import embed_query_node
from src.agents.hybrid_retrieval import hybrid_retrieval_node
from src.agents.rrf import rrf_node
from src.agents.reranker import rerank_node
from src.agents.crag_grader import crag_grader_node
from src.agents.tavily_search import tavily_search_node
from src.agents.spotlighting import spotlighting_node
from src.agents.rewriter import rewriter_node
from src.agents.sql_generate import sql_generate_node
from src.agents.sql_validate import sql_validate_node
from src.agents.sql_interrupt import sql_interrupt_node
from src.agents.sql_execute import sql_execute_node
from src.agents.llm_answer import llm_answer_node
from src.agents.self_rag_reflect import self_rag_reflect_node
from src.agents.finalize import finalize_node
from configs.settings import settings

logger = logging.getLogger(__name__)

def route_intent(state: AgentState) -> str:
    intent = state.get("intent", "rag")
    if intent in ["rag", "hybrid"]:
        return "hyde"
    elif intent == "sql":
        return "sql_generate"
    else:
        return "finalize"

def route_crag(state: AgentState) -> str:
    if state.get("context_sufficient", False):
        return "spotlighting"
    elif state.get("retrieval_attempts", 0) < settings.RETRIEVAL_MAX_ATTEMPTS:
        return "rewriter"
    elif state.get("crag_score", 0.0) < settings.CRAG_SCORE_THRESHOLD:
        return "tavily_search"
    else:
        return "spotlighting"

def route_self_rag(state: AgentState) -> str:
    if state.get("self_rag_score", 0.0) < settings.SELF_RAG_SCORE_THRESHOLD and state.get("self_rag_attempts", 0) < settings.SELF_RAG_MAX_ATTEMPTS:
        return "llm_answer"
    return "finalize"

def compile_graph(checkpointer=None):
    logger.info("Compiling LangGraph state machine...")
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("hyde", hyde_node)
    workflow.add_node("embed_query", embed_query_node)
    workflow.add_node("hybrid_retrieval", hybrid_retrieval_node)
    workflow.add_node("rrf", rrf_node)
    workflow.add_node("rerank", rerank_node)
    workflow.add_node("crag_grader", crag_grader_node)
    workflow.add_node("tavily_search", tavily_search_node)
    workflow.add_node("spotlighting", spotlighting_node)
    workflow.add_node("rewriter", rewriter_node)
    workflow.add_node("sql_generate", sql_generate_node)
    workflow.add_node("sql_validate", sql_validate_node)
    workflow.add_node("sql_interrupt", sql_interrupt_node)
    workflow.add_node("sql_execute", sql_execute_node)
    workflow.add_node("llm_answer", llm_answer_node)
    workflow.add_node("self_rag_reflect", self_rag_reflect_node)
    workflow.add_node("finalize", finalize_node)
    
    # Add edges
    workflow.add_edge(START, "intent_router")
    
    workflow.add_conditional_edges(
        "intent_router",
        route_intent,
        {
            "hyde": "hyde",
            "sql_generate": "sql_generate",
            "finalize": "finalize"
        }
    )
    
    # RAG Pipeline
    workflow.add_edge("hyde", "embed_query")
    workflow.add_edge("embed_query", "hybrid_retrieval")
    workflow.add_edge("hybrid_retrieval", "rrf")
    workflow.add_edge("rrf", "rerank")
    workflow.add_edge("rerank", "crag_grader")
    
    workflow.add_conditional_edges(
        "crag_grader",
        route_crag,
        {
            "spotlighting": "spotlighting",
            "rewriter": "rewriter",
            "tavily_search": "tavily_search"
        }
    )
    
    workflow.add_edge("tavily_search", "spotlighting")
    workflow.add_edge("spotlighting", "llm_answer")
    workflow.add_edge("rewriter", "hybrid_retrieval") # Loop back
    
    workflow.add_edge("llm_answer", "self_rag_reflect")
    
    workflow.add_conditional_edges(
        "self_rag_reflect",
        route_self_rag,
        {
            "llm_answer": "llm_answer",
            "finalize": "finalize"
        }
    )
    
    # SQL Pipeline
    workflow.add_edge("sql_generate", "sql_validate")
    workflow.add_edge("sql_validate", "sql_interrupt")
    workflow.add_edge("sql_interrupt", "sql_execute")
    workflow.add_edge("sql_execute", "finalize")
    
    # End
    workflow.add_edge("finalize", END)
    
    # Compile
    # Human-in-the-loop interrupt before SQL execute is handled by the interrupt() call inside sql_interrupt node in LangGraph >= 0.2
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    logger.info("LangGraph state machine compiled successfully.")
    return compiled_graph
