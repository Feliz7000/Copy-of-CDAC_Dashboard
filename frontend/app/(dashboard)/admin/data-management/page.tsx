"use client"

import { useEffect, useMemo, useState } from "react"
import { useSession } from "next-auth/react"
import { useRouter, useSearchParams } from "next/navigation"
import { m, LazyMotion, domAnimation, AnimatePresence } from "framer-motion"
import { 
  Settings2, 
  ClipboardList, 
  Trophy, 
  CalendarRange,
} from "lucide-react"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import CategoriesPage from "./categories"
import BatchesPage from "./batches"
import TestsPage from "./tests"
import MarksPage from "./MarksMatrixPage"

const ALL_TABS = [
  {
    id: "categories",
    label: "Main Categories",
    icon: Settings2,
    roles: ["admin"],
    component: <CategoriesPage />
  },
  {
    id: "batches",
    label: "Batches",
    icon: CalendarRange,
    roles: ["admin"],
    component: <BatchesPage />
  },
  {
    id: "tests",
    label: "Test Management",
    icon: ClipboardList,
    roles: ["admin", "hod"],
    component: <TestsPage />
  },
  {
    id: "marks",
    label: "Marks Management",
    icon: Trophy,
    roles: ["admin", "faculty", "hod"],
    component: <MarksPage />
  }
] as const

export default function DataManagementPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const searchParams = useSearchParams()
  const role = session?.user?.role ?? ""

  const tabs = useMemo(
    () => ALL_TABS.filter((tab) => tab.roles.includes(role)),
    [role]
  )

  const requestedTab = searchParams.get("tab")
  const defaultTab = tabs[0]?.id ?? "marks"
  const initialTab =
    requestedTab && tabs.some((t) => t.id === requestedTab) ? requestedTab : defaultTab

  const [activeTab, setActiveTab] = useState(initialTab)

  useEffect(() => {
    if (status === "loading") return
    if (!role || tabs.length === 0) {
      router.replace("/login")
      return
    }
    const validTab =
      requestedTab && tabs.some((t) => t.id === requestedTab) ? requestedTab : defaultTab
    setActiveTab(validTab)
  }, [status, role, tabs, requestedTab, defaultTab, router])

  const handleTabChange = (tab: string) => {
    setActiveTab(tab)
    router.replace(`/admin/data-management?tab=${tab}`, { scroll: false })
  }

  if (status === "loading" || tabs.length === 0) {
    return null
  }

  return (
    <LazyMotion features={domAnimation}>
      <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto pb-20 px-4 sm:px-6">
        <div className="flex flex-col gap-2">
          <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            Data Management
          </h2>
          <p className="text-muted-foreground max-w-2xl">
            {role === "faculty"
              ? "Enter and update student marks across assessment categories."
              : role === "hod"
              ? "Manage test structures and student marks for your course."
              : "Centralized management for assessment categories, test structures, and bulk data operations."}
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <div className="mb-8 p-1 bg-card/50 backdrop-blur-md border border-white/10 rounded-2xl inline-flex w-full sm:w-auto">
            <TabsList className="bg-transparent h-12 gap-1 p-0 flex-1 sm:flex-initial">
              {tabs.map((tab) => (
                <TabsTrigger
                  key={tab.id}
                  value={tab.id}
                  className="flex items-center gap-2 px-6 h-10 rounded-xl data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-lg transition-all duration-200"
                >
                  <tab.icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          <AnimatePresence mode="wait">
            {tabs.map((tab) => (
              <TabsContent key={tab.id} value={tab.id} className="mt-0 focus-visible:outline-none outline-none">
                <m.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  {tab.component}
                </m.div>
              </TabsContent>
            ))}
          </AnimatePresence>
        </Tabs>
      </div>
    </LazyMotion>
  )
}
