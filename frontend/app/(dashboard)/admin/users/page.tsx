"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Plus, Loader2, Key, Shield, User as UserIcon, CheckCircle2, AlertCircle, X, Edit2 } from "lucide-react"
import { api } from "@/lib/api"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { roleDashboardPath } from "@/lib/dashboard-utils"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: string
  prn?: string
  is_active: boolean
}

function getApiErrorMessage(error: any, fallback = "An error occurred.") {
  const data = error?.response?.data

  if (!data) return fallback
  if (typeof data === "string") return data

  const detail = data.detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail)) return detail.join("\n")
  if (detail && typeof detail === "object") {
    return Object.entries(detail)
      .flatMap(([field, value]) =>
        Array.isArray(value)
          ? value.map((item) => `${field}: ${item}`)
          : [`${field}: ${String(value)}`]
      )
      .join("\n")
  }

  if (typeof data === "object") {
    const messages = Object.entries(data).flatMap(([field, value]) =>
      Array.isArray(value)
        ? value.map((item) => `${field}: ${item}`)
        : [`${field}: ${String(value)}`]
    )
    if (messages.length > 0) {
      return messages.join("\n")
    }
  }

  return fallback
}

export default function UserManagementPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [createdUser, setCreatedUser] = useState<{username: string, pass: string} | null>(null)
  
  // Form State
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    password2: "",
    role: "student",
    prn: ""
  })

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login")
    } else if (status === "authenticated" && session.user.role !== "admin") {
      router.push(roleDashboardPath(session.user.role))
    }
  }, [status, session, router])

  useEffect(() => {
    if (status === "authenticated") {
      fetchUsers()
    }
  }, [status])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const res = await api.get("/users/")
      setUsers(res.data.results || res.data)
    } catch (error) {
      console.error("Failed to fetch users", error)
    } finally {
      setLoading(false)
    }
  }

  const generatePassword = () => {
    const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    let retVal = ""
    for (let i = 0, n = charset.length; i < 12; ++i) {
      retVal += charset.charAt(Math.floor(Math.random() * n))
    }
    setFormData({ ...formData, password: retVal, password2: retVal })
  }

  const handleOpenCreate = () => {
    setIsEditing(false)
    setFormData({
      username: "", email: "", first_name: "", last_name: "",
      password: "", password2: "", role: "student", prn: ""
    })
    setCreatedUser(null)
    setIsModalOpen(true)
  }

  const handleFileUpload = async (file: File, type: 'users') => {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await api.post(`/users/bulk/${type}_upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      alert(`Upload successful!\nCreated: ${res.data.summary.created}\nFailed: ${res.data.summary.failed}`)
      if (res.data.errors.length > 0) {
        alert("Sample errors:\n" + res.data.errors.slice(0, 5).join("\n"))
      }
      fetchUsers()
    } catch (error: any) {
      alert(getApiErrorMessage(error, "Upload failed"))
    }
  }

  const handleOpenEdit = (user: User) => {
    setIsEditing(true)
    setFormData({
      username: user.username,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      password: "", // Don't show password for edit
      password2: "",
      role: user.role,
      prn: user.prn || ""
    })
    setCreatedUser(null)
    setIsModalOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const passwordToSave = formData.password
    try {
      if (isEditing) {
        // Prepare update data (remove password if empty)
        const updateData: any = { ...formData }
        if (!updateData.password) {
          delete updateData.password
          delete updateData.password2
        }
        await api.patch(`/users/${formData.username}/`, updateData)
      } else {
        await api.post("/users/", formData)
        setCreatedUser({ username: formData.username, pass: passwordToSave })
      }
      
      if (!createdUser && !isEditing) {
        // Handled by the success view
      } else if (isEditing) {
        setIsModalOpen(false)
      }
      fetchUsers()
    } catch (error: any) {
      const msg = error.response?.data?.detail || JSON.stringify(error.response?.data) || "An error occurred."
      alert(msg)
    }
  }

  const filteredUsers = users.filter(u => 
    u.username.toLowerCase().includes(search.toLowerCase()) || 
    u.email.toLowerCase().includes(search.toLowerCase()) ||
    (u.first_name + " " + u.last_name).toLowerCase().includes(search.toLowerCase())
  )

  if (status === "loading" || loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto pb-10 relative">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">User Management</h2>
        <p className="text-muted-foreground">
          Create system users, assign roles, and manage access credentials.
        </p>
      </div>

      <Card className="bg-card/50 backdrop-blur-sm border-white/10 shadow-sm">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
          <div>
            <CardTitle>System Users</CardTitle>
            <CardDescription>Total users: {users.length}</CardDescription>
          </div>
          <div className="flex flex-col sm:flex-row gap-2 pt-0">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search users..."
                className="pl-8 sm:w-[300px] bg-background"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Button type="button" variant="outline" onClick={() => document.getElementById("user-upload-input")?.click()}>
              <Key className="mr-2 h-4 w-4" /> Bulk Upload
            </Button>
            <input
              id="user-upload-input"
              type="file"
              accept=".xlsx"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) handleFileUpload(file, 'users')
              }}
              style={{ display: 'none' }}
            />
            <Button onClick={handleOpenCreate}>
              <Plus className="mr-2 h-4 w-4" /> Create User
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>PRN/ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredUsers.map((user) => (
                <TableRow key={user.id} className="hover:bg-muted/30">
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-medium">{user.username}</span>
                      <span className="text-xs text-muted-foreground">{user.first_name} {user.last_name}</span>
                    </div>
                  </TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {user.role === 'admin' ? <Shield className="h-3 w-3 text-red-400" /> : <UserIcon className="h-3 w-3" />}
                      <span className="capitalize">{user.role}</span>
                    </div>
                  </TableCell>
                  <TableCell>{user.prn || "N/A"}</TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
                      user.is_active ? 'bg-emerald-400/10 text-emerald-400 ring-emerald-400/20' :
                      'bg-zinc-400/10 text-zinc-400 ring-zinc-400/20'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" size="sm" className="h-8 gap-2" onClick={() => handleOpenEdit(user)}>
                      <Edit2 className="h-3 w-3" /> Edit
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Modal for Create/Edit */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <Card className="w-full max-w-lg shadow-2xl animate-in zoom-in-95 duration-200">
            {createdUser ? (
              <>
                <CardHeader className="text-center">
                  <div className="mx-auto bg-emerald-500/20 text-emerald-500 p-3 rounded-full w-fit mb-4">
                    <CheckCircle2 className="h-8 w-8" />
                  </div>
                  <CardTitle className="text-2xl">User Created Successfully!</CardTitle>
                  <CardDescription>Please provide these credentials to the user.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="bg-muted/50 p-6 rounded-xl border border-white/5 space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground uppercase font-bold tracking-wider">Username</span>
                      <span className="font-mono text-lg text-primary">{createdUser.username}</span>
                    </div>
                    <div className="h-px bg-white/5"></div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground uppercase font-bold tracking-wider">Password</span>
                      <span className="font-mono text-lg text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded">{createdUser.pass}</span>
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button className="w-full" onClick={() => {setIsModalOpen(false); setCreatedUser(null)}}>Done</Button>
                </CardFooter>
              </>
            ) : (
              <>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>{isEditing ? "Edit User Account" : "Create New User"}</CardTitle>
                    <CardDescription>{isEditing ? "Modify access roles and profile details." : "Register a new member to the system."}</CardDescription>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => setIsModalOpen(false)}><X className="h-4 w-4" /></Button>
                </CardHeader>
                <form onSubmit={handleSubmit}>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="username">Username</Label>
                        <Input id="username" required disabled={isEditing} value={formData.username} onChange={(e) => setFormData({...formData, username: e.target.value})} />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" type="email" required value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="first_name">First Name</Label>
                        <Input id="first_name" required value={formData.first_name} onChange={(e) => setFormData({...formData, first_name: e.target.value})} />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="last_name">Last Name</Label>
                        <Input id="last_name" required value={formData.last_name} onChange={(e) => setFormData({...formData, last_name: e.target.value})} />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="role">Role</Label>
                        <Select value={formData.role} onValueChange={(v) => setFormData({...formData, role: v})}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="admin">Admin</SelectItem>
                            <SelectItem value="hod">HOD</SelectItem>
                            <SelectItem value="faculty">Faculty</SelectItem>
                            <SelectItem value="student">Student</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="prn">PRN (for Students)</Label>
                        <Input id="prn" placeholder="12 digit PRN" value={formData.prn} onChange={(e) => setFormData({...formData, prn: e.target.value})} />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="password">{isEditing ? "New Password (Optional)" : "Password"}</Label>
                      <div className="flex gap-2">
                        <Input 
                          id="password" 
                          type="text" 
                          minLength={isEditing ? undefined : 8}
                          required={!isEditing} 
                          placeholder={isEditing ? "Leave blank to keep current" : ""}
                          value={formData.password} 
                          onChange={(e) => setFormData({...formData, password: e.target.value, password2: e.target.value})} 
                        />
                        <Button type="button" variant="outline" onClick={generatePassword}><Key className="h-4 w-4 mr-2" /> Generate</Button>
                      </div>
                    </div>
                  </CardContent>
                  <div className="flex justify-end gap-3 p-6 pt-0">
                    <Button type="button" variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                    <Button type="submit">{isEditing ? "Save Changes" : "Create User"}</Button>
                  </div>
                </form>
              </>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
