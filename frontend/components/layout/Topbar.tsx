"use client"

import { Moon, Sun, User } from "lucide-react"
import { useEffect, useState } from "react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"

export function Topbar({ user }: { user: any }) {
  const { resolvedTheme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const isDarkMode = mounted && resolvedTheme === "dark"

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background/50 px-4 sm:static sm:h-auto sm:border-0 sm:bg-transparent sm:px-6 backdrop-blur-md">
      <div className="flex-1">
        <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
      </div>
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="icon"
          className="rounded-full"
          onClick={() => setTheme(isDarkMode ? "light" : "dark")}
          aria-label={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
        >
          {isDarkMode ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
          <span className="sr-only">Toggle theme</span>
        </Button>
        <div className="hidden md:flex flex-col items-end">
          <span className="text-sm font-medium">{user.name || 'User'}</span>
          <span className="text-xs text-muted-foreground capitalize">{user.role}</span>
        </div>
        <Button variant="secondary" size="icon" className="rounded-full">
          <User className="h-5 w-5" />
          <span className="sr-only">Toggle user menu</span>
        </Button>
      </div>
    </header>
  )
}
