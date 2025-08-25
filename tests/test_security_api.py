import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, Security
from datetime import datetime
import json

from app.main import app
from app.core.security import get_current_user
from app.api.security_dashboard import router

# Mock admin user with admin scope
mock_admin_user = {
    "id": "admin_user_id",
    "email": "admin@example.com",
    "username": "admin",
    "is_active": True,
    "scopes": ["admin", "read", "write"]
}

# Mock regular user without admin scope
mock_regular_user = {
    "id": "regular_user_id",
    "email": "user@example.com",
    "username": "user",
    "is_active": True,
    "scopes": ["read", "write"]
}

@pytest.fixture
def admin_client():
    """Create test client with admin authentication"""
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def regular_client():
    """Create test client with regular user authentication"""
    app.dependency_overrides[get_current_user] = lambda: mock_regular_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def unauth_client():
    """Create test client without authentication"""
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_security_monitor():
    """Mock security monitor"""
    with patch('app.api.security_dashboard.security_monitor') as mock_monitor:
        mock_monitor.get_security_status = AsyncMock()
        mock_monitor.get_recent_alerts = AsyncMock()
        yield mock_monitor

@pytest.fixture
def mock_advanced_security():
    """Mock advanced security"""
    with patch('app.api.security_dashboard.advanced_security') as mock_advanced:
        mock_advanced.get_security_status = AsyncMock()
        mock_advanced.get_threat_patterns = AsyncMock()
        mock_advanced.update_defense_rules = AsyncMock()
        yield mock_advanced

@pytest.fixture
def mock_ai_security_manager():
    """Mock AI security manager"""
    with patch('app.api.security_dashboard.ai_security_manager') as mock_ai:
        mock_ai.get_ai_security_status = AsyncMock()
        yield mock_ai

@pytest.fixture
def sample_security_status():
    """Sample security status data"""
    return {
        "threat_level": 2,
        "threat_level_text": "Medium",
        "recent_alerts": [
            {"severity": "critical", "message": "Critical threat detected"},
            {"severity": "high", "message": "High severity alert"},
            {"severity": "medium", "message": "Medium severity alert"},
            {"severity": "low", "message": "Low severity alert"}
        ],
        "recent_events": [
            {"type": "threat_detected", "message": "Threat detected"},
            {"type": "login_attempt", "message": "Login attempt"}
        ],
        "metrics": {
            "total_requests": 1000,
            "blocked_requests": 50,
            "active_sessions": 10
        }
    }

@pytest.fixture
def sample_advanced_security_status():
    """Sample advanced security status data"""
    return {
        "active_defenses": ["firewall", "ids", "waf"],
        "blocked_requests": 25,
        "blocked_ips": ["192.168.1.100", "10.0.0.1"]
    }

@pytest.fixture
def sample_ai_security_status():
    """Sample AI security status data"""
    return {
        "metrics": {
            "model_requests": 500,
            "suspicious_activities": 5
        },
        "model_usage": {
            "gpt-4": 300,
            "claude": 200
        },
        "events": [
            {"type": "ai_threat", "message": "AI threat detected"},
            {"type": "model_usage", "message": "Model usage spike"}
        ]
    }

@pytest.fixture
def sample_alerts():
    """Sample security alerts"""
    return [
        {"id": 1, "severity": "critical", "message": "Critical alert"},
        {"id": 2, "severity": "high", "message": "High alert"},
        {"id": 3, "severity": "medium", "message": "Medium alert"}
    ]

@pytest.fixture
def sample_threat_patterns():
    """Sample threat patterns"""
    return [
        {"pattern": "sql_injection", "count": 10},
        {"pattern": "xss_attempt", "count": 5},
        {"pattern": "path_traversal", "count": 3}
    ]

class TestSecurityDashboardAPI:
    """Comprehensive test suite for Security Dashboard API endpoints"""

    def test_get_security_dashboard_success(self, admin_client, mock_security_monitor,
                                         mock_advanced_security, mock_ai_security_manager,
                                         sample_security_status, sample_advanced_security_status,
                                         sample_ai_security_status):
        """Test successful security dashboard retrieval"""
        # Setup mocks
        mock_security_monitor.get_security_status.return_value = sample_security_status
        mock_advanced_security.get_security_status.return_value = sample_advanced_security_status
        mock_ai_security_manager.get_ai_security_status.return_value = sample_ai_security_status

        response = admin_client.get("/api/security/dashboard")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "timestamp" in data
        assert "threat_level" in data
        assert "threat_level_text" in data
        assert "alerts" in data
        assert "metrics" in data
        assert "events" in data
        assert "defenses" in data
        assert "ai_security" in data

        # Verify threat level data
        assert data["threat_level"] == 2
        assert data["threat_level_text"] == "Medium"

        # Verify alerts count
        alerts_count = data["alerts"]["count"]
        assert alerts_count["critical"] == 1
        assert alerts_count["high"] == 1
        assert alerts_count["medium"] == 1
        assert alerts_count["low"] == 1

        # Verify metrics
        assert "general" in data["metrics"]
        assert "ai_specific" in data["metrics"]

        # Verify defenses
        assert data["defenses"]["active"] == ["firewall", "ids", "waf"]
        assert data["defenses"]["blocked_requests"] == 25

    def test_get_security_dashboard_unauthorized(self, unauth_client):
        """Test security dashboard access without authentication"""
        response = unauth_client.get("/api/security/dashboard")
        assert response.status_code == 401

    def test_get_security_dashboard_insufficient_scope(self, regular_client):
        """Test security dashboard access without admin scope"""
        response = regular_client.get("/api/security/dashboard")
        assert response.status_code == 403

    def test_get_security_dashboard_service_error(self, admin_client, mock_security_monitor):
        """Test security dashboard with service error"""
        # Setup mock to raise exception
        mock_security_monitor.get_security_status.side_effect = Exception("Service error")

        response = admin_client.get("/api/security/dashboard")

        assert response.status_code == 500
        assert "Error retrieving security dashboard data" in response.json()["detail"]

    def test_get_security_alerts_success(self, admin_client, mock_security_monitor, sample_alerts):
        """Test successful security alerts retrieval"""
        # Setup mock
        mock_security_monitor.get_recent_alerts.return_value = sample_alerts

        response = admin_client.get("/api/security/alerts")

        assert response.status_code == 200
        data = response.json()

        assert "alerts" in data
        assert len(data["alerts"]) == 3
        assert data["alerts"][0]["severity"] == "critical"
        assert data["alerts"][1]["severity"] == "high"
        assert data["alerts"][2]["severity"] == "medium"

    def test_get_security_alerts_unauthorized(self, unauth_client):
        """Test security alerts access without authentication"""
        response = unauth_client.get("/api/security/alerts")
        assert response.status_code == 401

    def test_get_security_alerts_insufficient_scope(self, regular_client):
        """Test security alerts access without admin scope"""
        response = regular_client.get("/api/security/alerts")
        assert response.status_code == 403

    def test_get_security_alerts_empty(self, admin_client, mock_security_monitor):
        """Test security alerts retrieval with no alerts"""
        # Setup mock to return empty list
        mock_security_monitor.get_recent_alerts.return_value = []

        response = admin_client.get("/api/security/alerts")

        assert response.status_code == 200
        data = response.json()

        assert "alerts" in data
        assert len(data["alerts"]) == 0

    def test_get_active_threats_success(self, admin_client, mock_security_monitor,
                                       mock_advanced_security, sample_security_status,
                                       sample_advanced_security_status, sample_threat_patterns):
        """Test successful active threats retrieval"""
        # Setup mocks
        mock_security_monitor.get_security_status.return_value = sample_security_status
        mock_advanced_security.get_security_status.return_value = sample_advanced_security_status
        mock_advanced_security.get_threat_patterns.return_value = sample_threat_patterns

        response = admin_client.get("/api/security/threats")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "active_threats" in data
        assert "blocked_ips" in data
        assert "threat_patterns" in data

        # Verify active threats
        assert len(data["active_threats"]) == 1
        assert data["active_threats"][0]["type"] == "threat_detected"

        # Verify blocked IPs
        assert data["blocked_ips"] == ["192.168.1.100", "10.0.0.1"]

        # Verify threat patterns
        assert len(data["threat_patterns"]) == 3
        assert data["threat_patterns"][0]["pattern"] == "sql_injection"

    def test_get_active_threats_unauthorized(self, unauth_client):
        """Test active threats access without authentication"""
        response = unauth_client.get("/api/security/threats")
        assert response.status_code == 401

    def test_get_active_threats_insufficient_scope(self, regular_client):
        """Test active threats access without admin scope"""
        response = regular_client.get("/api/security/threats")
        assert response.status_code == 403

    def test_get_active_threats_no_threats(self, admin_client, mock_security_monitor,
                                           mock_advanced_security):
        """Test active threats retrieval with no threats"""
        # Setup mocks to return empty data
        mock_security_monitor.get_security_status.return_value = {
            "recent_events": []
        }
        mock_advanced_security.get_security_status.return_value = {
            "blocked_ips": []
        }
        mock_advanced_security.get_threat_patterns.return_value = []

        response = admin_client.get("/api/security/threats")

        assert response.status_code == 200
        data = response.json()

        assert data["active_threats"] == []
        assert data["blocked_ips"] == []
        assert data["threat_patterns"] == []

    def test_get_ai_security_status_success(self, admin_client, mock_ai_security_manager,
                                            sample_ai_security_status):
        """Test successful AI security status retrieval"""
        # Setup mock
        mock_ai_security_manager.get_ai_security_status.return_value = sample_ai_security_status

        response = admin_client.get("/api/security/ai-security")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "metrics" in data
        assert "model_usage" in data
        assert "events" in data

        # Verify metrics
        assert data["metrics"]["model_requests"] == 500
        assert data["metrics"]["suspicious_activities"] == 5

        # Verify model usage
        assert data["model_usage"]["gpt-4"] == 300
        assert data["model_usage"]["claude"] == 200

        # Verify events
        assert len(data["events"]) == 2
        assert data["events"][0]["type"] == "ai_threat"

    def test_get_ai_security_status_unauthorized(self, unauth_client):
        """Test AI security status access without authentication"""
        response = unauth_client.get("/api/security/ai-security")
        assert response.status_code == 401

    def test_get_ai_security_status_insufficient_scope(self, regular_client):
        """Test AI security status access without admin scope"""
        response = regular_client.get("/api/security/ai-security")
        assert response.status_code == 403

    def test_update_defense_rules_success(self, admin_client, mock_advanced_security):
        """Test successful defense rules update"""
        # Setup mock
        mock_advanced_security.update_defense_rules.return_value = None

        rules_data = {
            "firewall": {"enabled": True, "rules": ["block_sql_injection"]},
            "ids": {"enabled": True, "sensitivity": "high"},
            "waf": {"enabled": False}
        }

        response = admin_client.post("/api/security/update-defense-rules", json=rules_data)

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Defense rules updated successfully"
        mock_advanced_security.update_defense_rules.assert_called_once_with(rules_data)

    def test_update_defense_rules_unauthorized(self, unauth_client):
        """Test defense rules update without authentication"""
        rules_data = {"firewall": {"enabled": True}}

        response = unauth_client.post("/api/security/update-defense-rules", json=rules_data)
        assert response.status_code == 401

    def test_update_defense_rules_insufficient_scope(self, regular_client):
        """Test defense rules update without admin scope"""
        rules_data = {"firewall": {"enabled": True}}

        response = regular_client.post("/api/security/update-defense-rules", json=rules_data)
        assert response.status_code == 403

    def test_update_defense_rules_invalid_data(self, admin_client):
        """Test defense rules update with invalid data"""
        invalid_data = [
            "not_a_dict",
            123,
            None,
            [],
            {"invalid": "structure"}
        ]

        for invalid_input in invalid_data:
            response = admin_client.post("/api/security/update-defense-rules", json=invalid_input)
            assert response.status_code == 422

    def test_update_defense_rules_service_error(self, admin_client, mock_advanced_security):
        """Test defense rules update with service error"""
        # Setup mock to raise exception
        mock_advanced_security.update_defense_rules.side_effect = Exception("Update failed")

        rules_data = {"firewall": {"enabled": True}}

        response = admin_client.post("/api/security/update-defense-rules", json=rules_data)

        assert response.status_code == 500
        assert "Error updating defense rules" in response.json()["detail"]

    def test_security_api_rate_limiting(self, admin_client, mock_security_monitor,
                                        mock_advanced_security, mock_ai_security_manager,
                                        sample_security_status, sample_advanced_security_status,
                                        sample_ai_security_status):
        """Test rate limiting on security API endpoints"""
        # Setup mocks
        mock_security_monitor.get_security_status.return_value = sample_security_status
        mock_advanced_security.get_security_status.return_value = sample_advanced_security_status
        mock_ai_security_manager.get_ai_security_status.return_value = sample_ai_security_status

        # Make multiple requests to test rate limiting
        for i in range(50):
            response = admin_client.get("/api/security/dashboard")
            if response.status_code == 429:
                break

        # If we haven't hit rate limit, check the last response
        if response.status_code != 429:
            assert response.status_code == 200

    def test_security_dashboard_data_completeness(self, admin_client, mock_security_monitor,
                                                  mock_advanced_security, mock_ai_security_manager,
                                                  sample_security_status, sample_advanced_security_status,
                                                  sample_ai_security_status):
        """Test that security dashboard data is complete and well-formed"""
        # Setup mocks with comprehensive data
        mock_security_monitor.get_security_status.return_value = sample_security_status
        mock_advanced_security.get_security_status.return_value = sample_advanced_security_status
        mock_ai_security_manager.get_ai_security_status.return_value = sample_ai_security_status

        response = admin_client.get("/api/security/dashboard")
        data = response.json()

        # Check all required fields exist
        required_fields = [
            "timestamp", "threat_level", "threat_level_text", "alerts",
            "metrics", "events", "defenses", "ai_security"
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Check nested structures
        assert "count" in data["alerts"]
        assert "recent" in data["alerts"]
        assert "general" in data["metrics"]
        assert "ai_specific" in data["metrics"]
        assert "recent" in data["events"]
        assert "ai_events" in data["events"]
        assert "active" in data["defenses"]
        assert "blocked_requests" in data["defenses"]
        assert "model_usage" in data["ai_security"]
        assert "recent_threats" in data["ai_security"]

    def test_concurrent_security_requests(self, admin_client, mock_security_monitor,
                                          mock_advanced_security, mock_ai_security_manager,
                                          sample_security_status, sample_advanced_security_status,
                                          sample_ai_security_status):
        """Test concurrent security API requests"""
        import threading
        import time

        # Setup mocks
        mock_security_monitor.get_security_status.return_value = sample_security_status
        mock_advanced_security.get_security_status.return_value = sample_advanced_security_status
        mock_ai_security_manager.get_ai_security_status.return_value = sample_ai_security_status

        results = []

        def make_request():
            response = admin_client.get("/api/security/dashboard")
            results.append(response.status_code)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should be successful
        assert all(status == 200 for status in results)

    @pytest.mark.parametrize("endpoint", [
        "/api/security/dashboard",
        "/api/security/alerts",
        "/api/security/threats",
        "/api/security/ai-security"
    ])
    def test_security_endpoints_response_structure(self, admin_client, endpoint):
        """Test that all security endpoints return proper response structure"""
        # Mock responses for each endpoint
        with patch('app.api.security_dashboard.security_monitor') as mock_monitor, \
             patch('app.api.security_dashboard.advanced_security') as mock_advanced, \
             patch('app.api.security_dashboard.ai_security_manager') as mock_ai:

            # Setup basic mocks
            mock_monitor.get_security_status = AsyncMock(return_value={
                "threat_level": 1,
                "threat_level_text": "Low",
                "recent_alerts": [],
                "recent_events": [],
                "metrics": {}
            })
            mock_monitor.get_recent_alerts = AsyncMock(return_value=[])
            mock_advanced.get_security_status = AsyncMock(return_value={
                "active_defenses": [],
                "blocked_requests": 0
            })
            mock_advanced.get_threat_patterns = AsyncMock(return_value=[])
            mock_ai.get_ai_security_status = AsyncMock(return_value={
                "metrics": {},
                "model_usage": {},
                "events": []
            })

            response = admin_client.get(endpoint)

            # Should be successful
            assert response.status_code == 200

            # Should return JSON
            assert response.headers["content-type"] == "application/json"

            # Should have some data structure
            data = response.json()
            assert isinstance(data, dict)

    def test_security_api_error_handling(self, admin_client):
        """Test that security API handles errors gracefully"""
        with patch('app.api.security_dashboard.security_monitor') as mock_monitor:
            # Setup mock to raise exception
            mock_monitor.get_security_status.side_effect = Exception("Database connection failed")

            response = admin_client.get("/api/security/dashboard")

            # Should return 500 error
            assert response.status_code == 500

            # Should have error details
            data = response.json()
            assert "detail" in data
            assert "Error retrieving security dashboard data" in data["detail"]
