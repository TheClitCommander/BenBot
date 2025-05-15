"""Pytest fixtures for BensBot Trading System."""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Import your FastAPI app
# Update this import to match your actual app structure
try:
    from trading_bot.api.app import app
except ImportError:
    from backend.api.app import app


@pytest.fixture
def client() -> Generator:
    """Create a FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_api_key() -> str:
    """Mock API key for testing."""
    return "test_api_key"


@pytest.fixture
def mock_api_key_header(mock_api_key) -> dict:
    """Create mock API key header for testing."""
    return {"X-API-Key": mock_api_key}


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up the test environment with test configurations."""
    # Store original environment variables
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ["TESTING"] = "True"
    os.environ["API_KEY"] = "test_api_key"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    
    yield
    
    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env) 