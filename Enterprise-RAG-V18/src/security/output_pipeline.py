# src/security/output_pipeline.py
import logging
from typing import Dict, Any, Tuple
from llm_guard import scan_output
from src.security.llm_guard_setup import llm_guard_config
from src.security.pii_redactor import pii_redactor
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class ChatResponseSchema(BaseModel):
    answer: str
    sources: list = []
    tokens_used: int = 0
    latency_ms: int = 0
    degraded: bool = False

def run_output_pipeline(prompt: str, answer: str) -> Tuple[bool, str, str]:
    """
    Returns (is_safe, final_answer, reason)
    """
    try:
        # L7b: Output Moderation
        if llm_guard_config.output_scanners:
            sanitized_output, results_valid, results_score = scan_output(
                llm_guard_config.output_scanners, prompt, answer
            )
            if not all(results_valid.values()):
                failed_scanners = [k for k, v in results_valid.items() if not v]
                return False, "", f"L7b: Output moderation failed: {failed_scanners}"
                
            answer = sanitized_output
            
        # L7b: PII Redaction on final answer
        answer, _ = pii_redactor.redact(answer)
        
        return True, answer, "Passed"
        
    except Exception as e:
        logger.error(f"Output security pipeline error: {e}")
        return False, "", "Internal output security error"

def validate_response_schema(data: Dict[str, Any]) -> bool:
    """L9: Pydantic Schema Validation"""
    try:
        ChatResponseSchema(**data)
        return True
    except ValidationError as e:
        logger.error(f"L9: Schema validation failed: {e}")
        return False
