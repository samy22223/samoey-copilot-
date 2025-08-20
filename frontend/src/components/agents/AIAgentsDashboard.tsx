'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Activity, Bot, CheckCircle, Clock, AlertCircle, Play } from 'lucide-react'

interface Agent {
  id: number
  name: string
  status: 'active' | 'idle' | 'processing'
  lastActivity: Date
  logs: string[]
}

interface Workflow {
  id: number
  name: string
  status: 'running' | 'pending' | 'completed'
  steps: number
  progress: number
  logs: string[]
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'bg-green-500'
    case 'idle': return 'bg-gray-500'
    case 'processing': return 'bg-blue-500'
    case 'running': return 'bg-blue-500'
    case 'completed': return 'bg-green-500'
    case 'pending': return 'bg-yellow-500'
    default: return 'bg-gray-500'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'active':
    case 'completed':
      return <CheckCircle className="h-4 w-4" />
    case 'processing':
    case 'running':
      return <Play className="h-4 w-4" />
    case 'pending':
      return <Clock className="h-4 w-4" />
    default:
      return <AlertCircle className="h-4 w-4" />
  }
}

export default function AIAgentsDashboard() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [workflows, setWorkflows] = useState<Workflow[]>([])

  useEffect(() => {
    // Mock data for demo
    setAgents([
      { 
        id: 1, 
        name: 'Code Analyzer', 
        status: 'active', 
        lastActivity: new Date(), 
        logs: ['Analyzed file.js', 'Found 3 issues', 'Generated optimization suggestions']
      },
      { 
        id: 2, 
        name: 'Document Processor', 
        status: 'idle', 
        lastActivity: new Date(Date.now()-300000), 
        logs: ['Processed report.pdf', 'Extracted key insights']
      },
      { 
        id: 3, 
        name: 'Task Automator', 
        status: 'processing', 
        lastActivity: new Date(), 
        logs: ['Executing workflow #123', 'Completed step 2/5']
      },
      {
        id: 4,
        name: 'Security Scanner',
        status: 'active',
        lastActivity: new Date(),
        logs: ['Scanning dependencies', 'Checking for vulnerabilities']
      }
    ])
    
    setWorkflows([
      { 
        id: 1, 
        name: 'Code Review', 
        status: 'running', 
        steps: 5, 
        progress: 60, 
        logs: ['Cloned repo', 'Installed dependencies', 'Running tests', 'Analyzing code quality']
      },
      { 
        id: 2, 
        name: 'Data Processing', 
        status: 'pending', 
        steps: 3, 
        progress: 0, 
        logs: []
      },
      { 
        id: 3, 
        name: 'Report Generation', 
        status: 'completed', 
        steps: 4, 
        progress: 100, 
        logs: ['Generated PDF', 'Sent notification', 'Archived results']
      },
      {
        id: 4,
        name: 'Deployment Pipeline',
        status: 'running',
        steps: 7,
        progress: 85,
        logs: ['Built application', 'Ran tests', 'Created Docker image', 'Deployed to staging']
      }
    ])
  }, [])

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Agents Dashboard</h1>
          <p className="text-muted-foreground">
            Monitor and manage your AI-powered development assistants
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-green-500" />
          <span className="text-sm font-medium">System Active</span>
        </div>
      </div>

      <Tabs defaultValue="agents" className="space-y-4">
        <TabsList>
          <TabsTrigger value="agents" className="flex items-center gap-2">
            <Bot className="h-4 w-4" />
            AI Agents ({agents.length})
          </TabsTrigger>
          <TabsTrigger value="workflows" className="flex items-center gap-2">
            <Play className="h-4 w-4" />
            Workflows ({workflows.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {agents.map(agent => (
              <Card key={agent.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                    <div className="flex items-center gap-2">
                      <div className={`h-2 w-2 rounded-full ${getStatusColor(agent.status)}`} />
                      {getStatusIcon(agent.status)}
                    </div>
                  </div>
                  <CardDescription className="flex items-center justify-between">
                    <span>Status: {agent.status}</span>
                    <Badge variant="outline">
                      {agent.logs.length} activities
                    </Badge>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <h4 className="text-sm font-medium mb-2">Recent Activity:</h4>
                      <div className="space-y-1">
                        {agent.logs.slice(0, 3).map((log, i) => (
                          <div key={i} className="text-xs text-muted-foreground bg-muted p-2 rounded">
                            {log}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Last activity: {agent.lastActivity.toLocaleTimeString()}
                    </div>
                    <Button size="sm" className="w-full">
                      View Details
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="workflows" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {workflows.map(workflow => (
              <Card key={workflow.id}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{workflow.name}</CardTitle>
                    <div className="flex items-center gap-2">
                      <div className={`h-2 w-2 rounded-full ${getStatusColor(workflow.status)}`} />
                      {getStatusIcon(workflow.status)}
                    </div>
                  </div>
                  <CardDescription className="flex items-center justify-between">
                    <span>Status: {workflow.status}</span>
                    <Badge variant="outline">
                      {workflow.steps} steps
                    </Badge>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Progress</span>
                        <span>{workflow.progress}%</span>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div 
                          className="bg-primary h-2 rounded-full transition-all duration-300"
                          style={{ width: `${workflow.progress}%` }}
                        />
                      </div>
                    </div>
                    
                    {workflow.logs.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium mb-2">Execution Logs:</h4>
                        <div className="space-y-1">
                          {workflow.logs.slice(0, 3).map((log, i) => (
                            <div key={i} className="text-xs text-muted-foreground bg-muted p-2 rounded">
                              {log}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="flex gap-2">
                      <Button size="sm" className="flex-1">
                        {workflow.status === 'running' ? 'Stop' : 'Start'}
                      </Button>
                      <Button size="sm" variant="outline" className="flex-1">
                        View Logs
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
