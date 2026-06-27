# src/llm/cost_tracker.py
import logging
from configs.settings import settings
from src.db.postgres import execute_query

logger = logging.getLogger(__name__)

class CostTracker:
    # Approximate pricing per 1M tokens (USD)
    PRICING = {
        "gpt-4o": {"prompt": 5.0, "completion": 15.0},
        "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
        "llama-3.3-70b-versatile": {"prompt": 0.59, "completion": 0.79},
        "text-embedding-3-small": {"prompt": 0.02, "completion": 0.0},
    }

    @staticmethod
    def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        prices = CostTracker.PRICING.get(model, {"prompt": 0.0, "completion": 0.0})
        prompt_cost = (prompt_tokens / 1_000_000) * prices["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * prices["completion"]
        return prompt_cost + completion_cost

    @staticmethod
    async def log_query(
        session_id: str, 
        user_id: str, 
        query: str, 
        intent: str, 
        response: str, 
        latency_ms: int,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        error: str = None
    ):
        if not settings.COST_TRACKING_ENABLED:
            return
            
        total_tokens = prompt_tokens + completion_tokens
        cost_usd = CostTracker.calculate_cost(model, prompt_tokens, completion_tokens)
        
        try:
            sql = """
                INSERT INTO query_logs 
                (session_id, user_id, query, intent, response, latency_ms, tokens_used, cost_usd, error)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            await execute_query(
                sql, session_id, user_id, query, intent, response, 
                latency_ms, total_tokens, cost_usd, error
            )
            
            # Update token budget (upsert pattern)
            budget_sql = """
                INSERT INTO token_budgets (user_id, date, tokens_used)
                VALUES ($1, CURRENT_DATE, $2)
                ON CONFLICT (user_id, date) DO UPDATE 
                SET tokens_used = token_budgets.tokens_used + $2
            """
            await execute_query(budget_sql, user_id, total_tokens)
            
        except Exception as e:
            logger.error(f"Failed to log query cost: {e}")

cost_tracker = CostTracker()
