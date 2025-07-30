from typing import Dict, List
import asyncio
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, Histogram
import aioredis
from ..core.security_settings import security_settings
from ..core.security_audit import security_audit_logger

# Define Prometheus metrics
SECURITY_METRICS = {
    'events': Counter('security_events_total', 'Total security events', ['type']),
    'alerts': Counter('security_alerts_total', 'Total security alerts', ['severity']),
    'blocked_requests': Counter('blocked_requests_total', 'Total blocked requests', ['reason']),
    'ai_events': Counter('ai_security_events_total', 'Total AI security events', ['type']),
    'response_time': Histogram('security_response_time_seconds', 'Security response time'),
    'threat_level': Gauge('security_threat_level', 'Current security threat level')
}

class SecurityMetricsCollector:
    def __init__(self):
        self.redis = None
        self.collection_interval = 60  # seconds
        self._running = False

    async def initialize(self):
        """Initialize metrics collector"""
        self.redis = await aioredis.create_redis_pool(
            f'redis://{security_settings.REDIS_HOST}:{security_settings.REDIS_PORT}',
            db=security_settings.REDIS_SECURITY_DB
        )
        self._running = True
        asyncio.create_task(self._collect_metrics_loop())

    async def close(self):
        """Cleanup metrics collector"""
        self._running = False
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    async def _collect_metrics_loop(self):
        """Main metrics collection loop"""
        while self._running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                security_audit_logger.log_security_event(
                    "metrics_collection_error",
                    {"error": str(e)}
                )
                await asyncio.sleep(5)

    async def _collect_metrics(self):
        """Collect all security metrics"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=5)

        # Collect event metrics
        events = await self._get_recent_events(window_start)
        for event in events:
            SECURITY_METRICS['events'].labels(type=event['type']).inc()

        # Collect alert metrics
        alerts = await self._get_recent_alerts(window_start)
        for alert in alerts:
            SECURITY_METRICS['alerts'].labels(severity=alert['severity']).inc()

        # Collect AI security metrics
        ai_events = await self._get_recent_ai_events(window_start)
        for event in ai_events:
            SECURITY_METRICS['ai_events'].labels(type=event['type']).inc()

        # Update threat level
        threat_level = await self.redis.get('security:threat_level')
        if threat_level:
            SECURITY_METRICS['threat_level'].set(int(threat_level))

    async def _get_recent_events(self, since: datetime) -> List[Dict]:
        """Get recent security events"""
        events = []
        try:
            raw_events = await self.redis.lrange('security:events', 0, -1)
            for event in raw_events:
                event_data = eval(event)
                event_time = datetime.fromisoformat(event_data['timestamp'])
                if event_time >= since:
                    events.append(event_data)
        except Exception as e:
            security_audit_logger.log_security_event(
                "metrics_collection_error",
                {"error": f"Error getting recent events: {str(e)}"}
            )
        return events

    async def _get_recent_alerts(self, since: datetime) -> List[Dict]:
        """Get recent security alerts"""
        alerts = []
        try:
            raw_alerts = await self.redis.lrange('security:alerts', 0, -1)
            for alert in raw_alerts:
                alert_data = eval(alert)
                alert_time = datetime.fromisoformat(alert_data['timestamp'])
                if alert_time >= since:
                    alerts.append(alert_data)
        except Exception as e:
            security_audit_logger.log_security_event(
                "metrics_collection_error",
                {"error": f"Error getting recent alerts: {str(e)}"}
            )
        return alerts

    async def _get_recent_ai_events(self, since: datetime) -> List[Dict]:
        """Get recent AI security events"""
        events = []
        try:
            raw_events = await self.redis.lrange('ai:security:events', 0, -1)
            for event in raw_events:
                event_data = eval(event)
                event_time = datetime.fromisoformat(event_data['timestamp'])
                if event_time >= since:
                    events.append(event_data)
        except Exception as e:
            security_audit_logger.log_security_event(
                "metrics_collection_error",
                {"error": f"Error getting recent AI events: {str(e)}"}
            )
        return events

    async def get_metrics_summary(self) -> Dict:
        """Get summary of current security metrics"""
        try:
            return {
                'events_total': await self.redis.get('security:metrics:events_total'),
                'alerts_total': await self.redis.get('security:metrics:alerts_total'),
                'blocked_requests': await self.redis.get('security:metrics:blocked_requests'),
                'ai_events_total': await self.redis.get('security:metrics:ai_events_total'),
                'threat_level': await self.redis.get('security:threat_level'),
                'active_defenses': len(await self.redis.smembers('security:active_defenses'))
            }
        except Exception as e:
            security_audit_logger.log_security_event(
                "metrics_summary_error",
                {"error": str(e)}
            )
            return {}

# Create global instance
security_metrics = SecurityMetricsCollector()
