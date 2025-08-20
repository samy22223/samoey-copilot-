#!/usr/bin/env python3
"""
Storage Optimization CLI Script

This script provides command-line interface for running storage optimizations
on the Samoey Copilot project.

Usage:
    python scripts/storage_optimizer_cli.py [command] [options]

Commands:
    full            Run full storage optimization
    cache           Clean up Python cache files
    logs            Clean up old log files
    uploads         Optimize file uploads storage
    database        Optimize database storage
    stats           Show current storage statistics

Examples:
    python scripts/storage_optimizer_cli.py full
    python scripts/storage_optimizer_cli.py logs --days 30
    python scripts/storage_optimizer_cli.py stats
"""

import argparse
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.storage_optimizer import StorageOptimizer
from app.services.file_storage import FileStorageService
import logging

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def format_results(results: dict, title: str) -> str:
    """Format results for display."""
    output = [f"\n{'='*50}", f" {title}", f"{'='*50}"]

    for key, value in results.items():
        if isinstance(value, dict):
            output.append(f"\n{key}:")
            for sub_key, sub_value in value.items():
                if 'bytes' in sub_key:
                    output.append(f"  {sub_key}: {sub_value:,} ({sub_value / (1024*1024):.2f} MB)")
                else:
                    output.append(f"  {sub_key}: {sub_value}")
        else:
            if 'bytes' in key:
                output.append(f"{key}: {value:,} ({value / (1024*1024):.2f} MB)")
            else:
                output.append(f"{key}: {value}")

    return '\n'.join(output)

def main():
    parser = argparse.ArgumentParser(
        description="Storage Optimization CLI for Samoey Copilot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Full optimization command
    full_parser = subparsers.add_parser('full', help='Run full storage optimization')

    # Cache cleanup command
    cache_parser = subparsers.add_parser('cache', help='Clean up Python cache files')

    # Logs cleanup command
    logs_parser = subparsers.add_parser('logs', help='Clean up old log files')
    logs_parser.add_argument('--days', type=int, default=7,
                           help='Number of days to keep logs (default: 7)')

    # Uploads optimization command
    uploads_parser = subparsers.add_parser('uploads', help='Optimize file uploads storage')

    # Database optimization command
    database_parser = subparsers.add_parser('database', help='Optimize database storage')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show current storage statistics')

    # JSON output option
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    setup_logging()
    optimizer = StorageOptimizer()

    try:
        if args.command == 'full':
            results = optimizer.run_full_optimization()
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(format_results(results, "Full Storage Optimization Results"))

        elif args.command == 'cache':
            results = optimizer.cleanup_python_cache()
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(format_results(results, "Python Cache Cleanup Results"))

        elif args.command == 'logs':
            results = optimizer.cleanup_log_files(days=args.days)
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(format_results(results, f"Log Files Cleanup Results (>{args.days} days)"))

        elif args.command == 'uploads':
            results = optimizer.optimize_uploads_storage()
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(format_results(results, "Uploads Storage Optimization Results"))

        elif args.command == 'database':
            results = optimizer.optimize_database_storage()
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(format_results(results, "Database Storage Optimization Results"))

        elif args.command == 'stats':
            file_storage = FileStorageService()
            results = file_storage.get_storage_stats()
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(format_results(results, "Current Storage Statistics"))

        print(f"\n{'='*50}")
        print(" Optimization completed successfully!")
        print(f"{'='*50}")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
