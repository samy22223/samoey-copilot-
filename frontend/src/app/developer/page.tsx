import CodeToolsPanel from '@/components/developer/CodeToolsPanel'

export default function DeveloperPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Developer Tools</h1>
        <p className="text-muted-foreground">
          Configure and manage AI-powered development tools and assistants
        </p>
      </div>
      <CodeToolsPanel />
    </div>
  )
}
