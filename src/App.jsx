import { useState, useEffect, useContext } from 'react'
import { PinnacleProvider, PinnacleContext } from './context/PinnacleContext.jsx'
import './App.css'
import './styles/AIConfigPanel.css'
import './styles/CodeToolsPanel.css'
import './styles/CodeAssistant.css'
import ErrorBoundary from './components/ErrorBoundary'
import CodeAssistant from './components/CodeAssistant'
import LocalAgentManager from './components/LocalAgentManager'

function PinnacleApp() {
  const [activeTab, setActiveTab] = useState('chat')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [agents, setAgents] = useState([])
  const [workflows, setWorkflows] = useState([])
  const { loading, error, services, executePrompt } = useContext(PinnacleContext)
  
  if (loading) {
    return (
      <div className="loading-overlay">
        <h2>Initializing Pinnacle Copilot</h2>
        <p>Loading AI services and platform connections...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-overlay">
        <h2>Startup Error</h2>
        <p>{error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="retry-button"
        >
          Retry Initialization
        </button>
      </div>
    )
  }

  // ... rest of your existing component code ...

  return (
    <ErrorBoundary>
      <div className="app">
        {/* ... existing header and content ... */}
      </div>
    </ErrorBoundary>
  )
}

export default function App() {
  return (
    <PinnacleProvider>
      <PinnacleApp />
    </PinnacleProvider>
  )
}
