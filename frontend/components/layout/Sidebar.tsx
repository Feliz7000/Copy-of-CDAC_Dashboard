"use client"

import { useEffect, useState } from "react"
import { useSession, signOut } from "next-auth/react"
import { LayoutDashboard, Users, UserCog, LogOut, Settings, PanelLeft, BarChart3, Trophy, ClipboardList, PieChart } from "lucide-react"
import Link from "next/link"
import { usePathname, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { PRODUCT_NAME } from "@/lib/branding"


export function Sidebar({ role }: { role: string }) {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])
  
  const getLinks = () => {
    switch (role) {
      case "admin":
        return [
          { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
          { href: "/admin/students", label: "Students", icon: Users },
          { href: "/admin/users", label: "User Management", icon: UserCog },
          { href: "/admin/data-management", label: "Data Import", icon: UserCog },
          { href: "/admin/placement-report", label: "Placement Report", icon: BarChart3 },
          { href: "/admin/power-bi", label: "Power BI", icon: PieChart },
          { href: "/admin/model-training", label: "Model Training", icon: LayoutDashboard },
          { href: "/admin/calendar", label: "Exam Calendar", icon: LayoutDashboard },
          { href: "/settings", label: "Settings", icon: Settings },
        ]
      case "faculty":
        return [
          { href: "/faculty/dashboard", label: "Batch Dashboard", icon: LayoutDashboard },
          { href: "/faculty/students", label: "My Students", icon: Users },
          { href: "/faculty/power-bi", label: "Power BI", icon: PieChart },
          { href: "/admin/data-management?tab=marks", label: "Marks Management", icon: Trophy },
          { href: "/settings", label: "Settings", icon: Settings },
        ]
      case "hod":
        return [
          { href: "/hod/dashboard", label: "Course Dashboard", icon: LayoutDashboard },
          { href: "/hod/reports", label: "Reports", icon: UserCog },
          { href: "/hod/placement-report", label: "Placement Report", icon: BarChart3 },
          { href: "/hod/power-bi", label: "Power BI", icon: PieChart },
          { href: "/admin/data-management?tab=marks", label: "Marks Management", icon: Trophy },
          { href: "/admin/data-management?tab=tests", label: "Test Management", icon: ClipboardList },
          { href: "/settings", label: "Settings", icon: Settings },
        ]
      case "student":
        return [
          { href: "/student/dashboard", label: "My Dashboard", icon: LayoutDashboard },
          { href: "/student/scores", label: "My Scores", icon: LayoutDashboard },
          { href: "/student/power-bi", label: "My Marks", icon: PieChart },
          { href: "/settings", label: "Settings", icon: Settings },
        ]
      default:
        return []
    }
  }


  const links = getLinks()

  return (
    <aside className="fixed inset-y-0 left-0 z-10 hidden w-14 flex-col border-r bg-background sm:flex transition-all hover:w-48 group">
      <nav className="flex flex-col items-center gap-4 px-2 py-5 group-hover:items-start group-hover:px-4">
        <Link
          href="#"
          className="group flex h-9 w-9 shrink-0 items-center justify-center gap-2 rounded-full bg-primary text-lg font-semibold text-primary-foreground md:h-8 md:w-8 md:text-base mb-4"
        >
          <PanelLeft className="h-4 w-4 transition-all group-hover:scale-110" />
          <span className="sr-only group-hover:not-sr-only text-xs font-semibold leading-tight">
            {PRODUCT_NAME}
          </span>
        </Link>
        
        {links.map((link) => {
          const Icon = link.icon
          const [hrefPath, hrefQuery] = link.href.split('?')
          const hrefTab = hrefQuery ? new URLSearchParams(hrefQuery).get('tab') : null
          const isActive = isMounted && (
            hrefTab
              ? pathname === hrefPath && searchParams.get('tab') === hrefTab
              : pathname.startsWith(link.href)
          )
          
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center justify-center group-hover:justify-start gap-3 rounded-lg px-2 py-2 transition-colors hover:text-foreground w-full ${
                isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground"
              }`}
            >
              <Icon className="h-5 w-5 shrink-0" />
              <span className="hidden group-hover:block text-sm">{link.label}</span>
            </Link>
          )
        })}
      </nav>
      <nav className="mt-auto flex flex-col items-center gap-4 px-2 py-5 group-hover:items-start group-hover:px-4">
        <Button 
          variant="ghost" 
          size="icon" 
          className="group-hover:w-full group-hover:justify-start group-hover:px-2"
          onClick={() => signOut({ callbackUrl: "/login" })}
        >
          <LogOut className="h-5 w-5 shrink-0" />
          <span className="hidden group-hover:block ml-3">Log Out</span>
        </Button>
      </nav>
    </aside>
  )
}
