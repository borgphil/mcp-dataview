import pytest
from app.api.mcp.server import describe_view, list_views, query, validate_query

def test_mcp_metadata_tools():
    assert len(list_views()) == 5
    assert describe_view('customers')['name'] == 'customers'
    assert validate_query('SELECT id FROM customers')['valid'] is True


@pytest.mark.parametrize("payload", [
    "SELECT id FROM customers; DROP TABLE customers",
    "DROP TABLE customers",
    "INSERT INTO customers (id, name) VALUES (999, 'bad')",
    "UPDATE customers SET name = 'bad' WHERE id = 1",
    "DELETE FROM customers WHERE id = 1",
    "SELECT id FROM customers -- comment\nWHERE id = 1",
    "SELECT id FROM customers UNION SELECT id FROM users",
    "SELECT id FROM customers WHERE id IN (SELECT id FROM users)",
    "WITH x AS (SELECT id FROM customers) SELECT id FROM x",
    "SELECT UPPER(name) FROM customers",
    "SELECT ROW_NUMBER() OVER () FROM customers",
    "SELECT * FROM customers",
    "SELECT id FROM sqlite_master",
])
def test_mcp_query_rejects_sql_injection_payloads(payload):
    result = query(payload)
    assert result.get("valid") is False
    assert "error" in result


def test_mcp_query_parameterizes_malicious_literal():
    result = query("SELECT c.id FROM customers c WHERE c.name = 'x'' OR 1=1 --'")
    assert result.get("valid", True) is not False
    assert result["count"] == 0

