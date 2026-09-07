import pytest
from app.main import service

@pytest.mark.parametrize("sql", [
    "SELECT * FROM customers",
    "DROP TABLE customers",
    "SELECT id FROM users",
    "SELECT * FROM users",
    "SELECT id FROM customer_base_table",
    "SELECT id FROM customers; DROP TABLE customers",
    "SELECT c.id FROM customers c JOIN investments i ON c.id = i.customer_id",
    "SELECT id FROM customers UNION SELECT id FROM users",
    "SELECT id FROM customers WHERE id IN (SELECT id FROM users)",
    "WITH x AS (SELECT id FROM customers) SELECT id FROM x",
    "SELECT UPPER(name) FROM customers",
    "SELECT ROW_NUMBER() OVER () FROM customers",
])
def test_unsafe_sql_is_rejected(sql):
    with pytest.raises(ValueError):
        service.validate(sql)

def test_registered_logical_view_is_accepted():
    assert service.validate("SELECT c.id FROM customers c").root_view == "customers"

def test_malicious_literal_is_data_not_sql():
    result = service.execute("SELECT c.id FROM customers c WHERE c.name = 'x'' OR 1=1 --'")
    assert result["count"] == 0

def test_count_distinct_is_rejected_until_explicitly_supported():
    with pytest.raises(ValueError):
        service.validate("SELECT COUNT(DISTINCT c.id) FROM customers c")
