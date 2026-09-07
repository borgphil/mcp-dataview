from app.main import service


def test_composite_relationship_query_uses_all_configured_columns():
    result = service.execute(
        "SELECT a.account_id, a.account_version, p.quantity "
        "FROM accounts a JOIN positions p ORDER BY a.account_version"
    )
    assert result["count"] == 3
    assert {row["account_version"] for row in result["rows"]} == {1, 2}
