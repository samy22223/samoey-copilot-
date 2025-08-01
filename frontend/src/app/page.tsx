import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Icons } from '@/components/ui/icons';

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-200px)] p-6">
      <div className="w-full max-w-3xl mx-auto text-center">
        <div className="flex justify-center mb-8">
          <div className="p-4 rounded-full bg-primary/10">
            <Icons.logo className="h-12 w-12 text-primary" />
          </div>
        </div>
        
        <h1 className="text-4xl font-bold tracking-tight mb-6">Welcome to Pinnacle Copilot</h1>
        
        <p className="text-xl text-muted-foreground mb-8">
          Your AI-powered coding assistant for building better software, faster.
        </p>
        
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-12">
          {[
            {
              title: 'Code Generation',
              description: 'Generate code snippets in multiple languages',
              icon: <Icons.code className="h-6 w-6 text-primary" />
            },
            {
              title: 'AI Pair Programming',
              description: 'Get help with debugging and problem-solving',
              icon: <Icons.chat className="h-6 w-6 text-primary" />
            },
            {
              title: 'Code Review',
              description: 'Get instant feedback on your code',
              icon: <Icons.send className="h-6 w-6 text-primary" />
            }
          ].map((feature, i) => (
            <div key={i} className="p-6 border rounded-lg bg-card">
              <div className="flex items-center justify-center h-12 w-12 rounded-full bg-primary/10 mb-4 mx-auto">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button asChild size="lg" className="gap-2">
            <Link href="/chat">
              <Icons.chat className="h-4 w-4" />
              Start Chatting
            </Link>
          </Button>
          <Button variant="outline" asChild size="lg">
            <Link href="/docs">
              Documentation
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
