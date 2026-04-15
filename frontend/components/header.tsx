"use client"

import { useState, useRef, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Bell, Search, User, LogOut, FileText, Calendar } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ThemeToggle } from "@/components/theme-toggle"
import { useAppContext } from "@/lib/contexts/app-context"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface HeaderProps {
  onSearch: (value: string) => void
  onExport: () => void
  onDateRangeChange: (range: { start: string; end: string }) => void
  alerts?: Array<any>
  onNotificationClick: (alert: any) => void
}

export function Header({ onSearch, onExport, onDateRangeChange, alerts = [], onNotificationClick }: HeaderProps) {
  const router = useRouter()
  const { setIsLoggedIn, user, isLoggedIn } = useAppContext()
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [searchValue, setSearchValue] = useState("")
  const [dateRange, setDateRange] = useState({ start: "", end: "" })
  const notificationsRef = useRef<HTMLDivElement | null>(null)
  const profileRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notificationsRef.current && !notificationsRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false)
      }
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setProfileOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleSearch = (value: string) => {
    setSearchValue(value)
    onSearch(value)
  }

  const handleDateChange = (field: 'start' | 'end', value: string) => {
    const newRange = { ...dateRange, [field]: value }
    setDateRange(newRange)
    onDateRangeChange(newRange)
  }

  const handleLogout = async () => {
    try {
      setIsLoggedIn(false)
      setProfileOpen(false)
      router.push("/login")
    } catch (error) {
      console.error("Logout error:", error)
    }
  }

  return (
    <header className="bg-card border-b border-border px-6 py-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search persons, cases, or alerts..."
              className="pl-10"
              value={searchValue}
              onChange={(e) => handleSearch(e.target.value)}
            />
          </div>

          <div className="hidden md:flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <input
              type="date"
              className="px-2 py-1 border border-input rounded text-sm bg-background"
              value={dateRange.start}
              onChange={(e) => handleDateChange("start", e.target.value)}
            />
            <span className="text-muted-foreground text-sm">to</span>
            <input
              type="date"
              className="px-2 py-1 border border-input rounded text-sm bg-background"
              value={dateRange.end}
              onChange={(e) => handleDateChange("end", e.target.value)}
            />
          </div>
        </div>

        <div className="flex items-center gap-2 md:gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            className="hidden sm:flex items-center gap-2 bg-transparent"
          >
            <FileText className="h-4 w-4" />
            Export PDF
          </Button>

          <div ref={notificationsRef} className="relative">
            <Button
              variant="ghost"
              size="icon"
              className="relative"
              onClick={() => setNotificationsOpen(!notificationsOpen)}
            >
              <Bell className="h-5 w-5" />
              {alerts.length > 0 && (
                <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs bg-red-600">
                  {alerts.length > 9 ? "9+" : alerts.length}
                </Badge>
              )}
            </Button>

            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-card border border-border rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
                <div className="p-4 border-b border-border">
                  <h3 className="font-semibold text-sm">Recent Alerts</h3>
                </div>
                <div className="divide-y divide-border">
                  {alerts.length > 0 ? (
                    alerts.slice(0, 5).map((alert) => (
                      <div
                        key={alert.id}
                        className="p-3 hover:bg-muted cursor-pointer transition-colors"
                        onClick={() => {
                          onNotificationClick(alert)
                          setNotificationsOpen(false)
                        }}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <p className="font-medium text-sm">{alert.person}</p>
                            <p className="text-xs text-muted-foreground">{alert.camera}</p>
                            <p className="text-xs text-muted-foreground mt-1">{alert.timestamp}</p>
                          </div>
                          <Badge variant="destructive" className="text-xs whitespace-nowrap">
                            {alert.priority}
                          </Badge>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-sm text-muted-foreground">No alerts</div>
                  )}
                </div>
              </div>
            )}
          </div>

          <ThemeToggle />

          <div ref={profileRef} className="relative">
            {!isLoggedIn ? (
              <Button onClick={() => router.push('/login')}>Login</Button>
            ) : (
              <>
                <Button variant="ghost" size="icon" onClick={() => setProfileOpen(!profileOpen)}>
                  <User className="h-5 w-5" />
                </Button>

                {profileOpen && (
                  <DropdownMenu open={profileOpen} onOpenChange={setProfileOpen}>
                    <DropdownMenuTrigger asChild>
                      <div />
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                      <DropdownMenuLabel>
                        <div>
                          <p className="text-sm font-semibold">{user?.name || "Officer"}</p>
                          <p className="text-xs text-muted-foreground">{user?.email}</p>
                          {user?.badge && <p className="text-xs text-muted-foreground">Badge: {user.badge}</p>}
                        </div>
                      </DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem>View Profile</DropdownMenuItem>
                      <DropdownMenuItem>Settings</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={handleLogout}>
                        <LogOut className="h-4 w-4 mr-2" />
                        Logout
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
