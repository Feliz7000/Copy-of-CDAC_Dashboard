import { ReactNode } from "react"
import { Topbar } from "@/components/layout/Topbar"
import { Sidebar } from "@/components/layout/Sidebar"
import { auth } from "@/auth"
import { redirect } from "next/navigation"

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const session = await auth()
  
  if (!session) {
    redirect("/login")
  }

  return (
    <div className="flex min-h-screen w-full bg-muted/40">
      <Sidebar role={session.user.role} />
      <div className="flex flex-col sm:gap-4 sm:py-4 sm:pl-14 w-full">
        <Topbar user={session.user} />
        <main className="grid flex-1 items-start gap-4 p-4 sm:px-6 sm:py-0 md:gap-8">
          {children}
        </main>
      </div>
    </div>
  )
}
