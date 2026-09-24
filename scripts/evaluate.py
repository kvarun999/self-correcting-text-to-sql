import os
import sys
import json

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import TextToSQLAgent
from src.db import execute_query

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/eval_set.json"))
RESULTS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../results/evaluation_metrics.json"))


def canonicalize_results(results: list) -> set:
    """Converts a list of dicts/rows into a canonical set of tuples for execution accuracy comparison."""
    if not results:
        return set()
    
    canonical_rows = []
    for row in results:
        if isinstance(row, dict):
            # Sort keys so value order is deterministic
            tuple_val = tuple(row[k] for k in sorted(row.keys()))
        elif isinstance(row, (list, tuple)):
            tuple_val = tuple(row)
        else:
            tuple_val = (row,)
        canonical_rows.append(tuple_val)
    
    return set(canonical_rows)


def compare_result_sets(res1: list, res2: list) -> bool:
    """Compares two database result sets for execution accuracy."""
    if res1 is None and res2 is None:
        return True
    if res1 is None or res2 is None:
        return False
    if len(res1) != len(res2):
        return False
    
    set1 = canonicalize_results(res1)
    set2 = canonicalize_results(res2)
    
    return set1 == set2


def run_evaluation():
    print("Starting Text-to-SQL Batch Evaluation Framework...")
    
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Evaluation dataset not found at {DATA_PATH}")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        eval_set = json.load(f)

    total_questions = len(eval_set)
    print(f"Loaded {total_questions} questions from dataset.")

    agent = TextToSQLAgent(max_iterations=3)
    configurations = ["zero_shot", "syntax_schema_repair_only", "full_pipeline"]
    
    metrics = {
        "configurations": {}
    }

    for config in configurations:
        print(f"\n--- Evaluating Configuration: {config} ---")
        correct_count = 0
        total_iterations = 0
        total_schema_repairs = 0
        total_semantic_repairs = 0

        for item in eval_set:
            qid = item["id"]
            question = item["question"]
            gold_sql = item["gold_sql"]

            # Execute gold SQL to get ground truth results
            gold_exec = execute_query(gold_sql)
            gold_results = gold_exec.get("results", []) if gold_exec.get("success") else []

            # Run agent under specific configuration
            agent_res = agent.run(question, mode=config)
            
            iterations = agent_res.get("iterations", 1)
            total_iterations += iterations

            # Count repairs by failure type
            repair_history = agent_res.get("repair_history", [])
            for repair in repair_history:
                f_type = repair.get("failure_type")
                if f_type == "schema":
                    total_schema_repairs += 1
                elif f_type == "semantic":
                    total_semantic_repairs += 1

            # Check execution accuracy
            if agent_res.get("status") == "success":
                generated_results = agent_res.get("results", [])
                if compare_result_sets(generated_results, gold_results):
                    correct_count += 1

        accuracy_pct = round((correct_count / total_questions) * 100.0, 2)
        avg_iterations = round(total_iterations / total_questions, 2)

        config_metric = {
            "accuracy_pct": accuracy_pct,
            "avg_iterations": avg_iterations
        }

        if config == "syntax_schema_repair_only":
            config_metric["total_schema_repairs"] = total_schema_repairs
        elif config == "full_pipeline":
            config_metric["total_semantic_repairs"] = total_semantic_repairs

        metrics["configurations"][config] = config_metric
        print(f"Config '{config}' -> Accuracy: {accuracy_pct}%, Avg Iterations: {avg_iterations}")

    # Ensure results directory exists
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nEvaluation complete! Metrics written to {RESULTS_PATH}")


if __name__ == "__main__":
    run_evaluation()
