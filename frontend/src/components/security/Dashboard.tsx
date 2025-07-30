import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface SecurityMetrics {
  request_count: number;
  error_count: number;
  blocked_requests: number;
  ai_security_events: number;
  suspicious_activities: number;
}

interface SecurityStatus {
  timestamp: string;
  metrics: SecurityMetrics;
  ai_security: {
    total_events: number;
    recent_events: number;
    severity_distribution: Record<string, number>;
    threat_distribution: Record<string, number>;
    recommendations: string[];
  };
  blacklisted_ips: number;
  threat_level: string;
  active_defenses: Record<string, string[]>;
}

export default function SecurityDashboard() {
  const [securityStatus, setSecurityStatus] = useState<SecurityStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSecurityStatus = async () => {
      try {
        const response = await axios.get('/api/security/status');
        setSecurityStatus(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch security status');
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSecurityStatus();
    const interval = setInterval(fetchSecurityStatus, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !securityStatus) {
    return (
      <div className="p-4 bg-red-100 text-red-700 rounded-lg">
        {error || 'No security data available'}
      </div>
    );
  }

  const getThreatLevelColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-500';
      case 'HIGH':
        return 'bg-orange-500';
      case 'MEDIUM':
        return 'bg-yellow-500';
      default:
        return 'bg-green-500';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Security Dashboard</h1>

      {/* Threat Level Indicator */}
      <div className="mb-8">
        <div className="flex items-center space-x-4">
          <div className="text-xl font-semibold">Current Threat Level:</div>
          <div className={`px-4 py-2 rounded-lg text-white font-bold ${getThreatLevelColor(securityStatus.threat_level)}`}>
            {securityStatus.threat_level}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Metrics Card */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Security Metrics</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Total Requests:</span>
              <span className="font-mono">{securityStatus.metrics.request_count}</span>
            </div>
            <div className="flex justify-between">
              <span>Blocked Requests:</span>
              <span className="font-mono text-red-500">{securityStatus.metrics.blocked_requests}</span>
            </div>
            <div className="flex justify-between">
              <span>AI Security Events:</span>
              <span className="font-mono text-orange-500">{securityStatus.metrics.ai_security_events}</span>
            </div>
            <div className="flex justify-between">
              <span>Suspicious Activities:</span>
              <span className="font-mono text-yellow-500">{securityStatus.metrics.suspicious_activities}</span>
            </div>
          </div>
        </div>

        {/* AI Security Card */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">AI Security</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium mb-2">Severity Distribution</h3>
              {Object.entries(securityStatus.ai_security.severity_distribution).map(([severity, count]) => (
                <div key={severity} className="flex justify-between items-center mb-1">
                  <span className="capitalize">{severity}:</span>
                  <span className="font-mono">{count}</span>
                </div>
              ))}
            </div>
            <div>
              <h3 className="font-medium mb-2">Recent Events</h3>
              <div className="font-mono">{securityStatus.ai_security.recent_events}</div>
            </div>
          </div>
        </div>

        {/* Recommendations Card */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Security Recommendations</h2>
          <ul className="list-disc list-inside space-y-2">
            {securityStatus.ai_security.recommendations.map((rec, index) => (
              <li key={index} className="text-sm">
                {rec}
              </li>
            ))}
          </ul>
        </div>

        {/* Active Defenses Card */}
        <div className="bg-white rounded-lg shadow-lg p-6 col-span-full">
          <h2 className="text-xl font-semibold mb-4">Active Defenses</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(securityStatus.active_defenses).map(([ip, defenses]) => (
              <div key={ip} className="border rounded-lg p-3">
                <div className="font-mono text-sm mb-2">{ip}</div>
                <div className="flex flex-wrap gap-2">
                  {defenses.map((defense, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                    >
                      {defense}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
