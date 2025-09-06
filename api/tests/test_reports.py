import pytest
from fastapi.testclient import TestClient

def test_get_statistics(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test getting asset statistics"""
    
    # Create some test assets
    test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    
    response = test_client.get("/api/reports/statistics", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "total_assets" in data
    assert data["total_assets"] >= 1
    assert "by_status" in data
    assert "by_condition" in data
    assert "by_type" in data

def test_get_audit_logs(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test getting audit logs"""
    
    # Create an asset to generate audit logs
    test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    
    response = test_client.get("/api/reports/audit-logs", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["action"] == "CREATE"

def test_export_assets_csv(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test exporting assets to CSV"""
    
    # Create a test asset
    test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    
    response = test_client.get("/api/reports/export", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    
    # Check CSV content
    csv_content = response.text
    assert "Asset Tag" in csv_content
    assert sample_asset_data["asset_tag"] in csv_content

def test_get_missing_assets(test_client: TestClient, auth_headers: dict):
    """Test getting missing assets"""
    
    # Create a missing asset
    missing_asset = {
        "asset_tag": "MISSING001",
        "item_type": "Dumbbell",
        "location": "Storage",
        "status": "Missing"
    }
    test_client.post("/api/assets/", json=missing_asset, headers=auth_headers)
    
    response = test_client.get("/api/reports/missing", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "Missing"

def test_get_assets_needing_repair(test_client: TestClient, auth_headers: dict):
    """Test getting assets needing repair"""
    
    # Create an asset needing repair
    repair_asset = {
        "asset_tag": "REPAIR001",
        "item_type": "Bench",
        "location": "Gym Floor",
        "condition": "Needs Repair"
    }
    test_client.post("/api/assets/", json=repair_asset, headers=auth_headers)
    
    response = test_client.get("/api/reports/repair", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["condition"] == "Needs Repair"

def test_get_dashboard_data(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test getting dashboard data"""
    
    # Create test assets
    test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    
    response = test_client.get("/api/reports/dashboard", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "statistics" in data
    assert "missing_assets" in data
    assert "repair_assets" in data
    assert "recent_assets" in data
    assert "alerts" in data

def test_reports_require_auth(test_client: TestClient):
    """Test that report endpoints require authentication"""
    endpoints = [
        "/api/reports/statistics",
        "/api/reports/audit-logs", 
        "/api/reports/export",
        "/api/reports/missing",
        "/api/reports/repair",
        "/api/reports/dashboard"
    ]
    
    for endpoint in endpoints:
        response = test_client.get(endpoint)
        assert response.status_code == 401