# src/evals/ab_eval.py
import logging
import json
from src.evals.ragas_pipeline import ragas_evaluator
from configs.settings import settings

logger = logging.getLogger(__name__)

async def run_ab_eval(dataset_path: str = "tests/golden_dataset.json"):
    """Compare two model configs on golden dataset."""
    logger.info(f"Starting A/B evaluation using dataset {dataset_path}")
    
    try:
        with open(dataset_path, "r") as f:
            golden_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Golden dataset not found at {dataset_path}")
        return
        
    # We would normally generate the answers using our graph for Config A and Config B
    # For demonstration, we assume golden_data has 'question', 'answer_a', 'answer_b', 'contexts', 'ground_truth'
    
    # Run Eval for Config A
    data_a = [
        {
            "question": d["question"],
            "answer": d["answer_a"],
            "contexts": d["contexts_a"],
            "ground_truth": d["ground_truth"]
        } for d in golden_data
    ]
    
    logger.info("Running eval for Config A...")
    res_a = await ragas_evaluator.run_eval(data_a, "config_a")
    
    # Run Eval for Config B
    data_b = [
        {
            "question": d["question"],
            "answer": d["answer_b"],
            "contexts": d["contexts_b"],
            "ground_truth": d["ground_truth"]
        } for d in golden_data
    ]
    
    logger.info("Running eval for Config B...")
    res_b = await ragas_evaluator.run_eval(data_b, "config_b")
    
    logger.info("A/B Evaluation complete.")
    logger.info(f"Config A Metrics: {res_a['metrics']}")
    logger.info(f"Config B Metrics: {res_b['metrics']}")
    
    return {
        "config_a": res_a['metrics'],
        "config_b": res_b['metrics']
    }
