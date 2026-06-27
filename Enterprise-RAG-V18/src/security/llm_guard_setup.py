# src/security/llm_guard_setup.py
import logging
from llm_guard.input_scanners import PromptInjection, Toxicity, BanTopics
from llm_guard.output_scanners import NoRefusal, Sensitive, Toxicity as OutputToxicity

logger = logging.getLogger(__name__)

class LLMGuardConfig:
    def __init__(self):
        logger.info("Initializing LLM-Guard Scanners...")
        try:
            # Input Scanners
            self.input_scanners = [
                PromptInjection(threshold=0.7),
                Toxicity(threshold=0.7),
                BanTopics(topics=["politics", "religion"], threshold=0.75)
            ]
            
            # Output Scanners
            self.output_scanners = [
                NoRefusal(threshold=0.7),
                Sensitive(),
                OutputToxicity(threshold=0.7)
            ]
            logger.info("LLM-Guard Scanners initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize LLM-Guard: {e}")
            self.input_scanners = []
            self.output_scanners = []

llm_guard_config = LLMGuardConfig()
