import pytest
from src.heuristics import evaluate_semantic_sanity


def test_cartesian_product_heuristic():
    # Simulate a Cartesian product result set exceeding 1000 rows
    large_results = [{"id": i, "name": f"Item {i}"} for i in range(1001)]
    sql = "SELECT c.name, o.id FROM customers c, orders o;"
    question = "List customer orders"
    
    res = evaluate_semantic_sanity(sql, large_results, question)
    assert res["is_suspicious"] is True
    assert res["failure_type"] == "semantic"
    assert "Cartesian product" in res["reason"]


def test_unexpected_empty_results_heuristic():
    empty_results = []
    sql = "SELECT * FROM customers WHERE region = 'NonExistent';"
    question = "Who are the top spenders in New York?"

    res = evaluate_semantic_sanity(sql, empty_results, question)
    assert res["is_suspicious"] is True
    assert res["failure_type"] == "semantic"
    assert "0 rows" in res["reason"]


def test_single_null_aggregation_heuristic():
    null_results = [{"total_revenue": None}]
    sql = "SELECT SUM(total_amount) AS total_revenue FROM orders WHERE total_amount > 999999;"
    question = "What is the total revenue collected?"

    res = evaluate_semantic_sanity(sql, null_results, question)
    assert res["is_suspicious"] is True
    assert res["failure_type"] == "semantic"
    assert "NULL aggregation" in res["reason"]


def test_valid_semantic_result():
    valid_results = [{"customer_id": 1, "name": "Alice", "total_spent": 500.0}]
    sql = "SELECT c.customer_id, c.name, SUM(o.total_amount) FROM customers c JOIN orders o ON c.customer_id = o.cust_id GROUP BY c.customer_id, c.name;"
    question = "What is the total spending per customer?"

    res = evaluate_semantic_sanity(sql, valid_results, question)
    assert res["is_suspicious"] is False
    assert res["reason"] is None
