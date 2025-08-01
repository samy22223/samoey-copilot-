import * as React from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Icons } from "@/components/ui/icons"
import { cn } from "@/lib/utils"

export function Sidebar() {
  return (
    <div className="hidden md:flex md:flex-shrink-0">
      <div className="flex flex-col w-64 border-r">
        <div className="flex flex-col flex-1 h-0">
          <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
            <div className="flex items-center flex-shrink-0 px-4">
              <h2 className="text-lg font-semibold">Pinnacle Copilot</h2>
            </div>
            <nav className="mt-5 flex-1 px-2 space-y-1">
              <a
                href="#"
                className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white group flex items-center px-2 py-2 text-sm font-medium rounded-md"
              >
                <Icons.home className="mr-3 h-5 w-5 text-gray-500 dark:text-gray-400" />
                Dashboard
              </a>
              <a
                href="#"
                className="text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 group flex items-center px-2 py-2 text-sm font-medium rounded-md"
              >
                <Icons.chat className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300" />
                Chat History
              </a>
              <a
                href="#"
                className="text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 group flex items-center px-2 py-2 text-sm font-medium rounded-md"
              >
                <Icons.code className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300" />
                Code Snippets
              </a>
              <a
                href="#"
                className="text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 group flex items-center px-2 py-2 text-sm font-medium rounded-md"
              >
                <Icons.settings className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300" />
                Settings
              </a>
            </nav>
          </div>
          <div className="flex-shrink-0 flex border-t border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center">
              <div>
                <Avatar className="h-9 w-9">
                  <AvatarImage src="/avatars/01.png" alt="User" />
                  <AvatarFallback>U</AvatarFallback>
                </Avatar>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-200">
                  User
                </p>
                <button className="text-xs font-medium text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300">
                  View profile
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Mobile sidebar component
export function MobileSidebar() {
  const [open, setOpen] = React.useState(false)

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          className="mr-2 px-0 text-base hover:bg-transparent focus:ring-0 focus:ring-offset-0 md:hidden"
        >
          <Icons.menu className="h-6 w-6" />
          <span className="sr-only">Toggle Menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="pr-0">
        <div className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto">
            <nav className="mt-5 px-2 space-y-1">
              <a
                href="#"
                className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white group flex items-center px-2 py-2 text-base font-medium rounded-md"
              >
                <Icons.home className="mr-4 h-6 w-6 text-gray-500 dark:text-gray-400" />
                Dashboard
              </a>
              <a
                href="#"
                className="text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 group flex items-center px-2 py-2 text-base font-medium rounded-md"
              >
                <Icons.chat className="mr-4 h-6 w-6 text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300" />
                Chat History
              </a>
              <a
                href="#"
                className="text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 group flex items-center px-2 py-2 text-base font-medium rounded-md"
              >
                <Icons.code className="mr-4 h-6 w-6 text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300" />
                Code Snippets
              </a>
              <a
                href="#"
                className="text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 group flex items-center px-2 py-2 text-base font-medium rounded-md"
              >
                <Icons.settings className="mr-4 h-6 w-6 text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300" />
                Settings
              </a>
            </nav>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
