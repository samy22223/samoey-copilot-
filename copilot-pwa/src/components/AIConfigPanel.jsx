import { useState } from 'react'
import { LLM_OPTIONS, EMBEDDING_MODELS, VISION_MODELS, AUDIO_MODELS } from '../config/aiModels'

export default function AIConfigPanel({ onConfigChange }) {
  const [config, setConfig] = useState({
    llm: 'LLaMA 3',
    embedding: 'Instructor XL',
    vision: 'CLIP',
    audio: 'Whisper'
  })

  const handleChange = (key, value) => {
    const newConfig = {...config, [key]: value}
    setConfig(newConfig)
    onConfigChange(newConfig)
  }

  return (
    <div className="ai-config-panel">
      <h2>AI Configuration</h2>
      
      <div className="config-section">
        <label>
          <h3>Language Model</h3>
          <select
            value={config.llm}
            onChange={(e) => handleChange('llm', e.target.value)}
          >
            {Object.keys(LLM_OPTIONS).map(model => (
              <option key={model} value={model}>
                {model} ({LLM_OPTIONS[model].params})
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="config-section">
        <label>
          <h3>Embedding Model</h3>
          <select
            value={config.embedding}
            onChange={(e) => handleChange('embedding', e.target.value)}  
          >
            {Object.keys(EMBEDDING_MODELS).map(model => (
              <option key={model} value={model}>
                {model} ({EMBEDDING_MODELS[model].dims}D)
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="config-section">
        <label>
          <h3>Vision Model</h3>
          <select
            value={config.vision}
            onChange={(e) => handleChange('vision', e.target.value)}
          >
            {Object.keys(VISION_MODELS).map(model => (
              <option key={model} value={model}>
                {model} - {VISION_MODELS[model].tasks.join(', ')}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="config-section">
        <label>
          <h3>Audio Model</h3>
          <select
            value={config.audio}
            onChange={(e) => handleChange('audio', e.target.value)}
          >
            {Object.keys(AUDIO_MODELS).map(model => (
              <option key={model} value={model}>
                {model} - {AUDIO_MODELS[model].tasks.join(', ')}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  )
}
