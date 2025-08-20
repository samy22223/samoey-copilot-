'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ExternalLink } from 'lucide-react'

const CODE_ASSISTANTS = {
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

const AI_APP_BUILDERS = {
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

const MODEL_RUNNERS = {
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

export default function CodeToolsPanel() {
  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Developer Tools Configuration</CardTitle>
        <CardDescription>
          Configure and manage AI-powered development tools and assistants
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="assistants" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="assistants">Code Assistants</TabsTrigger>
            <TabsTrigger value="builders">App Builders</TabsTrigger>
            <TabsTrigger value="runners">Model Runners</TabsTrigger>
          </TabsList>
          
          <TabsContent value="assistants" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {Object.entries(CODE_ASSISTANTS).map(([name, tool]) => (
                <Card key={name}>
                  <CardHeader>
                    <CardTitle className="text-lg">{name}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div><strong>Type:</strong> {tool.type}</div>
                      <div><strong>Models:</strong> {tool.models.join(', ')}</div>
                      <div><strong>Offline:</strong> {tool.offline ? '✅' : '❌'}</div>
                    </div>
                    <a
                      href={tool.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 mt-4 text-sm text-blue-600 hover:underline"
                    >
                      View Tool <ExternalLink className="h-4 w-4" />
                    </a>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
          
          <TabsContent value="builders" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {Object.entries(AI_APP_BUILDERS).map(([name, tool]) => (
                <Card key={name}>
                  <CardHeader>
                    <CardTitle className="text-lg">{name}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div><strong>Type:</strong> {tool.type}</div>
                      <div><strong>Features:</strong> {tool.features.join(', ')}</div>
                    </div>
                    <a
                      href={tool.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 mt-4 text-sm text-blue-600 hover:underline"
                    >
                      View Builder <ExternalLink className="h-4 w-4" />
                    </a>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
          
          <TabsContent value="runners" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {Object.entries(MODEL_RUNNERS).map(([name, tool]) => (
                <Card key={name}>
                  <CardHeader>
                    <CardTitle className="text-lg">{name}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div><strong>Type:</strong> {tool.type}</div>
                      <div><strong>Models:</strong> {tool.supportedModels.join(', ')}</div>
                    </div>
                    <a
                      href={tool.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 mt-4 text-sm text-blue-600 hover:underline"
                    >
                      View Runner <ExternalLink className="h-4 w-4" />
                    </a>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
