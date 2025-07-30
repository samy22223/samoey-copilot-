from typing import Dict, List, Optional
import asyncio
from datetime import datetime, timedelta
import json
import logging
import aioredis
from prometheus_client import Counter, Gauge, Histogram
from ..core.security_settings import security_settings

# Setup logging
logger = logging.getLogger(__name__)

# Prometheus metrics
SECURITY_ALERTS = Counter('security_alerts_total', 'Total security alerts', ['severity'])
THREAT_LEVEL = Gauge('security_threat_level', 'Current security threat level')
RESPONSE_TIME = Histogram('security_response_time_seconds', 'Security response time')

class SecurityMonitor:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.alert_thresholds = {
            'critical': {
                'rate_limit_violations': 10,
                'threat_detections': 5,
                'ai_security_events': 3
            },
            'high': {
                'rate_limit_violations': 5,
                'threat_detections': 3,
                'ai_security_events': 2
            },
            'medium': {
                'rate_limit_violations': 3,
                'threat_detections': 2,
                'ai_security_events': 1
            }
        }

    async def initialize(self):
        """Initialize Redis connection and start monitoring"""
        self.redis = await aioredis.create_redis_pool(
            f'redis://{security_settings.REDIS_HOST}:{security_settings.REDIS_PORT}',
            db=security_settings.REDIS_SECURITY_DB
        )
        asyncio.create_task(self._monitor_loop())

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await self._check_security_metrics()
                await self._update_threat_level()
                await self._cleanup_old_data()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in security monitoring: {str(e)}")
                await asyncio.sleep(5)

    async def _check_security_metrics(self):
        """Check security metrics and generate alerts"""
        now = datetime.utcnow()
        window = now - timedelta(minutes=5)  # 5-minute window
        
        # Get recent events
        events = await self._get_recent_events(window)
        
        # Check against thresholds
        for severity, thresholds in self.alert_thresholds.items():
            for metric, threshold in thresholds.items():
                count = sum(1 for e in events if e['type'] == metric)
                if count >= threshold:
                    await self._generate_alert(
                        severity=severity,
                        metric=metric,
                        count=count,
                        threshold=threshold
                    )

    async def _get_recent_events(self, since: datetime) -> List[Dict]:
        """Get recent security events"""
        events = []
        raw_events = await self.redis.lrange('security:events', 0, -1)
        
        for event in raw_events:
            try:
                event_data = json.loads(event)
                event_time = datetime.fromisoformat(event_data['timestamp'])
                if event_time >= since:
                    events.append(event_data)
            except Exception as e:
                logger.error(f"Error parsing event: {str(e)}")
        
        return events

    async def _generate_alert(self, severity: str, metric: str, count: int, threshold: int):
        """Generate security alert"""
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': severity,
            'metric': metric,
            'count': count,
            'threshold': threshold,
            'message': f"{severity.upper()} alert: {metric} threshold exceeded ({count}/{threshold})"
        }
        
        # Store alert in Redis
        await self.redis.lpush('security:alerts', json.dumps(alert))
        await self.redis.ltrim('security:alerts', 0, 999)  # Keep last 1000 alerts
        
        # Update Prometheus metrics
        SECURITY_ALERTS.labels(severity=severity).inc()
        
        # Log alert
        logger.warning(f"Security Alert: {alert['message']}")

    async def _update_threat_level(self):
        """Update current threat level"""
        events = await self._get_recent_events(
            datetime.utcnow() - timedelta(minutes=15)
        )
        
        # Calculate threat score
        threat_score = sum([
            10 if e.get('severity') == 'critical' else
            5 if e.get('severity') == 'high' else
            2 if e.get('severity') == 'medium' else 1
            for e in events
        ])
        
        # Update threat level
        if threat_score >= 50:
            threat_level = 4  # Critical
        elif threat_score >= 30:
            threat_level = 3  # High
        elif threat_score >= 10:
            threat_level = 2  # Medium
        else:
            threat_level = 1  # Low
            
        await self.redis.set('security:threat_level', threat_level)
        THREAT_LEVEL.set(threat_level)

    async def _cleanup_old_data(self):
        """Clean up old security data"""
        retention_days = security_settings.METRICS_RETENTION_DAYS
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        
        # Clean up old events and alerts
        events = await self._get_recent_events(cutoff)
        await self.redis.delete('security:events')
        for event in events:
            await self.redis.rpush('security:events', json.dumps(event))

    async def get_security_status(self) -> Dict:
        """Get current security status"""
        threat_level = int(await self.redis.get('security:threat_level') or 1)
        recent_alerts = await self.redis.lrange('security:alerts', 0, 9)
        recent_events = await self.redis.lrange('security:events', 0, 9)
        
        return {
            'threat_level': threat_level,
            'threat_level_text': {
                1: 'LOW',
                2: 'MEDIUM',
                3: 'HIGH',
                4: 'CRITICAL'
            }.get(threat_level, 'UNKNOWN'),
            'recent_alerts': [json.loads(alert) for alert in recent_alerts],
            'recent_events': [json.loads(event) for event in recent_events],
            'metrics': {
                'events_today': await self.redis.get('security:metrics:events_today') or 0,
                'alerts_today': await self.redis.get('security:metrics:alerts_today') or 0,
                'blocked_requests': await self.redis.get('security:metrics:blocked_requests') or 0
            }
        }

security_monitor = SecurityMonitor()
