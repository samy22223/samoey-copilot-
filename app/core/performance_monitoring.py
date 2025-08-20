"""
Advanced Performance Monitoring System for Samoey Copilot
Implements comprehensive monitoring, metrics collection, and real-time alerts
Target: Sub-100ms response times with 99.999% uptime
"""

import time
import asyncio
import threading
import psutil
import os
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import json
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Metric:
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE

@dataclass
class Alert:
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metric_name: str = ""
    threshold: float = 0.0
    current_value: float = 0.0

@dataclass
class PerformanceThreshold:
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    operator: str = "gt"  # gt, lt, eq, ne
    window_seconds: int = 60
    evaluation_count: int = 3

class PerformanceMonitor:
    """
    Advanced performance monitoring system with real-time metrics collection
    and intelligent alerting
    """

    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[Alert] = []
        self.thresholds: List[PerformanceThreshold] = []
        self.subscribers: List[Callable[[Alert], None]] = []
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.evaluation_counters: Dict[str, int] = defaultdict(int)
        self.last_evaluation_values: Dict[str, float] = {}

        # Initialize default thresholds
        self._initialize_default_thresholds()

    def _initialize_default_thresholds(self):
        """Initialize default performance thresholds"""
        default_thresholds = [
            PerformanceThreshold(
                metric_name="response_time_p95",
                warning_threshold=0.5,
                critical_threshold=1.0,
                operator="gt"
            ),
            PerformanceThreshold(
                metric_name="response_time_p99",
                warning_threshold=1.0,
                critical_threshold=2.0,
                operator="gt"
            ),
            PerformanceThreshold(
                metric_name="error_rate",
                warning_threshold=0.01,
                critical_threshold=0.05,
                operator="gt"
            ),
            PerformanceThreshold(
                metric_name="memory_usage_percent",
                warning_threshold=80.0,
                critical_threshold=95.0,
                operator="gt"
            ),
            PerformanceThreshold(
                metric_name="cpu_usage_percent",
                warning_threshold=70.0,
                critical_threshold=90.0,
                operator="gt"
            ),
            PerformanceThreshold(
                metric_name="active_connections",
                warning_threshold=1000,
                critical_threshold=2000,
                operator="gt"
            ),
            PerformanceThreshold(
                metric_name="cache_hit_rate",
                warning_threshold=0.8,
                critical_threshold=0.6,
                operator="lt"
            ),
            PerformanceThreshold(
                metric_name="database_query_time_p95",
                warning_threshold=0.1,
                critical_threshold=0.5,
                operator="gt"
            )
        ]

        self.thresholds.extend(default_thresholds)

    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None,
                     metric_type: MetricType = MetricType.GAUGE):
        """Record a performance metric"""
        try:
            metric = Metric(
                name=name,
                value=value,
                labels=labels or {},
                metric_type=metric_type
            )

            self.metrics[name].append(metric)
            logger.debug(f"Recorded metric: {name}={value}")

            # Evaluate thresholds for this metric
            self._evaluate_thresholds(name, value)

        except Exception as e:
            logger.error(f"Error recording metric {name}: {e}")

    def _evaluate_thresholds(self, metric_name: str, value: float):
        """Evaluate if metric value triggers any thresholds"""
        for threshold in self.thresholds:
            if threshold.metric_name == metric_name:
                self._evaluate_single_threshold(threshold, value)

    def _evaluate_single_threshold(self, threshold: PerformanceThreshold, value: float):
        """Evaluate a single threshold"""
        try:
            triggered = False

            if threshold.operator == "gt" and value > threshold.critical_threshold:
                triggered = True
                severity = AlertSeverity.CRITICAL
            elif threshold.operator == "gt" and value > threshold.warning_threshold:
                triggered = True
                severity = AlertSeverity.MEDIUM
            elif threshold.operator == "lt" and value < threshold.critical_threshold:
                triggered = True
                severity = AlertSeverity.CRITICAL
            elif threshold.operator == "lt" and value < threshold.warning_threshold:
                triggered = True
                severity = AlertSeverity.MEDIUM

            if triggered:
                # Check if we have enough consecutive evaluations
                key = f"{threshold.metric_name}_{severity.value}"
                self.evaluation_counters[key] += 1

                if self.evaluation_counters[key] >= threshold.evaluation_count:
                    self._create_alert(
                        name=f"{threshold.metric_name}_{severity.value}_alert",
                        severity=severity,
                        message=f"{threshold.metric_name} is {value:.3f} (threshold: {threshold.critical_threshold if severity == AlertSeverity.CRITICAL else threshold.warning_threshold})",
                        metric_name=threshold.metric_name,
                        threshold=threshold.critical_threshold if severity == AlertSeverity.CRITICAL else threshold.warning_threshold,
                        current_value=value
                    )
                    self.evaluation_counters[key] = 0
            else:
                # Reset counter if threshold not triggered
                key = f"{threshold.metric_name}_{AlertSeverity.CRITICAL.value}"
                self.evaluation_counters[key] = 0
                key = f"{threshold.metric_name}_{AlertSeverity.MEDIUM.value}"
                self.evaluation_counters[key] = 0

        except Exception as e:
            logger.error(f"Error evaluating threshold {threshold.metric_name}: {e}")

    def _create_alert(self, name: str, severity: AlertSeverity, message: str,
                     metric_name: str = "", threshold: float = 0.0, current_value: float = 0.0):
        """Create and broadcast an alert"""
        try:
            alert = Alert(
                name=name,
                severity=severity,
                message=message,
                metric_name=metric_name,
                threshold=threshold,
                current_value=current_value
            )

            self.alerts.append(alert)

            # Keep only last 1000 alerts
            if len(self.alerts) > 1000:
                self.alerts = self.alerts[-1000:]

            # Broadcast to subscribers
            for subscriber in self.subscribers:
                try:
                    subscriber(alert)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")

            # Log alert
            log_level = {
                AlertSeverity.LOW: logging.INFO,
                AlertSeverity.MEDIUM: logging.WARNING,
                AlertSeverity.HIGH: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL
            }.get(severity, logging.INFO)

            logger.log(log_level, f"ALERT [{severity.value}]: {message}")

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    def subscribe_to_alerts(self, callback: Callable[[Alert], None]):
        """Subscribe to alert notifications"""
        self.subscribers.append(callback)

    def get_metrics(self, name: str = None, limit: int = 100) -> List[Metric]:
        """Get metrics, optionally filtered by name"""
        if name:
            return list(self.metrics[name])[-limit:]
        else:
            all_metrics = []
            for metrics_list in self.metrics.values():
                all_metrics.extend(metrics_list)
            return sorted(all_metrics, key=lambda x: x.timestamp)[-limit:]

    def get_alerts(self, severity: AlertSeverity = None, limit: int = 100) -> List[Alert]:
        """Get alerts, optionally filtered by severity"""
        alerts = self.alerts
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        return alerts[-limit:]

    def get_metric_statistics(self, name: str, window_seconds: int = 300) -> Dict[str, float]:
        """Get statistical summary of a metric"""
        try:
            cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
            recent_metrics = [m for m in self.metrics[name] if m.timestamp > cutoff_time]

            if not recent_metrics:
                return {}

            values = [m.value for m in recent_metrics]

            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "p95": self._percentile(values, 95),
                "p99": self._percentile(values, 99),
                "stddev": statistics.stdev(values) if len(values) > 1 else 0.0
            }
        except Exception as e:
            logger.error(f"Error calculating statistics for {name}: {e}")
            return {}

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def start_monitoring(self):
        """Start the performance monitoring thread"""
        if self.is_running:
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop the performance monitoring thread"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                self._collect_system_metrics()
                self._cleanup_old_metrics()
                time.sleep(10)  # Collect metrics every 10 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric("cpu_usage_percent", cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric("memory_usage_percent", memory.percent)
            self.record_metric("memory_available_bytes", memory.available)
            self.record_metric("memory_total_bytes", memory.total)

            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_metric("disk_usage_percent", disk.percent)
            self.record_metric("disk_free_bytes", disk.free)
            self.record_metric("disk_total_bytes", disk.total)

            # Network I/O
            net_io = psutil.net_io_counters()
            self.record_metric("network_bytes_sent", net_io.bytes_sent)
            self.record_metric("network_bytes_recv", net_io.bytes_recv)

            # Process metrics
            process = psutil.Process()
            self.record_metric("process_cpu_percent", process.cpu_percent())
            self.record_metric("process_memory_percent", process.memory_percent())
            self.record_metric("process_memory_rss", process.memory_info().rss)
            self.record_metric("process_memory_vms", process.memory_info().vms)
            self.record_metric("process_num_threads", process.num_threads())
            self.record_metric("process_num_handles", process.num_handles())

            # Process I/O
            io_counters = process.io_counters()
            self.record_metric("process_read_bytes", io_counters.read_bytes)
            self.record_metric("process_write_bytes", io_counters.write_bytes)

            # Process context switches
            try:
                ctx_switches = process.num_ctx_switches()
                self.record_metric("process_voluntary_ctx_switches", ctx_switches.voluntary)
                self.record_metric("process_involuntary_ctx_switches", ctx_switches.involuntary)
            except (psutil.AccessDenied, AttributeError):
                pass

            # System load average
            try:
                load_avg = os.getloadavg()
                self.record_metric("system_load_1min", load_avg[0])
                self.record_metric("system_load_5min", load_avg[1])
                self.record_metric("system_load_15min", load_avg[2])
            except (AttributeError, OSError):
                pass

            # System uptime
            try:
                uptime = time.time() - psutil.boot_time()
                self.record_metric("system_uptime_seconds", uptime)
            except Exception:
                pass

            # Number of processes
            try:
                num_processes = len(psutil.pids())
                self.record_metric("system_num_processes", num_processes)
            except Exception:
                pass

    def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory bloat"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)  # Keep 24 hours of data

            for metric_name in list(self.metrics.keys()):
                # Remove metrics older than cutoff time
                while self.metrics[metric_name] and self.metrics[metric_name][0].timestamp < cutoff_time:
                    self.metrics[metric_name].popleft()

                # Remove empty metric collections
                if not self.metrics[metric_name]:
                    del self.metrics[metric_name]

        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Get recent metrics (last 5 minutes)
            recent_stats = {}
            metric_names = [
                "cpu_usage_percent", "memory_usage_percent", "response_time_p95",
                "error_rate", "active_connections", "cache_hit_rate"
            ]

            for metric_name in metric_names:
                recent_stats[metric_name] = self.get_metric_statistics(metric_name, 300)

            # Get recent alerts (last hour)
            recent_alerts = self.get_alerts(limit=50)
            critical_alerts = [a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]

            # System health summary
            system_health = self._calculate_system_health()

            return {
                "timestamp": datetime.now().isoformat(),
                "metrics": recent_stats,
                "alerts": {
                    "total": len(recent_alerts),
                    "critical": len(critical_alerts),
                    "recent": [alert.__dict__ for alert in recent_alerts[-10:]]
                },
                "system_health": system_health,
                "monitoring_status": {
                    "is_running": self.is_running,
                    "metrics_count": sum(len(metrics) for metrics in self.metrics.values()),
                    "thresholds_count": len(self.thresholds)
                }
            }
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}

    def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health score"""
        try:
            health_factors = {}

            # CPU health
            cpu_stats = self.get_metric_statistics("cpu_usage_percent", 300)
            if cpu_stats:
                cpu_health = max(0, 100 - cpu_stats["mean"])
                health_factors["cpu"] = cpu_health

            # Memory health
            memory_stats = self.get_metric_statistics("memory_usage_percent", 300)
            if memory_stats:
                memory_health = max(0, 100 - memory_stats["mean"])
                health_factors["memory"] = memory_health

            # Response time health
            response_stats = self.get_metric_statistics("response_time_p95", 300)
            if response_stats:
                # Lower response times are better
                response_health = max(0, 100 - (response_stats["p95"] * 100))
                health_factors["response_time"] = response_health

            # Error rate health
            error_stats = self.get_metric_statistics("error_rate", 300)
            if error_stats:
                # Lower error rates are better
                error_health = max(0, 100 - (error_stats["mean"] * 10000))
                health_factors["error_rate"] = error_health

            # Calculate overall health
            if health_factors:
                overall_health = sum(health_factors.values()) / len(health_factors)
            else:
                overall_health = 100.0

            return {
                "overall": round(overall_health, 2),
                "factors": {k: round(v, 2) for k, v in health_factors.items()},
                "status": "healthy" if overall_health >= 80 else "degraded" if overall_health >= 60 else "critical"
            }
        except Exception as e:
            logger.error(f"Error calculating system health: {e}")
            return {"overall": 0, "factors": {}, "status": "unknown"}

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Performance monitoring decorator
def monitor_performance(metric_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record performance metric
                name = metric_name or f"function_{func.__name__}"
                performance_monitor.record_metric(f"{name}_duration", duration)
                performance_monitor.record_metric(f"{name}_success", 1)

                return result
            except Exception as e:
                duration = time.time() - start_time

                # Record error metric
                name = metric_name or f"function_{func.__name__}"
                performance_monitor.record_metric(f"{name}_duration", duration)
                performance_monitor.record_metric(f"{name}_error", 1)

                raise

        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Record performance metric
                name = metric_name or f"function_{func.__name__}"
                performance_monitor.record_metric(f"{name}_duration", duration)
                performance_monitor.record_metric(f"{name}_success", 1)

                return result
            except Exception as e:
                duration = time.time() - start_time

                # Record error metric
                name = metric_name or f"function_{func.__name__}"
                performance_monitor.record_metric(f"{name}_duration", duration)
                performance_monitor.record_metric(f"{name}_error", 1)

                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# Utility functions for easy metric recording
def record_response_time(endpoint: str, duration: float):
    """Record API response time"""
    performance_monitor.record_metric("api_response_time", duration, {"endpoint": endpoint})

def record_error(endpoint: str, error_type: str = "unknown"):
    """Record API error"""
    performance_monitor.record_metric("api_errors", 1, {"endpoint": endpoint, "error_type": error_type})

def record_cache_hit(cache_key: str = ""):
    """Record cache hit"""
    performance_monitor.record_metric("cache_hits", 1, {"cache_key": cache_key})

def record_cache_miss(cache_key: str = ""):
    """Record cache miss"""
    performance_monitor.record_metric("cache_misses", 1, {"cache_key": cache_key})

def record_database_query(query_type: str, duration: float):
    """Record database query performance"""
    performance_monitor.record_metric("database_query_duration", duration, {"query_type": query_type})

def get_system_health() -> Dict[str, Any]:
    """Get current system health status"""
    return performance_monitor._calculate_system_health()

def get_performance_dashboard() -> Dict[str, Any]:
    """Get performance dashboard data"""
    return performance_monitor.get_dashboard_data()
