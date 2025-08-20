import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.api.v1.notifications_optimized import router as notifications_router, NotificationType

class TestNotificationsAPI:
    """Test suite for the optimized Notifications API."""

    @pytest.mark.asyncio
    async def test_get_notifications_success(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test successful notifications retrieval."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/notifications/",
                headers=auth_headers,
                params={"skip": 0, "limit": 10, "unread_only": False}
            )

            assert response.status_code == 200
            data = response.json()
            assert "notifications" in data
            assert "total" in data
            assert "unread_count" in data
            assert "page" in data
            assert "limit" in data
            assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_notifications_unread_only(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test notifications retrieval with unread_only filter."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/notifications/",
                headers=auth_headers,
                params={"skip": 0, "limit": 10, "unread_only": True}
            )

            assert response.status_code == 200
            data = response.json()
            assert "notifications" in data

            # Verify service was called with correct parameters
            mock_notification_service.get_user_notifications.assert_called_once_with(
                user_id="test_user_id",
                limit=10,
                offset=0,
                unread_only=True
            )

    @pytest.mark.asyncio
    async def test_get_notifications_invalid_params(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test notifications retrieval with invalid parameters."""
        with patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            # Test with negative skip value
            response = await async_client.get(
                "/api/v1/notifications/",
                headers=auth_headers,
                params={"skip": -1, "limit": 10}
            )

            assert response.status_code == 422  # Validation error

            # Test with limit too high
            response = await async_client.get(
                "/api/v1/notifications/",
                headers=auth_headers,
                params={"skip": 0, "limit": 200}
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_mark_notification_read_success(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test successful notification marking as read."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache), \
             patch('app.api.v1.notifications_optimized.FastAPICache') as mock_fastapi_cache:

            response = await async_client.post(
                "/api/v1/notifications/test_notification_id/read",
                headers=auth_headers
            )

            assert response.status_code == 200
            assert response.json()["message"] == "Notification marked as read"

            # Verify cache was cleared
            mock_fastapi_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_notification_read_not_found(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test marking non-existent notification as read."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            # Mock service to return False
            mock_notification_service.mark_notification_read.return_value = False

            response = await async_client.post(
                "/api/v1/notifications/nonexistent_notification/read",
                headers=auth_headers
            )

            assert response.status_code == 404
            assert response.json()["detail"] == "Notification not found"

    @pytest.mark.asyncio
    async def test_mark_all_notifications_read_success(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test successful marking all notifications as read."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache), \
             patch('app.api.v1.notifications_optimized.FastAPICache') as mock_fastapi_cache:

            response = await async_client.post(
                "/api/v1/notifications/mark-all-read",
                headers=auth_headers
            )

            assert response.status_code == 200
            assert "Marked 5 notifications as read" in response.json()["message"]

            # Verify cache was cleared
            mock_fastapi_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_notification_success(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test successful notification deletion."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache), \
             patch('app.api.v1.notifications_optimized.FastAPICache') as mock_fastapi_cache:

            response = await async_client.delete(
                "/api/v1/notifications/test_notification_id",
                headers=auth_headers
            )

            assert response.status_code == 200
            assert response.json()["message"] == "Notification deleted successfully"

            # Verify cache was cleared
            mock_fastapi_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_notification_not_found(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test deletion of non-existent notification."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            # Mock service to return False
            mock_notification_service.delete_notification.return_value = False

            response = await async_client.delete(
                "/api/v1/notifications/nonexistent_notification",
                headers=auth_headers
            )

            assert response.status_code == 404
            assert response.json()["detail"] == "Notification not found"

    @pytest.mark.asyncio
    async def test_get_notification_stats_success(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test successful notification stats retrieval."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/notifications/stats",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 10
            assert data["unread"] == 3
            assert data["read"] == 7
            assert "by_type" in data
            assert data["by_type"]["info"] == 5

    @pytest.mark.asyncio
    async def test_create_notification_success(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test successful notification creation."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache), \
             patch('app.api.v1.notifications_optimized.FastAPICache') as mock_fastapi_cache:

            notification_data = {
                "title": "Test Notification",
                "message": "This is a test notification",
                "type": "info",
                "data": {"key": "value"}
            }

            response = await async_client.post(
                "/api/v1/notifications/create",
                headers=auth_headers,
                json=notification_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Notification created successfully"
            assert "notification" in data
            assert data["notification"]["title"] == "Test Notification"

            # Verify cache was cleared
            mock_fastapi_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_notification_invalid_data(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test notification creation with invalid data."""
        with patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            # Test with empty title
            response = await async_client.post(
                "/api/v1/notifications/create",
                headers=auth_headers,
                json={"title": "", "message": "Test message", "type": "info"}
            )

            assert response.status_code == 400
            assert "Title cannot be empty" in response.json()["detail"]

            # Test with empty message
            response = await async_client.post(
                "/api/v1/notifications/create",
                headers=auth_headers,
                json={"title": "Test Title", "message": "", "type": "info"}
            )

            assert response.status_code == 400
            assert "Message cannot be empty" in response.json()["detail"]

            # Test with invalid notification type
            response = await async_client.post(
                "/api/v1/notifications/create",
                headers=auth_headers,
                json={"title": "Test Title", "message": "Test message", "type": "invalid_type"}
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_cleanup_old_notifications_success(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test successful cleanup of old notifications."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache), \
             patch('app.api.v1.notifications_optimized.FastAPICache') as mock_fastapi_cache:

            response = await async_client.delete(
                "/api/v1/notifications/cleanup-old",
                headers=auth_headers,
                params={"days": 30}
            )

            assert response.status_code == 200
            assert "Cleaned up" in response.json()["message"]
            assert "old notifications" in response.json()["message"]

            # Verify cache was cleared
            mock_fastapi_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_notifications_invalid_params(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test cleanup with invalid parameters."""
        with patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            # Test with days too low
            response = await async_client.delete(
                "/api/v1/notifications/cleanup-old",
                headers=auth_headers,
                params={"days": 0}
            )

            assert response.status_code == 422  # Validation error

            # Test with days too high
            response = await async_client.delete(
                "/api/v1/notifications/cleanup-old",
                headers=auth_headers,
                params={"days": 800}
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_notification_id_validation(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test notification ID validation."""
        with patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            # Test with empty notification ID
            response = await async_client.post(
                "/api/v1/notifications/ /read",
                headers=auth_headers
            )

            assert response.status_code == 400
            assert "Notification ID is required" in response.json()["detail"]

            # Test with whitespace-only notification ID
            response = await async_client.post(
                "/api/v1/notifications/   /read",
                headers=auth_headers
            )

            assert response.status_code == 400
            assert "Notification ID is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_notification_type_enum(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test notification type enum validation."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            # Test all valid notification types
            valid_types = ["info", "warning", "error", "success", "system", "security"]

            for notification_type in valid_types:
                notification_data = {
                    "title": f"Test {notification_type}",
                    "message": "Test message",
                    "type": notification_type
                }

                response = await async_client.post(
                    "/api/v1/notifications/create",
                    headers=auth_headers,
                    json=notification_data
                )

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limiting(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test rate limiting functionality."""
        # Mock rate limiter to raise exception
        from fastapi import HTTPException
        mock_rate_limiter.side_effect = HTTPException(status_code=429, detail="Rate limit exceeded")

        with patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/notifications/",
                headers=auth_headers
            )

            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_error_handling(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test error handling for various scenarios."""
        with patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache), \
             patch('app.api.v1.notifications_optimized.notification_service') as mock_service:

            # Test service error
            mock_service.get_user_notifications.side_effect = Exception("Database error")

            response = await async_client.get(
                "/api/v1/notifications/",
                headers=auth_headers
            )

            assert response.status_code == 500
            assert "An unexpected error occurred" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_authentication_required(self, async_client):
        """Test that authentication is required for all endpoints."""
        endpoints = [
            ("GET", "/api/v1/notifications/"),
            ("POST", "/api/v1/notifications/test_id/read"),
            ("POST", "/api/v1/notifications/mark-all-read"),
            ("DELETE", "/api/v1/notifications/test_id"),
            ("GET", "/api/v1/notifications/stats"),
            ("POST", "/api/v1/notifications/create"),
            ("DELETE", "/api/v1/notifications/cleanup-old"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            elif method == "POST":
                response = await async_client.post(endpoint)
            elif method == "DELETE":
                response = await async_client.delete(endpoint)

            assert response.status_code == 401

class TestNotificationsAPIPerformance:
    """Performance tests for Notifications API."""

    @pytest.mark.asyncio
    async def test_notifications_listing_performance(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test notifications listing performance with large datasets."""
        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            # Mock large notification list
            large_notification_list = [
                {
                    "id": f"notification_{i}",
                    "user_id": "test_user_id",
                    "title": f"Notification {i}",
                    "message": f"This is notification number {i}",
                    "type": "info",
                    "data": {},
                    "created_at": "2023-01-01T00:00:00",
                    "read": i % 2 == 0  # Alternate read/unread
                }
                for i in range(1000)
            ]
            mock_notification_service.get_user_notifications.return_value = large_notification_list
            mock_notification_service.get_user_notifications_count.return_value = 1000
            mock_notification_service.get_user_unread_notifications_count.return_value = 500

            import time
            start_time = time.time()

            response = await async_client.get(
                "/api/v1/notifications/",
                headers=auth_headers,
                params={"skip": 0, "limit": 100}
            )

            end_time = time.time()

            assert response.status_code == 200
            assert (end_time - start_time) < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_concurrent_notification_operations(self, async_client, auth_headers, mock_notification_service, mock_rate_limiter, mock_cache):
        """Test concurrent notification operations."""
        import asyncio

        with patch('app.api.v1.notifications_optimized.notification_service', mock_notification_service), \
             patch('app.api.v1.notifications_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.notifications_optimized.cache', mock_cache):

            async def make_request():
                return await async_client.get(
                    "/api/v1/notifications/",
                    headers=auth_headers
                )

            # Make 10 concurrent requests
            tasks = [make_request() for _ in range(10)]
            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
