from app.main import service

def test_query_returns_parameterized_sample_data():
    result = service.execute("SELECT c.id, c.name FROM customers c WHERE c.name = 'Smith Holdings'")
    assert result["rows"] == [{"customer_id": 1, "customer_name": "Smith Holdings"}]

def test_metadata_driven_join_executes_without_user_on_clause():
    result = service.execute(
        "SELECT c.name, p.name FROM customers c JOIN investments i JOIN products p "
        "WHERE p.name = 'Product X' ORDER BY c.name LIMIT 100"
    )
    assert result["count"] == 2

def test_count_is_allowed():
    result = service.execute("SELECT COUNT(*) AS customer_count FROM customers")
    assert result["rows"] == [{"customer_count": 150}]

def test_left_join_and_order_alias_are_supported():
    result = service.execute(
        "SELECT p.id, SUM(i.investment_value) AS total "
        "FROM products p LEFT JOIN investments i GROUP BY p.id "
        "ORDER BY total DESC LIMIT 2"
    )
    assert result["rows"][0]["product_id"] == 10
