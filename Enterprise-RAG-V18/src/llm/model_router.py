# src/llm/model_router.py
import logging
from enum import Enum
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TaskType(Enum):
    EMBEDDING = "embedding"
    GENERATION = "generation"
    FAST = "fast"
    JSON_STRUCTURED = "json_structured"
    SQL_GENERATION = "sql_generation"

class ModelRouter:
    @staticmethod
    def get_model(task: TaskType) -> str:
        """Route to appropriate model string based on task."""
        mapping = {
            TaskType.EMBEDDING: "text-embedding-3-small",
            TaskType.GENERATION: "gpt-4o",
            TaskType.FAST: "gpt-4o-mini",
            TaskType.JSON_STRUCTURED: "gpt-4o",  # gpt-4o handles JSON mode well
            TaskType.SQL_GENERATION: "gpt-4o"
        }
        model = mapping.get(task, "gpt-4o")
        logger.debug(f"Routed task {task.value} to model {model}")
        return model
        
    @staticmethod
    def get_llm_kwargs(task: TaskType) -> Dict[str, Any]:
        """Get model kwargs depending on task."""
        model = ModelRouter.get_model(task)
        kwargs = {"model": model}
        
        if task == TaskType.JSON_STRUCTURED:
            kwargs["response_format"] = {"type": "json_object"}
            
        return kwargs

model_router = ModelRouter()
