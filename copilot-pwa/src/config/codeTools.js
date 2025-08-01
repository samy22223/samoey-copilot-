export const CODE_ASSISTANTS = {
  'CodeGeeX': {
    type: 'VS Code Extension',
    models: ['Gemini', 'GPT', 'LLaMA'],
    offline: false,
    link: 'https://codegeex.cn/'
  },
  'Tabby': {
    type: 'Self-hosted',
    models: ['StarCoder', 'CodeLLaMA', 'WizardCoder'],
    offline: true,
    link: 'https://github.com/TabbyML/tabby'
  },
  'Continue': {
    type: 'VS Code Plugin', 
    models: ['GPT-J', 'Mistral', 'Claude'],
    offline: true,
    link: 'https://continue.dev/'
  },
  'OpenDevin': {
    type: 'AI Agent',
    models: ['LLaMA', 'Mistral', 'GPT-4'],
    offline: true,
    link: 'https://github.com/OpenDevin/OpenDevin'
  }
}

export const AI_APP_BUILDERS = {
  'Flowise': {
    type: 'No-code UI',
    features: ['LLM Agents', 'Workflows'],
    link: 'https://github.com/FlowiseAI/Flowise'
  },
  'Langflow': {
    type: 'LangChain UI',
    features: ['Drag & Drop', 'Multi-Model'],
    link: 'https://github.com/langflow-ai/langflow'
  }
}

export const MODEL_RUNNERS = {
  'LM Studio': {
    type: 'Desktop App',
    supportedModels: ['LLaMA', 'Mistral', 'Phi-2'],
    link: 'https://lmstudio.ai/'
  },
  'Ollama': {
    type: 'CLI/Desktop',
    supportedModels: ['LLaMA 3', 'Mistral', 'CodeLLaMA'],
    link: 'https://ollama.ai/'
  }
}
