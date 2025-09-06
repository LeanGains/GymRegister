import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from ..database import Base, get_db
from ..main import app
from ..config import settings

# Test database
TEST_DATABASE_URL = "sqlite:///./test_gym_assets.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup
    try:
        os.remove("./test_gym_assets.db")
    except FileNotFoundError:
        pass

@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_engine
    )
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up tables
        for table in reversed(Base.metadata.sorted_tables):
            test_engine.execute(table.delete())

@pytest.fixture(scope="function")
def test_client(test_db):
    """Create test client with test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    """Authentication headers for testing"""
    return {"X-API-Key": settings.api_key}

@pytest.fixture
def sample_asset_data():
    """Sample asset data for testing"""
    return {
        "asset_tag": "TEST001",
        "name": "Test Dumbbell",
        "item_type": "Dumbbell",
        "description": "25 lb dumbbell for testing",
        "location": "Test Room A",
        "status": "Active",
        "condition": "Excellent",
        "weight": "25 lbs",
        "notes": "Test asset for unit testing"
    }

@pytest.fixture
def temp_upload_dir():
    """Temporary upload directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_upload_dir = settings.upload_dir
        settings.upload_dir = temp_dir
        yield temp_dir
        settings.upload_dir = original_upload_dir