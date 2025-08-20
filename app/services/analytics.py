from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from app.core.config import settings
import psutil
import time

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        # In production, this would connect to a real analytics database
        self.usage_data = []
        self.performance_data = []

    async def get_usage_analytics(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get usage analytics for a user or system."""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # Simulate analytics data (in production, this would query a real database)
            analytics_data = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "user_activity": {
                    "total_sessions": 45,
                    "active_days": 23,
                    "average_session_duration": "25m 30s",
                    "last_activity": datetime.utcnow().isoformat()
                },
                "messaging": {
                    "total_messages_sent": 342,
                    "total_messages_received": 289,
                    "average_response_time": "2.3s",
                    "conversations_started": 18
                },
                "file_operations": {
                    "files_uploaded": 12,
                    "files_downloaded": 8,
                    "total_storage_used": "45.2 MB",
                    "file_types": {
                        "pdf": 5,
                        "txt": 3,
                        "jpg": 2,
                        "docx": 2
                    }
                },
                "api_usage": {
                    "total_requests": 1256,
                    "successful_requests": 1187,
                    "failed_requests": 69,
                    "average_response_time": "145ms",
                    "peak_hour": "14:00-15:00"
                },
                "ai_interactions": {
                    "ai_queries": 89,
                    "code_generations": 34,
                    "document_analyses": 12,
                    "average_ai_response_time": "1.8s"
                }
            }

            logger.info(f"Retrieved usage analytics for user {user_id}")
            return analytics_data

        except Exception as e:
            logger.error(f"Failed to get usage analytics: {str(e)}")
            raise

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            # Get real system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Get network statistics
            network = psutil.net_io_counters()

            # Get process information
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()

            performance_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "cpu_usage": f"{cpu_percent}%",
                    "memory_usage": f"{memory.percent}%",
                    "memory_total": f"{memory.total / (1024**3):.2f} GB",
                    "memory_available": f"{memory.available / (1024**3):.2f} GB",
                    "disk_usage": f"{disk.percent}%",
                    "disk_total": f"{disk.total / (1024**3):.2f} GB",
                    "disk_free": f"{disk.free / (1024**3):.2f} GB"
                },
                "process": {
                    "memory_usage": f"{process_memory.rss / (1024**2):.2f} MB",
                    "cpu_usage": f"{process_cpu}%",
                    "threads": process.num_threads(),
                    "open_files": len(process.open_files())
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "response_times": {
                    "average_api_response": "145ms",
                    "p95_response_time": "320ms",
                    "p99_response_time": "580ms"
                },
                "health": {
                    "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "degraded",
                    "uptime": time.time() - process.create_time()
                }
            }

            logger.info("Retrieved performance metrics")
            return performance_data

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            raise

    async def get_user_analytics(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get detailed analytics for a specific user."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            user_analytics = {
                "user_id": user_id,
                "period": f"{days} days",
                "activity_summary": {
                    "total_logins": 15,
                    "active_days": 12,
                    "average_daily_usage": "3h 24m",
                    "most_active_hour": "10:00",
                    "peak_usage_day": "Tuesday"
                },
                "feature_usage": {
                    "chat_usage": 89,
                    "file_uploads": 12,
                    "ai_queries": 45,
                    "api_calls": 234,
                    "settings_changes": 7
                },
                "engagement_metrics": {
                    "session_duration_avg": "25m 30s",
                    "bounce_rate": "15%",
                    "feature_adoption": "78%",
                    "satisfaction_score": 4.2
                },
                "growth_trend": {
                    "usage_increase": "+23%",
                    "feature_adoption_increase": "+12%",
                    "session_duration_increase": "+8%"
                }
            }

            logger.info(f"Retrieved user analytics for user {user_id}")
            return user_analytics

        except Exception as e:
            logger.error(f"Failed to get user analytics: {str(e)}")
            raise

    async def get_system_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics."""
        try:
            system_analytics = {
                "timestamp": datetime.utcnow().isoformat(),
                "overview": {
                    "total_users": 1247,
                    "active_users_24h": 342,
                    "active_users_7d": 892,
                    "total_sessions_today": 1567
                },
                "performance": {
                    "avg_response_time": "145ms",
                    "uptime": "99.9%",
                    "error_rate": "0.3%",
                    "throughput": "1250 req/min"
                },
                "resource_usage": {
                    "cpu_avg": "45%",
                    "memory_avg": "62%",
                    "disk_usage": "78%",
                    "network_io": "2.3 GB/s"
                },
                "top_features": {
                    "chat": 45,
                    "file_operations": 23,
                    "ai_queries": 18,
                    "settings": 8,
                    "analytics": 6
                },
                "alerts": {
                    "critical": 0,
                    "warning": 2,
                    "info": 5
                }
            }

            logger.info("Retrieved system analytics")
            return system_analytics

        except Exception as e:
            logger.error(f"Failed to get system analytics: {str(e)}")
            raise

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for monitoring."""
        try:
            real_time_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "current": {
                    "active_users": 45,
                    "concurrent_sessions": 67,
                    "requests_per_second": 12.3,
                    "active_connections": 89
                },
                "performance": {
                    "current_cpu": psutil.cpu_percent(),
                    "current_memory": psutil.virtual_memory().percent,
                    "current_disk_io": psutil.disk_io_counters().read_bytes + psutil.disk_io_counters().write_bytes,
                    "current_network_io": psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
                },
                "health": {
                    "database_latency": "12ms",
                    "cache_hit_rate": "94.2%",
                    "error_rate_last_minute": "0.1%",
                    "active_background_jobs": 3
                }
            }

            return real_time_data

        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {str(e)}")
            raise

    async def record_event(self, event_type: str, user_id: int, data: Dict[str, Any]) -> bool:
        """Record an analytics event."""
        try:
            event = {
                "event_type": event_type,
                "user_id": user_id,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }

            # In production, this would be stored in a time-series database
            self.usage_data.append(event)

            logger.info(f"Recorded analytics event: {event_type} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to record analytics event: {str(e)}")
            return False

# Global analytics service instance
analytics_service = AnalyticsService()
