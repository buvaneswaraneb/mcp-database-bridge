import pytest, json, sys
sys.path.insert(0, 'src')
from server import list_tables, get_schema, run_select, explain_query, init_sample_db

def setup_module():
    init_sample_db()

def test_list_tables_returns_dict():
    result = list_tables("sample.db")
    assert "tables" in result and isinstance(result["tables"], list)

def test_list_tables_includes_customers():
    result = list_tables("sample.db")
    assert "customers" in result["tables"]

def test_get_schema_customers():
    result = get_schema("customers", "sample.db")
    assert "columns" in result
    col_names = [c["name"] for c in result["columns"]]
    assert "id" in col_names and "email" in col_names

def test_get_schema_unknown_table():
    result = get_schema("nonexistent_table", "sample.db")
    assert "error" in result

def test_run_select_allowed():
    result = run_select("SELECT * FROM customers LIMIT 2", "sample.db")
    assert "rows" in result

def test_run_select_blocks_insert():
    result = run_select("INSERT INTO customers VALUES (99,'x','x@x.com','US','now')", "sample.db")
    assert "error" in result

def test_run_select_blocks_drop():
    result = run_select("DROP TABLE customers", "sample.db")
    assert "error" in result
