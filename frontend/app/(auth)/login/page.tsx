"use client"

import { useState, useTransition } from "react"
import { signIn } from "next-auth/react"
import { useRouter } from "next/navigation"
import { m, LazyMotion, domAnimation } from "framer-motion"
import { Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { PRODUCT_NAME, PRODUCT_TAGLINE } from "@/lib/branding"

export default function LoginPage() {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const [isPending, startTransition] = useTransition()

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    
    const formData = new FormData(event.currentTarget)
    const username = formData.get("username") as string
    const password = formData.get("password") as string

    startTransition(async () => {
      try {
        const res = await signIn("credentials", {
          username,
          password,
          redirect: false,
        })

        if (res?.error) {
          setError("Invalid credentials. Please try again.")
        } else {
          router.push("/")
          router.refresh()
        }
      } catch (err) {
        setError("An unexpected error occurred.")
      }
    })
  }

  return (
    <LazyMotion features={domAnimation}>
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 p-4">
        {/* Animated background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <m.div 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 0.5, scale: 1 }}
            transition={{ duration: 2, repeat: Infinity, repeatType: "reverse" }}
            className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-primary/20 blur-[100px]"
          />
          <m.div 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 0.3, scale: 1.2 }}
            transition={{ duration: 3, delay: 1, repeat: Infinity, repeatType: "reverse" }}
            className="absolute top-[60%] left-[80%] w-[30%] h-[40%] rounded-full bg-blue-600/20 blur-[120px]"
          />
        </div>

        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative z-10 w-full max-w-md"
        >
          <Card className="border-white/10 bg-black/40 backdrop-blur-xl shadow-2xl">
            <CardHeader className="space-y-1 pb-6">
              <CardTitle className="text-xl font-semibold tracking-tight text-white text-center leading-snug px-1">
                {PRODUCT_NAME}
                <span className="mt-2 block text-sm font-normal leading-snug text-zinc-300">
                  {PRODUCT_TAGLINE}
                </span>
              </CardTitle>
              <CardDescription className="text-zinc-400 text-center">
                Enter your credentials to access your portal
              </CardDescription>
            </CardHeader>
            <form onSubmit={onSubmit}>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-zinc-300">Username</Label>
                  <Input 
                    id="username" 
                    name="username" 
                    type="text" 
                    required 
                    className="bg-zinc-900/50 border-zinc-800 text-white placeholder:text-zinc-500 focus-visible:ring-primary"
                    placeholder="Enter your PRN or Admin ID"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-zinc-300">Password</Label>
                  </div>
                  <Input 
                    id="password" 
                    name="password" 
                    type="password" 
                    required 
                    className="bg-zinc-900/50 border-zinc-800 text-white focus-visible:ring-primary"
                  />
                </div>
                {error && (
                  <m.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="text-sm text-destructive"
                  >
                    {error}
                  </m.div>
                )}
              </CardContent>
              <CardFooter>
                <Button 
                  className="w-full bg-primary hover:bg-primary/90 text-white font-medium shadow-lg shadow-primary/20 transition-all" 
                  type="submit" 
                  disabled={isPending}
                >
                  {isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Authenticating...
                    </>
                  ) : (
                    "Sign In"
                  )}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </m.div>
      </div>
    </LazyMotion>
  )
}
