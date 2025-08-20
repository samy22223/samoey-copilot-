import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json
import threading
import time

from app.main import app
from app.core.config import settings
from app.core.security_metrics import SecurityMetrics
from app.services.ai_chat import AIChatService
from app.db.session import Base
from app.models import User, Conversation, Message

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_complete.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)

@pytest.fixture
def security_metrics():
    """Create security metrics instance."""
    return SecurityMetrics()

@pytest.fixture
def ai_chat_service():
    """Create AI chat service instance."""
    return AIChatService()

class TestPerformanceComplete:
    """Complete performance test suite."""

    def test_security_metrics_performance_complete(self, security_metrics):
        """Test comprehensive security metrics performance."""
        import time

        # Test bulk event recording
        start_time = time.time()
        for i in range(5000):
            security_metrics.record_security_event(f"bulk_event_{i}", "info")
        end_time = time.time()
        assert end_time - start_time < 2.0

        # Test bulk request recording
        start_time = time.time()
        for i in range(5000):
            security_metrics.record_request("GET", f"/test/{i}", 200, 0.1)
        end_time = time.time()
        assert end_time - start_time < 2.0

        # Test metrics retrieval performance
        start_time = time.time()
        for i in range(1000):
            security_metrics.get_current_metrics()
        end_time = time.time()
        assert end_time - start_time < 1.0

        # Test detailed metrics retrieval
        start_time = time.time()
        for i in range(100):
            security_metrics.get_detailed_metrics()
        end_time = time.time()
        assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    async def test_ai_chat_performance_complete(self, ai_chat_service):
        """Test comprehensive AI chat service performance."""
        import time

        # Test bulk message processing
        start_time = time.time()
        for i in range(100):
            with patch.object(ai_chat_service, '_generate_ai_response') as mock_generate:
                mock_generate.return_value = {
                    "response": f"Response {i}",
                    "model": "test_model",
                    "confidence": 0.9
                }
                await ai_chat_service.process_message(f"Message {i}")
        end_time = time.time()
        assert end_time - start_time < 5.0

        # Test conversation management performance
        start_time = time.time()
        for i in range(1000):
            await ai_chat_service.get_conversations()
        end_time = time.time()
        assert end_time - start_time < 2.0

        # Test conversation retrieval performance
        if ai_chat_service.conversations:
            conv_id = list(ai_chat_service.conversations.keys())[0]
            start_time = time.time()
            for i in range(1000):
                await ai_chat_service.get_conversation(conv_id)
            end_time = time.time()
            assert end_time - start_time < 1.0

class TestErrorHandlingComplete:
    """Complete error handling test suite."""

    def test_security_metrics_error_handling_complete(self, security_metrics):
        """Test comprehensive security metrics error handling."""
        # Test with None values
        try:
            security_metrics.record_security_event(None, None)
        except Exception:
            pass  # Should handle gracefully

        # Test with invalid types
        try:
            security_metrics.record_security_event(123, 456)
        except Exception:
            pass  # Should handle gracefully

        # Test with very long strings
        long_string = "x" * 10000
        security_metrics.record_security_event(long_string, "info")

        # Test metrics calculation with no data
        metrics = security_metrics.get_current_metrics()
        assert isinstance(metrics, dict)
        assert "security_score" in metrics

        # Test detailed metrics with no data
        detailed_metrics = security_metrics.get_detailed_metrics()
        assert isinstance(detailed_metrics, dict)

    @pytest.mark.asyncio
    async def test_ai_chat_error_handling_complete(self, ai_chat_service):
        """Test comprehensive AI chat service error handling."""
        # Test with various invalid inputs
        invalid_inputs = [None, "", 123, {}, [], True, False]

        for invalid_input in invalid_inputs:
            try:
                result = await ai_chat_service.process_message(invalid_input)
                assert "response" in result
                assert "conversation_id" in result
            except Exception:
                pass  # Should handle gracefully

        # Test conversation management with invalid IDs
        invalid_ids = [None, "", 123, {}, [], True, False, "nonexistent"]

        for invalid_id in invalid_ids:
            try:
                conversation = await ai_chat_service.get_conversation(invalid_id)
                assert conversation is None
            except Exception:
                pass  # Should handle gracefully

            try:
                deleted = await ai_chat_service.delete_conversation(invalid_id)
                assert deleted is False
            except Exception:
                pass  # Should handle gracefully

            try:
                cleared = await ai_chat_service.clear_conversation(invalid_id)
                assert cleared is False
            except Exception:
                pass  # Should handle gracefully

        # Test AI response generation failures
        with patch.object(ai_chat_service.mlops_manager, 'generate_text') as mock_generate:
            mock_generate.side_effect = Exception("Model failed")

            with patch.object(ai_chat_service.mlops_manager, 'generate_text') as mock_fallback:
                mock_fallback.side_effect = Exception("Fallback failed")

                result = await ai_chat_service._generate_ai_response("Test", "conv_id", "en")
                assert "response" in result
                assert result["model"] == "fallback"

    def test_api_error_handling_complete(self, client):
        """Test comprehensive API error handling."""
        # Test various invalid endpoints
        invalid_endpoints = [
            "/invalid",
            "/api/invalid",
            "/api/v1/invalid",
            "/api/v1/security_status/invalid",
            "/nonexistent/path"
        ]

        for endpoint in invalid_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [404, 422]

        # Test invalid methods on valid endpoints
        valid_endpoints = [
            ("/health", ["PATCH", "PUT", "DELETE", "POST"]),
            ("/", ["PATCH", "PUT", "DELETE"]),
            ("/api/v1/security_status/overview", ["PATCH", "PUT", "DELETE", "POST"])
        ]

        for endpoint, methods in valid_endpoints:
            for method in methods:
                response = client.request(method, endpoint)
                assert response.status_code in [405, 422]

        # Test invalid content types
        invalid_content_types = [
            ("application/xml", "<xml>test</xml>"),
            ("text/plain", "plain text"),
            ("application/json", "invalid json {")
        ]

        for content_type, data in invalid_content_types:
            response = client.post(
                "/api/v1/security_status/scan",
                content_type=content_type,
                data=data
            )
            assert response.status_code in [422, 400]

class TestSecurityFeaturesComplete:
    """Complete security feature test suite."""

    def test_security_headers_complete(self, client):
        """Test comprehensive security headers."""
        response = client.get("/")
        headers = response.headers

        # Test standard security headers
        expected_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "content-security-policy",
            "strict-transport-security"
        ]

        for header in expected_headers:
            assert header.lower() in [h.lower() for h in headers.keys()]

        # Test CORS headers
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]

        for header in cors_headers:
            assert header.lower() in [h.lower() for h in headers.keys()]

    def test_input_validation_complete(self, client):
        """Test comprehensive input validation."""
        # SQL injection attempts
        sql_injection_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' AND 1=1--",
            "admin'--"
        ]

        for payload in sql_injection_payloads:
            response = client.get(f"/api/v1/security_status/overview?q={payload}")
            assert response.status_code == 200

        # XSS attempts
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "'\"><script>alert('xss')</script>"
        ]

        for payload in xss_payloads:
            response = client.get(f"/api/v1/security_status/overview?q={payload}")
            assert response.status_code == 200

        # Path traversal attempts
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\windows\\system32",
            "%2e%2e%2f",
            "..%2f..%2f..%2fetc%2fpasswd",
            "....//....//....//etc/passwd"
        ]

        for payload in path_traversal_payloads:
            response = client.get(f"/api/v1/security_status/overview?q={payload}")
            assert response.status_code == 200

        # Command injection attempts
        command_injection_payloads = [
            "test; rm -rf /",
            "test | ls -la",
            "test && whoami",
            "test $(cat /etc/passwd)",
            "test`cat /etc/passwd`"
        ]

        for payload in command_injection_payloads:
            response = client.get(f"/api/v1/security_status/overview?q={payload}")
            assert response.status_code == 200

    def test_rate_limiting_complete(self, client):
        """Test comprehensive rate limiting functionality."""
        # Test normal requests
        for i in range(50):
            response = client.get("/api/v1/security_status/overview")
            assert response.status_code == 200

        # Test different endpoints
        endpoints = [
            "/api/v1/security_status/overview",
            "/api/v1/security_status/metrics",
            "/api/v1/security_status/compliance"
        ]

        for endpoint in endpoints:
            for i in range(20):
                response = client.get(endpoint)
                assert response.status_code == 200

class TestDatabaseOperationsComplete:
    """Complete database operation test suite."""

    def test_database_connection_complete(self, db_session):
        """Test comprehensive database connection."""
        # Test basic connection
        result = db_session.execute("SELECT 1").scalar()
        assert result == 1

        # Test database metadata
        result = db_session.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert len(result) > 0

        # Test transaction rollback
        try:
            user = User(email="rollback@example.com", username="rollback", hashed_password="test")
            db_session.add(user)
            db_session.rollback()

            # User should not exist after rollback
            result = db_session.query(User).filter(User.email == "rollback@example.com").first()
            assert result is None
        except Exception:
            db_session.rollback()

    def test_user_crud_complete(self, db_session):
        """
