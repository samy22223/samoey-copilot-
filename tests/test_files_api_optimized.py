import pytest
from fastapi import UploadFile
from unittest.mock import AsyncMock, patch
import io
from datetime import datetime

from app.api.v1.files_optimized import router as files_router

class TestFilesAPI:
    """Test suite for the optimized Files API."""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, async_client, auth_headers, mock_file_storage_service, mock_rate_limiter, mock_cache):
        """Test successful file upload."""
        with patch('app.api.v1.files_optimized.file_storage_service', mock_file_storage_service), \
             patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            # Create test file
            file_content = b"Test file content"
            file = UploadFile(filename="test.txt", file=io.BytesIO(file_content))

            # Mock the file size validation
            file.size = len(file_content)

            response = await async_client.post(
                "/api/v1/files/upload",
                files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
                data={"description": "Test file description"},
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "File uploaded successfully"
            assert data["file_id"] == "test_file_id"
            assert data["filename"] == "test.txt"
            assert data["file_size"] == 1024

    @pytest.mark.asyncio
    async def test_upload_file_no_auth(self, async_client):
        """Test file upload without authentication."""
        file_content = b"Test file content"

        response = await async_client.post(
            "/api/v1/files/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test file upload with file size exceeding limit."""
        with patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            # Create large file content (over 100MB)
            large_content = b"x" * (100 * 1024 * 1024 + 1)  # 100MB + 1 byte

            response = await async_client.post(
                "/api/v1/files/upload",
                files={"file": ("large.txt", io.BytesIO(large_content), "text/plain")},
                headers=auth_headers
            )

            assert response.status_code == 400
            assert "File size exceeds maximum limit" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test file upload with invalid file type."""
        with patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            # Try to upload an executable file
            file_content = b"executable content"

            response = await async_client.post(
                "/api/v1/files/upload",
                files={"file": ("test.exe", io.BytesIO(file_content), "application/x-executable")},
                headers=auth_headers
            )

            assert response.status_code == 400
            assert "File type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_files_success(self, async_client, auth_headers, mock_file_storage_service, mock_rate_limiter, mock_cache):
        """Test successful file listing."""
        with patch('app.api.v1.files_optimized.file_storage_service', mock_file_storage_service), \
             patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/files/",
                headers=auth_headers,
                params={"skip": 0, "limit": 10}
            )

            assert response.status_code == 200
            data = response.json()
            assert "files" in data
            assert "total" in data
            assert "page" in data
            assert "limit" in data
            assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_list_files_invalid_pagination(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test file listing with invalid pagination parameters."""
        with patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            # Test with negative skip value
            response = await async_client.get(
                "/api/v1/files/",
                headers=auth_headers,
                params={"skip": -1, "limit": 10}
            )

            assert response.status_code == 422  # Validation error

            # Test with limit too high
            response = await async_client.get(
                "/api/v1/files/",
                headers=auth_headers,
                params={"skip": 0, "limit": 200}
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_file_info_success(self, async_client, auth_headers, mock_file_storage_service, mock_rate_limiter, mock_cache):
        """Test successful file info retrieval."""
        with patch('app.api.v1.files_optimized.file_storage_service', mock_file_storage_service), \
             patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/files/test_file_id",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "test_file_id"
            assert data["original_filename"] == "test.txt"
            assert data["file_size"] == 1024

    @pytest.mark.asyncio
    async def test_get_file_info_not_found(self, async_client, auth_headers, mock_file_storage_service, mock_rate_limiter, mock_cache):
        """Test file info retrieval for non-existent file."""
        with patch('app.api.v1.files_optimized.file_storage_service', mock_file_storage_service), \
             patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            # Mock service to return None
            mock_file_storage_service.get_file_info.return_value = None

            response = await async_client.get(
                "/api/v1/files/nonexistent_file",
                headers=auth_headers
            )

            assert response.status_code == 404
            assert response.json()["detail"] == "File not found"

    @pytest.mark.asyncio
    async def test_download_file_success(self, async_client, auth_headers, mock_file_storage_service, mock_rate_limiter, mock_cache):
        """Test successful file download."""
        with patch('app.api.v1.files_optimized.file_storage_service', mock_file_storage_service), \
             patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/files/test_file_id/download",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == "test.txt"
            assert data["content_type"] == "text/plain"

    @pytest.mark.asyncio
    async def test_delete_file_success(self, async_client, auth_headers, mock_file_storage_service, mock_rate_limiter, mock_cache):
        """Test successful file deletion."""
        with patch('app.api.v1.files_optimized.file_storage_service', mock_file_storage_service), \
             patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache), \
             patch('app.api.v1.files_optimized.FastAPICache') as mock_fastapi_cache:

            response = await async_client.delete(
                "/api/v1/files/test_file_id",
                headers=auth_headers
            )

            assert response.status_code == 200
            assert response.json()["message"] == "File deleted successfully"

            # Verify cache was cleared
            mock_fastapi_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_file_description_success(self, async_client, auth_headers, mock_file_storage_service, mock_rate_limiter, mock_cache):
        """Test successful file description update."""
        with patch('app.api.v1.files_optimized.file_storage_service', mock_file_storage_service), \
             patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache), \
             patch('app.api.v1.files_optimized.FastAPICache') as mock_fastapi_cache:

            response = await async_client.put(
                "/api/v1/files/test_file_id",
                headers=auth_headers,
                json={"description": "Updated description"}
            )

            assert response.status_code == 200
            assert response.json()["message"] == "File description updated successfully"

    @pytest.mark.asyncio
    async def test_update_file_description_invalid_data(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test file description update with invalid data."""
        with patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            # Test with empty description
            response = await async_client.put(
                "/api/v1/files/test_file_id",
                headers=auth_headers,
                json={"description": ""}
            )

            assert response.status_code == 422  # Validation error

            # Test with description too long
            long_description = "x" * 501
            response = await async_client.put(
                "/api/v1/files/test_file_id",
                headers=auth_headers,
                json={"description": long_description}
            )

            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_storage_stats_success(self, async_client, auth_headers, mock_file_storage_service, mock_rate_limiter, mock_cache):
        """Test successful storage stats retrieval."""
        with patch('app.api.v1.files_optimized.file_storage_service', mock_file_storage_service), \
             patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/files/stats/storage",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_files"] == 10
            assert data["total_size_bytes"] == 10240
            assert data["total_downloads"] == 5
            assert "by_file_type" in data

    @pytest.mark.asyncio
    async def test_rate_limiting(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test rate limiting functionality."""
        # Mock rate limiter to raise exception
        from fastapi import HTTPException
        mock_rate_limiter.side_effect = HTTPException(status_code=429, detail="Rate limit exceeded")

        with patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            response = await async_client.get(
                "/api/v1/files/",
                headers=auth_headers
            )

            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_error_handling(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test error handling for various scenarios."""
        with patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache), \
             patch('app.api.v1.files_optimized.file_storage_service') as mock_service:

            # Test service error
            mock_service.get_user_files.side_effect = Exception("Database error")

            response = await async_client.get(
                "/api/v1/files/",
                headers=auth_headers
            )

            assert response.status_code == 500
            assert "An unexpected error occurred" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_file_id(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test handling of invalid file IDs."""
        with patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            # Test with empty file ID
            response = await async_client.get(
                "/api/v1/files/ ",
                headers=auth_headers
            )

            assert response.status_code == 400
            assert "File ID is required" in response.json()["detail"]

            # Test with None file ID (this would be handled by FastAPI routing)
            # but we can test the validation function directly if needed

    @pytest.mark.asyncio
    async def test_file_validation_helpers(self, async_client, auth_headers, mock_rate_limiter, mock_cache):
        """Test file validation helper functions."""
        with patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            # Test file size validation
            from app.api.v1.files_optimized import validate_file_size
            from fastapi import UploadFile

            # Create test file with valid size
            valid_file = UploadFile(filename="test.txt", file=io.BytesIO(b"x" * 1000))
            valid_file.size = 1000
            result = validate_file_size(valid_file)
            assert result == valid_file

            # Create test file with invalid size
            invalid_file = UploadFile(filename="large.txt", file=io.BytesIO(b"x" * 200))
            invalid_file.size = 200 * 1024 * 1024  # 200MB
            with pytest.raises(ValueError, match="File size exceeds maximum limit"):
                validate_file_size(invalid_file)

            # Test file ID validation
            from app.api.v1.files_optimized import validate_file_id

            # Valid file ID
            result = validate_file_id("valid_file_id")
            assert result == "valid_file_id"

            # Empty file ID
            with pytest.raises(ValueError, match="File ID is required"):
                validate_file_id("")

            # Whitespace-only file ID
            with pytest.raises(ValueError, match="File ID is required"):
                validate_file_id("   ")

class TestFilesAPIPerformance:
    """Performance tests for Files API."""

    @pytest.mark.asyncio
    async def test_file_listing_performance(self, async_client, auth_headers, mock_file_storage_service, mock_rate_limiter, mock_cache, benchmark_data):
        """Test file listing performance with different dataset sizes."""
        with patch('app.api.v1.files_optimized.file_storage_service', mock_file_storage_service), \
             patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            # Mock large dataset
            large_file_list = [
                {
                    "id": f"file_{i}",
                    "original_filename": f"file_{i}.txt",
                    "stored_filename": f"stored_file_{i}.txt",
                    "file_size": 1024,
                    "content_type": "text/plain",
                    "description": f"Test file {i}",
                    "uploaded_at": "2023-01-01T00:00:00",
                    "downloads": i
                }
                for i in range(1000)
            ]
            mock_file_storage_service.get_user_files.return_value = large_file_list
            mock_file_storage_service.get_user_files_count.return_value = 1000

            import time
            start_time = time.time()

            response = await async_client.get(
                "/api/v1/files/",
                headers=auth_headers,
                params={"skip": 0, "limit": 100}
            )

            end_time = time.time()

            assert response.status_code == 200
            assert (end_time - start_time) < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_concurrent_file_operations(self, async_client, auth_headers, mock_file_storage_service, mock_rate_limiter, mock_cache):
        """Test concurrent file operations."""
        import asyncio

        with patch('app.api.v1.files_optimized.file_storage_service', mock_file_storage_service), \
             patch('app.api.v1.files_optimized.rate_limit', mock_rate_limiter), \
             patch('app.api.v1.files_optimized.cache', mock_cache):

            async def make_request():
                return await async_client.get(
                    "/api/v1/files/",
                    headers=auth_headers
                )

            # Make 10 concurrent requests
            tasks = [make_request() for _ in range(10)]
            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
