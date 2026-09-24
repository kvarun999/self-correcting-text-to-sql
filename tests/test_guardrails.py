import pytest
from src.guardrails import validate_and_guard_sql, clean_sql_markdown


def test_clean_sql_markdown():
    raw_markdown = "```sql\nSELECT * FROM customers;\n```"
    assert clean_sql_markdown(raw_markdown) == "SELECT * FROM customers;"

    raw_backticks = "`SELECT customer_id FROM customers;`"
    assert clean_sql_markdown(raw_backticks) == "SELECT customer_id FROM customers;"


def test_valid_select_query():
    sql = "SELECT customer_id, name FROM customers WHERE region = 'North';"
    res = validate_and_guard_sql(sql)
    assert res["is_valid"] is True
    assert res["error"] is None
    assert "SELECT" in res["sql"].upper()


def test_reject_drop_table():
    sql = "DROP TABLE customers;"
    res = validate_and_guard_sql(sql)
    assert res["is_valid"] is False
    assert res["error_type"] == "syntax"
    assert "Security Guardrail Violation" in res["error"] or "Syntax Error" in res["error"]


def test_reject_delete_statement():
    sql = "DELETE FROM orders WHERE id = 1;"
    res = validate_and_guard_sql(sql)
    assert res["is_valid"] is False
    assert res["error_type"] == "syntax"


def test_reject_update_statement():
    sql = "UPDATE customers SET name = 'Hacked';"
    res = validate_and_guard_sql(sql)
    assert res["is_valid"] is False
    assert res["error_type"] == "syntax"


def test_invalid_syntax():
    sql = "SELECT FROM WHERE customer_id = ;"
    res = validate_and_guard_sql(sql)
    assert res["is_valid"] is False
    assert res["error_type"] == "syntax"
    assert "Syntax Error" in res["error"]
