import { useState, useEffect } from 'react'
import './App.css'
import './styles/AIConfigPanel.css'
import './styles/CodeToolsPanel.css'
import CodeToolsPanel from './components/CodeToolsPanel'

export default function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [agents, setAgents] = useState([])
  const [workflows, setWorkflows] = useState([])

  // Mock data for demo
  useEffect(() => {
    setAgents([
      { 
        id: 1, 
        name: 'Code Analyzer', 
        status: 'active', 
        lastActivity: new Date(), 
        logs: ['Analyzed file.js', 'Found 3 issues']
      },
      { 
        id: 2, 
        name: 'Document Processor', 
        status: 'idle', 
        lastActivity: new Date(Date.now()-300000), 
        logs: ['Processed report.pdf']
      },
      { 
        id: 3, 
        name: 'Task Automator', 
        status: 'processing', 
        lastActivity: new Date(), 
        logs: ['Executing workflow #123']
      }
    ])
    
    setWorkflows([
      { 
        id: 1, 
        name: 'Code Review', 
        status: 'running', 
        steps: 5, 
        progress: 60, 
        logs: ['Cloned repo', 'Installed dependencies', 'Running tests']
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
        logs: ['Generated PDF', 'Sent notification']
      }
    ])
  }, [])

  const handleSend = () => {
    if (input.trim()) {
      setMessages([...messages, { text: input, sender: 'user' }])
      setInput('')
    }
  }

  const getStatusColor = (status) => {
    switch(status) {
      case 'active': return 'status-active'
      case 'idle': return 'status-idle'
      case 'processing': return 'status-processing'
      case 'running': return 'status-running' 
      case 'completed': return 'status-completed'
      default: return 'status-idle'
    }
  }

  return (
    <ErrorBoundary>
      <div className="app">
      <header className="header">
        <h1>Pinnacle Copilot</h1>
        <div className="tabs">
          <button 
            className={activeTab === 'chat' ? 'active' : ''}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
          <button 
            className={activeTab === 'agents' ? 'active' : ''}
            onClick={() => setActiveTab('agents')}
          >
            AI Agents ({agents.length})
          </button>
          <button 
            className={activeTab === 'workflows' ? 'active' : ''}
            onClick={() => setActiveTab('workflows')}
          >
            Workflows ({workflows.length})
          </button>
          <button 
            className={activeTab === 'tools' ? 'active' : ''}
            onClick={() => setActiveTab('tools')}
          >
            Developer Tools
          </button>
        </div>
      </header>

      <div className="content-area">
        {activeTab === 'chat' && (
          <div className="tab-content">
            <div className="chat-container">
              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.sender}`}>
                  {msg.text}
                </div>
              ))}
            </div>
            <div className="input-area">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask something..." 
              />
              <button onClick={handleSend}>Send</button>
            </div>
          </div>
        )}

        {activeTab === 'agents' && (
          <div className="tab-content">
            <div className="agent-grid">
              {agents.map(agent => (
                <div key={agent.id} className={`agent-card ${getStatusColor(agent.status)}`}>
                  <h3>{agent.name}</h3>
                  <div className="agent-status">Status: {agent.status}</div>
                  <div className="agent-logs">
                    <h4>Recent Activity:</h4>
                    <ul>
                      {agent.logs.map((log, i) => (
                        <li key={i}>{log}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'workflows' && (
          <div className="tab-content">
            <div className="workflow-list">
              {workflows.map(workflow => (
                <div key={workflow.id} className={`workflow-item ${getStatusColor(workflow.status)}`}>
                  <h3>{workflow.name}</h3>
                  <div className="workflow-progress">
                    <div 
                      className="progress-bar" 
                      style={{ width: `${workflow.progress}%` }}
                    ></div>
                  </div>
                  <div className="workflow-steps">
                    <span>Steps: {workflow.steps}</span>
                    <span>Progress: {workflow.progress}%</span>
                  </div>
                  <div className="workflow-logs">
                    <h4>Execution Logs:</h4>
                    <ul>
                      {workflow.logs.slice(0, 3).map((log, i) => (
                        <li key={i}>{log}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}
