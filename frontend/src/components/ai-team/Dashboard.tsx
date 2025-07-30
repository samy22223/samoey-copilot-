import React from 'react';
import { useState, useEffect } from 'react';
import axios from 'axios';

interface TeamMember {
  role: string;
  tasks: string[];
}

interface TeamStatus {
  [key: string]: string[];
}

export default function AITeamDashboard() {
  const [teamStatus, setTeamStatus] = useState<TeamStatus>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTeamStatus = async () => {
      try {
        const response = await axios.get('/api/team/status');
        setTeamStatus(response.data);
      } catch (error) {
        console.error('Error fetching team status:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTeamStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchTeamStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">AI Team Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.entries(teamStatus).map(([role, tasks]) => (
          <div key={role} className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">{role}</h2>
            <div className="space-y-2">
              {tasks.map((task, index) => (
                <div
                  key={index}
                  className="bg-gray-50 rounded p-3 flex items-center"
                >
                  <div className="h-2 w-2 rounded-full bg-green-500 mr-3"></div>
                  <span>{task}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
