"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { User, Camera, Shield, Save, LogIn, LogOut } from "lucide-react"
import { useTheme } from "next-themes"
import { useAppContext } from "@/lib/contexts/app-context"
import { useFetchSystemHealth } from "@/lib/api"


export default function Settings() {
  const router = useRouter()
  const { isLoggedIn, isLoading } = useAppContext()
  
  // Declare ALL hooks at the top (before any conditional returns)
  const [confidenceThreshold, setConfidenceThreshold] = useState([85])
  const [autoAlerts, setAutoAlerts] = useState(true)
  const [userProfile, setUserProfile] = useState({
    firstName: "John",
    lastName: "Officer",
    email: "john.officer@police.gov",
    badge: "12345",
    department: "surveillance",
  })
  const { theme, setTheme } = useTheme()
  const { health: systemHealth, loading: healthLoading, error: healthError } = useFetchSystemHealth()

  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      console.log("[v0] User not authenticated, redirecting to login")
      router.push("/login")
    }
  }, [isLoggedIn, isLoading, router])

  if (isLoading || !isLoggedIn) {
    return null
  }

  const handleSaveSettings = () => {
    alert("All settings saved successfully")
  }

  const handleLogin = () => {
    alert("All settings saved successfully")
  }

  const handleLogout = () => {
    alert("All settings saved successfully")
  }

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme)
    alert("All settings saved successfully")
  }

  const cctvNetworkStatus = healthLoading
    ? "Checking..."
    : healthError
    ? "Offline"
    : typeof systemHealth?.network_connectivity === "number" && systemHealth.network_connectivity > 0
    ? "Connected"
    : "No CCTV Connected"

  const cctvNetworkBadgeVariant = cctvNetworkStatus === "Connected" ? "secondary" : "destructive"

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <div className="flex-1 md:ml-64">
        <Header onSearch={() => {}} onExport={() => {}} onDateRangeChange={() => {}} onNotificationClick={() => {}} />

        <main className="p-6 space-y-6 overflow-auto">
          {/* Page Header */}
          <div>
            <h1 className="text-3xl font-bold">Settings</h1>
            <p className="text-muted-foreground">
              Configure your surveillance system preferences and security settings
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Settings */}
            <div className="lg:col-span-2 space-y-6">
              {/* User Profile */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    User Profile
                  </CardTitle>
                  <CardDescription>Manage your account information and preferences</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">First Name</Label>
                      <Input
                        id="firstName"
                        value={userProfile.firstName}
                        onChange={(e) => setUserProfile({ ...userProfile, firstName: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">Last Name</Label>
                      <Input
                        id="lastName"
                        value={userProfile.lastName}
                        onChange={(e) => setUserProfile({ ...userProfile, lastName: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      value={userProfile.email}
                      onChange={(e) => setUserProfile({ ...userProfile, email: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="badge">Badge Number</Label>
                    <Input
                      id="badge"
                      value={userProfile.badge}
                      onChange={(e) => setUserProfile({ ...userProfile, badge: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="department">Department</Label>
                    <Select
                      value={userProfile.department}
                      onValueChange={(value) => setUserProfile({ ...userProfile, department: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="surveillance">Surveillance Unit</SelectItem>
                        <SelectItem value="investigations">Investigations</SelectItem>
                        <SelectItem value="patrol">Patrol Division</SelectItem>
                        <SelectItem value="admin">Administration</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              {/* Facial Recognition Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Camera className="h-5 w-5" />
                    Facial Recognition
                  </CardTitle>
                  <CardDescription>Configure facial recognition engine parameters</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-3">
                    <Label>Confidence Threshold: {confidenceThreshold[0]}%</Label>
                    <Slider
                      value={confidenceThreshold}
                      onValueChange={setConfidenceThreshold}
                      max={100}
                      min={50}
                      step={5}
                      className="w-full"
                    />
                    <p className="text-sm text-muted-foreground">
                      Minimum confidence level required to trigger an alert
                    </p>
                  </div>

                  <Separator />

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Auto-generate Alerts</Label>
                        <p className="text-sm text-muted-foreground">
                          Automatically create alerts for matches above threshold
                        </p>
                      </div>
                      <Switch checked={autoAlerts} onCheckedChange={setAutoAlerts} />
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Real-time Processing</Label>
                        <p className="text-sm text-muted-foreground">Process video feeds in real-time</p>
                      </div>
                      <Switch defaultChecked />
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Multi-face Detection</Label>
                        <p className="text-sm text-muted-foreground">Detect multiple faces in single frame</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar Settings */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Account Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button
                    onClick={handleLogin}
                    variant="outline"
                    className="w-full justify-start bg-transparent"
                    size="sm"
                  >
                    <LogIn className="h-4 w-4 mr-2" />
                    Login
                  </Button>
                  <Button
                    onClick={handleLogout}
                    variant="outline"
                    className="w-full justify-start bg-transparent"
                    size="sm"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Appearance</CardTitle>
                  <CardDescription>Customize the interface appearance</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Theme</Label>
                    <Select value={theme || "dark"} onValueChange={handleThemeChange}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="dark">Dark Theme</SelectItem>
                        <SelectItem value="light">Light Theme</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              {/* System Status */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    System Status
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Recognition Engine</span>
                    <Badge variant="secondary">Online</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Database</span>
                    <Badge variant="secondary">Connected</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">CCTV Network</span>
                    <Badge variant={cctvNetworkBadgeVariant}>{cctvNetworkStatus}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Last Backup</span>
                    <span className="text-sm text-muted-foreground">2 hours ago</span>
                  </div>
                </CardContent>
              </Card>

              {/* Save Settings */}
              <Card>
                <CardContent className="pt-6">
                  <Button onClick={handleSaveSettings} className="w-full gap-2">
                    <Save className="h-4 w-4" />
                    Save All Settings
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
