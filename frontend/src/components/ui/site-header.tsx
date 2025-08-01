import * as React from "react"
import { cn } from "@/lib/utils"

type SiteHeaderProps = React.HTMLAttributes<HTMLElement> & {
  children: React.ReactNode
}

export function SiteHeader({ className, children, ...props }: SiteHeaderProps) {
  return (
    <header
      className={cn(
        "sticky top-0 z-40 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
        className
      )}
      {...props}
    >
      <div className="container flex h-14 items-center">
        <div className="mr-4 hidden md:flex">
          <a href="/" className="mr-6 flex items-center space-x-2">
            <span className="font-bold inline-block">Pinnacle Copilot</span>
          </a>
        </div>
        {children}
      </div>
    </header>
  )
}
