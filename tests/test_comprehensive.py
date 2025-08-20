import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json

from app.main import app
from app.core.config import settings
from app.core.security_metrics import SecurityMetrics
from app.services.ai_chat import AIChatService
from app.db.session import Base
from app.models import User, Conversation, Message

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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

class TestSecurityMetrics:
    """Comprehensive test suite for SecurityMetrics."""

    def test_security_metrics_initialization(self, security_metrics):
        """Test that security metrics initialize correctly."""
        assert security_metrics.SYSTEM_SECURITY_SCORE._value.get() == 100
        assert security_metrics.ACTIVE_SESSIONS._value.get() == 0
        assert security_metrics.BLOCKED_IPS._value.get() == 0

    def test_record_security_event(self, security_metrics):
        """Test recording security events."""
        security_metrics.record_security_event("test_event", "high")

        # Check that the event was recorded
        events = security_metrics._get_events_breakdown()
        assert "test_event" in events
        assert events["test_event"]["high"] == 1

    def test_record_request(self, security_metrics):
        """Test recording HTTP requests."""
        security_metrics.record_request("GET", "/test", 200, 0.1)

        requests = security_metrics._get_requests_breakdown()
        assert "GET /test" in requests
        assert requests["GET /test"]["200"] == 1

    def test_record_auth_attempt(self, security_metrics):
        """Test recording authentication attempts."""
        security_metrics.record_auth_attempt("success")
        security_metrics.record_auth_attempt("failure")

        auth = security_metrics._get_auth_breakdown()
        assert auth["success"] == 1
        assert auth["failure"] == 1

    def test_auth_success_rate_calculation(self, security_metrics):
        """Test authentication success rate calculation."""
        # Record some auth attempts
        security_metrics.record_auth_attempt("success")
        security_metrics.record_auth_attempt("success")
        security_metrics.record_auth_attempt("failure")

        rate = security_metrics._calculate_auth_success_rate()
        assert rate == 66.66666666666666  # 2/3 * 100

    def test_get_current_metrics(self, security_metrics):
        """Test getting current metrics snapshot."""
        # Record some data
        security_metrics.record_security_event("test", "info")
        security_metrics.record_auth_attempt("success")

        metrics = security_metrics.get_current_metrics()

        assert "security_score" in metrics
        assert "active_sessions" in metrics
        assert "blocked_ips" in metrics
        assert "total_events" in metrics
        assert "auth_success_rate" in metrics
        assert metrics["security_score"] == 100

    def test_get_detailed_metrics(self, security_metrics):
        """Test getting detailed metrics."""
        # Record some data
        security_metrics.record_security_event("test", "high")
        security_metrics.record_auth_attempt("success")
        security_metrics.record_request("GET", "/test", 200, 0.1)

        metrics = security_metrics.get_detailed_metrics()

        assert "security_score" in metrics
        assert "events" in metrics
        assert "auth" in metrics
        assert "requests" in metrics
        assert metrics["security_score"] == 100

class TestAIChatService:
    """Comprehensive test suite for AIChatService."""

    @pytest.mark.asyncio
    async def test_process_message_new_conversation(self, ai_chat_service):
        """Test processing a message with new conversation."""
        with patch.object(ai_chat_service, '_generate_ai_response') as mock_generate:
            mock_generate.return_value = {
                "response": "Test response",
                "model": "test_model",
                "confidence": 0.9
            }

            result = await ai_chat_service.process_message("Hello")

            assert result["response"] == "Test response"
            assert result["model_used"] == "test_model"
            assert result["confidence"] == 0.9
            assert "conversation_id" in result
            assert "message_id" in result

    @pytest.mark.asyncio
    async def test_process_message_existing_conversation(self, ai_chat_service):
        """Test processing a message with existing conversation."""
        conversation_id = "test_conv_id"
        ai_chat_service.conversations[conversation_id] = []

        with patch.object(ai_chat_service, '_generate_ai_response') as mock_generate:
            mock_generate.return_value = {
                "response": "Test response",
                "model": "test_model",
                "confidence": 0.9
            }

            result = await ai_chat_service.process_message("Hello", conversation_id)

            assert result["conversation_id"] == conversation_id
            assert len(ai_chat_service.conversations[conversation_id]) == 2  # User + AI message

    @pytest.mark.asyncio
    async def test_generate_ai_response_coding_task(self, ai_chat_service):
        """Test AI response generation for coding tasks."""
        with patch.object(ai_chat_service.mlops_manager, 'generate_code') as mock_generate:
            mock_generate.return_value = {"generated_text": "def test(): pass"}

            result = await ai_chat_service._generate_ai_response("Write a function", "conv_id", "en")

            assert result["response"] == "def test(): pass"
            assert result["model"] == "phind-codellama"

    @pytest.mark.asyncio
    async def test_generate_ai_response_general_task(self, ai_chat_service):
        """Test AI response generation for general tasks."""
        with patch.object(ai_chat_service.mlops_manager, 'generate_text') as mock_generate:
            mock_generate.return_value = "General response"

            result = await ai_chat_service._generate_ai_response("Hello", "conv_id", "en")

            assert result["response"] == "General response"
            assert result["model"] == "mistral"

    @pytest.mark.asyncio
    async def test_generate_ai_response_fallback(self, ai_chat_service):
        """Test AI response generation fallback mechanism."""
        with patch.object(ai_chat_service.mlops_manager, 'generate_text') as mock_generate:
            mock_generate.side_effect = Exception("Primary model failed")

            with patch.object(ai_chat_service.mlops_manager, 'generate_text') as mock_fallback:
                mock_fallback.return_value = "Fallback response"

                result = await ai_chat_service._generate_ai_response("Hello", "conv_id", "en")

                assert result["response"] == "Fallback response"
                assert result["model"] == "llama3"

    def test_is_coding_task(self, ai_chat_service):
        """Test coding task detection."""
        assert ai_chat_service._is_coding_task("Write a function in Python")
        assert ai_chat_service._is_coding_task("Debug this code")
        assert ai_chat_service._is_coding_task("Create an API")
        assert not ai_chat_service._is_coding_task("Hello, how are you?")
        assert not ai_chat_service._is_coding_task("What's the weather?")

    def test_detect_programming_language(self, ai_chat_service):
        """Test programming language detection."""
        assert ai_chat_service._detect_programming_language("Write Python code") == "python"
        assert ai_chat_service._detect_programming_language("JavaScript function") == "javascript"
        assert ai_chat_service._detect_programming_language("Java class") == "java"
        assert ai_chat_service._detect_programming_language("Generic code") == "python"  # Default

    def test_clean_response(self, ai_chat_service):
        """Test response cleaning."""
        dirty_response = "Assistant: Hello\n\n\nUser: Hi\n\nHello world"
        clean_response = ai_chat_service._clean_response(dirty_response)
        assert clean_response == "Hello\n\nHi\n\nHello world"

    @pytest.mark.asyncio
    async def test_conversation_management(self, ai_chat_service):
        """Test conversation management methods."""
        # Create a conversation
        result = await ai_chat_service.process_message("Hello")
        conversation_id = result["conversation_id"]

        # Get conversation
        conversation = await ai_chat_service.get_conversation(conversation_id)
        assert conversation is not None
        assert len(conversation["messages"]) == 2

        # Get conversations list
        conversations = await ai_chat_service.get_conversations()
        assert len(conversations) == 1
        assert conversations[0]["id"] == conversation_id

        # Clear conversation
        cleared = await ai_chat_service.clear_conversation(conversation_id)
        assert cleared is True
        assert len(ai_chat_service.conversations[conversation_id]) == 0

        # Delete conversation
        deleted = await ai_chat_service.delete_conversation(conversation_id)
        assert deleted is True
        assert conversation_id not in ai_chat_service.conversations

        # Clear all conversations
        await ai_chat_service.clear_all_conversations()
        assert len(ai_chat_service.conversations) == 0

class TestAPIEndpoints:
    """Comprehensive test suite for API endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data

    def test_security_overview(self, client):
        """Test security overview endpoint."""
        response = client.get("/api/v1/security_status/overview")
        assert response.status_code == 200
        data = response.json()
        assert "security_score" in data
        assert data["security_score"] == 100
        assert "security_enabled" in data

    def test_compliance_status(self, client):
        """Test compliance status endpoint."""
        response = client.get("/api/v1/security_status/compliance")
        assert response.status_code == 200
        data = response.json()
        assert "gdpr" in data
        assert "soc2" in data
        assert "iso27001" in data
        assert data["gdpr"]["compliant"] is True
        assert data["soc2"]["compliant"] is True
        assert data["iso27001"]["compliant"] is True
        assert data["gdpr"]["compliance_score"] == 100

    def test_security_metrics(self, client):
        """Test security metrics endpoint."""
        response = client.get("/api/v1/security_status/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "security_score" in data
        assert "active_sessions" in data
        assert "blocked_ips" in data

    def test_firewall_rules(self, client):
        """Test firewall rules endpoint."""
        response = client.get("/api/v1/security_status/firewall-rules")
        assert response.status_code == 200
        data = response.json()
        assert "rate_limiting" in data
        assert "cors_origins" in data
        assert "security_headers" in data

    def test_backup_status(self, client):
        """Test backup status endpoint."""
        response = client.get("/api/v1/security_status/backup-status")
        assert response.status_code == 200
        data = response.json()
        assert "last_backup" in data
        assert "backup_status" in data
        assert "encryption_enabled" in data
        assert data["encryption_enabled"] is True

class TestDatabaseModels:
    """Comprehensive test suite for database models."""

    def test_user_model(self, db_session):
        """Test User model."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        retrieved_user = db_session.query(User).filter(User.email == "test@example.com").first()
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.is_active is True

    def test_conversation_model(self, db_session):
        """Test Conversation model."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass"
        )
        db_session.add(user)
        db_session.commit()

        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation"
        )
        db_session.add(conversation)
        db_session.commit()

        retrieved_conversation = db_session.query(Conversation).filter(Conversation.title == "Test Conversation").first()
        assert retrieved_conversation is not None
        assert retrieved_conversation.user_id == user.id

    def test_message_model(self, db_session):
        """Test Message model."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashedpass"
        )
        db_session.add(user)
        db_session.commit()

        conversation = Conversation(
            user_id=user.id,
            title="Test Conversation"
        )
        db_session.add(conversation)
        db_session.commit()

        message = Message(
            conversation_id=conversation.id,
            role="user",
            content="Hello world"
        )
        db_session.add(message)
        db_session.commit()

        retrieved_message = db_session.query(Message).filter(Message.content == "Hello world").first()
        assert retrieved_message is not None
        assert retrieved_message.conversation_id == conversation.id
        assert retrieved_message.role == "user"

class TestConfiguration:
    """Comprehensive test suite for configuration."""

    def test_settings_initialization(self):
        """Test that settings initialize correctly."""
        assert settings.PROJECT_NAME == "Samoey Copilot"
        assert settings.VERSION == "1.0.0"
        assert settings.API_V1_STR == "/api/v1"
        assert settings.SECURITY_ENABLED is True
        assert settings.RATE_LIMIT_ENABLED is True

    def test_cors_origins_validation(self):
        """Test CORS origins validation."""
        assert len(settings.BACKEND_CORS_ORIGINS) > 0
        for origin in settings.BACKEND_CORS_ORIGINS:
            assert str(origin).startswith("http")

    def test_database_url_generation(self):
        """Test database URL generation."""
        assert settings.DATABASE_URL is not None
        assert settings.DATABASE_URL.startswith("postgresql://")

    def test_redis_url(self):
        """Test Redis URL configuration."""
        assert settings.REDIS_URL == "redis://localhost:6379"

    def test_security_settings(self):
        """Test security-related settings."""
        assert settings.SECURITY_ENABLED is True
        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.RATE_LIMIT_REQUESTS == 100
        assert settings.RATE_LIMIT_WINDOW == 60

# Integration tests
class TestIntegration:
    """Integration tests for the complete system."""

    def test_full_request_cycle(self, client):
        """Test a full request cycle through the system."""
        # Test health check
        health_response = client.get("/health")
        assert health_response.status_code == 200

        # Test root endpoint
        root_response = client.get("/")
        assert root_response.status_code == 200

        # Test security endpoint
        security_response = client.get("/api/v1/security_status/overview")
        assert security_response.status_code == 200

        # Verify consistency across endpoints
        security_data = security_response.json()
        assert security_data["security_score"] == 100

    @pytest.mark.asyncio
    async def test_ai_chat_integration(self, ai_chat_service):
        """Test AI chat service integration."""
        # Test message processing
        with patch.object(ai_chat_service, '_generate_ai_response') as mock_generate:
            mock_generate.return_value = {
                "response": "Integration test response",
                "model": "test_model",
                "confidence": 0.95
            }

            result = await ai_chat_service.process_message("Integration test")

            # Verify the complete flow
            assert result["response"] == "Integration test response"
            assert result["confidence"] == 0.95
            assert "conversation_id" in result

            # Verify conversation was stored
            conversation = await ai_chat_service.get_conversation(result["conversation_id"])
            assert conversation is not None
            assert len(conversation["messages"]) == 2

    def test_error_handling_integration(self, client):
        """Test error handling across the system."""
        # Test 404 handling
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        # Test method not allowed
        response = client.patch("/health")
        assert response.status_code == 405

# Performance tests
class TestPerformance:
    """Performance tests for the system."""

    def test_security_metrics_performance(self, security_metrics):
        """Test security metrics performance."""
        import time

        # Record many events quickly
        start_time = time.time()
        for i in range(1000):
            security_metrics.record_security_event(f"event_{i}", "info")
        end_time = time.time()

        # Should complete in under 1 second
        assert end_time - start_time < 1.0

    @pytest.mark.asyncio
    async def test_ai_chat_performance(self, ai_chat_service):
        """Test AI chat service performance."""
        import time
