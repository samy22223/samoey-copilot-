import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.models.user import User
from app.core.security import create_access_token, get_password_hash
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create async engine for tests
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for debugging SQL queries
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

# Create async session factory
TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def test_db() -> AsyncGenerator[None, None]:
    """Create test database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_db) -> AsyncGenerator[AsyncSession, None]:
    """Get test database session."""
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def client(db_session) -> Generator[TestClient, None, None]:
    """Create test client with database session."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with database session."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_admin_user(db_session) -> User:
    """Create a test admin user."""
    user = User(
        email="admin@example.com",
        name="Admin User",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def auth_headers(test_user) -> dict:
    """Create authentication headers for test user."""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
async def admin_auth_headers(test_admin_user) -> dict:
    """Create authentication headers for admin user."""
    access_token = create_access_token(data={"sub": test_admin_user.email})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def mock_file_storage_service():
    """Mock file storage service."""
    from unittest.mock import AsyncMock
    mock_service = AsyncMock()
    mock_service.upload_file.return_value = {
        "id": "test_file_id",
        "original_filename": "test.txt",
        "file_size": 1024,
        "uploaded_at": "2023-01-01T00:00:00"
    }
    mock_service.get_user_files.return_value = []
    mock_service.get_file_info.return_value = {
        "id": "test_file_id",
        "original_filename": "test.txt",
        "stored_filename": "stored_test.txt",
        "file_size": 1024,
        "content_type": "text/plain",
        "description": "Test file",
        "uploaded_at": "2023-01-01T00:00:00",
        "downloads": 0
    }
    mock_service.download_file.return_value = {
        "file_path": "/path/to/file",
        "filename": "test.txt",
        "content_type": "text/plain",
        "downloads": 1
    }
    mock_service.delete_file.return_value = True
    mock_service.update_file_description.return_value = True
    mock_service.get_storage_stats.return_value = {
        "total_files": 10,
        "total_size_bytes": 10240,
        "total_size_mb": 0.01,
        "total_downloads": 5,
        "by_file_type": {"text/plain": 5, "image/jpeg": 5}
    }
    return mock_service

@pytest.fixture
def mock_notification_service():
    """Mock notification service."""
    from unittest.mock import AsyncMock
    mock_service = AsyncMock()
    mock_service.get_user_notifications.return_value = []
    mock_service.mark_notification_read.return_value = True
    mock_service.mark_all_notifications_read.return_value = 5
    mock_service.delete_notification.return_value = True
    mock_service.get_notification_stats.return_value = {
        "total": 10,
        "unread": 3,
        "read": 7,
        "by_type": {"info": 5, "warning": 3, "error": 2}
    }
    mock_service.create_notification.return_value = {
        "id": "test_notification_id",
        "user_id": "test_user_id",
        "title": "Test Notification",
        "message": "This is a test notification",
        "type": "info",
        "data": {},
        "created_at": "2023-01-01T00:00:00",
        "read": False
    }
    return mock_service

@pytest.fixture
def mock_analytics_service():
    """Mock analytics service."""
    from unittest.mock import AsyncMock
    mock_service = AsyncMock()
    mock_service.get_usage_analytics.return_value = {
        "period": {"start_date": "2023-01-01", "end_date": "2023-01-31"},
        "user_activity": {"total_sessions": 100, "active_days": 20},
        "messaging": {"total_messages_sent": 500, "total_messages_received": 450},
        "file_operations": {"files_uploaded": 25, "files_downloaded": 15},
        "api_usage": {"total_requests": 1000, "successful_requests": 950},
        "ai_interactions": {"ai_queries": 50, "code_generations": 25}
    }
    mock_service.get_performance_metrics.return_value = {
        "timestamp": "2023-01-01T00:00:00",
        "system": {"cpu_usage": "25%", "memory_usage": "50%"},
        "process": {"memory_usage": "100MB", "cpu_usage": "10%"},
        "network": {"bytes_sent": 1024, "bytes_recv": 2048},
        "response_times": {"average_api_response": "100ms"},
        "health": {"status": "healthy", "uptime": 86400}
    }
    mock_service.get_user_analytics.return_value = {
        "user_id": "test_user_id",
        "period": "30d",
        "activity_summary": {"total_sessions": 50},
        "feature_usage": {"messages": 200, "files": 10},
        "engagement_metrics": {"daily_active": True},
        "growth_trend": {"weekly_growth": "5%"}
    }
    mock_service.get_system_analytics.return_value = {
        "timestamp": "2023-01-01T00:00:00",
        "overview": {"total_users": 1000, "active_users": 500},
        "performance": {"avg_response_time": "150ms"},
        "resource_usage": {"cpu": "30%", "memory": "60%"},
        "top_features": [{"name": "messaging", "usage": 80}],
        "alerts": []
    }
    mock_service.get_real_time_metrics.return_value = {
        "timestamp": "2023-01-01T00:00:00",
        "current": {"active_users": 100, "requests_per_second": 10},
        "performance": {"cpu": "25%", "memory": "55%"},
        "health": {"status": "healthy"}
    }
    mock_service.record_event.return_value = True
    return mock_service

@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter."""
    from unittest.mock import AsyncMock
    mock_limiter = AsyncMock()
    mock_limiter.return_value = None  # Rate limiter decorator should not raise
    return mock_limiter

@pytest.fixture
def mock_cache():
    """Mock cache."""
    from unittest.mock import AsyncMock
    mock_cache = AsyncMock()
    mock_cache.return_value = None  # Cache decorator should not raise
    return mock_cache

# Test data fixtures
@pytest.fixture
def sample_file_data():
    """Sample file data for testing."""
    return {
        "filename": "test.txt",
        "content": b"This is a test file content",
        "content_type": "text/plain",
        "description": "Test file description"
    }

@pytest.fixture
def sample_notification_data():
    """Sample notification data for testing."""
    return {
        "title": "Test Notification",
        "message": "This is a test notification message",
        "type": "info",
        "data": {"key": "value"}
    }

@pytest.fixture
def sample_analytics_event_data():
    """Sample analytics event data for testing."""
    return {
        "event_type": "user_action",
        "data": {
            "action": "button_click",
            "page": "/dashboard",
            "timestamp": "2023-01-01T00:00:00"
        }
    }

# Performance testing fixtures
@pytest.fixture
def benchmark_data():
    """Benchmark data for performance testing."""
    return {
        "small_dataset": list(range(100)),
        "medium_dataset": list(range(1000)),
        "large_dataset": list(range(10000))
    }
