# src/security/pipeline.py
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any
import tiktoken
import time
from llm_guard import scan_prompt
from src.security.prompt_shield import prompt_shield, QueryInput
from src.security.llm_guard_setup import llm_guard_config
from src.security.pii_redactor import pii_redactor
from src.db.postgres import fetch_rows
from configs.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class SecurityResult:
    safe: bool
    reason: str
    redacted_query: str
    pii_found: List[str] = field(default_factory=list)
    tokens_used: int = 0

async def run_input_pipeline(query: str, token_claims: Dict[str, Any]) -> SecurityResult:
    try:
        # L1: Pydantic + Regex, Unicode normalisation
        try:
            validated = QueryInput(query=query)
        except Exception:
            return SecurityResult(safe=False, reason="L1: Schema validation failed", redacted_query="")
            
        normalized = prompt_shield.normalize(validated.query)
        cleaned = prompt_shield.clean(normalized)
        
        if prompt_shield.detect_injection(cleaned):
            return SecurityResult(safe=False, reason="L1: Injection pattern detected", redacted_query="")
            
        # L2 & L7a: llm-guard Scan (Content Moderation + BanTopics + PromptInjection)
        if llm_guard_config.input_scanners:
            # llm_guard is synchronous, but fast enough for this pipeline usually
            sanitized_prompt, results_valid, results_score = scan_prompt(
                llm_guard_config.input_scanners, cleaned
            )
            if not all(results_valid.values()):
                failed_scanners = [k for k, v in results_valid.items() if not v]
                return SecurityResult(safe=False, reason=f"L2/L7a: llm-guard rejected: {failed_scanners}", redacted_query="")
        
        # L4a: JWT Auth check
        # Assuming token_claims contains exp, sub, roles (validated by FastAPI, but we double check here)
        user_id = token_claims.get("sub")
        if not user_id:
            return SecurityResult(safe=False, reason="L4a: Missing 'sub' claim in token", redacted_query="")
            
        # L4b: Rate Limit - assumed handled by slowapi in FastAPI middleware
        
        # L5: Token truncation & whitespace
        encoder = tiktoken.get_encoding("cl100k_base")
        tokens = encoder.encode(cleaned)
        if len(tokens) > 4096:
            tokens = tokens[:4096]
            cleaned = encoder.decode(tokens)
            
        # L6: Token Budget
        budget_sql = """
            SELECT tokens_used FROM token_budgets 
            WHERE user_id = $1 AND date = CURRENT_DATE
        """
        rows = await fetch_rows(budget_sql, user_id)
        tokens_used_today = rows[0]['tokens_used'] if rows else 0
        
        if tokens_used_today > settings.TOKEN_BUDGET_DAILY:
            return SecurityResult(safe=False, reason="L6: Daily token budget exceeded", redacted_query="")
            
        # L7b: PII Redaction
        redacted_query, pii_found = pii_redactor.redact(cleaned)
        
        # L8: Spotlighting happens in LangGraph
        
        return SecurityResult(
            safe=True, 
            reason="Passed", 
            redacted_query=redacted_query,
            pii_found=pii_found,
            tokens_used=len(tokens)
        )
        
    except Exception as e:
        logger.error(f"Security pipeline error: {e}")
        # Fail closed
        return SecurityResult(safe=False, reason="Internal security error", redacted_query="")
