# src/agents/llm_answer.py
import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.memory import ConversationSummaryMemory
from src.agents.state import AgentState
from src.llm.gateway import llm_gateway
from src.llm.model_router import TaskType
from src.cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)

async def _compress_history(chat_history: list) -> list:
    """Feature F: Multi-turn Context Compression"""
    if len(chat_history) <= 10:
        return chat_history
        
    logger.info("Compressing chat history (length > 10)")
    llm = llm_gateway.get_llm(task=TaskType.FAST, temperature=0.0)
    memory = ConversationSummaryMemory(llm=llm)
    
    for i in range(0, len(chat_history) - 4, 2):
        if i+1 < len(chat_history):
            memory.save_context(
                {"input": chat_history[i].content}, 
                {"output": chat_history[i+1].content}
            )
            
    summary = memory.load_memory_variables({})["history"]
    
    # Return compressed summary + last 4 messages
    compressed = [SystemMessage(content=f"Previous conversation summary: {summary}")]
    compressed.extend(chat_history[-4:])
    return compressed
    
async def _verify_hallucinations(answer: str, context: str, llm) -> str:
    """Feature H: Hallucination Detection"""
    logger.info("Running hallucination detection verification.")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a verification assistant. Read the provided answer and the provided context. If the answer makes any factual claims that are NOT supported by the context, append [unverified] to those claims in the text. Output the verified text. DO NOT change the answer otherwise, only add [unverified] tags where needed."),
        ("human", "Context:\n{context}\n\nAnswer:\n{answer}")
    ])
    chain = prompt | llm
    res = await chain.ainvoke({"context": context, "answer": answer})
    
    p_tok = 0
    c_tok = 0
    if hasattr(res, "usage_metadata") and res.usage_metadata:
        p_tok = res.usage_metadata.get("input_tokens", 0)
        c_tok = res.usage_metadata.get("output_tokens", 0)
    elif hasattr(res, "response_metadata") and "token_usage" in res.response_metadata:
        p_tok = res.response_metadata["token_usage"].get("prompt_tokens", 0)
        c_tok = res.response_metadata["token_usage"].get("completion_tokens", 0)
        
    return res.content, p_tok, c_tok

async def llm_answer_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    original_query = state.get("original_query", query)
    chat_history = state.get("chat_history", [])
    docs = state.get("reranked_docs", [])
    intent = state.get("intent", "rag")
    sql_result = state.get("sql_result", [])
    
    # Check L5 Cache
    cache_key = f"{original_query}:{intent}"
    cached = await redis_cache.get(tier=5, content=cache_key)
    if cached and isinstance(cached, str):
        logger.info("L5 Cache hit for final answer.")
        state["answer"] = cached
        state["prompt_tokens"] = 0
        state["tokens_used"] = 0
        return state
        
    logger.info("Generating LLM Answer.")
    llm = llm_gateway.get_llm(task=TaskType.GENERATION, temperature=0.0)
    
    try:
        compressed_history = await _compress_history(chat_history)
        
        if intent == "sql":
            context = f"SQL Result:\n{sql_result}"
            system_prompt = "You are a helpful IT Operations assistant. Answer the user's question based on the provided SQL query result. Keep it concise and accurate."
        else:
            context_pieces = [d.content for d in docs]
            context = "\n\n".join(context_pieces)
            system_prompt = """You are a highly technical Kubernetes SRE assistant.
Answer the user's question using ONLY the provided context. 
If the context is insufficient to answer the question completely, explicitly state that you cannot answer based on the provided documents.
You MUST cite your sources inline using [doc id=N] where N is the id attribute of the `<doc>` tag.
DO NOT use outside knowledge."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Context:\n{context}\n\nQuestion:\n{question}")
        ])
        
        chain = prompt | llm
        res = await chain.ainvoke({
            "history": compressed_history,
            "context": context,
            "question": original_query
        })
        
        answer = res.content
        
        # Capture accurate token counts directly from the main LLM response
        p_tok = 0
        c_tok = 0
        if hasattr(res, "usage_metadata") and res.usage_metadata:
            p_tok = res.usage_metadata.get("input_tokens", 0)
            c_tok = res.usage_metadata.get("output_tokens", 0)
        elif hasattr(res, "response_metadata") and "token_usage" in res.response_metadata:
            p_tok = res.response_metadata["token_usage"].get("prompt_tokens", 0)
            c_tok = res.response_metadata["token_usage"].get("completion_tokens", 0)
            
        state["prompt_tokens"] = p_tok
        state["tokens_used"] = c_tok
        
        if intent != "sql" and docs:
            # Feature H: Hallucination Detection
            verify_llm = llm_gateway.get_llm(task=TaskType.FAST, temperature=0.0)
            answer, vp_tok, vc_tok = await _verify_hallucinations(answer, context, verify_llm)
            state["prompt_tokens"] += vp_tok
            state["tokens_used"] += vc_tok
            
        state["answer"] = answer
        
        # Save to L5 cache
        await redis_cache.set(tier=5, content=cache_key, value=answer)
        
        return state
        
    except Exception as e:
        logger.error(f"LLM Answer error: {e}")
        state["error"] = f"LLMAnswer: {str(e)}"
        state["answer"] = "An error occurred while generating the answer."
        return state
