"use client"

import { useEffect, useState } from "react"
import { m, LazyMotion, domAnimation, Variants } from "framer-motion"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2, Key, CheckCircle2, AlertCircle, Shield, User } from "lucide-react"
import { changePassword, getUserProfile } from "@/lib/api"
import { useSession } from "next-auth/react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

type UserProfile = {
  username: string
  email: string
  first_name: string
  last_name: string
  role: string
  prn?: string | null
}

function formatApiError(error: any): string {
  const data = error?.response?.data
  if (!data) return "Something went wrong. Please try again."
  if (typeof data.detail === "string") return data.detail
  for (const key of ["old_password", "new_password", "non_field_errors"]) {
    const val = data[key]
    if (Array.isArray(val) && val.length) return val[0]
    if (typeof val === "string") return val
  }
  return "Failed to update password. Check your current password and try again."
}

export function SettingsPageContent() {
  const { data: session } = useSession()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [profileLoading, setProfileLoading] = useState(true)

  const [passData, setPassData] = useState({
    old_password: "",
    new_password: "",
    new_password2: "",
  })

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null)

  useEffect(() => {
    getUserProfile()
      .then(setProfile)
      .catch(() => setProfile(null))
      .finally(() => setProfileLoading(false))
  }, [])

  const displayName =
    profile
      ? [profile.first_name, profile.last_name].filter(Boolean).join(" ") || profile.username
      : session?.user?.name || "User"

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)

    try {
      await changePassword(passData)
      setResult({ success: true, msg: "Password updated successfully." })
      setPassData({ old_password: "", new_password: "", new_password2: "" })
    } catch (error: any) {
      setResult({ success: false, msg: formatApiError(error) })
    } finally {
      setLoading(false)
    }
  }

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } },
  }

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: { type: "spring" as const, stiffness: 300, damping: 24 },
    },
  }

  return (
    <LazyMotion features={domAnimation}>
      <m.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="flex flex-col gap-8 w-full max-w-5xl mx-auto pb-20"
      >
        <m.div variants={itemVariants} className="flex flex-col gap-2">
          <h2 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
            Account Settings
          </h2>
          <p className="text-muted-foreground text-lg">
            View your account details and change your password.
          </p>
        </m.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <m.div variants={itemVariants} className="lg:col-span-1 space-y-6">
            <Card className="bg-card/40 backdrop-blur-xl border-white/10 overflow-hidden shadow-2xl relative">
              <div className="h-24 bg-gradient-to-r from-primary/40 to-primary/10" />
              <CardContent className="pt-0 relative">
                <div className="absolute -top-10 left-6 p-1.5 bg-background rounded-full border-4 border-card/50">
                  <div className="bg-gradient-to-br from-primary/20 to-primary/5 p-4 rounded-full">
                    <User className="h-8 w-8 text-primary" />
                  </div>
                </div>
                <div className="mt-14 space-y-3">
                  {profileLoading ? (
                    <div className="flex items-center gap-2 text-muted-foreground text-sm">
                      <Loader2 className="h-4 w-4 animate-spin" /> Loading profile…
                    </div>
                  ) : (
                    <>
                      <h3 className="text-2xl font-bold tracking-tight">{displayName}</h3>
                      <p className="text-sm text-muted-foreground">{profile?.email || "—"}</p>
                      <p className="text-sm text-muted-foreground">@{profile?.username || session?.user?.name}</p>
                      {profile?.prn && (
                        <p className="text-sm text-muted-foreground">PRN: {profile.prn}</p>
                      )}
                      <div className="flex items-center gap-2 pt-4 border-t border-white/5">
                        <Shield className="h-4 w-4 text-emerald-400" />
                        <span className="text-xs font-bold uppercase tracking-widest text-emerald-400">
                          {(profile?.role || session?.user?.role || "user")} account
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            <div className="p-5 rounded-2xl bg-blue-500/5 border border-blue-500/10 text-sm text-blue-400/90">
              <strong className="block text-blue-400 mb-1">Managed account</strong>
              Role and email changes are handled by your administrator or HOD.
            </div>
          </m.div>

          <m.div variants={itemVariants} className="lg:col-span-2">
            <Card className="bg-card/40 backdrop-blur-xl border-white/10 shadow-2xl h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-3 text-2xl">
                  <div className="p-2.5 rounded-xl bg-primary/10 text-primary border border-primary/20">
                    <Key className="h-5 w-5" />
                  </div>
                  Change password
                </CardTitle>
                <CardDescription>
                  Use at least 8 characters. You will stay signed in after saving.
                </CardDescription>
              </CardHeader>
              <form onSubmit={handlePasswordChange}>
                <CardContent className="space-y-6">
                  {result && (
                    <Alert
                      className={
                        result.success
                          ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                          : "bg-destructive/10 border-destructive/30 text-destructive"
                      }
                    >
                      {result.success ? <CheckCircle2 className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
                      <AlertTitle>{result.success ? "Success" : "Error"}</AlertTitle>
                      <AlertDescription>{result.msg}</AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-3">
                    <Label htmlFor="old_pass">Current password</Label>
                    <Input
                      id="old_pass"
                      type="password"
                      required
                      autoComplete="current-password"
                      value={passData.old_password}
                      onChange={(e) => setPassData({ ...passData, old_password: e.target.value })}
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <Label htmlFor="new_pass">New password</Label>
                      <Input
                        id="new_pass"
                        type="password"
                        required
                        minLength={8}
                        autoComplete="new-password"
                        value={passData.new_password}
                        onChange={(e) => setPassData({ ...passData, new_password: e.target.value })}
                      />
                    </div>
                    <div className="space-y-3">
                      <Label htmlFor="new_pass2">Confirm new password</Label>
                      <Input
                        id="new_pass2"
                        type="password"
                        required
                        minLength={8}
                        autoComplete="new-password"
                        value={passData.new_password2}
                        onChange={(e) => setPassData({ ...passData, new_password2: e.target.value })}
                      />
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="border-t border-white/5 py-5 flex justify-end">
                  <Button type="submit" disabled={loading}>
                    {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Save password
                  </Button>
                </CardFooter>
              </form>
            </Card>
          </m.div>
        </div>
      </m.div>
    </LazyMotion>
  )
}
