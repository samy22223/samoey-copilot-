# Storage Optimization Guide

This document provides a comprehensive guide to the storage optimization system implemented for the Samoey Copilot project.

## Overview

The storage optimization system is designed to automatically and manually clean up unnecessary files, compress large files, remove duplicates, and optimize database storage to save disk space and improve system performance.

## Components

### 1. Storage Optimizer Service (`app/services/storage_optimizer.py`)

The core service that provides various optimization methods:

- **Python Cache Cleanup**: Removes `__pycache__` directories and `.pyc` files
- **Log Files Cleanup**: Removes old log files based on configurable age
- **Temporary Files Cleanup**: Removes temporary files and system files
- **Uploads Storage Optimization**: Compresses large text files and removes duplicates
- **Database Storage Optimization**: Cleans old database records
- **Full Optimization**: Runs all optimization methods and provides comprehensive results

### 2. API Endpoints (`app/api/v1/endpoints/storage.py`)

RESTful API endpoints for storage optimization:

- `POST /api/v1/storage/optimize` - Run full optimization
- `POST /api/v1/storage/optimize/cache` - Clean Python cache
- `POST /api/v1/storage/optimize/logs` - Clean log files
- `POST /api/v1/storage/optimize/uploads` - Optimize uploads storage
- `POST /api/v1/storage/optimize/database` - Optimize database storage
- `GET /api/v1/storage/stats` - Get current storage statistics

### 3. CLI Tool (`scripts/storage_optimizer_cli.py`)

Command-line interface for running optimizations:

```bash
# Run full optimization
python scripts/storage_optimizer_cli.py full

# Clean Python cache
python scripts/storage_optimizer_cli.py cache

# Clean log files older than 30 days
python scripts/storage_optimizer_cli.py logs --days 30

# Optimize uploads storage
python scripts/storage_optimizer_cli.py uploads

# Optimize database storage
python scripts/storage_optimizer_cli.py database

# Show storage statistics
python scripts/storage_optimizer_cli.py stats

# Output in JSON format
python scripts/storage_optimizer_cli.py full --json
```

### 4. Test Suite (`app/tests/test_storage_optimizer.py`)

Comprehensive test suite covering all optimization methods with proper error handling and edge cases.

## Features

### Automatic Cleanup

The system automatically identifies and removes:

- **Python Cache Files**: `__pycache__` directories and `.pyc` files
- **Old Log Files**: Log files older than configured days (default: 7 days)
- **Temporary Files**: `.tmp`, `.temp`, `.cache`, `.DS_Store`, `Thumbs.db` files

### File Compression

Large text files (>1MB) with extensions `.txt`, `.json`, `.xml`, `.csv`, `.log`, `.md` are automatically compressed using gzip to save space.

### Duplicate Detection

The system uses MD5 hashing to identify and remove duplicate files in the uploads directory, keeping only the first occurrence.

### Database Optimization

Old database records are cleaned up based on configurable thresholds:

- Messages older than 30 days
- Conversations without messages older than 30 days
- File records older than 30 days

### Comprehensive Reporting

All operations provide detailed reports including:

- Number of files cleaned/removed
- Amount of space freed (in bytes and MB)
- Extension distribution for uploads
- Timestamps and operation summaries

## Configuration

### Environment Variables

The system uses the following configuration from `app/core/config.py`:

- `UPLOAD_DIR`: Directory for file uploads (default: "uploads")
- `MAX_UPLOAD_SIZE`: Maximum file size for uploads (default: 10MB)
- `ALLOWED_EXTENSIONS`: Comma-separated list of allowed file extensions

### Customization

You can customize the optimization behavior by modifying the `StorageOptimizer` class:

```python
# Change cleanup threshold
optimizer.cleanup_threshold_days = 60  # Clean files older than 60 days

# Add more file patterns to clean
temp_patterns = ["*.tmp", "*.temp", "*.cache", ".DS_Store", "Thumbs.db", "*.bak"]

# Modify compression settings
compressible_extensions = {'.txt', '.json', '.xml', '.csv', '.log', '.md', '.yaml', '.yml'}
```

## Security Considerations

### Authentication

All API endpoints require authentication via JWT tokens. Only authenticated users can perform storage operations.

### File Access

The system only operates within the project directory and configured upload directories. It cannot access files outside these boundaries.

### Database Operations

Database operations use proper transaction handling with rollback on errors to prevent data corruption.

### Error Handling

All operations include comprehensive error handling to prevent system crashes and provide meaningful error messages.

## Usage Examples

### API Usage

```bash
# Get storage statistics
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/storage/stats

# Run full optimization
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/storage/optimize

# Clean cache only
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/storage/optimize/cache
```

### Programmatic Usage

```python
from app.services.storage_optimizer import StorageOptimizer

# Initialize optimizer
optimizer = StorageOptimizer()

# Run full optimization
results = optimizer.run_full_optimization()
print(f"Space saved: {results['total_space_saved_mb']} MB")

# Clean only Python cache
cache_results = optimizer.cleanup_python_cache()
print(f"Cleaned {cache_results['files_cleaned']} cache files")

# Get storage statistics
from app.services.file_storage import FileStorageService
file_storage = FileStorageService()
stats = file_storage.get_storage_stats()
print(f"Total files: {stats['total_files']}")
print(f"Total size: {stats['total_size_mb']} MB")
```

## Monitoring and Logging

### Logging

All operations are logged with appropriate levels:

- `INFO`: Normal operation logs
- `ERROR`: Error conditions
- `WARNING`: Warning conditions

Log messages include details about files processed, space saved, and any errors encountered.

### Monitoring

The system integrates with the existing monitoring infrastructure:

- Prometheus metrics can be added for tracking space saved over time
- Health checks can include storage optimization status
- Alerts can be configured for low disk space conditions

## Performance Considerations

### Impact on System Performance

- **File Operations**: Large-scale file operations may temporarily impact system performance
- **Database Operations**: Database cleanup operations are optimized to use efficient queries
- **Memory Usage**: File hashing operations use memory-efficient streaming

### Best Practices

1. **Schedule During Low Traffic**: Run optimizations during off-peak hours
2. **Monitor Disk Space**: Set up alerts for low disk space conditions
3. **Regular Maintenance**: Schedule regular optimization runs (e.g., weekly)
4. **Backup Important Data**: Ensure important files are backed up before cleanup

## Troubleshooting

### Common Issues

#### Permission Errors
If you encounter permission errors:
```bash
# Check file permissions
ls -la uploads/

# Fix permissions if needed
chmod 755 uploads/
chmod 644 uploads/*
```

#### Database Connection Issues
If database optimization fails:
```bash
# Check database connection
python -c "from app.db.session import SessionLocal; print('Database connection OK')"

# Check database status
docker-compose ps
```

#### File Access Issues
If file operations fail:
```bash
# Check if directories exist
ls -la uploads/
ls -la data/vectorstore/

# Create directories if missing
mkdir -p uploads/processed
mkdir -p uploads/temp
mkdir -p uploads/quarantine
```

#### API Authentication Issues
If API endpoints return 401 errors:
```bash
# Check if you have a valid token
curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'
```

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run optimization with debug output
optimizer = StorageOptimizer()
results = optimizer.run_full_optimization()
```

### Performance Issues

If optimizations are slow:
1. **Check Disk I/O**: Monitor disk usage during operations
2. **Reduce Batch Size**: Process files in smaller batches
3. **Schedule During Off-Peak**: Run during low-traffic periods
4. **Monitor Memory Usage**: Ensure sufficient RAM is available

### Recovery

If important files were accidentally deleted:
1. **Check Backups**: Restore from backup if available
2. **Check System Logs**: Review logs for deleted file information
3. **Use File Recovery Tools**: Use tools like `testdisk` or `photorec` if needed

## Future Enhancements

### Planned Features

1. **Automated Scheduling**: Add cron job support for automatic optimization
2. **Cloud Storage Integration**: Support for S3, Google Cloud Storage, etc.
3. **Advanced Compression**: Add support for more compression algorithms
4. **Smart Cleanup**: Machine learning-based file importance analysis
5. **Real-time Monitoring**: Dashboard for storage usage and optimization history
6. **Multi-tenant Support**: Per-user or per-organization storage optimization

### Integration Opportunities

1. **CI/CD Pipeline**: Add optimization steps to deployment pipeline
2. **Monitoring Systems**: Integrate with Prometheus, Grafana, etc.
3. **Alerting Systems**: Send notifications when space is low
4. **Backup Systems**: Coordinate with backup solutions
5. **Container Orchestration**: Kubernetes operator for storage optimization

## Conclusion

The storage optimization system provides a comprehensive solution for managing disk space in the Samoey Copilot project. With its combination of automatic cleanup, file compression, duplicate detection, and database optimization, it helps maintain system performance and reduce storage costs.

The system is designed to be:
- **Safe**: Includes proper error handling and authentication
- **Flexible**: Configurable and extensible for different needs
- **Comprehensive**: Covers all major areas of storage optimization
- **Monitorable**: Provides detailed logging and reporting
- **Testable**: Includes comprehensive test coverage

By implementing regular storage optimization practices, you can ensure that your system remains efficient and cost-effective as it grows.
