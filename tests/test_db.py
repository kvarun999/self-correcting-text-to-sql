import pytest
from src.db import fetch_schema_ddl, execute_query


def test_fetch_schema_ddl():
    ddl = fetch_schema_ddl()
    assert "customers" in ddl
    assert "orders" in ddl
    assert "line_items" in ddl
    assert "customer_id" in ddl
    assert "cust_id" in ddl


def test_invalid_sql_execution_schema_error():
    # Attempting to query non-existent table / column triggers a DB schema failure type
    invalid_query = "SELECT non_existent_column FROM non_existent_table;"
    res = execute_query(invalid_query)
    assert res["success"] is False
    assert res["failure_type"] == "schema"
    assert "Error" in res["error"]
