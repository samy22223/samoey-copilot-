import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

export function MainNav({
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  const pathname = usePathname()

  const items = [
    {
      href: "/chat",
      label: "Chat",
      active: pathname === "/chat",
    },
    {
      href: "/agents",
      label: "AI Agents",
      active: pathname.startsWith("/agents"),
    },
    {
      href: "/developer",
      label: "Developer Tools",
      active: pathname.startsWith("/developer"),
    },
    {
      href: "/models",
      label: "AI Models",
      active: pathname.startsWith("/models"),
    },
    {
      href: "/team",
      label: "Team",
      active: pathname.startsWith("/team"),
    },
    {
      href: "/settings",
      label: "Settings",
      active: pathname.startsWith("/settings"),
    },
  ]

  return (
    <nav
      className={cn("flex items-center space-x-4 lg:space-x-6", className)}
      {...props}
    >
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            "text-sm font-medium transition-colors hover:text-primary",
            item.active ? "text-primary" : "text-muted-foreground"
          )}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  )
}
