#!/usr/bin/env python3
"""
Simple test script to verify the assets API endpoint fix
"""

import requests
import json
import sys

def test_assets_endpoint():
    """Test the /api/assets endpoint"""
    base_url = "http://localhost:8000"
    
    # Test headers (you'll need to adjust these based on your auth setup)
    headers = {
        "X-API-Key": "gym-api-key-123",
        "Content-Type": "application/json"
    }
    
    print("Testing /api/assets endpoint...")
    
    try:
        # Test GET /api/assets
        response = requests.get(f"{base_url}/api/assets/", headers=headers)
        print(f"GET /api/assets/ - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            print(f"Number of assets: {len(data) if isinstance(data, list) else 'Not a list'}")
            
            if isinstance(data, list):
                print("✅ SUCCESS: Endpoint returns a list as expected")
                if len(data) > 0:
                    print(f"Sample asset fields: {list(data[0].keys())}")
                else:
                    print("No assets in database")
            else:
                print("❌ ERROR: Endpoint does not return a list")
                print(f"Actual response: {data}")
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server. Make sure the API is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
    
    return True

def test_create_asset():
    """Test creating an asset"""
    base_url = "http://localhost:8000"
    
    headers = {
        "X-API-Key": "gym-api-key-123",
        "Content-Type": "application/json"
    }
    
    # Sample asset data
    asset_data = {
        "asset_tag": "TEST001",
        "name": "Test Treadmill",
        "item_type": "Treadmill",
        "location": "Test Area",
        "status": "Active",
        "condition": "Good",
        "description": "Test asset for API validation"
    }
    
    print("\nTesting asset creation...")
    
    try:
        response = requests.post(f"{base_url}/api/assets/", headers=headers, json=asset_data)
        print(f"POST /api/assets/ - Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ SUCCESS: Asset created successfully")
            print(f"Created asset ID: {data.get('id', 'N/A')}")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print("ℹ️  INFO: Asset already exists (this is expected on subsequent runs)")
            return True
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Assets API Fix")
    print("=" * 50)
    
    # Test asset creation first
    create_success = test_create_asset()
    
    # Test asset retrieval
    get_success = test_assets_endpoint()
    
    print("\n" + "=" * 50)
    if create_success and get_success:
        print("✅ All tests passed! The fix appears to be working.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the API implementation.")
        sys.exit(1)