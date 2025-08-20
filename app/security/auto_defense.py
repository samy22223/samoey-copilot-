from typing import Dict, List, Any, Optional
import asyncio
import ipaddress
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel
import aioredis
from .monitor import SecurityMonitor
import json

logger = logging.getLogger(__name__)

class DefenseRule(BaseModel):
    name: str
    type: str
    conditions: Dict[str, Any]
    action: str
    priority: int
    enabled: bool = True

class AutoDefense:
    def __init__(self, security_monitor: SecurityMonitor):
        self.monitor = security_monitor
        self.active_defenses: Dict[str, List[str]] = defaultdict(list)
        self.defense_rules: List[DefenseRule] = self._initialize_rules()
        
        # Defense thresholds
        self.thresholds = {
            "rate_limit": 100,           # requests per minute
            "error_rate": 0.1,           # 10% error rate
            "suspicious_score": 0.7,      # suspicious activity score
            "block_score": 0.9           # auto-block score
        }

    def _initialize_rules(self) -> List[DefenseRule]:
        """Initialize default defense rules."""
        return [
            DefenseRule(
                name="rate_limit_defense",
                type="rate_limit",
                conditions={
                    "requests_per_minute": 100,
                    "burst_limit": 20
                },
                action="block_temporarily",
                priority=1
            ),
            DefenseRule(
                name="ai_security_defense",
                type="ai_security",
                conditions={
                    "threat_score": 0.8,
                    "suspicious_patterns": ["prompt_injection", "data_exfiltration"]
                },
                action="block_permanently",
                priority=2
            ),
            DefenseRule(
                name="anomaly_defense",
                type="anomaly",
                conditions={
                    "deviation_threshold": 3.0,
                    "min_samples": 10
                },
                action="increase_monitoring",
                priority=3
            ),
            DefenseRule(
                name="ddos_defense",
                type="ddos",
                conditions={
                    "request_rate": 1000,
                    "concurrent_connections": 50
                },
                action="enable_challenge",
                priority=1
            )
        ]

    async def analyze_threat(self, request: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze incoming request for threats and apply defenses."""
        threat_score = 0.0
        active_defenses = []
        client_ip = request.client.host

        # Rate limiting check
        rate_info = await self._check_rate_limit(client_ip)
        if rate_info["blocked"]:
            return {"blocked": True, "reason": "rate_limit", "expires": rate_info["expires"]}

        # AI security check
        if "prompt" in context:
            ai_security = await self.monitor.monitor_ai_request(context["prompt"], context)
            if not ai_security["safe"]:
                threat_score += 0.5
                active_defenses.append("ai_security")

        # Anomaly detection
        anomalies = await self._detect_anomalies(request, context)
        if anomalies:
            threat_score += len(anomalies) * 0.1
            active_defenses.append("anomaly_detection")

        # Apply defense rules
        for rule in self.defense_rules:
            if rule.enabled and await self._evaluate_rule(rule, request, context):
                defense_action = await self._apply_defense(rule, client_ip)
                active_defenses.append(defense_action)

        # Store defense state
        if active_defenses:
            self.active_defenses[client_ip] = active_defenses

        return {
            "threat_score": threat_score,
            "active_defenses": active_defenses,
            "blocked": threat_score > self.thresholds["block_score"],
            "monitoring_level": "high" if threat_score > self.thresholds["suspicious_score"] else "normal"
        }

    async def _check_rate_limit(self, client_ip: str) -> Dict[str, Any]:
        """Check and enforce rate limits."""
        key = f"defense:rate_limit:{client_ip}"
        count = await self.monitor.redis.incr(key)
        await self.monitor.redis.expire(key, 60)

        if count > self.thresholds["rate_limit"]:
            expires = datetime.now() + timedelta(minutes=5)
            await self._block_ip(client_ip, expires)
            return {"blocked": True, "expires": expires}

        return {"blocked": False, "count": count}

    async def _detect_anomalies(self, request: Any, context: Dict[str, Any]) -> List[str]:
        """Detect anomalous behavior patterns."""
        anomalies = []
        
        # Request pattern analysis
        if await self._is_anomalous_pattern(request):
            anomalies.append("request_pattern")
        
        # Payload analysis
        if await self._is_anomalous_payload(request):
            anomalies.append("payload")
        
        # Behavioral analysis
        if await self._is_anomalous_behavior(request.client.host):
            anomalies.append("behavior")
        
        return anomalies

    async def _evaluate_rule(self, rule: DefenseRule, request: Any, context: Dict[str, Any]) -> bool:
        """Evaluate if a defense rule should be triggered."""
        if rule.type == "rate_limit":
            return await self._evaluate_rate_limit_rule(rule, request.client.host)
        elif rule.type == "ai_security":
            return await self._evaluate_ai_security_rule(rule, context)
        elif rule.type == "anomaly":
            return await self._evaluate_anomaly_rule(rule, request, context)
        elif rule.type == "ddos":
            return await self._evaluate_ddos_rule(rule, request.client.host)
        return False

    async def _apply_defense(self, rule: DefenseRule, client_ip: str) -> str:
        """Apply appropriate defense mechanism."""
        if rule.action == "block_temporarily":
            expires = datetime.now() + timedelta(minutes=30)
            await self._block_ip(client_ip, expires)
            return "temporary_block"
            
        elif rule.action == "block_permanently":
            await self._block_ip(client_ip, None)
            return "permanent_block"
            
        elif rule.action == "increase_monitoring":
            await self._increase_monitoring(client_ip)
            return "increased_monitoring"
            
        elif rule.action == "enable_challenge":
            await self._enable_challenge(client_ip)
            return "challenge_enabled"
            
        return "no_action"

    async def _block_ip(self, ip: str, expires: Optional[datetime]):
        """Block an IP address."""
        key = f"defense:blocked:{ip}"
        value = json.dumps({
            "timestamp": datetime.now().isoformat(),
            "expires": expires.isoformat() if expires else None
        })
        
        if expires:
            await self.monitor.redis.set(key, value, expire=int((expires - datetime.now()).total_seconds()))
        else:
            await self.monitor.redis.set(key, value)

    async def _increase_monitoring(self, ip: str):
        """Increase monitoring level for an IP."""
        key = f"defense:monitoring:{ip}"
        await self.monitor.redis.set(key, "high", expire=3600)

    async def _enable_challenge(self, ip: str):
        """Enable challenge-response security for an IP."""
        key = f"defense:challenge:{ip}"
        await self.monitor.redis.set(key, "enabled", expire=1800)

    async def get_defense_status(self) -> Dict[str, Any]:
        """Get current defense system status."""
        return {
            "active_defenses": dict(self.active_defenses),
            "blocked_ips": len(await self._get_blocked_ips()),
            "rules": [rule.dict() for rule in self.defense_rules],
            "current_threat_level": await self._calculate_current_threat_level()
        }

    async def _calculate_current_threat_level(self) -> str:
        """Calculate current overall threat level."""
        blocked_count = len(await self._get_blocked_ips())
        active_defense_count = sum(len(defenses) for defenses in self.active_defenses.values())
        
        if blocked_count > 10 or active_defense_count > 20:
            return "CRITICAL"
        elif blocked_count > 5 or active_defense_count > 10:
            return "HIGH"
        elif blocked_count > 0 or active_defense_count > 5:
            return "MEDIUM"
        return "LOW"

    async def _get_blocked_ips(self) -> List[str]:
        """Get list of currently blocked IPs."""
        keys = await self.monitor.redis.keys("defense:blocked:*")
        return [key.split(":")[-1] for key in keys]
