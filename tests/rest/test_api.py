from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_views_endpoint():
    response = client.get('/api/views')
    assert response.status_code == 200
    assert {view['name'] for view in response.json()} == {'customers', 'investments', 'products', 'accounts', 'positions'}

def test_query_endpoint():
    response = client.post('/api/query', json={'sql': 'SELECT c.id FROM customers c LIMIT 1'})
    assert response.status_code == 200
    assert response.json()['count'] == 1

def test_invalid_query_has_structured_error():
    response = client.post('/api/query', json={'sql': 'SELECT * FROM customers'})
    assert response.status_code == 400
    assert response.json()['detail']['error'] == 'UNSUPPORTED_SQL'
