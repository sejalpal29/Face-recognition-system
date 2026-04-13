"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { User, Mail, Badge, Building, Save } from "lucide-react"
import { useState } from "react"
import { useAppContext } from "@/lib/contexts/app-context"

export default function ProfilePage() {
  const router = useRouter()
  const { user, setUser, isLoggedIn, isLoading } = useAppContext()
  const [formData, setFormData] = useState({
    name: user?.name || "Officer John Smith",
    email: user?.email || "john.smith@police.gov",
    badge: user?.badge || "P-12345",
    department: user?.department || "Surveillance Unit",
  })

  const [isSaved, setIsSaved] = useState(false)

  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      console.log("[v0] User not authenticated, redirecting to login")
      router.push("/login")
    }
  }, [isLoggedIn, isLoading, router])

  if (isLoading || !isLoggedIn) {
    return null
  }

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = () => {
    setUser(formData)
    setIsSaved(true)
    console.log("[v0] Profile saved:", formData)
    setTimeout(() => setIsSaved(false), 3000)
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <div className="flex-1 md:ml-64">
        <Header onSearch={() => {}} onExport={() => {}} onDateRangeChange={() => {}} onNotificationClick={() => {}} />

        <main className="p-6 space-y-6">
          {/* Page Header */}
          <div>
            <h1 className="text-3xl font-bold">My Profile</h1>
            <p className="text-muted-foreground">Manage your account information</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Profile Card */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Personal Information
                </CardTitle>
                <CardDescription>Update your profile details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => handleChange("name", e.target.value)}
                      placeholder="Enter your full name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleChange("email", e.target.value)}
                      placeholder="Enter your email"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="badge">Badge Number</Label>
                    <Input
                      id="badge"
                      value={formData.badge}
                      onChange={(e) => handleChange("badge", e.target.value)}
                      placeholder="Enter badge number"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="department">Department</Label>
                    <Select value={formData.department} onValueChange={(value) => handleChange("department", value)}>
                      <SelectTrigger id="department">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Surveillance Unit">Surveillance Unit</SelectItem>
                        <SelectItem value="Investigations">Investigations</SelectItem>
                        <SelectItem value="Patrol Division">Patrol Division</SelectItem>
                        <SelectItem value="Administration">Administration</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button onClick={handleSave} className="flex items-center gap-2">
                    <Save className="h-4 w-4" />
                    Save Changes
                  </Button>
                  {isSaved && <div className="text-green-600 text-sm flex items-center">✓ Profile updated successfully</div>}
                </div>
              </CardContent>
            </Card>

            {/* Info Card */}
            <Card>
              <CardHeader>
                <CardTitle>Account Info</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <User className="h-4 w-4" />
                    <span>Account Type</span>
                  </div>
                  <p className="font-medium">Administrator</p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <Badge className="h-4 w-4" />
                    <span>Access Level</span>
                  </div>
                  <p className="font-medium">Full Access</p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-muted-foreground text-sm">
                    <Mail className="h-4 w-4" />
                    <span>Account Status</span>
                  </div>
                  <p className="font-medium text-green-600">Active</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}
