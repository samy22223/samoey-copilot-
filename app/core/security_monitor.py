import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from app.core.config import settings
from app.core.security_metrics import security_metrics


class SecurityMonitor:
    """
    Real-time security monitoring and threat detection.
    """

    def __init__(self):
        self.active_threats = {}
        self.security_scans = {}
        self.incidents = {}
        self.alerts = deque(maxlen=1000)
        self.blocked_ips = set()
        self.suspicious_activities = defaultdict(list)
        self.vulnerability_database = {}
        self.threat_intelligence_feeds = {}
        self.last_scan_time = None

        # Detection thresholds
        self.failed_login_threshold = 5
        self.rate_limit_threshold = 100
        self.suspicious_ip_threshold = 10

        # Initialize monitoring
        self._initialize_monitoring()

    def _initialize_monitoring(self):
        """Initialize security monitoring components."""
        # Load threat intelligence
        self._load_threat_intelligence()

        # Initialize vulnerability database
        self._initialize_vulnerability_database()

        # Start background monitoring tasks
        self._start_background_tasks()

    def _load_threat_intelligence(self):
        """Load threat intelligence feeds."""
        # This would typically load from external sources
        # For now, we'll initialize with some basic data
        self.threat_intelligence_feeds = {
            "malicious_ips": set(),
            "suspicious_domains": set(),
            "known_vulnerabilities": [],
            "threat_signatures": {}
        }

    def _initialize_vulnerability_database(self):
        """Initialize vulnerability database."""
        # This would typically load from CVE databases
        # For now, we'll initialize with basic structure
        self.vulnerability_database = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }

    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        # This would typically start asyncio tasks
        # For now, we'll implement basic scheduling
        pass

    def detect_suspicious_activity(self, activity_type: str, details: Dict[str, Any]):
        """
        Detect and log suspicious activities.
        """
        timestamp = datetime.now()

        activity = {
            "timestamp": timestamp.isoformat(),
            "type": activity_type,
            "details": details,
            "severity": self._calculate_activity_severity(activity_type, details)
        }

        # Log suspicious activity
        self.suspicious_activities[activity_type].append(activity)

        # Check if this activity should trigger an alert
        if self._should_trigger_alert(activity):
            self._create_security_alert(
                alert_type="suspicious_activity",
                level=activity["severity"],
                message=f"Suspicious {activity_type} detected",
                details=activity
            )

        # Update metrics
        security_metrics.record_security_event(
            event_type=f"suspicious_{activity_type}",
            severity=activity["severity"]
        )

    def _calculate_activity_severity(self, activity_type: str, details: Dict[str, Any]) -> str:
        """Calculate severity of suspicious activity."""
        # Simple severity calculation based on activity type
        high_severity_activities = [
            "brute_force", "injection_attempt", "privilege_escalation"
        ]

        medium_severity_activities = [
            "failed_login", "unauthorized_access", "suspicious_request"
        ]

        if activity_type in high_severity_activities:
            return "high"
        elif activity_type in medium_severity_activities:
            return "medium"
        else:
            return "low"

    def _should_trigger_alert(self, activity: Dict[str, Any]) -> bool:
        """Determine if an activity should trigger a security alert."""
        # Check if activity severity is high enough
        if activity["severity"] in ["high", "critical"]:
            return True

        # Check for repeated suspicious activities
        activity_type = activity["type"]
        recent_activities = [
            a for a in self.suspicious_activities[activity_type]
            if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=1)
        ]

        if len(recent_activities) > self.suspicious_ip_threshold:
            return True

        return False

    def _create_security_alert(self, alert_type: str, level: str, message: str, details: Dict[str, Any]):
        """Create a security alert."""
        alert_id = f"alert_{int(time.time())}_{alert_type}"

        alert = {
            "id": alert_id,
            "type": alert_type,
            "level": level,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "status": "active",
            "resolved": False
        }

        self.alerts.append(alert)

        # Update metrics
        security_metrics.record_security_alert(alert_type=alert_type, level=level)

        # Log the alert
        print(f"SECURITY ALERT [{level.upper()}]: {message}")

    def monitor_failed_logins(self, ip_address: str, username: str):
        """
        Monitor failed login attempts.
        """
        key = f"{ip_address}:{username}"

        # Track failed attempts
        if not hasattr(self, '_failed_login_attempts'):
            self._failed_login_attempts = defaultdict(int)

        self._failed_login_attempts[key] += 1

        # Check if threshold exceeded
        if self._failed_login_attempts[key] >= self.failed_login_threshold:
            self.detect_suspicious_activity(
                activity_type="failed_login",
                details={
                    "ip_address": ip_address,
                    "username": username,
                    "attempts": self._failed_login_attempts[key]
                }
            )

            # Block IP if necessary
            self.block_ip_address(ip_address, reason="too_many_failed_logins")

    def block_ip_address(self, ip_address: str, reason: str, duration: int = 3600):
        """
        Block an IP address for security reasons.
        """
        block_until = datetime.now() + timedelta(seconds=duration)

        self.blocked_ips.add(ip_address)

        # Log the block
        self.detect_suspicious_activity(
            activity_type="ip_blocked",
            details={
                "ip_address": ip_address,
                "reason": reason,
                "duration": duration,
                "block_until": block_until.isoformat()
            }
        )

        # Update metrics
        security_metrics.update_blocked_ips(len(self.blocked_ips))

        print(f"IP BLOCKED: {ip_address} - {reason} (duration: {duration}s)")

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is currently blocked."""
        return ip_address in self.blocked_ips

    def initiate_scan(self) -> str:
        """Initiate a comprehensive security scan."""
        scan_id = f"scan_{int(time.time())}"

        self.security_scans[scan_id] = {
            "id": scan_id,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "results": {},
            "progress": 0
        }

        # Start the scan (in a real implementation, this would be async)
        self._run_security_scan(scan_id)

        return scan_id

    def _run_security_scan(self, scan_id: str):
        """Run a comprehensive security scan."""
        scan = self.security_scans[scan_id]

        try:
            # Scan for vulnerabilities
            scan["results"]["vulnerabilities"] = self._scan_vulnerabilities()
            scan["progress"] = 25

            # Scan for security misconfigurations
            scan["results"]["misconfigurations"] = self._scan_misconfigurations()
            scan["progress"] = 50

            # Scan for active threats
            scan["results"]["active_threats"] = self._scan_active_threats()
            scan["progress"] = 75

            # Generate security score
            scan["results"]["security_score"] = self._calculate_security_score(scan["results"])
            scan["progress"] = 100

            # Update scan status
            scan["status"] = "completed"
            scan["end_time"] = datetime.now().isoformat()

            self.last_scan_time = scan["end_time"]

            # Update metrics
            security_metrics.update_security_score(scan["results"]["security_score"])

        except Exception as e:
            scan["status"] = "failed"
            scan["end_time"] = datetime.now().isoformat()
            scan["error"] = str(e)

    def _scan_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scan for known vulnerabilities."""
        # This would typically check against CVE databases
        # For now, return simulated results
        return [
            {
                "id": "CVE-2023-1234",
                "severity": "high",
                "description": "Simulated vulnerability",
                "affected_component": "web_server"
            }
        ]

    def _scan_misconfigurations(self) -> List[Dict[str, Any]]:
        """Scan for security misconfigurations."""
        # This would typically check system configurations
        # For now, return simulated results
        return [
            {
                "type": "weak_password_policy",
                "severity": "medium",
                "description": "Password policy could be stronger"
            }
        ]

    def _scan_active_threats(self) -> List[Dict[str, Any]]:
        """Scan for active threats and intrusions."""
        # This would typically check for active intrusions
        # For now, return simulated results
        return [
            {
                "type": "suspicious_login_pattern",
                "severity": "low",
                "description": "Unusual login pattern detected"
            }
        ]

    def _calculate_security_score(self, scan_results: Dict[str, Any]) -> float:
        """Calculate overall security score based on scan results."""
        base_score = 100.0

        # Deduct points for vulnerabilities
        vuln_deductions = {
            "critical": 20,
            "high": 10,
            "medium": 5,
            "low": 2
        }

        for vuln in scan_results.get("vulnerabilities", []):
            severity = vuln.get("severity", "low")
            base_score -= vuln_deductions.get(severity, 2)

        # Deduct points for misconfigurations
        for misconfig in scan_results.get("misconfigurations", []):
            severity = misconfig.get("severity", "low")
            base_score -= vuln_deductions.get(severity, 2)

        # Deduct points for active threats
        for threat in scan_results.get("active_threats", []):
            severity = threat.get("severity", "low")
            base_score -= vuln_deductions.get(severity, 2)

        # Ensure score doesn't go below 0
        return max(0.0, base_score)

    def get_scan_results(self
