from fastapi.testclient import TestClient

def test_root_endpoint(test_client: TestClient):
    """Test root endpoint"""
    response = test_client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "GymRegister API"
    assert "version" in data
    assert data["status"] == "operational"

def test_health_check(test_client: TestClient):
    """Test health check endpoint"""
    response = test_client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_api_info(test_client: TestClient):
    """Test API info endpoint"""
    response = test_client.get("/api/info")
    
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "version" in data
    assert "endpoints" in data
    assert "authentication" in data

def test_openapi_docs_accessible(test_client: TestClient):
    """Test that OpenAPI docs are accessible"""
    response = test_client.get("/docs")
    assert response.status_code == 200
    
    response = test_client.get("/openapi.json")
    assert response.status_code == 200