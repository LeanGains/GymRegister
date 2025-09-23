import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_get_assets_empty_database(test_client: TestClient, auth_headers: dict):
    """Test getting assets from empty database returns empty list"""
    response = test_client.get("/api/assets/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_assets_with_single_asset(test_client: TestClient, auth_headers: dict, sample_asset_data: dict):
    """Test getting assets with one asset in database"""
    # Create an asset first
    create_response = test_client.post("/api/assets/", json=sample_asset_data, headers=auth_headers)
    assert create_response.status_code == 201
    
    # Get assets
    response = test_client.get("/api/assets/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    
    # Validate asset structure
    asset = data[0]
    assert "id" in asset
    assert "asset_tag" in asset
    assert "item_type" in asset
    assert "location" in asset
    assert "status" in asset
    assert "condition" in asset
    assert "created_at" in asset
    assert "updated_at" in asset
    assert "last_seen" in asset
    assert "metadata" in asset  # This should be present now
    
    # Validate values
    assert asset["asset_tag"] == sample_asset_data["asset_tag"]
    assert asset["item_type"] == sample_asset_data["item_type"]
    assert asset["location"] == sample_asset_data["location"]

def test_get_assets_with_multiple_assets(test_client: TestClient, auth_headers: dict):
    """Test getting assets with multiple assets in database"""
    # Create multiple assets
    assets = [
        {
            "asset_tag": "GYM001",
            "name": "Treadmill 1",
            "item_type": "Treadmill",
            "location": "Cardio Area",
            "status": "Active",
            "condition": "Good"
        },
        {
            "asset_tag": "GYM002",
            "name": "Bench Press",
            "item_type": "Weight Bench",
            "location": "Free Weights",
            "status": "Active",
            "condition": "Excellent"
        }
    ]
    
    for asset_data in assets:
        create_response = test_client.post("/api/assets/", json=asset_data, headers=auth_headers)
        assert create_response.status_code == 201
    
    # Get assets
    response = test_client.get("/api/assets/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    
    # Check that both assets are returned
    asset_tags = {asset["asset_tag"] for asset in data}
    assert asset_tags == {"GYM001", "GYM002"}

def test_get_assets_with_filters(test_client: TestClient, auth_headers: dict):
    """Test getting assets with various filters"""
    # Create test assets with different attributes
    assets = [
        {
            "asset_tag": "CARDIO001",
            "name": "Treadmill 1",
            "item_type": "Treadmill",
            "location": "Cardio Area",
            "status": "Active",
            "condition": "Good"
        },
        {
            "asset_tag": "WEIGHT001",
            "name": "Bench Press",
            "item_type": "Weight Bench",
            "location": "Free Weights",
            "status": "Missing",
            "condition": "Poor"
        }
    ]
    
    for asset_data in assets:
        create_response = test_client.post("/api/assets/", json=asset_data, headers=auth_headers)
        assert create_response.status_code == 201
    
    # Test status filter
    response = test_client.get("/api/assets/?status=Active", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["asset_tag"] == "CARDIO001"
    
    # Test item_type filter
    response = test_client.get("/api/assets/?item_type=Treadmill", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["asset_tag"] == "CARDIO001"
    
    # Test search filter
    response = test_client.get("/api/assets/?search=treadmill", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["asset_tag"] == "CARDIO001"

def test_get_assets_pagination(test_client: TestClient, auth_headers: dict):
    """Test pagination parameters"""
    # Create multiple assets
    for i in range(5):
        asset_data = {
            "asset_tag": f"TEST{i:03d}",
            "name": f"Test Equipment {i}",
            "item_type": "Test Type",
            "location": "Test Location",
        }
        create_response = test_client.post("/api/assets/", json=asset_data, headers=auth_headers)
        assert create_response.status_code == 201
    
    # Test limit
    response = test_client.get("/api/assets/?limit=3", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3
    
    # Test skip
    response = test_client.get("/api/assets/?skip=2&limit=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2