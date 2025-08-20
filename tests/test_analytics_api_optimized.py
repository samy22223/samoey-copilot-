import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app.api.v1.analytics_optimized import router as analytics_router, AnalyticsPeriod, EventType

class TestAnalyticsAPI:
    """Test suite for the optimized Analytics API."""

    @pytest.mark.asyncio
    async def test_get_usage_analytics_success(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test successful usage analytics retrieval."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/usage",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "period" in data
            assert "user_activity" in data
            assert "messaging" in data
            assert "file_operations" in data
            assert "api_usage" in data
            assert "ai_interactions" in data

    @pytest.mark.asyncio
    async def test_get_usage_analytics_with_dates(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test usage analytics retrieval with custom date range."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()

            response = await async_client.get(
                "/api/v1/analytics/usage",
                headers=auth_headers,
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "period" in data

            # Verify service was called with correct parameters
            mock_analytics_service.get_usage_analytics.assert_called_once()
            call_args = mock_analytics_service.get_usage_analytics.call_args
            assert call_args[1]["start_date"] == start_date
            assert call_args[1]["end_date"] == end_date

    @pytest.mark.asyncio
    async def test_get_usage_analytics_with_period(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test usage analytics retrieval with predefined period."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/usage",
                headers=auth_headers,
                params={"period": "7d"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "period" in data

    @pytest.mark.asyncio
    async def test_get_usage_analytics_invalid_dates(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test usage analytics retrieval with invalid date range."""
        with patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            start_date = datetime.now()
            end_date = datetime.now() - timedelta(days=1)  # End date before start date

            response = await async_client.get(
                "/api/v1/analytics/usage",
                headers=auth_headers,
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            )

            assert response.status_code == 400
            assert "End date must be after start date" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_performance_metrics_success(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test successful performance metrics retrieval."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/performance",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "timestamp" in data
            assert "system" in data
            assert "process" in data
            assert "network" in data
            assert "response_times" in data
            assert "health" in data

    @pytest.mark.asyncio
    async def test_get_user_analytics_success(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test successful user analytics retrieval."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/user",
                headers=auth_headers,
                params={"days": 30}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "test_user_id"
            assert data["period"] == "30d"
            assert "activity_summary" in data
            assert "feature_usage" in data
            assert "engagement_metrics" in data
            assert "growth_trend" in data

    @pytest.mark.asyncio
    async def test_get_user_analytics_invalid_days(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test user analytics retrieval with invalid days parameter."""
        with patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            # Test with days too low
            response = await async_client.get(
                "/api/v1/analytics/user",
                headers=auth_headers,
                params={"days": 0}
            )

            assert response.status_code == 422  # Validation error

            # Test with days too high
            response = await async_client.get(
                "/api/v1/analytics/user",
                headers=auth_headers,
                params={"days": 400}
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_system_analytics_success(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test successful system analytics retrieval."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/system",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "timestamp" in data
            assert "overview" in data
            assert "performance" in data
            assert "resource_usage" in data
            assert "top_features" in data
            assert "alerts" in data

    @pytest.mark.asyncio
    async def test_get_realtime_metrics_success(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test successful realtime metrics retrieval."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/realtime",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "timestamp" in data
            assert "current" in data
            assert "performance" in data
            assert "health" in data

    @pytest.mark.asyncio
    async def test_record_analytics_event_success(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test successful analytics event recording."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache), \
             patch('app.api.v1.analytics_optimized.FastAPICache') as mock_fastapi_cache:

            event_data = {
                "event_type": "user_action",
                "data": {
                    "action": "button_click",
                    "page": "/dashboard",
                    "timestamp": "2023-01-01T00:00:00"
                }
            }

            response = await async_client.post(
                "/api/v1/analytics/events",
                headers=auth_headers,
                json=event_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Event recorded successfully"
            assert "event_id" in data

            # Verify cache was cleared
            mock_fastapi_cache.clear.assert_called()

    @pytest.mark.asyncio
    async def test_record_analytics_event_invalid_type(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test analytics event recording with invalid event type."""
        with patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            event_data = {
                "event_type": "invalid_event_type",
                "data": {"action": "test"}
            }

            response = await async_client.post(
                "/api/v1/analytics/events",
                headers=auth_headers,
                json=event_data
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_export_analytics_success(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test successful analytics data export."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/export",
                headers=auth_headers,
                params={"format": "json"}
            )

            assert response.status_code == 200
            # Export data should be returned

    @pytest.mark.asyncio
    async def test_export_analytics_invalid_format(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test analytics data export with invalid format."""
        with patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/export",
                headers=auth_headers,
                params={"format": "xml"}
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_dashboard_data_success(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test successful dashboard data retrieval."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/dashboard",
                headers=auth_headers,
                params={"period": "7d"}
            )

            assert response.status_code == 200
            # Dashboard data should be returned

    @pytest.mark.asyncio
    async def test_get_dashboard_data_invalid_period(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test dashboard data retrieval with invalid period."""
        with patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/dashboard",
                headers=auth_headers,
                params={"period": "invalid_period"}
            )

            assert response.status_code == 400
            assert "Period must be one of" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_cleanup_old_analytics_success(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test successful cleanup of old analytics data."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.delete(
                "/api/v1/analytics/cleanup",
                headers=auth_headers,
                params={"days": 90}
            )

            assert response.status_code == 200
            assert "Cleaned up" in response.json()["message"]
            assert "old analytics records" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_cleanup_old_analytics_invalid_params(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test cleanup with invalid parameters."""
        with patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            # Test with days too low
            response = await async_client.delete(
                "/api/v1/analytics/cleanup",
                headers=auth_headers,
                params={"days": 10}
            )

            assert response.status_code == 422  # Validation error

            # Test with days too high
            response = await async_client.delete(
                "/api/v1/analytics/cleanup",
                headers=auth_headers,
                params={"days": 800}
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_analytics_period_enum(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test analytics period enum validation."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            # Test all valid periods
            valid_periods = ["1h", "24h", "7d", "30d", "90d", "365d"]

            for period in valid_periods:
                response = await async_client.get(
                    "/api/v1/analytics/usage",
                    headers=auth_headers,
                    params={"period": period}
                )

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_event_type_enum(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test event type enum validation."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            # Test all valid event types
            valid_types = ["page_view", "user_action", "api_call", "error", "performance", "security"]

            for event_type in valid_types:
                event_data = {
                    "event_type": event_type,
                    "data": {"action": "test"}
                }

                response = await async_client.post(
                    "/api/v1/analytics/events",
                    headers=auth_headers,
                    json=event_data
                )

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limiting(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test rate limiting functionality."""
        # Mock rate limiter to raise exception
        from fastapi import HTTPException
        mock_rate_limiter.side_effect = HTTPException(status_code=429, detail="Rate limit exceeded")

        with patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/analytics/usage",
                headers=auth_headers
            )

            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_error_handling(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test error handling for various scenarios."""
        with patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache), \
             patch('app.api.v1.analytics_optimized.analytics_service') as mock_service:

            # Test service error
            mock_service.get_usage_analytics.side_effect = Exception("Database error")

            response = await async_client.get(
                "/api/v1/analytics/usage",
                headers=auth_headers
            )

            assert response.status_code == 500
            assert "An unexpected error occurred" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_authentication_required(self, async_client):
        """Test that authentication is required for all endpoints."""
        endpoints = [
            ("GET", "/api/v1/analytics/usage"),
            ("GET", "/api/v1/analytics/performance"),
            ("GET", "/api/v1/analytics/user"),
            ("GET", "/api/v1/analytics/system"),
            ("GET", "/api/v1/analytics/realtime"),
            ("POST", "/api/v1/analytics/events"),
            ("GET", "/api/v1/analytics/export"),
            ("GET", "/api/v1/analytics/dashboard"),
            ("DELETE", "/api/v1/analytics/cleanup"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            elif method == "POST":
                response = await async_client.post(endpoint)
            elif method == "DELETE":
                response = await async_client.delete(endpoint)

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_validation_helpers(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test validation helper functions."""
        with patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            # Test days parameter validation
            from app.api.v1.analytics_optimized import validate_days_param

            # Valid days
            result = validate_days_param(30)
            assert result == 30

            # Invalid days (too low)
            with pytest.raises(ValueError, match="Days parameter must be between 1 and 365"):
                validate_days_param(0)

            # Invalid days (too high)
            with pytest.raises(ValueError, match="Days parameter must be between 1 and 365"):
                validate_days_param(400)

            # Test period parameter validation
            from app.api.v1.analytics_optimized import validate_period_param

            # Valid period
            result = validate_period_param("7d")
            assert result == "7d"

            # Invalid period
            with pytest.raises(ValueError, match="Period must be one of"):
                validate_period_param("invalid_period")

class TestAnalyticsAPIPerformance:
    """Performance tests for Analytics API."""

    @pytest.mark.asyncio
    async def test_analytics_retrieval_performance(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test analytics retrieval performance with large datasets."""
        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            # Mock large analytics dataset
            large_analytics_data = {
                "period": {"start_date": "2023-01-01", "end_date": "2023-12-31"},
                "user_activity": {
                    "total_sessions": 10000,
                    "active_days": 300,
                    "average_session_duration": "15m 30s",
                    "last_activity": "2023-12-31T23:59:59"
                },
                "messaging": {
                    "total_messages_sent": 50000,
                    "total_messages_received": 45000,
                    "average_response_time": "2m 15s",
                    "conversations_started": 1000
                },
                "file_operations": {
                    "files_uploaded": 2500,
                    "files_downloaded": 1500,
                    "total_storage_used": "2.5 GB",
                    "file_types": {"image/jpeg": 1000, "application/pdf": 800, "text/plain": 700}
                },
                "api_usage": {
                    "total_requests": 100000,
                    "successful_requests": 95000,
                    "failed_requests": 5000,
                    "average_response_time": "150ms",
                    "peak_hour": "14:00"
                },
                "ai_interactions": {
                    "ai_queries": 5000,
                    "code_generations": 2500,
                    "document_analyses": 1000,
                    "average_ai_response_time": "3s 500ms"
                }
            }
            mock_analytics_service.get_usage_analytics.return_value = large_analytics_data

            import time
            start_time = time.time()

            response = await async_client.get(
                "/api/v1/analytics/usage",
                headers=auth_headers,
                params={"period": "365d"}
            )

            end_time = time.time()

            assert response.status_code == 200
            assert (end_time - start_time) < 3.0  # Should complete within 3 seconds

    @pytest.mark.asyncio
    async def test_concurrent_analytics_operations(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test concurrent analytics operations."""
        import asyncio

        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            async def make_request():
                return await async_client.get(
                    "/api/v1/analytics/realtime",
                    headers=auth_headers
                )

            # Make 20 concurrent requests (realtime metrics should handle high concurrency)
            tasks = [make_request() for _ in range(20)]
            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            for response in responses:
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_event_recording_performance(self, async_client, auth_headers, mock_analytics_service, mock_rate_limiter, mock_cache):
        """Test event recording performance under load."""
        import asyncio

        with patch('app.api.v1.analytics_optimized.analytics_service', mock_analytics_service), \
             patch('app.api.v1.analytics_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.analytics_optimized.cache', mock_cache):

            async def record_event():
                event_data = {
                    "event_type": "user_action",
                    "data": {
                        "action": "click",
                        "element": "button",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                return await async_client.post(
                    "/api/v1/analytics/events",
                    headers=auth_headers,
                    json=event_data
                )

            # Record 100 events concurrently
            tasks = [record_event() for _ in range(100)]
            responses = await asyncio.gather(*tasks)

            # All events should be recorded successfully
            for response in responses:
                assert response.status_code == 200
                assert response.json()["message"] == "Event recorded successfully"
