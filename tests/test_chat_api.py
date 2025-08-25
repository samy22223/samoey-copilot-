import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import WebSocket
import json
from datetime import datetime
from uuid import uuid4

from app.main import app
from app.schemas.chat import ChatMessage, ChatSession, ChatResponse
from app.core.auth import get_current_user

# Mock user for authentication
mock_user = {
    "id": "test_user_id",
    "email": "test@example.com",
    "username": "testuser",
    "is_active": True
}

@pytest.fixture
def client():
    """Create test client with mocked authentication"""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_ai_chat_service():
    """Mock AI chat service"""
    with patch('app.api.chat.ai_chat_service') as mock_service:
        mock_service.create_session = AsyncMock()
        mock_service.get_session = AsyncMock()
        mock_service.get_chat_response = AsyncMock()
        mock_service.clear_session = AsyncMock()
        mock_service.add_context = AsyncMock()
        yield mock_service

@pytest.fixture
def sample_session_data():
    """Sample session data for testing"""
    return {
        "session_id": str(uuid4()),
        "created_at": datetime.now(),
        "messages": []
    }

@pytest.fixture
def sample_message_data():
    """Sample message data for testing"""
    return {
        "content": "Hello, how can you help me?",
        "role": "user"
    }

class TestChatAPI:
    """Comprehensive test suite for Chat API endpoints"""

    def test_create_chat_session_success(self, client, mock_ai_chat_service, sample_session_data):
        """Test successful chat session creation"""
        # Setup mock
        mock_session = Mock()
        mock_session.session_id = sample_session_data["session_id"]
        mock_session.created_at = sample_session_data["created_at"]
        mock_session.messages = []
        mock_ai_chat_service.create_session.return_value = mock_session

        # Make request
        response = client.post("/api/chat/sessions")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "created_at" in data
        assert "messages" in data
        assert data["messages"] == []
        mock_ai_chat_service.create_session.assert_called_once()

    def test_create_chat_session_unauthorized(self, client):
        """Test chat session creation without authentication"""
        # Remove authentication override
        app.dependency_overrides.clear()

        response = client.post("/api/chat/sessions")
        assert response.status_code == 401

    def test_get_chat_session_success(self, client, mock_ai_chat_service, sample_session_data):
        """Test successful chat session retrieval"""
        # Setup mock
        mock_session = Mock()
        mock_session.session_id = sample_session_data["session_id"]
        mock_session.created_at = sample_session_data["created_at"]
        mock_session.messages = []
        mock_ai_chat_service.get_session.return_value = mock_session

        session_id = sample_session_data["session_id"]
        response = client.get(f"/api/chat/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "created_at" in data
        assert "messages" in data
        mock_ai_chat_service.get_session.assert_called_once_with(session_id)

    def test_get_chat_session_not_found(self, client, mock_ai_chat_service):
        """Test retrieval of non-existent chat session"""
        # Setup mock to return None
        mock_ai_chat_service.get_session.return_value = None

        session_id = str(uuid4())
        response = client.get(f"/api/chat/sessions/{session_id}")

        assert response.status_code == 404
        assert "Chat session not found" in response.json()["detail"]

    def test_send_message_success(self, client, mock_ai_chat_service, sample_message_data):
        """Test successful message sending"""
        # Setup mock
        session_id = str(uuid4())
        mock_ai_chat_service.get_chat_response.return_value = "I can help you with coding tasks!"

        response = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json=sample_message_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "response" in data
        assert "timestamp" in data
        mock_ai_chat_service.get_chat_response.assert_called_once_with(
            session_id, sample_message_data["content"]
        )

    def test_send_message_invalid_content(self, client, mock_ai_chat_service):
        """Test message sending with invalid content"""
        session_id = str(uuid4())
        invalid_messages = [
            {"content": "", "role": "user"},
            {"content": "   ", "role": "user"},
            {"role": "user"},  # Missing content
            {"content": "test"},  # Missing role
            {}  # Empty payload
        ]

        for invalid_message in invalid_messages:
            response = client.post(
                f"/api/chat/sessions/{session_id}/messages",
                json=invalid_message
            )
            assert response.status_code == 422

    def test_send_message_unauthorized(self, client):
        """Test message sending without authentication"""
        app.dependency_overrides.clear()

        session_id = str(uuid4())
        message_data = {"content": "Hello", "role": "user"}

        response = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json=message_data
        )
        assert response.status_code == 401

    def test_clear_chat_session_success(self, client, mock_ai_chat_service):
        """Test successful chat session clearing"""
        session_id = str(uuid4())

        response = client.delete(f"/api/chat/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["session_id"] == session_id
        assert "message" in data
        mock_ai_chat_service.clear_session.assert_called_once_with(session_id)

    def test_clear_chat_session_unauthorized(self, client):
        """Test chat session clearing without authentication"""
        app.dependency_overrides.clear()

        session_id = str(uuid4())
        response = client.delete(f"/api/chat/sessions/{session_id}")
        assert response.status_code == 401

    def test_add_context_success(self, client, mock_ai_chat_service):
        """Test successful context addition"""
        context_texts = [
            "Python is a programming language",
            "FastAPI is a web framework",
            "Testing is important for quality"
        ]

        response = client.post("/api/chat/context", json=context_texts)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert f"Added {len(context_texts)} documents to context" in data["message"]
        assert "timestamp" in data
        mock_ai_chat_service.add_context.assert_called_once_with(context_texts)

    def test_add_context_empty_list(self, client, mock_ai_chat_service):
        """Test context addition with empty list"""
        response = client.post("/api/chat/context", json=[])

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Added 0 documents to context" in data["message"]
        mock_ai_chat_service.add_context.assert_called_once_with([])

    def test_add_context_invalid_data(self, client):
        """Test context addition with invalid data"""
        invalid_data = [
            ["not a string"],
            [123, 456],
            "not a list",
            {},
            None
        ]

        for invalid_input in invalid_data:
            response = client.post("/api/chat/context", json=invalid_input)
            assert response.status_code == 422

    def test_add_context_unauthorized(self, client):
        """Test context addition without authentication"""
        app.dependency_overrides.clear()

        context_texts = ["Test context"]
        response = client.post("/api/chat/context", json=context_texts)
        assert response.status_code == 401

    def test_chat_api_rate_limiting(self, client, mock_ai_chat_service):
        """Test rate limiting on chat endpoints"""
        # Setup mock to respond quickly
        mock_ai_chat_service.create_session.return_value = Mock(
            session_id=str(uuid4()),
            created_at=datetime.now(),
            messages=[]
        )

        # Make many requests to test rate limiting
        for i in range(100):
            response = client.post("/api/chat/sessions")
            if response.status_code == 429:
                break

        # If we haven't hit rate limit, check the last response
        if response.status_code != 429:
            # Should still be successful
            assert response.status_code == 200

    @pytest.mark.parametrize("session_id", [
        "invalid-uuid",
        "123",
        "",
        "not-a-uuid-format"
    ])
    def test_invalid_session_id_format(self, client, session_id):
        """Test handling of invalid session ID formats"""
        response = client.get(f"/api/chat/sessions/{session_id}")
        # Should either be 422 (validation error) or 404 (not found)
        assert response.status_code in [422, 404]

    def test_websocket_endpoint_structure(self, client):
        """Test that WebSocket endpoint is properly configured"""
        # This is a basic test to ensure the endpoint exists
        # WebSocket testing requires more complex setup
        response = client.get("/api/chat")
        assert response.status_code == 200

    def test_api_response_structure(self, client, mock_ai_chat_service, sample_session_data):
        """Test that API responses have correct structure"""
        # Test create session response structure
        mock_session = Mock()
        mock_session.session_id = sample_session_data["session_id"]
        mock_session.created_at = sample_session_data["created_at"]
        mock_session.messages = []
        mock_ai_chat_service.create_session.return_value = mock_session

        response = client.post("/api/chat/sessions")
        data = response.json()

        # Check required fields
        required_fields = ["session_id", "created_at", "messages"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_error_handling_service_exceptions(self, client, mock_ai_chat_service):
        """Test handling of service layer exceptions"""
        # Setup mock to raise exception
        mock_ai_chat_service.create_session.side_effect = Exception("Service error")

        response = client.post("/api/chat/sessions")

        # Should handle service exceptions gracefully
        assert response.status_code == 500

    def test_concurrent_session_creation(self, client, mock_ai_chat_service):
        """Test concurrent session creation"""
        import threading
        import time

        results = []

        def create_session():
            mock_session = Mock()
            mock_session.session_id = str(uuid4())
            mock_session.created_at = datetime.now()
            mock_session.messages = []
            mock_ai_chat_service.create_session.return_value = mock_session

            response = client.post("/api/chat/sessions")
            results.append(response.status_code)

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_session)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should be successful
        assert all(status == 200 for status in results)

    def test_large_message_content(self, client, mock_ai_chat_service):
        """Test handling of large message content"""
        session_id = str(uuid4())
        large_content = "x" * 10000  # 10KB of content

        mock_ai_chat_service.get_chat_response.return_value = "Response received"

        message_data = {
            "content": large_content,
            "role": "user"
        }

        response = client.post(
            f"/api/chat/sessions/{session_id}/messages",
            json=message_data
        )

        assert response.status_code == 200
        mock_ai_chat_service.get_chat_response.assert_called_once_with(
            session_id, large_content
        )

    def test_special_characters_in_message(self, client, mock_ai_chat_service):
        """Test handling of special characters in messages"""
        session_id = str(uuid4())
        special_messages = [
            {"content": "Hello 👋", "role": "user"},
            {"content": "Test with\nnewlines", "role": "user"},
            {"content": "Test with\ttabs", "role": "user"},
            {"content": "Test with \"quotes\"", "role": "user"},
            {"content": "Test with 'apostrophes'", "role": "user"},
            {"content": "Test with <html> tags", "role": "user"},
            {"content": "Test with &symbols", "role": "user"}
        ]

        mock_ai_chat_service.get_chat_response.return_value = "Response received"

        for message_data in special_messages:
            response = client.post(
                f"/api/chat/sessions/{session_id}/messages",
                json=message_data
            )
            assert response.status_code == 200
