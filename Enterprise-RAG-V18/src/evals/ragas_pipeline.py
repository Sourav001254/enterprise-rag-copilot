import logging
from typing import List, Dict
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from src.llm.gateway import llm_gateway
from src.llm.model_router import TaskType

logger = logging.getLogger(__name__)

class RagasEvaluator:
    async def run_eval(self, data: List[Dict], config_name: str) -> Dict:
        logger.info(f"Running Ragas eval for {len(data)} rows on {config_name}")
        if not data:
            return {"metrics": {}}

        # Ragas requires a HuggingFace Dataset
        # Expected keys: question, answer, contexts, ground_truth
        dataset = Dataset.from_list(data)

        # Ragas 0.1.x requires wrapping Langchain models
        from ragas.llms import LangchainLLMWrapper
        llm = llm_gateway.get_llm(task=TaskType.JSON_STRUCTURED, temperature=0.0)
        ragas_llm = LangchainLLMWrapper(llm)
        
        try:
            result = evaluate(
                dataset=dataset,
                metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                llm=ragas_llm
            )
            
            return {
                "metrics": {
                    "faithfulness": result.get("faithfulness", 0.0),
                    "answer_relevancy": result.get("answer_relevancy", 0.0),
                    "context_precision": result.get("context_precision", 0.0),
                    "context_recall": result.get("context_recall", 0.0)
                }
            }
        except Exception as e:
            logger.error(f"Ragas eval error: {e}")
            return {"metrics": {}}

ragas_evaluator = RagasEvaluator()
