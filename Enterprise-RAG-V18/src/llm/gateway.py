# src/llm/gateway.py
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import BaseMessage
from portkey_ai import createHeaders, PORTKEY_GATEWAY_URL
from configs.settings import settings
from src.llm.model_router import ModelRouter, TaskType

logger = logging.getLogger(__name__)

class LLMGateway:
    def __init__(self):
        # We define a fallback strategy via Portkey
        self.portkey_headers = createHeaders(
            api_key=settings.PORTKEY_API_KEY,
            virtual_key=settings.PORTKEY_VIRTUAL_KEY_PRIMARY,
            # Fallback strategy injected via config if available
        ) if settings.PORTKEY_API_KEY else None

    def get_llm(self, task: TaskType = TaskType.GENERATION, temperature: float = 0.0) -> ChatOpenAI:
        """Get Langchain LLM configured with Portkey routing."""
        kwargs = ModelRouter.get_llm_kwargs(task)
        
        # Base setup
        base_kwargs = {
            "temperature": temperature,
            "timeout": 30.0,
            "max_retries": 3,
        }
        
        # Merge kwargs
        final_kwargs = {**base_kwargs, **kwargs}
        
        if self.portkey_headers:
            logger.debug(f"Using Portkey Gateway for LLM task {task}")
            return ChatOpenAI(
                base_url=PORTKEY_GATEWAY_URL,
                default_headers=self.portkey_headers,
                api_key="dummy", # Portkey handles auth
                **final_kwargs
            )
        else:
            logger.debug(f"Using Direct OpenAI for LLM task {task}")
            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                **final_kwargs
            )

    def get_embeddings(self) -> OpenAIEmbeddings:
        """Get OpenAI embeddings."""
        if self.portkey_headers:
            return OpenAIEmbeddings(
                base_url=PORTKEY_GATEWAY_URL,
                default_headers=self.portkey_headers,
                api_key="dummy",
                model=settings.EMBEDDING_MODEL
            )
        else:
            return OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL
            )

llm_gateway = LLMGateway()
