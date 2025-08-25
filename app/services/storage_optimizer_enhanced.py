import os
import shutil
import gzip
import json
import subprocess
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from app.core.config import settings
from app.services.file_storage import FileStorageService

logger = logging.getLogger(__name__)

class EnhancedStorageOptimizer:
    def __init__(self):
        self.file_storage = FileStorageService()
        self.project_root = Path(__file__).parent.parent.parent
        self.cleanup_threshold_days = 30

    def cleanup_python_cache(self) -> Dict[str, int]:
        """Clean up Python cache files and __pycache__ directories."""
        cleaned_count = 0
        space_freed = 0

        try:
            # Find all __pycache__ directories
            for cache_dir in self.project_root.rglob("__pycache__"):
                try:
                    dir_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                    shutil.rmtree(cache_dir)
                    cleaned_count += 1
                    space_freed += dir_size
                    logger.info(f"Removed __pycache__ directory: {cache_dir}")
                except Exception as e:
                    logger.error(f"Error removing {cache_dir}: {str(e)}")

            # Find .pyc files
            for pyc_file in self.project_root.rglob("*.pyc"):
                try:
                    file_size = pyc_file.stat().st_size
                    pyc_file.unlink()
                    cleaned_count += 1
                    space_freed += file_size
                    logger.info(f"Removed .pyc file: {pyc_file}")
                except Exception as e:
                    logger.error(f"Error removing {pyc_file}: {str(e)}")

        except Exception as e:
            logger.error(f"Error in Python cache cleanup: {str(e)}")

        return {
            "files_cleaned": cleaned_count,
            "space_freed_bytes": space_freed,
            "space_freed_mb": round(space_freed / (1024 * 1024), 2)
        }

    def cleanup_log_files(self, days: int = 7) -> Dict[str, int]:
        """Clean up old log files."""
        cleaned_count = 0
        space_freed = 0
        cutoff_time = datetime.now() - timedelta(days=days)

        try:
            for log_file in self.project_root.rglob("*.log"):
                try:
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_size = log_file.stat().st_size
                        log_file.unlink()
                        cleaned_count += 1
                        space_freed += file_size
                        logger.info(f"Removed old log file: {log_file}")
                except Exception as e:
                    logger.error(f"Error removing {log_file}: {str(e)}")

        except Exception as e:
            logger.error(f"Error in log file cleanup: {str(e)}")

        return {
            "files_cleaned": cleaned_count,
            "space_freed_bytes": space_freed,
            "space_freed_mb": round(space_freed / (1024 * 1024), 2)
        }

    def cleanup_temp_files(self) -> Dict[str, int]:
        """Clean up temporary files."""
        cleaned_count = 0
        space_freed = 0

        temp_patterns = ["*.tmp", "*.temp", "*.cache", ".DS_Store", "Thumbs.db"]

        try:
            for pattern in temp_patterns:
                for temp_file in self.project_root.rglob(pattern):
                    try:
                        file_size = temp_file.stat().st_size
                        temp_file.unlink()
                        cleaned_count += 1
                        space_freed += file_size
                        logger.info(f"Removed temporary file: {temp_file}")
                    except Exception as e:
                        logger.error(f"Error removing {temp_file}: {str(e)}")

        except Exception as e:
            logger.error(f"Error in temporary file cleanup: {str(e)}")

        return {
            "files_cleaned": cleaned_count,
            "space_freed_bytes": space_freed,
            "space_freed_mb": round(space_freed / (1024 * 1024), 2)
        }

    def optimize_uploads_storage(self) -> Dict[str, Any]:
        """Optimize file uploads storage with compression and cleanup."""
        results = {
            "files_compressed": 0,
            "space_saved_bytes": 0,
            "old_files_cleaned": 0,
            "duplicate_files_removed": 0
        }

        try:
            # Clean up old files
            old_files = self.file_storage.cleanup_old_files(days=self.cleanup_threshold_days)
            results["old_files_cleaned"] = old_files

            # Compress large text files
            upload_dir = Path(settings.UPLOAD_DIR or "uploads")
            if upload_dir.exists():
                for file_path in upload_dir.rglob("*"):
                    if file_path.is_file() and self._should_compress(file_path):
                        compression_result = self._compress_file(file_path)
                        if compression_result:
                            results["files_compressed"] += 1
                            results["space_saved_bytes"] += compression_result

            # Remove duplicate files
            duplicate_result = self._remove_duplicate_files(upload_dir)
            results["duplicate_files_removed"] = duplicate_result["files_removed"]
            results["space_saved_bytes"] += duplicate_result["space_freed"]

        except Exception as e:
            logger.error(f"Error in uploads storage optimization: {str(e)}")

        results["space_saved_mb"] = round(results["space_saved_bytes"] / (1024 * 1024), 2)
        return results

    def _should_compress(self, file_path: Path) -> bool:
        """Check if file should be compressed."""
        compressible_extensions = {'.txt', '.json', '.xml', '.csv', '.log', '.md'}
        return (
            file_path.suffix.lower() in compressible_extensions and
            file_path.stat().st_size > 1024 * 1024 and  # Larger than 1MB
            not file_path.name.endswith('.gz')
        )

    def _compress_file(self, file_path: Path) -> Optional[int]:
        """Compress a file and return space saved."""
        try:
            original_size = file_path.stat().st_size

            with open(file_path, 'rb') as f_in:
                with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            compressed_size =
