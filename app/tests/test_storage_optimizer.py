import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.services.storage_optimizer import StorageOptimizer
from app.services.file_storage import FileStorageService
from app.core.config import settings

class TestStorageOptimizer:

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.optimizer = StorageOptimizer()
        self.optimizer.project_root = self.temp_dir

        # Create test files
        self.test_files = []

        # Create some Python cache files
        cache_dir = self.temp_dir / "test_cache" / "__pycache__"
        cache_dir.mkdir(parents=True)
        cache_file = cache_dir / "test_module.cpython-39.pyc"
        cache_file.write_text("fake cache content")
        self.test_files.append(cache_file)

        # Create some log files
        old_log = self.temp_dir / "old_log.log"
        old_log.write_text("old log content")
        # Modify file to be old
        old_time = datetime.now() - timedelta(days=10)
        old_time_timestamp = old_time.timestamp()
        import os
        os.utime(old_log, (old_time_timestamp, old_time_timestamp))
        self.test_files.append(old_log)

        # Create temp files
        temp_file = self.temp_dir / "test.tmp"
        temp_file.write_text("temp content")
        self.test_files.append(temp_file)

        # Create uploads directory with test files
        upload_dir = self.temp_dir / "uploads"
        upload_dir.mkdir()

        # Create a large text file for compression testing
        large_text_file = upload_dir / "large_text.txt"
        large_text_file.write_text("x" * (1024 * 1024 * 2))  # 2MB file
        self.test_files.append(large_text_file)

        # Create duplicate files
        duplicate_file = upload_dir / "duplicate.txt"
        duplicate_file.write_text("duplicate content")
        self.test_files.append(duplicate_file)

        duplicate_file2 = upload_dir / "duplicate2.txt"
        duplicate_file2.write_text("duplicate content")
        self.test_files.append(duplicate_file2)

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_cleanup_python_cache(self):
        """Test Python cache cleanup."""
        results = self.optimizer.cleanup_python_cache()

        assert results["files_cleaned"] > 0
        assert results["space_freed_bytes"] > 0
        assert not (self.temp_dir / "test_cache" / "__pycache__").exists()

    def test_cleanup_log_files(self):
        """Test log file cleanup."""
        results = self.optimizer.cleanup_log_files(days=7)

        assert results["files_cleaned"] > 0
        assert results["space_freed_bytes"] > 0
        assert not (self.temp_dir / "old_log.log").exists()

    def test_cleanup_temp_files(self):
        """Test temporary file cleanup."""
        results = self.optimizer.cleanup_temp_files()

        assert results["files_cleaned"] > 0
        assert results["space_freed_bytes"] > 0
        assert not (self.temp_dir / "test.tmp").exists()

    def test_should_compress(self):
        """Test file compression decision logic."""
        # Test large text file (should be compressed)
        large_file = self.temp_dir / "uploads" / "large_text.txt"
        assert self.optimizer._should_compress(large_file) == True

        # Test small file (should not be compressed)
        small_file = self.temp_dir / "small.txt"
        small_file.write_text("small content")
        assert self.optimizer._should_compress(small_file) == False

        # Test already compressed file (should not be compressed)
        compressed_file = self.temp_dir / "already.gz"
        compressed_file.write_text("compressed content")
        assert self.optimizer._should_compress(compressed_file) == False

    def test_compress_file(self):
        """Test file compression."""
        large_file = self.temp_dir / "uploads" / "large_text.txt"
        original_size = large_file.stat().st_size

        space_saved = self.optimizer._compress_file(large_file)

        assert space_saved is not None
        assert space_saved > 0
        assert not large_file.exists()  # Original file should be removed
        assert (self.temp_dir / "uploads" / "large_text.txt.gz").exists()

    def test_get_file_hash(self):
        """Test file hashing."""
        file1 = self.temp_dir / "test1.txt"
        file1.write_text("test content")

        file2 = self.temp_dir / "test2.txt"
        file2.write_text("test content")

        file3 = self.temp_dir / "test3.txt"
        file3.write_text("different content")

        hash1 = self.optimizer._get_file_hash(file1)
        hash2 = self.optimizer._get_file_hash(file2)
        hash3 = self.optimizer._get_file_hash(file3)

        assert hash1 == hash2  # Same content should have same hash
        assert hash1 != hash3  # Different content should have different hash

    def test_remove_duplicate_files(self):
        """Test duplicate file removal."""
        upload_dir = self.temp_dir / "uploads"

        # Count files before removal
        files_before = list(upload_dir.rglob("*"))

        results = self.optimizer._remove_duplicate_files(upload_dir)

        # Count files after removal
        files_after = list(upload_dir.rglob("*"))

        assert results["files_removed"] > 0
        assert results["space_freed"] > 0
        assert len(files_after) < len(files_before)

    @patch('app.services.storage_optimizer.FileStorageService')
    def test_optimize_uploads_storage(self, mock_file_storage):
        """Test uploads storage optimization."""
        # Mock the file storage service
        mock_service = Mock()
        mock_service.cleanup_old_files.return_value = 2
        mock_file_storage.return_value = mock_service

        optimizer = StorageOptimizer()
        optimizer.project_root = self.temp_dir

        results = optimizer.optimize_uploads_storage()

        assert "files_compressed" in results
        assert "space_saved_bytes" in results
        assert "old_files_cleaned" in results
        assert "duplicate_files_removed" in results
        assert results["old_files_cleaned"] == 2

    @patch('app.services.storage_optimizer.SessionLocal')
    def test_optimize_database_storage(self, mock_session):
        """Test database storage optimization."""
        # Mock database session
        mock_db = Mock()
        mock_session.return_value.__enter__.return_value = mock_db

        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 5
        mock_query.filter.return_value.delete.return_value = None
        mock_db.query.return_value = mock_query

        optimizer = StorageOptimizer()
        results = optimizer.optimize_database_storage()

        assert "old_messages_cleaned" in results
        assert "old_conversations_cleaned" in results
        assert "old_files_cleaned" in results
        assert "space_estimated_saved" in results

    def test_run_full_optimization(self):
        """Test full storage optimization run."""
        with patch.object(self.optimizer, 'cleanup_python_cache') as mock_cache, \
             patch.object(self.optimizer, 'cleanup_log_files') as mock_logs, \
             patch.object(self.optimizer, 'cleanup_temp_files') as mock_temp, \
             patch.object(self.optimizer, 'optimize_uploads_storage') as mock_uploads, \
             patch.object(self.optimizer, 'optimize_database_storage') as mock_db:

            # Mock return values
            mock_cache.return_value = {"files_cleaned": 1, "space_freed_bytes": 1024}
            mock_logs.return_value = {"files_cleaned": 2, "space_freed_bytes": 2048}
            mock_temp.return_value = {"files_cleaned": 3, "space_freed_bytes": 3072}
            mock_uploads.return_value = {"files_compressed": 1, "space_saved_bytes": 4096, "old_files_cleaned": 2, "duplicate_files_removed": 1}
            mock_db.return_value = {"old_messages_cleaned": 5, "space_estimated_saved": 5120}

            results = self.optimizer.run_full_optimization()

            assert "timestamp" in results
            assert "python_cache_cleanup" in results
            assert "log_files_cleanup" in results
            assert "temp_files_cleanup" in results
            assert "uploads_optimization" in results
            assert "database_optimization" in results
            assert "total_space_saved_bytes" in results
            assert "total_files_cleaned" in results
            assert "total_space_saved_mb" in results

            # Verify totals are calculated correctly
            expected_total_space = 1024 + 2048 + 3072 + 4096 + 5120
            assert results["total_space_saved_bytes"] == expected_total_space

            expected_total_files = 1 + 2 + 3 + 2 + 1  # cache + logs + temp + old uploads + duplicates
            assert results["total_files_cleaned"] == expected_total_files

    def test_get_file_hash_error_handling(self):
        """Test file hashing error handling."""
        # Test with non-existent file
        non_existent_file = self.temp_dir / "nonexistent.txt"

        # Should not raise an exception but handle gracefully
        with pytest.raises(Exception):
            self.optimizer._get_file_hash(non_existent_file)

    def test_compress_file_error_handling(self):
        """Test file compression error handling."""
        # Test with non-existent file
        non_existent_file = self.temp_dir / "nonexistent.txt"

        result = self.optimizer._compress_file(non_existent_file)
        assert result is None

    def test_cleanup_methods_error_handling(self):
        """Test cleanup methods error handling."""
        # Test with invalid directory
        original_root = self.optimizer.project_root
        self.optimizer.project_root = Path("/nonexistent/path")

        # Should not raise exceptions but handle gracefully
        results = self.optimizer.cleanup_python_cache()
        assert isinstance(results, dict)
        assert "files_cleaned" in results

        results = self.optimizer.cleanup_log_files()
        assert isinstance(results, dict)
        assert "files_cleaned" in results

        results = self.optimizer.cleanup_temp_files()
        assert isinstance(results, dict)
        assert "files_cleaned" in results

        # Restore original project root
        self.optimizer.project_root = original_root
