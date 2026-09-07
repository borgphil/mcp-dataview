from app.api.mcp.server import describe_view, list_views, validate_query

def test_mcp_metadata_tools():
    assert len(list_views()) == 5
    assert describe_view('customers')['name'] == 'customers'
    assert validate_query('SELECT id FROM customers')['valid'] is True
