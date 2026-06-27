# src/agents/spotlighting.py
import logging
from src.agents.state import AgentState

logger = logging.getLogger(__name__)

async def spotlighting_node(state: AgentState) -> AgentState:
    docs = state.get("reranked_docs", [])
    
    if not docs:
        return state
        
    logger.info(f"Applying spotlighting to {len(docs)} documents.")
    
    # Layer 8 Security: XML tag wrapping to prevent indirect prompt injection
    for i, doc in enumerate(docs):
        source = doc.metadata.get("source", "unknown")
        # Ensure malicious XML closure doesn't break out
        safe_content = doc.content.replace("</doc>", "<\doc>")
        
        spotlighted = f"""<doc id="{i}" source="{source}" score="{doc.score:.3f}">
{safe_content}
</doc>"""
        # Update content in place
        docs[i].content = spotlighted
        
    state["reranked_docs"] = docs
    return state
