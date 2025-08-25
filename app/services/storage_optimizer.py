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

class StorageOptimizer:
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

            compressed_size = Path(f"{file_path}.gz").stat().st_size
            space_saved = original_size - compressed_size

            if space_saved > 0:
                file_path.unlink()  # Remove original file
                logger.info(f"Compressed {file_path} (saved {space_saved} bytes)")
                return space_saved
            else:
                # Remove compressed file if no benefit
                Path(f"{file_path}.gz").unlink()
                return None

        except Exception as e:
            logger.error(f"Error compressing {file_path}: {str(e)}")
            return None

    def _remove_duplicate_files(self, directory: Path) -> Dict[str, int]:
        """Remove duplicate files based on content hash."""
        file_hashes = {}
        duplicates_removed = 0
        space_freed = 0

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    try:
                        file_hash = self._get_file_hash(file_path)
                        if file_hash in file_hashes:
                            # Found duplicate
                            duplicate_size = file_path.stat().st_size
                            file_path.unlink()
                            duplicates_removed += 1
                            space_freed += duplicate_size
                            logger.info(f"Removed duplicate file: {file_path}")
                        else:
                            file_hashes[file_hash] = file_path
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {str(e)}")

        except Exception as e:
            logger.error(f"Error in duplicate file removal: {str(e)}")

        return {
            "files_removed": duplicates_removed,
            "space_freed": space_freed
        }

    def _get_file_hash(self, file_path: Path) -> str:
        """Get simple hash of file content."""
        import hashlib
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def optimize_database_storage(self) -> Dict[str, Any]:
        """Optimize database storage by cleaning old records."""
        results = {
            "old_messages_cleaned": 0,
            "old_conversations_cleaned": 0,
            "old_files_cleaned": 0,
            "space_estimated_saved": 0
        }

        try:
            from app.db.session import SessionLocal
            from app.models import Message, Conversation, File
            from sqlalchemy import func
            from datetime import datetime, timedelta

            db = SessionLocal()
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=self.cleanup_threshold_days)

                # Clean old messages
                old_messages = db.query(Message).filter(Message.created_at < cutoff_date).count()
                if old_messages > 0:
                    db.query(Message).filter(Message.created_at < cutoff_date).delete()
                    results["old_messages_cleaned"] = old_messages

                # Clean old conversations without messages
                old_conversations = db.query(Conversation).filter(
                    Conversation.created_at < cutoff_date,
                    ~Conversation.messages.any()
                ).count()
                if old_conversations > 0:
                    db.query(Conversation).filter(
                        Conversation.created_at < cutoff_date,
                        ~Conversation.messages.any()
                    ).delete()
                    results["old_conversations_cleaned"] = old_conversations

                # Clean old files
                old_files = db.query(File).filter(File.created_at < cutoff_date).count()
                if old_files > 0:
                    db.query(File).filter(File.created_at < cutoff_date).delete()
                    results["old_files_cleaned"] = old_files

                db.commit()

                # Estimate space saved (rough estimate)
                avg_message_size = 1024  # 1KB per message
                avg_file_size = 1024 * 1024  # 1MB per file
                results["space_estimated_saved"] = (
                    results["old_messages_cleaned"] * avg_message_size +
                    results["old_files_cleaned"] * avg_file_size
                )

            except Exception as e:
                db.rollback()
                logger.error(f"Error in database optimization: {str(e)}")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")

        results["space_estimated_saved_mb"] = round(results["space_estimated_saved"] / (1024 * 1024), 2)
        return results

    def optimize_node_modules(self) -> Dict[str, Any]:
        """Optimize node_modules by deduplication, pruning, and cache cleanup."""
        results = {
            "packages_pruned": 0,
            "cache_cleaned": 0,
            "space_saved_bytes": 0,
            "duplicate_packages_removed": 0
        }

        try:
            # Clean npm cache
            try:
                result = subprocess.run(['npm', 'cache', 'clean', '--force'],
                                      capture_output=True, text=True, cwd=self.project_root)
                if result.returncode == 0:
                    results["cache_cleaned"] = 1
                    logger.info("npm cache cleaned successfully")
            except Exception as e:
                logger.error(f"Error cleaning npm cache: {str(e)}")

            # Prune unused packages in root node_modules
            root_node_modules = self.project_root / "node_modules"
            if root_node_modules.exists():
                try:
                    result = subprocess.run(['npm', 'prune'],
                                          capture_output=True, text=True, cwd=self.project_root)
                    if result.returncode == 0:
                        results["packages_pruned"] = 1
                        results["space_saved_bytes"] += 50 * 1024 * 1024  # Estimate 50MB saved
                        logger.info("Root node_modules pruned successfully")
                except Exception as e:
                    logger.error(f"Error pruning root node_modules: {str(e)}")

            # Prune frontend node_modules
            frontend_node_modules = self.project_root / "frontend" / "node_modules"
            if frontend_node_modules.exists():
                try:
                    result = subprocess.run(['npm', 'prune'],
                                          capture_output=True, text=True, cwd=frontend_node_modules.parent)
                    if result.returncode == 0:
                        results["packages_pruned"] += 1
                        results["space_saved_bytes"] += 10 * 1024 * 1024  # Estimate 10MB saved
                        logger.info("Frontend node_modules pruned successfully")
                except Exception as e:
                    logger.error(f"Error pruning frontend node_modules: {str(e)}")

        except Exception as e:
            logger.error(f"Error in node_modules optimization: {str(e)}")

        results["space_saved_mb"] = round(results["space_saved_bytes"] / (1024 * 1024), 2)
        return results

    def cleanup_build_artifacts(self) -> Dict[str, Any]:
        """Clean up build artifacts and temporary build files."""
        results = {
            "build_dirs_removed": 0,
            "dist_files_removed": 0,
            "space_freed_bytes": 0
        }

        build_patterns = ["build", "dist", "out", ".next", ".cache"]

        try:
            for pattern in build_patterns:
                for item in self.project_root.rglob(pattern):
                    if item.is_dir():
                        try:
                            dir_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                            shutil.rmtree(item)
                            results["build_dirs_removed"] += 1
                            results["space_freed_bytes"] += dir_size
                            logger.info(f"Removed build directory: {item}")
                        except Exception as e:
                            logger.error(f"Error removing {item}: {str(e)}")

        except Exception as e:
            logger.error(f"Error in build artifacts cleanup: {str(e)}")

        results["space_freed_mb"] = round(results["space_freed_bytes"] / (1024 * 1024), 2)
        return results

    def optimize_sqlite_database(self, db_path: Optional[str] = None) -> Dict[str, Any]:
        """Optimize SQLite database with VACUUM and REINDEX."""
        results = {
            "database_optimized": False,
            "space_freed_bytes": 0
        }

        try:
            # Find database files if not specified
            if not db_path:
                db_files = list(self.project_root.rglob("*.db"))
                if not db_files:
                    logger.info("No SQLite database files found")
                    return results
                db_path = str(db_files[0])

            db_file = Path(db_path)
            if not db_file.exists():
                logger.warning(f"Database file not found: {db_path}")
                return results

            # Get size before optimization
            before_size = db_file.stat().st_size

            # Optimize database
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("VACUUM")
                conn.execute("REINDEX")
                conn.commit()

                # Get size after optimization
                after_size = db_file.stat().st_size
                results["space_freed_bytes"] = before_size - after_size
                results["database_optimized"] = True

                logger.info(f"Database optimized: {db_path}, saved {results['space_freed_bytes']} bytes")
            finally:
                conn.close()

        except Exception as e:
            logger.error(f"Error in database optimization: {str(e)}")

        results["space_freed_mb"] = round(results["space_freed_bytes"] / (1024 * 1024), 2)
        return results

    def run_full_optimization(self) -> Dict[str, Any]:
        """Run all storage optimization methods."""
        total_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "python_cache_cleanup": {},
            "log_files_cleanup": {},
            "temp_files_cleanup": {},
            "uploads_optimization": {},
            "database_optimization": {},
            "total_space_saved_bytes": 0,
            "total_files_cleaned": 0
        }

        try:
            # Python cache cleanup
            total_results["python_cache_cleanup"] = self.cleanup_python_cache()

            # Log files cleanup
            total_results["log_files_cleanup"] = self.cleanup_log_files()

            # Temporary files cleanup
            total_results["temp_files_cleanup"] = self.cleanup_temp_files()

            # Uploads optimization
            total_results["uploads_optimization"] = self.optimize_uploads_storage()

            # Database optimization
            total_results["database_optimization"] = self.optimize_database_storage()

            # Calculate totals
            total_results["total_space_saved_bytes"] = (
                total_results["python_cache_cleanup"]["space_freed_bytes"] +
                total_results["log_files_cleanup"]["space_freed_bytes"] +
                total_results["temp_files_cleanup"]["space_freed_bytes"] +
                total_results["uploads_optimization"]["space_saved_bytes"] +
                total_results["database_optimization"]["space_estimated_saved"]
            )

            total_results["total_files_cleaned"] = (
                total_results["python_cache_cleanup"]["files_cleaned"] +
                total_results["log_files_cleanup"]["files_cleaned"] +
                total_results["temp_files_cleanup"]["files_cleaned"] +
                total_results["uploads_optimization"]["old_files_cleaned"] +
                total_results["uploads_optimization"]["duplicate_files_removed"]
            )

            total_results["total_space_saved_mb"] = round(total_results["total_space_saved_bytes"] / (1024 * 1024), 2)

            logger.info(f"Storage optimization completed. Total space saved: {total_results['total_space_saved_mb']} MB")

        except Exception as e:
            logger.error(f"Error in full optimization: {str(e)}")

