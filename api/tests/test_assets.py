import pytest
from fastapi.testclient import TestClient

def test_create_asset(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test creating a new asset"""
    response = test_client.post(
        "/api/assets/",
        json=sample_asset_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["asset_tag"] == sample_asset_data["asset_tag"]
    assert data["item_type"] == sample_asset_data["item_type"]
    assert data["location"] == sample_asset_data["location"]

def test_create_duplicate_asset(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test creating duplicate asset returns error"""
    # Create first asset
    test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    
    # Try to create duplicate
    response = test_client.post(
        "/api/assets/",
        json=sample_asset_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_get_assets(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test getting list of assets"""
    # Create an asset first
    test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    
    response = test_client.get("/api/assets/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["asset_tag"] == sample_asset_data["asset_tag"]

def test_get_asset_by_tag(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test getting specific asset by tag"""
    # Create an asset first
    test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    
    response = test_client.get(f"/api/assets/{sample_asset_data['asset_tag']}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["asset_tag"] == sample_asset_data["asset_tag"]

def test_get_nonexistent_asset(test_client: TestClient, auth_headers: dict):
    """Test getting nonexistent asset returns 404"""
    response = test_client.get("/api/assets/NONEXISTENT", headers=auth_headers)
    
    assert response.status_code == 404

def test_update_asset(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test updating an existing asset"""
    # Create an asset first
    test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    
    # Update the asset
    update_data = {"location": "Updated Room B", "condition": "Good"}
    response = test_client.put(
        f"/api/assets/{sample_asset_data['asset_tag']}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Updated Room B"
    assert data["condition"] == "Good"

def test_delete_asset(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test deleting an asset"""
    # Create an asset first
    test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    
    # Delete the asset
    response = test_client.delete(f"/api/assets/{sample_asset_data['asset_tag']}", headers=auth_headers)
    
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = test_client.get(f"/api/assets/{sample_asset_data['asset_tag']}", headers=auth_headers)
    assert get_response.status_code == 404

def test_update_asset_location(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test updating asset location via PATCH endpoint"""
    # Create an asset first
    test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    
    # Update location
    new_location = "New Location"
    response = test_client.patch(
        f"/api/assets/{sample_asset_data['asset_tag']}/location",
        params={"location": new_location},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["asset"]["location"] == new_location

def test_unauthorized_access(test_client: TestClient, sample_asset_data: dict):
    """Test that endpoints require authentication"""
    response = test_client.get("/api/assets/")
    assert response.status_code == 401
    
    response = test_client.post("/api/assets/", json=sample_asset_data)
    assert response.status_code == 401