# src/agents/finalize.py
import logging
from src.agents.state import AgentState
from src.security.output_pipeline import run_output_pipeline
from configs.settings import settings

logger = logging.getLogger(__name__)

async def finalize_node(state: AgentState) -> AgentState:
    logger.info("Finalizing graph execution.")
    
    answer = state.get("answer", "")
    intent = state.get("intent", "")
    
    # Handle direct returns for chitchat/out_of_scope
    if intent in ["chitchat", "out_of_scope"]:
        if intent == "chitchat":
            answer = "Hello! I am the Enterprise Kubernetes SRE Copilot. How can I assist you with your clusters today?"
        else:
            answer = "I'm sorry, I am specifically trained to assist with Kubernetes IT operations and cluster data. I cannot answer queries outside this scope."
            
    if state.get("error"):
        answer = f"I encountered an error while processing your request: {state.get('error')}"
        state["degraded"] = True
    elif state.get("web_search_used"):
        answer += "\n\n*(Note: This answer incorporates information from live web search due to insufficient local context.)*"
        
    # Output Security Pipeline
    is_safe, sanitized_answer, reason = run_output_pipeline(state.get("original_query", ""), answer)
    if not is_safe:
        logger.warning(f"Output security blocked answer: {reason}")
        answer = "I'm sorry, my response violated our safety policies and was blocked."
        
    state["answer"] = answer
    
    # Extract sources
    sources = []
    for doc in state.get("reranked_docs", []):
        s = doc.metadata.get("source", "unknown")
        title = doc.metadata.get("title", "")
        if s not in [src.get("url") for src in sources]:
            sources.append({"url": s, "title": title, "score": doc.score})
            
    state["sources"] = sources
    
    return state
