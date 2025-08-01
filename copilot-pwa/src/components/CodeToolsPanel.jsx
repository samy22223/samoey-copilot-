import { useState } from 'react'
import { CODE_ASSISTANTS, AI_APP_BUILDERS, MODEL_RUNNERS } from '../config/codeTools'

export default function CodeToolsPanel() {
  const [activeTab, setActiveTab] = useState('assistants')

  return (
    <div className="code-tools-panel">
      <h2>Developer Tools Configuration</h2>
      
      <div className="tabs">
        <button 
          className={activeTab === 'assistants' ? 'active' : ''}
          onClick={() => setActiveTab('assistants')}
        >
          Code Assistants
        </button>
        <button
          className={activeTab === 'builders' ? 'active' : ''}
          onClick={() => setActiveTab('builders')}
        >
          App Builders
        </button>
        <button
          className={activeTab === 'runners' ? 'active' : ''}
          onClick={() => setActiveTab('runners')}
        >
          Model Runners
        </button>
      </div>

      <div className="tools-list">
        {activeTab === 'assistants' && Object.entries(CODE_ASSISTANTS).map(([name, tool]) => (
          <div key={name} className="tool-card">
            <h3>{name}</h3>
            <div className="tool-meta">
              <span>Type: {tool.type}</span>
              <span>Models: {tool.models.join(', ')}</span>
              <span>Offline: {tool.offline ? '✅' : '❌'}</span>
            </div>
            <a href={tool.link} target="_blank" rel="noopener noreferrer">
              View Tool
            </a>
          </div>
        ))}

        {activeTab === 'builders' && Object.entries(AI_APP_BUILDERS).map(([name, tool]) => (
          <div key={name} className="tool-card">
            <h3>{name}</h3>
            <div className="tool-meta">
              <span>Type: {tool.type}</span>
              <span>Features: {tool.features.join(', ')}</span>
            </div>
            <a href={tool.link} target="_blank" rel="noopener noreferrer">
              View Builder
            </a>
          </div>
        ))}

        {activeTab === 'runners' && Object.entries(MODEL_RUNNERS).map(([name, tool]) => (
          <div key={name} className="tool-card">
            <h3>{name}</h3>
            <div className="tool-meta">
              <span>Type: {tool.type}</span>
              <span>Models: {tool.supportedModels.join(', ')}</span>
            </div>
            <a href={tool.link} target="_blank" rel="noopener noreferrer">
              View Runner
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}
