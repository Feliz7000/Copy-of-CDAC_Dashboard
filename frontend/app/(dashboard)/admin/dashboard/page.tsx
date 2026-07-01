"use client"

import { useEffect, useState } from "react"
import { m, LazyMotion, domAnimation, Variants } from "framer-motion"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AnimatedAreaChart } from "@/components/ui/charts/AreaChart"
import { Users, BookOpen, GraduationCap, Activity, ShieldCheck, Zap, ArrowUpRight, Loader2 } from "lucide-react"
import { api, getActivityTrend, getSystemOverview } from "@/lib/api"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"

interface SystemStats {
  total_students: number
  total_staff: number
  total_courses: number
  total_batches: number
  recent_activity_count: number
  system_status: string
}

export default function AdminDashboard() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [activityData, setActivityData] = useState<{ name: string; score: number }[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login")
    } else if (status === "authenticated") {
      // Temporarily disabled - IntegrityError in /api/users/admin/
      fetchStats()
    }
  }, [status, router])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const [overview, trend] = await Promise.all([
        getSystemOverview(),
        getActivityTrend().catch(() => []),
      ])
      setStats(overview)
      setActivityData(trend)
    } catch (error) {
      console.error("Failed to fetch system stats", error)
    } finally {
      setLoading(false)
    }
  }

  if (status === "loading" || loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  }

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { 
      opacity: 1, 
      y: 0, 
      transition: { 
        type: "spring" as const, 
        stiffness: 300, 
        damping: 24 
      } 
    }
  }

  return (
    <LazyMotion features={domAnimation}>
      <m.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="flex flex-col gap-8 w-full max-w-7xl mx-auto pb-10"
      >
        {/* Welcome Section */}
        <m.div variants={itemVariants} className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
          <div className="space-y-1">
            <h2 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
              Admin Console
            </h2>
            <p className="text-muted-foreground text-lg">
              Welcome back, <span className="text-white font-medium">{session?.user?.name}</span>. Here's what's happening today.
            </p>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-medium">
            <Zap className="h-4 w-4 fill-emerald-400" />
            System {stats?.system_status || 'Healthy'}
          </div>
        </m.div>

        {/* Stats Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <m.div variants={itemVariants}>
            <Card className="bg-card/40 backdrop-blur-xl border-white/10 hover:border-primary/50 transition-all duration-300 group overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <Users className="h-24 w-24" />
              </div>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Total Students</CardTitle>
                <Users className="h-5 w-5 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-black tracking-tighter">{(stats?.total_students ?? 0).toLocaleString()}</div>
                <div className="flex items-center gap-1 mt-2 text-emerald-400 text-xs font-bold">
                  <ArrowUpRight className="h-3 w-3" />
                  <span>Enrolled across all centres</span>
                </div>
              </CardContent>
            </Card>
          </m.div>
          
          <m.div variants={itemVariants}>
            <Card className="bg-card/40 backdrop-blur-xl border-white/10 hover:border-primary/50 transition-all duration-300 group overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <ShieldCheck className="h-24 w-24" />
              </div>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Active Staff</CardTitle>
                <ShieldCheck className="h-5 w-5 text-blue-400" />
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-black tracking-tighter">{(stats?.total_staff ?? 0).toLocaleString()}</div>
                <div className="flex items-center gap-1 mt-2 text-blue-400 text-xs font-bold">
                  <span>Admins, HODs, & Faculty</span>
                </div>
              </CardContent>
            </Card>
          </m.div>

          <m.div variants={itemVariants}>
            <Card className="bg-card/40 backdrop-blur-xl border-white/10 hover:border-primary/50 transition-all duration-300 group overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <BookOpen className="h-24 w-24" />
              </div>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Courses</CardTitle>
                <BookOpen className="h-5 w-5 text-purple-400" />
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-black tracking-tighter">{stats?.total_courses ?? 0}</div>
                <div className="flex items-center gap-1 mt-2 text-purple-400 text-xs font-bold">
                  <span>Unique programs offered</span>
                </div>
              </CardContent>
            </Card>
          </m.div>

          <m.div variants={itemVariants}>
            <Card className="bg-card/40 backdrop-blur-xl border-white/10 hover:border-primary/50 transition-all duration-300 group overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                <Activity className="h-24 w-24" />
              </div>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Recent Activity</CardTitle>
                <Activity className="h-5 w-5 text-amber-400" />
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-black tracking-tighter">{(stats?.recent_activity_count ?? 0).toLocaleString()}</div>
                <div className="flex items-center gap-1 mt-2 text-amber-400 text-xs font-bold">
                  <span>Audit logs in last 7 days</span>
                </div>
              </CardContent>
            </Card>
          </m.div>
        </div>

        {/* Audit activity chart — live data only */}
        {activityData.some((d) => d.score > 0) && (
        <m.div variants={itemVariants}>
          <Card className="bg-card/40 backdrop-blur-xl border-white/10 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 rounded-full blur-[100px] -mr-48 -mt-48 pointer-events-none"></div>
            <CardHeader className="relative z-10">
              <CardTitle className="text-2xl font-bold tracking-tight">Audit Activity (7 days)</CardTitle>
              <CardDescription className="text-base mt-1">
                Daily count of system audit log entries.
              </CardDescription>
            </CardHeader>
            <CardContent className="relative z-10 pt-4">
              <div className="h-[350px] w-full">
                <AnimatedAreaChart 
                  data={activityData}
                  color="hsl(var(--primary))"
                />
              </div>
            </CardContent>
          </Card>
        </m.div>
        )}

        {/* Recent Activity Mini-Panel (Optional but optimal) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
           <m.div variants={itemVariants} className="lg:col-span-1">
             <Card className="bg-card/40 backdrop-blur-xl border-white/10 h-full">
               <CardHeader>
                 <CardTitle className="text-lg">Quick Actions</CardTitle>
                 <CardDescription>Common administrative tasks</CardDescription>
               </CardHeader>
               <CardContent className="grid gap-3">
                 <Button onClick={() => router.push('/admin/users')} variant="outline" className="justify-start border-white/5 bg-white/5 hover:bg-white/10">
                    <Users className="w-4 h-4 mr-2" /> Manage Users
                 </Button>
                 <Button onClick={() => router.push('/admin/data-management')} variant="outline" className="justify-start border-white/5 bg-white/5 hover:bg-white/10">
                    <GraduationCap className="w-4 h-4 mr-2" /> Import Results
                 </Button>
                 <Button onClick={() => router.push('/admin/settings')} variant="outline" className="justify-start border-white/5 bg-white/5 hover:bg-white/10">
                    <Settings className="w-4 h-4 mr-2" /> System Settings
                 </Button>
               </CardContent>
             </Card>
           </m.div>

           <m.div variants={itemVariants} className="lg:col-span-2">
             <Card className="bg-card/40 backdrop-blur-xl border-white/10 h-full overflow-hidden">
               <CardHeader className="pb-2">
                 <CardTitle className="text-lg">System Health</CardTitle>
                 <CardDescription>Infrastructure and service status</CardDescription>
               </CardHeader>
               <CardContent className="p-0">
                  <div className="divide-y divide-white/5">
                    <div className="px-6 py-4 flex items-center justify-between">
                       <span className="text-sm font-medium">Database (PostgreSQL)</span>
                       <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded font-bold uppercase tracking-widest">Operational</span>
                    </div>
                    <div className="px-6 py-4 flex items-center justify-between">
                       <span className="text-sm font-medium">API Server (Django)</span>
                       <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded font-bold uppercase tracking-widest">Operational</span>
                    </div>
                    <div className="px-6 py-4 flex items-center justify-between">
                       <span className="text-sm font-medium">Frontend (Next.js)</span>
                       <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded font-bold uppercase tracking-widest">Operational</span>
                    </div>
                  </div>
               </CardContent>
             </Card>
           </m.div>
        </div>
      </m.div>
    </LazyMotion>
  )
}

function Settings(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}
