import asyncio
from typing import Dict, List
import aioredis
import logging
from datetime import datetime, timedelta
import json
from prometheus_client import Counter, Gauge, Histogram
from ..core.security_settings import security_settings
from ..core.security_audit import security_audit_logger
from ..core.security_metrics import security_metrics
from ..core.ai_security import ai_security_manager
from ..core.advanced_security import advanced_security

# Setup logging
logger = logging.getLogger(__name__)

# Prometheus metrics
AUTO_ACTIONS = Counter('security_auto_actions_total', 'Total automatic security actions', ['action_type'])
THREAT_MITIGATIONS = Counter('security_threat_mitigations_total', 'Total threats mitigated', ['threat_type'])
AUTO_RESPONSE_TIME = Histogram('security_auto_response_seconds', 'Automated response time')

class SecurityOrchestrator:
    def __init__(self):
        self.redis = None
        self._running = False
        self.current_threat_level = 1
        self.auto_defense_rules = {}
        self.mitigation_strategies = {}
        self.active_mitigations = set()

    async def initialize(self):
        """Initialize the security orchestrator"""
        self.redis = await aioredis.create_redis_pool(
            f'redis://{security_settings.REDIS_HOST}:{security_settings.REDIS_PORT}',
            db=security_settings.REDIS_SECURITY_DB
        )
        self._running = True
        
        # Start monitoring and auto-response tasks
        asyncio.create_task(self._monitor_security_events())
        asyncio.create_task(self._auto_scale_defenses())
        asyncio.create_task(self._update_security_rules())
        asyncio.create_task(self._cleanup_old_data())

    async def close(self):
        """Cleanup orchestrator resources"""
        self._running = False
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    async def _monitor_security_events(self):
        """Monitor security events and trigger automated responses"""
        while self._running:
            try:
                # Get recent security events
                events = await self._get_recent_events()
                
                # Analyze events and determine threat level
                new_threat_level = await self._calculate_threat_level(events)
                
                if new_threat_level != self.current_threat_level:
                    await self._adjust_security_posture(new_threat_level)
                
                # Process events and trigger automated responses
                await self._process_security_events(events)
                
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in security monitoring: {str(e)}")
                await asyncio.sleep(5)

    async def _auto_scale_defenses(self):
        """Automatically scale security defenses based on threat level"""
        while self._running:
            try:
                threat_level = await self.redis.get('security:threat_level')
                if threat_level:
                    threat_level = int(threat_level)
                    await self._adjust_rate_limits(threat_level)
                    await self._adjust_security_rules(threat_level)
                    await self._scale_monitoring(threat_level)
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in auto-scaling defenses: {str(e)}")
                await asyncio.sleep(5)

    async def _adjust_rate_limits(self, threat_level: int):
        """Adjust rate limits based on threat level"""
        base_limits = {
            'default': 100,
            'ai_endpoints': 50,
            'security': 20
        }
        
        # Reduce limits as threat level increases
        multiplier = max(0.2, 1 - (threat_level * 0.2))  # Minimum 20% of base limits
        
        new_limits = {
            k: int(v * multiplier)
            for k, v in base_limits.items()
        }
        
        await self.redis.hmset('security:rate_limits', new_limits)
        AUTO_ACTIONS.labels(action_type='adjust_rate_limits').inc()

    async def _adjust_security_rules(self, threat_level: int):
        """Adjust security rules based on threat level"""
        rules = {
            'max_failed_attempts': max(3, 10 - threat_level * 2),
            'session_duration': max(5, 30 - threat_level * 5),
            'require_mfa': threat_level >= 3,
            'enhanced_validation': threat_level >= 2
        }
        
        await self.redis.hmset('security:rules', rules)
        AUTO_ACTIONS.labels(action_type='adjust_security_rules').inc()

    async def _scale_monitoring(self, threat_level: int):
        """Scale security monitoring based on threat level"""
        monitoring_config = {
            'log_level': 'DEBUG' if threat_level >= 3 else 'INFO',
            'metrics_interval': max(5, 30 - threat_level * 5),
            'detailed_tracking': threat_level >= 2
        }
        
        await self.redis.hmset('security:monitoring', monitoring_config)
        AUTO_ACTIONS.labels(action_type='scale_monitoring').inc()

    async def _process_security_events(self, events: List[Dict]):
        """Process security events and trigger automated responses"""
        for event in events:
            event_type = event.get('type')
            if not event_type:
                continue
            
            with AUTO_RESPONSE_TIME.time():
                if event_type == 'threat_detected':
                    await self._handle_threat(event)
                elif event_type == 'rate_limit_exceeded':
                    await self._handle_rate_limit_violation(event)
                elif event_type == 'ai_security_event':
                    await self._handle_ai_security_event(event)
                elif event_type == 'auth_failure':
                    await self._handle_auth_failure(event)

    async def _handle_threat(self, event: Dict):
        """Handle detected threats"""
        threat_type = event.get('threat_type')
        source_ip = event.get('source_ip')
        
        if not threat_type or not source_ip:
            return
        
        # Apply immediate mitigation
        mitigation = await self._get_mitigation_strategy(threat_type)
        if mitigation:
            await self._apply_mitigation(source_ip, mitigation)
            THREAT_MITIGATIONS.labels(threat_type=threat_type).inc()

    async def _handle_rate_limit_violation(self, event: Dict):
        """Handle rate limit violations"""
        source_ip = event.get('source_ip')
        if not source_ip:
            return
        
        # Increment violation counter
        violations = await self.redis.hincrby(
            f'security:violations:{source_ip}',
            'rate_limit',
            1
        )
        
        if violations >= 5:  # Auto-block after 5 violations
            await self._block_ip(source_ip, duration=3600)  # 1 hour
            AUTO_ACTIONS.labels(action_type='ip_block').inc()

    async def _handle_ai_security_event(self, event: Dict):
        """Handle AI security events"""
        event_type = event.get('ai_event_type')
        source_ip = event.get('source_ip')
        
        if not event_type or not source_ip:
            return
        
        if event_type == 'prompt_injection':
            await self._block_ip(source_ip, duration=7200)  # 2 hours
            AUTO_ACTIONS.labels(action_type='prompt_injection_block').inc()
        elif event_type == 'model_abuse':
            await self._restrict_model_access(source_ip)
            AUTO_ACTIONS.labels(action_type='model_restriction').inc()

    async def _handle_auth_failure(self, event: Dict):
        """Handle authentication failures"""
        username = event.get('username')
        source_ip = event.get('source_ip')
        
        if not username or not source_ip:
            return
        
        # Increment failure counter
        failures = await self.redis.hincrby(
            f'security:auth_failures:{source_ip}',
            username,
            1
        )
        
        if failures >= 10:  # Auto-block after 10 failures
            await self._block_ip(source_ip, duration=1800)  # 30 minutes
            AUTO_ACTIONS.labels(action_type='auth_failure_block').inc()

    async def _block_ip(self, ip: str, duration: int):
        """Block an IP address"""
        await self.redis.setex(f'security:blocked:{ip}', duration, '1')
        security_audit_logger.log_security_event(
            'ip_blocked',
            {'ip': ip, 'duration': duration}
        )

    async def _restrict_model_access(self, ip: str):
        """Restrict AI model access"""
        await self.redis.sadd('security:restricted_model_access', ip)
        security_audit_logger.log_security_event(
            'model_access_restricted',
            {'ip': ip}
        )

    async def _update_security_rules(self):
        """Periodically update security rules based on recent events"""
        while self._running:
            try:
                # Analyze recent patterns
                patterns = await self._analyze_attack_patterns()
                
                # Update rules based on patterns
                await self._update_defense_rules(patterns)
                
                # Update AI security patterns
                await self._update_ai_security_patterns(patterns)
                
                await asyncio.sleep(300)  # Update every 5 minutes
            except Exception as e:
                logger.error(f"Error updating security rules: {str(e)}")
                await asyncio.sleep(5)

    async def _analyze_attack_patterns(self) -> Dict:
        """Analyze recent attack patterns"""
        recent_events = await self._get_recent_events()
        patterns = {
            'threats': {},
            'ips': {},
            'techniques': {}
        }
        
        for event in recent_events:
            if 'threat_type' in event:
                patterns['threats'][event['threat_type']] = \
                    patterns['threats'].get(event['threat_type'], 0) + 1
            if 'source_ip' in event:
                patterns['ips'][event['source_ip']] = \
                    patterns['ips'].get(event['source_ip'], 0) + 1
            if 'technique' in event:
                patterns['techniques'][event['technique']] = \
                    patterns['techniques'].get(event['technique'], 0) + 1
        
        return patterns

    async def _update_defense_rules(self, patterns: Dict):
        """Update defense rules based on attack patterns"""
        # Update IP blacklist
        for ip, count in patterns['ips'].items():
            if count >= 50:  # High activity threshold
                await self._block_ip(ip, duration=86400)  # 24 hours
        
        # Update threat patterns
        await self.redis.delete('security:threat_patterns')
        for threat, count in patterns['threats'].items():
            if count >= 10:
                await self.redis.sadd('security:threat_patterns', threat)
        
        AUTO_ACTIONS.labels(action_type='update_defense_rules').inc()

    async def _update_ai_security_patterns(self, patterns: Dict):
        """Update AI security patterns"""
        # Update prompt injection patterns
        injection_patterns = [
            t for t, c in patterns['techniques'].items()
            if 'injection' in t.lower() and c >= 5
        ]
        
        await self.redis.delete('security:ai:injection_patterns')
        for pattern in injection_patterns:
            await self.redis.sadd('security:ai:injection_patterns', pattern)
        
        AUTO_ACTIONS.labels(action_type='update_ai_patterns').inc()

    async def _cleanup_old_data(self):
        """Cleanup old security data"""
        while self._running:
            try:
                # Clean up old events
                cutoff = datetime.utcnow() - timedelta(
                    days=security_settings.METRICS_RETENTION_DAYS
                )
                
                # Clean up old blocks
                async for key in self.redis.scan_iter('security:blocked:*'):
                    if not await self.redis.exists(key):
                        await self.redis.delete(key)
                
                # Clean up old metrics
                await security_metrics.cleanup_old_metrics()
                
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Error in data cleanup: {str(e)}")
                await asyncio.sleep(5)

# Create global instance
security_orchestrator = SecurityOrchestrator()
