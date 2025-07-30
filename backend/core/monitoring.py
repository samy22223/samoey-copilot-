import psutil
import time
from datetime import datetime
import asyncio
from typing import Dict, Any
import redis.asyncio as aioredis
from config.settings import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

class SystemMonitor:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.metrics_key = f"{settings.METRICS_PREFIX}:metrics"
        self.system_metrics_key = f"{settings.METRICS_PREFIX}:system"
        
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "network": {
                    "connections": len(psutil.net_connections())
                },
                "processes": {
                    "total": len(psutil.pids())
                }
            }
            
            # Store in Redis
            await self.redis.set(
                self.system_metrics_key,
                str(metrics),
                ex=300  # expire after 5 minutes
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    async def collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics."""
        try:
            metrics = await self.redis.hgetall(self.metrics_key) or {}
            process = psutil.Process()
            
            app_metrics = {
                "timestamp": datetime.now().isoformat(),
                "process": {
                    "cpu_percent": process.cpu_percent(),
                    "memory_percent": process.memory_percent(),
                    "threads": process.num_threads(),
                    "open_files": len(process.open_files()),
                    "connections": len(process.connections())
                },
                "application": {
                    "total_requests": int(metrics.get("total_requests", 0)),
                    "active_users": int(metrics.get("active_users", 0)),
                    "error_count": int(metrics.get("error_count", 0)),
                    "last_error": metrics.get("last_error", ""),
                    "last_update": metrics.get("last_update", "")
                }
            }
            
            return app_metrics
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return {}
    
    async def monitor_loop(self):
        """Continuous monitoring loop."""
        while True:
            try:
                # Collect metrics
                system_metrics = await self.collect_system_metrics()
                app_metrics = await self.collect_application_metrics()
                
                # Combine metrics
                all_metrics = {
                    "system": system_metrics,
                    "application": app_metrics,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Store combined metrics
                await self.redis.set(
                    f"{settings.METRICS_PREFIX}:all",
                    str(all_metrics),
                    ex=300
                )
                
                # Check thresholds and alert if needed
                await self.check_thresholds(system_metrics)
                
                # Wait before next collection
                await asyncio.sleep(settings.MONITORING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retry
    
    async def check_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and alert if needed."""
        try:
            if metrics.get("cpu", {}).get("percent", 0) > 80:
                await self.alert("High CPU usage detected")
                
            if metrics.get("memory", {}).get("percent", 0) > 85:
                await self.alert("High memory usage detected")
                
            if metrics.get("disk", {}).get("percent", 0) > 90:
                await self.alert("Low disk space warning")
                
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")
    
    async def alert(self, message: str):
        """Send alert for critical issues."""
        try:
            alert = {
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "level": "warning"
            }
            
            # Store alert in Redis
            await self.redis.lpush(f"{settings.METRICS_PREFIX}:alerts", str(alert))
            await self.redis.ltrim(f"{settings.METRICS_PREFIX}:alerts", 0, 99)  # Keep last 100 alerts
            
            # Log alert
            logger.warning(f"System Alert: {message}")
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")

async def init_monitoring(redis_client: aioredis.Redis):
    """Initialize system monitoring."""
    monitor = SystemMonitor(redis_client)
    asyncio.create_task(monitor.monitor_loop())
    logger.info("System monitoring initialized")
