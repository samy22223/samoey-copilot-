import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from ..middleware.security import SecurityMiddleware, setup_security_middleware
from ..core.errors import RateLimitError
import json

@pytest.fixture
def app():
    """Create test FastAPI application"""
    app = FastAPI()
    setup_security_middleware(app)
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}
    
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)

def test_valid_request(client):
    """Test valid request passes security checks"""
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}
    
    # Check security headers
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-XSS-Protection" in response.headers
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers

def test_rate_limit(client):
    """Test rate limiting"""
    # Make requests up to limit
    for _ in range(100):
        response = client.get("/test")
        assert response.status_code == 200
    
    # Next request should fail
    response = client.get("/test")
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["message"]

def test_blocked_ip(client):
    """Test IP blocking"""
    # Trigger IP block with malicious request
    response = client.get("/test?q=<script>alert(1)</script>")
    assert response.status_code == 400
    
    # Subsequent requests should be blocked
    response = client.get("/test")
    assert response.status_code == 429
    assert "IP address is blocked" in response.json()["message"]

def test_xss_protection(client):
    """Test XSS protection"""
    payloads = [
        "<script>alert(1)</script>",
        "javascript:alert(1)",
        'onclick="alert(1)"',
        "<img src=x onerror=alert(1)>",
    ]
    
    for payload in payloads:
        response = client.get(f"/test?q={payload}")
        assert response.status_code == 400
        assert "Malicious content detected" in response.json()["message"]

def test_sql_injection_protection(client):
    """Test SQL injection protection"""
    payloads = [
        "UNION SELECT * FROM users",
        "1; DROP TABLE users",
        "admin' --",
        "' OR '1'='1",
    ]
    
    for payload in payloads:
        response = client.get(f"/test?q={payload}")
        assert response.status_code == 400
        assert "Malicious content detected" in response.json()["message"]

def test_path_traversal_protection(client):
    """Test path traversal protection"""
    payloads = [
        "../../../etc/passwd",
        "..\\windows\\system32",
        "%2e%2e%2f",
    ]
    
    for payload in payloads:
        response = client.get(f"/test/{payload}")
        assert response.status_code == 400
        assert "Path traversal attempt detected" in response.json()["message"]

def test_content_size_limit(client):
    """Test content size limit"""
    large_data = "x" * (10 * 1024 * 1024 + 1)  # Exceeds 10MB
    response = client.post("/test", json={"data": large_data})
    assert response.status_code == 400
    assert "Request body too large" in response.json()["message"]

def test_invalid_method(client):
    """Test invalid HTTP method"""
    response = client.trace("/test")
    assert response.status_code == 400
    assert "Method not allowed" in response.json()["message"]
