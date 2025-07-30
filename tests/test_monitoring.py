import pytest
import asyncio
from unittest.mock import patch, MagicMock
from ..core.monitoring import SystemMonitor, system_monitor
from prometheus_client import REGISTRY

@pytest.fixture
async def monitor():
    """Create test monitor instance"""
    monitor = SystemMonitor()
    yield monitor
    await monitor.stop()

async def test_monitor_start_stop(monitor):
    """Test monitor start and stop"""
    assert not monitor._running
    
    await monitor.start()
    assert monitor._running
    assert monitor._task is not None
    
    await monitor.stop()
    assert not monitor._running
    assert monitor._task is None

@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
@patch('psutil.disk_usage')
async def test_system_stats(mock_disk, mock_memory, mock_cpu):
    """Test system statistics collection"""
    # Mock system metrics
    mock_cpu.return_value = 50.0
    
    mock_memory.return_value = MagicMock(
        percent=60.0,
        used=8000000000,
        total=16000000000
    )
    
    mock_disk.return_value = MagicMock(
        percent=70.0,
        used=500000000000,
        total=1000000000000
    )
    
    stats = system_monitor.get_system_stats()
    
    assert stats["cpu_percent"] == 50.0
    assert stats["memory_percent"] == 60.0
    assert stats["disk_percent"] == 70.0
    assert "timestamp" in stats

def test_request_metrics():
    """Test request metrics recording"""
    # Clear any existing metrics
    for metric in REGISTRY.collect():
        if metric.name in ["pinnacle_request_total", "pinnacle_request_latency_seconds"]:
            REGISTRY.unregister(metric)
    
    # Record test requests
    system_monitor.record_request("GET", "/test", 200, 0.1)
    system_monitor.record_request("POST", "/test", 201, 0.2)
    system_monitor.record_request("GET", "/test", 404, 0.3)
    
    # Verify metrics
    metrics = {metric.name: metric for metric in REGISTRY.collect()}
    
    assert "pinnacle_request_total" in metrics
    assert "pinnacle_request_latency_seconds" in metrics

def test_error_metrics():
    """Test error metrics recording"""
    # Clear any existing metrics
    for metric in REGISTRY.collect():
        if metric.name == "pinnacle_error_total":
            REGISTRY.unregister(metric)
    
    # Record test errors
    system_monitor.record_error("validation_error")
    system_monitor.record_error("database_error")
    system_monitor.record_error("validation_error")
    
    # Verify metrics
    metrics = {metric.name: metric for metric in REGISTRY.collect()}
    
    assert "pinnacle_error_total" in metrics
    
    # Get error counts
    error_counts = {}
    for sample in metrics["pinnacle_error_total"].samples:
        if sample.name == "pinnacle_error_total":
            error_counts[sample.labels["type"]] = sample.value
    
    assert error_counts["validation_error"] == 2
    assert error_counts["database_error"] == 1

@pytest.mark.asyncio
async def test_monitoring_alerts():
    """Test monitoring alerts"""
    with patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk, \
         patch('backend.core.monitoring.logger') as mock_logger:
        
        # Set values above thresholds
        mock_cpu.return_value = 95.0
        mock_memory.return_value = MagicMock(percent=90.0)
        mock_disk.return_value = MagicMock(percent=95.0)
        
        monitor = SystemMonitor()
        await monitor.start()
        
        # Wait for one monitoring cycle
        await asyncio.sleep(monitor.interval + 0.1)
        
        # Verify alerts were logged
        mock_logger.warning.assert_any_call("High CPU usage: 95.0%")
        mock_logger.warning.assert_any_call("High memory usage: 90.0%")
        
        await monitor.stop()
