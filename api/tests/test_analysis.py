import pytest
import tempfile
import io
from PIL import Image
from fastapi.testclient import TestClient

@pytest.fixture
def test_image():
    """Create a test image for analysis"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_analyze_image_endpoint(test_client: TestClient, auth_headers: dict, test_image, temp_upload_dir):
    """Test image analysis endpoint"""
    
    # Mock the analysis since we don't have OpenAI key in tests
    files = {"file": ("test_image.jpg", test_image, "image/jpeg")}
    data = {"asset_tag": "TEST001"}
    
    response = test_client.post(
        "/api/analyze",
        files=files,
        data=data,
        headers=auth_headers
    )
    
    # Should accept the request even if OpenAI processing fails
    assert response.status_code == 202
    result = response.json()
    assert "job_id" in result
    assert result["status"] == "pending"

def test_get_analysis_result(test_client: TestClient, auth_headers: dict, test_image, temp_upload_dir):
    """Test getting analysis result"""
    
    # First create an analysis job
    files = {"file": ("test_image.jpg", test_image, "image/jpeg")}
    response = test_client.post(
        "/api/analyze",
        files=files,
        headers=auth_headers
    )
    
    job_id = response.json()["job_id"]
    
    # Get the analysis result
    response = test_client.get(f"/api/analyze/{job_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id

def test_get_nonexistent_analysis(test_client: TestClient, auth_headers: dict):
    """Test getting nonexistent analysis returns 404"""
    response = test_client.get("/api/analyze/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404

def test_analysis_history(test_client: TestClient, auth_headers: dict, test_image, temp_upload_dir):
    """Test getting analysis history"""
    
    # Create an analysis job
    files = {"file": ("test_image.jpg", test_image, "image/jpeg")}
    test_client.post("/api/analyze", files=files, headers=auth_headers)
    
    # Get analysis history
    response = test_client.get("/api/analysis/history", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_analyze_invalid_file_type(test_client: TestClient, auth_headers: dict):
    """Test analyzing invalid file type returns error"""
    
    # Create a text file instead of image
    text_file = io.BytesIO(b"This is not an image")
    files = {"file": ("test.txt", text_file, "text/plain")}
    
    response = test_client.post(
        "/api/analyze",
        files=files,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "must be an image" in response.json()["detail"]

def test_analyze_without_auth(test_client: TestClient, test_image):
    """Test analysis endpoint requires authentication"""
    
    files = {"file": ("test_image.jpg", test_image, "image/jpeg")}
    response = test_client.post("/api/analyze", files=files)
    
    assert response.status_code == 401