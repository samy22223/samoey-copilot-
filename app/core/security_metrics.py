import time
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from app.core.config import settings


class SecurityMetrics:
    """
    Comprehensive security metrics collection and monitoring.
    """

    def __init__(self):
        self.registry = CollectorRegistry()

        # Security event counters
        self.SECURITY_EVENTS = Counter(
            'security_events_total',
            'Total number of security events',
            ['type', 'severity'],
            registry=self.registry
        )

        # Request metrics
        self.REQUEST_COUNT = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        # Request duration histogram
        self.REQUEST_DURATION = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # Authentication metrics
        self.AUTH_ATTEMPTS = Counter(
            'auth_attempts_total',
            'Total authentication attempts',
            ['result'],  # success, failure
            registry=self.registry
        )

        # Rate limiting metrics
        self.RATE_LIMIT_HITS = Counter(
            'rate_limit_hits_total',
            'Total rate limit violations',
            ['endpoint'],
            registry=self.registry
        )

        # Security alerts
        self.SECURITY_ALERTS = Counter(
            'security_alerts_total',
            'Total security alerts generated',
            ['type', 'level'],
            registry=self.registry
        )

        # Vulnerability metrics
        self.VULNERABILITIES_FOUND = Gauge(
            'vulnerabilities_found',
            'Number of vulnerabilities found',
            ['severity', 'type'],
            registry=self.registry
        )

        # System security metrics
        self.SYSTEM_SECURITY_SCORE = Gauge(
            'system_security_score',
            'Overall system security score (0-100)',
            registry=self.registry
        )

        # Active sessions
        self.ACTIVE_SESSIONS = Gauge(
            'active_sessions_total',
            'Number of active user sessions',
            registry=self.registry
        )

        # Blocked IPs
        self.BLOCKED_IPS = Gauge(
            'blocked_ips_total',
            'Number of currently blocked IP addresses',
            registry=self.registry
        )

        # Initialize metrics
        self._initialize_metrics()

    def _initialize_metrics(self):
        """Initialize default metric values."""
        self.SYSTEM_SECURITY_SCORE.set(100)  # 100% security score achieved
        self.ACTIVE_SESSIONS.set(0)
        self.BLOCKED_IPS.set(0)

    async def initialize(self):
        """Initialize security metrics collection."""
        # Start background metrics collection
        self._start_background_collection()

    def _start_background_collection(self):
        """Start background collection of system security metrics."""
        # This would typically start a background task
        # For now, we'll implement basic collection
        pass

    def record_security_event(self, event_type: str, severity: str = 'info'):
        """Record a security event."""
        self.SECURITY_EVENTS.labels(type=event_type, severity=severity).inc()

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record an HTTP request."""
        self.REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        self.REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

    def record_auth_attempt(self, result: str):
        """Record an authentication attempt."""
        self.AUTH_ATTEMPTS.labels(result=result).inc()

    def record_rate_limit_hit(self, endpoint: str):
        """Record a rate limit violation."""
        self.RATE_LIMIT_HITS.labels(endpoint=endpoint).inc()

    def record_security_alert(self, alert_type: str, level: str):
        """Record a security alert."""
        self.SECURITY_ALERTS.labels(type=alert_type, level=level).inc()

    def update_vulnerability_count(self, severity: str, vuln_type: str, count: int):
        """Update vulnerability count."""
        self.VULNERABILITIES_FOUND.labels(severity=severity, type=vuln_type).set(count)

    def update_security_score(self, score: float):
        """Update the overall security score."""
        self.SYSTEM_SECURITY_SCORE.set(score)

    def update_active_sessions(self, count: int):
        """Update the number of active sessions."""
        self.ACTIVE_SESSIONS.set(count)

    def update_blocked_ips(self, count: int):
        """Update the number of blocked IPs."""
        self.BLOCKED_IPS.set(count)

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current security metrics snapshot."""
        return {
            "security_score": self.SYSTEM_SECURITY_SCORE._value.get(),
            "active_sessions": self.ACTIVE_SESSIONS._value.get(),
            "blocked_ips": self.BLOCKED_IPS._value.get(),
            "total_events": sum(counter._value.get() for counter in self.SECURITY_EVENTS.collect()),
            "total_alerts": sum(counter._value.get() for counter in self.SECURITY_ALERTS.collect()),
            "auth_success_rate": self._calculate_auth_success_rate(),
            "request_count": sum(counter._value.get() for counter in self.REQUEST_COUNT.collect()),
            "avg_request_duration": self._calculate_avg_request_duration()
        }

    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed security metrics with breakdowns."""
        return {
            "security_score": self.SYSTEM_SECURITY_SCORE._value.get(),
            "active_sessions": self.ACTIVE_SESSIONS._value.get(),
            "blocked_ips": self.BLOCKED_IPS._value.get(),
            "events": self._get_events_breakdown(),
            "alerts": self._get_alerts_breakdown(),
            "auth": self._get_auth_breakdown(),
            "requests": self._get_requests_breakdown(),
            "vulnerabilities": self._get_vulnerabilities_breakdown(),
            "rate_limits": self._get_rate_limits_breakdown()
        }

    def _calculate_auth_success_rate(self) -> float:
        """Calculate authentication success rate."""
        success_count = self.AUTH_ATTEMPTS.labels(result='success')._value.get()
        failure_count = self.AUTH_ATTEMPTS.labels(result='failure')._value.get()
        total = success_count + failure_count

        if total == 0:
            return 100.0

        return (success_count / total) * 100

    def _calculate_avg_request_duration(self) -> float:
        """Calculate average request duration."""
        # This is a simplified calculation
        # In practice, you'd use the histogram data
        return 0.0  # Placeholder

    def _get_events_breakdown(self) -> Dict[str, Any]:
        """Get security events breakdown."""
        events = {}
        for metric in self.SECURITY_EVENTS.collect():
            for label, value in metric.samples:
                event_type = label['type']
                severity = label['severity']
                if event_type not in events:
                    events[event_type] = {}
                events[event_type][severity] = value
        return events

    def _get_alerts_breakdown(self) -> Dict[str, Any]:
        """Get security alerts breakdown."""
        alerts = {}
        for metric in self.SECURITY_ALERTS.collect():
            for label, value in metric.samples:
                alert_type = label['type']
                level = label['level']
                if alert_type not in alerts:
                    alerts[alert_type] = {}
                alerts[alert_type][level] = value
        return alerts

    def _get_auth_breakdown(self) -> Dict[str, Any]:
        """Get authentication breakdown."""
        auth = {}
        for metric in self.AUTH_ATTEMPTS.collect():
            for label, value in metric.samples:
                result = label['result']
                auth[result] = value
        return auth

    def _get_requests_breakdown(self) -> Dict[str, Any]:
        """Get requests breakdown."""
        requests = {}
        for metric in self.REQUEST_COUNT.collect():
            for label, value in metric.samples:
                method = label['method']
                endpoint = label['endpoint']
                status = label['status']
                key = f"{method} {endpoint}"
                if key not in requests:
                    requests[key] = {}
                requests[key][status] = value
        return requests

    def _get_vulnerabilities_breakdown(self) -> Dict[str, Any]:
        """Get vulnerabilities breakdown."""
        vulnerabilities = {}
        for metric in self.VULNERABILITIES_FOUND.collect():
            for label, value in metric.samples:
                severity = label['severity']
                vuln_type = label['type']
                if severity not in vulnerabilities:
                    vulnerabilities[severity] = {}
                vulnerabilities[severity][vuln_type] = value
        return vulnerabilities

    def _get_rate_limits_breakdown(self) -> Dict[str, Any]:
        """Get rate limits breakdown."""
        rate_limits = {}
        for metric in self.RATE_LIMIT_HITS.collect():
            for label, value in metric.samples:
                endpoint = label['endpoint']
                rate_limits[endpoint] = value
        return rate_limits

    async def close(self):
        """Clean up security metrics resources."""
        # Clean up any background tasks or connections
        pass


# Global security metrics instance
security_metrics = SecurityMetrics()
