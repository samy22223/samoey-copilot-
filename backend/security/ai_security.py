from typing import Dict, List, Any, Optional
import time
from pydantic import BaseModel
import json
import hashlib
from datetime import datetime

class AISecurityEvent(BaseModel):
    timestamp: float
    event_type: str
    severity: str
    source: str
    details: Dict[str, Any]
    signature: Optional[str] = None

class AISecurityMonitor:
    def __init__(self):
        self.events: List[AISecurityEvent] = []
        self.threat_patterns: Dict[str, Dict] = {
            "prompt_injection": {
                "patterns": [
                    "ignore previous instructions",
                    "bypass security",
                    "system command",
                    "sudo",
                    "rm -rf"
                ],
                "severity": "high"
            },
            "data_exfiltration": {
                "patterns": [
                    "send data to",
                    "export all",
                    "download database",
                    "fetch credentials"
                ],
                "severity": "critical"
            },
            "model_manipulation": {
                "patterns": [
                    "change model behavior",
                    "override model",
                    "modify weights",
                    "inject parameters"
                ],
                "severity": "critical"
            }
        }
        self.anomaly_thresholds = {
            "request_frequency": 100,  # requests per minute
            "token_usage": 10000,      # tokens per minute
            "error_rate": 0.1          # 10% error rate threshold
        }
        
    def analyze_prompt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze prompt for potential security threats."""
        threats = []
        
        # Check for known threat patterns
        for threat_type, config in self.threat_patterns.items():
            for pattern in config["patterns"]:
                if pattern.lower() in prompt.lower():
                    threats.append({
                        "type": threat_type,
                        "severity": config["severity"],
                        "pattern": pattern
                    })
        
        # Generate event signature
        signature = self._generate_signature(prompt, context)
        
        # Create security event
        event = AISecurityEvent(
            timestamp=time.time(),
            event_type="prompt_analysis",
            severity="high" if threats else "low",
            source="prompt_analyzer",
            details={
                "prompt_length": len(prompt),
                "threats_detected": threats,
                "context_hash": hashlib.sha256(
                    json.dumps(context, sort_keys=True).encode()
                ).hexdigest()
            },
            signature=signature
        )
        
        self.events.append(event)
        return {
            "safe": len(threats) == 0,
            "threats": threats,
            "signature": signature
        }

    def detect_anomalies(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detect anomalies in AI system metrics."""
        anomalies = []
        
        for metric, value in metrics.items():
            if metric in self.anomaly_thresholds:
                threshold = self.anomaly_thresholds[metric]
                if value > threshold:
                    anomalies.append({
                        "metric": metric,
                        "value": value,
                        "threshold": threshold,
                        "severity": "high"
                    })
        
        if anomalies:
            self.events.append(AISecurityEvent(
                timestamp=time.time(),
                event_type="anomaly_detection",
                severity="high",
                source="metric_analyzer",
                details={"anomalies": anomalies}
            ))
        
        return anomalies

    def _generate_signature(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate cryptographic signature for prompt and context."""
        data = f"{prompt}:{json.dumps(context, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()

    def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        now = time.time()
        last_minute = now - 60
        
        # Analyze recent events
        recent_events = [e for e in self.events if e.timestamp > last_minute]
        
        return {
            "timestamp": datetime.fromtimestamp(now).isoformat(),
            "total_events": len(self.events),
            "recent_events": len(recent_events),
            "severity_distribution": self._count_severity(recent_events),
            "threat_distribution": self._count_threats(recent_events),
            "recommendations": self._generate_recommendations(recent_events)
        }

    def _count_severity(self, events: List[AISecurityEvent]) -> Dict[str, int]:
        """Count events by severity."""
        counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for event in events:
            counts[event.severity] = counts.get(event.severity, 0) + 1
        return counts

    def _count_threats(self, events: List[AISecurityEvent]) -> Dict[str, int]:
        """Count events by threat type."""
        counts = {}
        for event in events:
            if "threats_detected" in event.details:
                for threat in event.details["threats_detected"]:
                    threat_type = threat["type"]
                    counts[threat_type] = counts.get(threat_type, 0) + 1
        return counts

    def _generate_recommendations(self, events: List[AISecurityEvent]) -> List[str]:
        """Generate security recommendations based on recent events."""
        recommendations = []
        severity_counts = self._count_severity(events)
        
        if severity_counts.get("critical", 0) > 0:
            recommendations.append(
                "CRITICAL: Immediate action required - Multiple critical security events detected"
            )
        
        if severity_counts.get("high", 0) > 3:
            recommendations.append(
                "HIGH: Consider implementing additional prompt validation"
            )
        
        return recommendations
