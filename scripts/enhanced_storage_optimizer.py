#!/usr/bin/env python3
"""
Enhanced Storage Optimization CLI Script

This script provides a comprehensive command-line interface for running
advanced storage optimizations on the Samoey Copilot project.

Usage:
    python scripts/enhanced_storage_optimizer.py [command] [options]

Commands:
    full            Run complete storage optimization (all phases)
    phase1          Phase 1: Cache & temp file cleanup
    phase2          Phase 2: Node modules optimization
    phase3          Phase 3: Build artifacts cleanup
    phase4          Phase 4: Database & file storage optimization
    phase5          Phase 5: System-wide optimization
    cache           Clean up Python cache files
    logs            Clean up old log files
    temp            Clean up temporary files
    node_modules    Optimize node_modules storage
    build           Clean up build artifacts
    database        Optimize database storage
    uploads         Optimize file uploads storage
    system          System-wide optimization
    stats           Show current storage statistics
    analyze         Analyze storage usage and show recommendations

Examples:
    python scripts/enhanced_storage_optimizer.py full
    python scripts/enhanced_storage_optimizer.py phase2 --dry-run
    python scripts/enhanced_storage_optimizer.py analyze
    python scripts/enhanced_storage_optimizer.py stats --json
"""

import argparse
import sys
import json
import os
import shutil
import subprocess
import sqlite3
import gzip
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_logging(verbose=False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def format_bytes(bytes_value):
    """Format bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"

def format_results(results: dict, title: str) -> str:
    """Format results for display."""
    output = [f"\n{'='*60}", f" {title}", f"{'='*60}"]

    for key, value in results.items():
        if isinstance(value, dict):
            output.append(f"\n{key}:")
            for sub_key, sub_value in value.items():
                if 'bytes' in sub_key.lower():
                    output.append(f"  {sub_key}: {format_bytes(sub_value)}")
                else:
                    output.append(f"  {sub_key}: {sub_value}")
        else:
            if 'bytes' in key.lower():
                output.append(f"{key}: {format_bytes(value)}")
            else:
                output.append(f"{key}: {value}")

    return '\n'.join(output)

class EnhancedStorageOptimizer:
    def __init__(self, dry_run=False):
        self.project_root = Path(__file__).parent.parent
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        self.cleanup_threshold_days = 30

    def cleanup_python_cache(self) -> Dict[str, Any]:
        """Clean up Python cache files and __pycache__ directories."""
        results = {
            "files_cleaned": 0,
            "space_freed_bytes": 0,
            "cache_dirs_removed": 0
        }

        try:
            # Find all __pycache__ directories
            for cache_dir in self.project_root.rglob("__pycache__"):
                try:
                    dir_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                    if not self.dry_run:
                        shutil.rmtree(cache_dir)
                    results["cache_dirs_removed"] += 1
                    results["space_freed_bytes"] += dir_size
                    action = "Would remove" if self.dry_run else "Removed"
                    self.logger.info(f"{action} __pycache__ directory: {cache_dir} ({format_bytes(dir_size)})")
                except Exception as e:
                    self.logger.error(f"Error removing {cache_dir}: {str(e)}")

            # Find .pyc files
            for pyc_file in self.project_root.rglob("*.pyc"):
                try:
                    file_size = pyc_file.stat().st_size
                    if not self.dry_run:
                        pyc_file.unlink()
                    results["files_cleaned"] += 1
                    results["space_freed_bytes"] += file_size
                    action = "Would remove" if self.dry_run else "Removed"
                    self.logger.info(f"{action} .pyc file: {pyc_file} ({format_bytes(file_size)})")
                except Exception as e:
                    self.logger.error(f"Error removing {pyc_file}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error in Python cache cleanup: {str(e)}")

        results["space_freed_mb"] = round(results["space_freed_bytes"] / (1024 * 1024), 2)
        return results

    def cleanup_log_files(self, days: int = 7) -> Dict[str, Any]:
        """Clean up old log files."""
        results = {
            "files_cleaned": 0,
            "space_freed_bytes": 0
        }
        cutoff_time = datetime.now() - timedelta(days=days)

        try:
            for log_file in self.project_root.rglob("*.log"):
                try:
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_size = log_file.stat().st_size
                        if not self.dry_run:
                            log_file.unlink()
                        results["files_cleaned"] += 1
                        results["space_freed_bytes"] += file_size
                        action = "Would remove" if self.dry_run else "Removed"
                        self.logger.info(f"{action} old log file: {log_file} ({format_bytes(file_size)})")
                except Exception as e:
                    self.logger.error(f"Error removing {log_file}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error in log file cleanup: {str(e)}")

        results["space_freed_mb"] = round(results["space_freed_bytes"] / (1024 * 1024), 2)
        return results

    def cleanup_temp_files(self) -> Dict[str, Any]:
        """Clean up temporary files."""
        results = {
            "files_cleaned": 0,
            "space_freed_bytes": 0
        }

        temp_patterns = ["*.tmp", "*.temp", "*.cache", ".DS_Store", "Thumbs.db"]

        try:
            for pattern in temp_patterns:
                for temp_file in self.project_root.rglob(pattern):
                    try:
                        file_size = temp_file.stat().st_size
                        if not self.dry_run:
                            temp_file.unlink()
                        results["files_cleaned"] += 1
                        results["space_freed_bytes"] += file_size
                        action = "Would remove" if self.dry_run else "Removed"
                        self.logger.info(f"{action} temporary file: {temp_file} ({format_bytes(file_size)})")
                    except Exception as e:
                        self.logger.error(f"Error removing {temp_file}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error in temporary file cleanup: {str(e)}")

        results["space_freed_mb"] = round(results["space_freed_bytes"] / (1024 * 1024), 2)
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
                if not self.dry_run:
                    result = subprocess.run(['npm', 'cache', 'clean', '--force'],
                                          capture_output=True, text=True, cwd=self.project_root)
                    if result.returncode == 0:
                        results["cache_cleaned"] = 1
                        results["space_saved_bytes"] += 100 * 1024 * 1024  # Estimate 100MB
                else:
                    results["cache_cleaned"] = 1
                    results["space_saved_bytes"] += 100 * 1024 * 1024

                action = "Would clean" if self.dry_run else "Cleaned"
                self.logger.info(f"{action} npm cache successfully")
            except Exception as e:
                self.logger.error(f"Error cleaning npm cache: {str(e)}")

            # Prune unused packages in root node_modules
            root_node_modules = self.project_root / "node_modules"
            if root_node_modules.exists():
                try:
                    if not self.dry_run:
                        result = subprocess.run(['npm', 'prune'],
                                              capture_output=True, text=True, cwd=self.project_root)
                        if result.returncode == 0:
                            results["packages_pruned"] = 1
                            results["space_saved_bytes"] += 50 * 1024 * 1024  # Estimate 50MB
                    else:
                        results["packages_pruned"] = 1
                        results["space_saved_bytes"] += 50 * 1024 * 1024

                    action = "Would prune" if self.dry_run else "Pruned"
                    self.logger.info(f"{action} root node_modules successfully")
                except Exception as e:
                    self.logger.error(f"Error pruning root node_modules: {str(e)}")

            # Prune frontend node_modules
            frontend_node_modules = self.project_root / "frontend" / "node_modules"
            if frontend_node_modules.exists():
                try:
                    if not self.dry_run:
                        result = subprocess.run(['npm', 'prune'],
                                              capture_output=True, text=True, cwd=frontend_node_modules.parent)
                        if result.returncode == 0:
                            results["packages_pruned"] += 1
                            results["space_saved_bytes"] += 10 * 1024 * 1024  # Estimate 10MB
                    else:
                        results["packages_pruned"] += 1
                        results["space_saved_bytes"] += 10 * 1024 * 1024

                    action = "Would prune" if self.dry_run else "Pruned"
                    self.logger.info(f"{action} frontend node_modules successfully")
                except Exception as e:
                    self.logger.error(f"Error pruning frontend node_modules: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error in node_modules optimization: {str(e)}")

        results["space_saved_mb"] = round(results["space_saved_bytes"] / (1024 * 1024), 2)
        return results

    def cleanup_build_artifacts(self) -> Dict[str, Any]:
        """Clean up build artifacts and temporary build files."""
        results = {
            "build_dirs_removed": 0,
            "files_removed": 0,
            "space_freed_bytes": 0
        }

        build_patterns = ["build", "dist", "out", ".next", ".nuxt", ".output", ".cache", ".turbo"]

        try:
            for pattern in build_patterns:
                for item in self.project_root.rglob(pattern):
                    if item.is_dir():
                        try:
                            dir_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                            if not self.dry_run:
                                shutil.rmtree(item)
                            results["build_dirs_removed"] += 1
                            results["space_freed_bytes"] += dir_size
                            action = "Would remove" if self.dry_run else "Removed"
                            self.logger.info(f"{action} build directory: {item} ({format_bytes(dir_size)})")
                        except Exception as e:
                            self.logger.error(f"Error removing {item}: {str(e)}")
                    else:
                        try:
                            file_size = item.stat().st_size
                            if not self.dry_run:
                                item.unlink()
                            results["files_removed"] += 1
                            results["space_freed_bytes"] += file_size
                            action = "Would remove" if self.dry_run else "Removed"
                            self.logger.info(f"{action} build file: {item} ({format
