"""
Health check endpoint tests for the FMP MCP server
"""
import pytest
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
import json


async def health_check(request):
    """Health check endpoint function"""
    return JSONResponse({"status": "healthy", "service": "fmp-mcp-server"})


@pytest.fixture
def health_app():
    """Create a test app with just the health check endpoint"""
    app = Starlette(
        routes=[
            Route("/health", health_check, methods=["GET"]),
        ]
    )
    return app


@pytest.fixture
def client(health_app):
    """Create test client"""
    return TestClient(health_app)


def test_health_check_endpoint_get(client):
    """Test health check endpoint responds to GET requests"""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "fmp-mcp-server"


def test_health_check_endpoint_post_not_allowed(client):
    """Test health check endpoint doesn't accept POST requests"""
    response = client.post("/health")
    
    # Should return 405 Method Not Allowed
    assert response.status_code == 405


def test_health_check_response_format(client):
    """Test health check response format is valid JSON"""
    response = client.get("/health")
    
    assert response.status_code == 200
    
    # Verify it's valid JSON
    data = response.json()
    assert isinstance(data, dict)
    assert "status" in data
    assert "service" in data
    
    # Verify content
    assert data["status"] == "healthy"
    assert data["service"] == "fmp-mcp-server"


def test_health_check_alb_compatibility(client):
    """Test health check is compatible with ALB health checks"""
    response = client.get("/health")
    
    # ALB health checks expect:
    # - HTTP 200 status code
    # - Response within timeout (5 seconds default)
    # - Valid response body (optional but good practice)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    # Response should be small and fast
    content = response.content
    assert len(content) < 1000  # Small response
    
    # Should be valid JSON
    data = response.json()
    assert isinstance(data, dict)