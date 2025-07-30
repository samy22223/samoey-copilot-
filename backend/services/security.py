from typing import Dict, List
import redis
from datetime import datetime, timedelta
from ..core.config import settings

class SecurityService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_SECURITY_DB,
            decode_responses=True
        )

    async def get_metrics(self) -> Dict:
        """Get security metrics from Redis"""
        try:
            # Get metrics for the last hour
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            
            return {
                "request_count": int(self.redis_client.get("security:metrics:request_count") or 0),
                "error_count": int(self.redis_client.get("security:metrics:error_count") or 0),
                "blocked_requests": int(self.redis_client.get("security:metrics:blocked_requests") or 0),
                "ai_security_events": int(self.redis_client.get("security:metrics:ai_events") or 0),
                "suspicious_activities": int(self.redis_client.get("security:metrics:suspicious") or 0)
            }
        except Exception as e:
            print(f"Error getting security metrics: {str(e)}")
            return {
                "request_count": 0,
                "error_count": 0,
                "blocked_requests": 0,
                "ai_security_events": 0,
                "suspicious_activities": 0
            }

    async def get_ai_security_status(self) -> Dict:
        """Get AI security status and events"""
        try:
            # Get recent AI security events
            recent_events = self.redis_client.lrange("security:ai:recent_events", 0, 9)
            
            # Get severity distribution
            severity_dist = {
                "critical": int(self.redis_client.get("security:ai:severity:critical") or 0),
                "high": int(self.redis_client.get("security:ai:severity:high") or 0),
                "medium": int(self.redis_client.get("security:ai:severity:medium") or 0),
                "low": int(self.redis_client.get("security:ai:severity:low") or 0)
            }
            
            # Get threat distribution
            threat_dist = {
                "prompt_injection": int(self.redis_client.get("security:ai:threat:prompt_injection") or 0),
                "data_leakage": int(self.redis_client.get("security:ai:threat:data_leakage") or 0),
                "model_abuse": int(self.redis_client.get("security:ai:threat:model_abuse") or 0),
                "other": int(self.redis_client.get("security:ai:threat:other") or 0)
            }
            
            return {
                "total_events": sum(severity_dist.values()),
                "recent_events": len(recent_events),
                "severity_distribution": severity_dist,
                "threat_distribution": threat_dist,
                "recommendations": self.generate_recommendations(severity_dist, threat_dist)
            }
        except Exception as e:
            print(f"Error getting AI security status: {str(e)}")
            return {
                "total_events": 0,
                "recent_events": 0,
                "severity_distribution": {},
                "threat_distribution": {},
                "recommendations": []
            }

    def generate_recommendations(self, severity_dist: Dict, threat_dist: Dict) -> List[str]:
        """Generate security recommendations based on current status"""
        recommendations = []
        
        if severity_dist.get("critical", 0) > 0:
            recommendations.append("Immediate attention required: Critical security events detected")
            
        if threat_dist.get("prompt_injection", 0) > 0:
            recommendations.append("Review and strengthen prompt validation rules")
            
        if threat_dist.get("data_leakage", 0) > 0:
            recommendations.append("Audit data access patterns and strengthen data filters")
            
        return recommendations[:5]  # Return top 5 recommendations

    async def get_active_defenses(self) -> Dict[str, List[str]]:
        """Get currently active defense mechanisms"""
        try:
            active_defenses = {}
            defense_keys = self.redis_client.keys("security:defense:*")
            
            for key in defense_keys:
                ip = key.split(":")[-1]
                defenses = self.redis_client.smembers(key)
                if defenses:
                    active_defenses[ip] = list(defenses)
            
            return active_defenses
        except Exception as e:
            print(f"Error getting active defenses: {str(e)}")
            return {}

    async def get_blacklisted_ips_count(self) -> int:
        """Get count of blacklisted IPs"""
        try:
            return int(self.redis_client.scard("security:blacklist:ips") or 0)
        except Exception as e:
            print(f"Error getting blacklisted IPs count: {str(e)}")
            return 0

    async def calculate_threat_level(self, metrics: Dict, ai_security: Dict) -> str:
        """Calculate overall threat level based on metrics and AI security status"""
        try:
            # Weight different factors
            critical_events = ai_security["severity_distribution"].get("critical", 0)
            high_events = ai_security["severity_distribution"].get("high", 0)
            blocked_requests = metrics["blocked_requests"]
            suspicious_activities = metrics["suspicious_activities"]
            
            # Calculate threat score
            threat_score = (
                critical_events * 10 +
                high_events * 5 +
                blocked_requests * 2 +
                suspicious_activities
            )
            
            # Determine threat level
            if threat_score >= 50:
                return "CRITICAL"
            elif threat_score >= 30:
                return "HIGH"
            elif threat_score >= 10:
                return "MEDIUM"
            else:
                return "LOW"
        except Exception as e:
            print(f"Error calculating threat level: {str(e)}")
            return "UNKNOWN"
