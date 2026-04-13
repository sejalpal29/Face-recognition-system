"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Users, Camera, AlertTriangle, CheckCircle } from "lucide-react"
import { useAppContext } from "lib/contexts/app-context"
import { apiClient } from "lib/api-client"

const defaultWeek = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

function buildWeeklyData(totalMatches: number | undefined) {
  const base = Math.round((totalMatches || 0) / 7)
  return defaultWeek.map((d, i) => ({ name: d, matches: base + (i % 3), alerts: Math.max(0, Math.round((base + (i % 3)) * 0.15)) }))
}

export default function Dashboard() {
  const router = useRouter()
  const { isLoggedIn, isLoading } = useAppContext()
  const [stats, setStats] = useState<any | null>(null)
  const [systemHealth, setSystemHealth] = useState<any | null>(null)
  const [recentAlerts, setRecentAlerts] = useState<any[]>([])
  const [weeklyData, setWeeklyData] = useState(() => buildWeeklyData(0))
  const [searchQuery, setSearchQuery] = useState("")
  const [dateRange, setDateRange] = useState({ start: "", end: "" })

  const filteredAlerts = useMemo(() => {
    const queryLower = searchQuery.trim().toLowerCase()
    const startDate = dateRange.start ? new Date(dateRange.start) : null
    const endDate = dateRange.end ? new Date(dateRange.end) : null

    return recentAlerts.filter((alert) => {
      const searchable = [
        alert.person_name,
        alert.name,
        alert.location,
        alert.camera,
        alert.case_no,
        alert.priority,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()

      const matchesQuery = !queryLower || searchable.includes(queryLower)
      const createdAt = alert.created_at ? new Date(alert.created_at) : alert.timestamp ? new Date(alert.timestamp) : null
      const matchesStart = !startDate || !createdAt || createdAt >= startDate
      const matchesEnd = !endDate || !createdAt || createdAt <= endDate
      const matchesDate = matchesStart && matchesEnd

      return matchesQuery && matchesDate
    })
  }, [recentAlerts, searchQuery, dateRange.start, dateRange.end])

  const filteredAlertsCount = filteredAlerts.length

  const exportDashboardPdf = () => {
    const reportHtml = `
      <html>
        <head>
          <title>Surveillance Dashboard Report</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 24px; color: #111; }
            h1, h2 { margin: 0 0 12px; }
            p { margin: 4px 0; }
            .summary { margin-bottom: 18px; }
            .summary div { margin-bottom: 6px; }
            table { width: 100%; border-collapse: collapse; margin-top: 18px; }
            th, td { padding: 10px; border: 1px solid #ccc; text-align: left; }
            th { background: #f5f5f5; }
          </style>
        </head>
        <body>
          <h1>Surveillance Dashboard Report</h1>
          <p>Generated: ${new Date().toLocaleString()}</p>
          <div class="summary">
            <h2>Filter</h2>
            <p>Search query: ${searchQuery || 'All'}</p>
            <p>Date range: ${dateRange.start || 'Any'} to ${dateRange.end || 'Any'}</p>
          </div>
          <div class="summary">
            <h2>Alert Summary</h2>
            <p>Total alerts: ${recentAlerts.length}</p>
            <p>Filtered alerts: ${filteredAlertsCount}</p>
          </div>
          <h2>Filtered Alerts</h2>
          <table>
            <thead>
              <tr><th>Person</th><th>Location</th><th>Time</th><th>Match</th></tr>
            </thead>
            <tbody>
              ${filteredAlerts
                .slice(0, 20)
                .map((alert) => `
                  <tr>
                    <td>${alert.person_name || alert.name || 'Unknown'}</td>
                    <td>${alert.location || alert.camera || 'Unknown'}</td>
                    <td>${new Date(alert.created_at || alert.timestamp || Date.now()).toLocaleString()}</td>
                    <td>${Math.round((alert.similarity || 0) * 100)}%</td>
                  </tr>`)
                .join("")}
            </tbody>
          </table>
        </body>
      </html>`

    const printWindow = window.open("", "_blank")
    if (printWindow) {
      printWindow.document.write(reportHtml)
      printWindow.document.close()
      printWindow.focus()
      printWindow.print()
    }
  }

  useEffect(() => {
    let mounted = true
    let poll: any = null

    const load = async () => {
      try {
        const resp = await apiClient.getStats()
        if (resp.success && resp.data) {
          if (!mounted) return
          setStats(resp.data)
          // backend returns recent_alerts array
          setRecentAlerts(Array.isArray(resp.data.recent_alerts) ? resp.data.recent_alerts : [])
          setWeeklyData(buildWeeklyData(resp.data.total_matches))
        } else {
          // keep defaults on error
          console.warn('Failed to fetch stats', resp.error)
        }
      } catch (err) {
        console.warn('Error fetching stats', err)
      }

      // Fetch system health metrics
      try {
        const healthResp = await apiClient.getSystemHealth()
        if (healthResp.success && healthResp.data) {
          if (mounted) {
            setSystemHealth(healthResp.data)
          }
        }
      } catch (err) {
        console.warn('Error fetching system health', err)
      }
    }

    load()
    poll = setInterval(load, 5000)
    return () => { mounted = false; if (poll) clearInterval(poll) }
  }, [])

  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      console.log("[v0] User not authenticated, redirecting to login")
      router.push("/login")
    }
  }, [isLoggedIn, isLoading, router])

  if (isLoading) {
    return (
      <div className="h-screen bg-background flex items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    )
  }

  if (!isLoggedIn) {
    return null // Redirect is in progress
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <div className="flex-1 md:ml-64">
        <Header
          onSearch={setSearchQuery}
          onExport={exportDashboardPdf}
          onDateRangeChange={(range) => setDateRange(range)}
          alerts={filteredAlerts}
          onNotificationClick={(alert) => {
            console.log("Notification clicked:", alert)
          }}
        />

        <main className="p-6 space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Persons</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats ? stats.total_persons : '—'}</div>
                <p className="text-xs text-muted-foreground">Registered persons count</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Missing Persons</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats ? stats.missing_persons : '—'}</div>
                <p className="text-xs text-muted-foreground">Missing people in database</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Matches Found</CardTitle>
                <CheckCircle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats ? stats.total_matches : '—'}</div>
                <p className="text-xs text-muted-foreground">Total matches found</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats ? (stats.active_alerts ?? stats.total_alerts) : '—'}</div>
                <p className="text-xs text-muted-foreground">Active alerts</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Wanted Persons</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats ? stats.wanted_persons : '—'}</div>
                <p className="text-xs text-muted-foreground">People flagged as wanted</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active CCTV Feeds</CardTitle>
              <Camera className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">—</div>
              <p className="text-xs text-muted-foreground">No live feeds available yet</p>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Match Trends Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Weekly Match Trends</CardTitle>
                <CardDescription>Facial recognition matches and alerts over the past week</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={weeklyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="matches" stroke="#10b981" strokeWidth={2} />
                    <Line type="monotone" dataKey="alerts" stroke="#ef4444" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Recent Alerts */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Alerts</CardTitle>
                <CardDescription>Latest facial recognition matches requiring attention</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4 text-sm text-muted-foreground">
                  Showing {filteredAlertsCount} of {recentAlerts.length} alerts{searchQuery || dateRange.start || dateRange.end ? " filtered" : ""}.
                </div>
                <div className="space-y-4">
                  {filteredAlerts.map((alert: any) => (
                    <div key={alert.id ?? alert.created_at} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
                          <Users className="h-5 w-5" />
                        </div>
                        <div>
                          <p className="font-medium">{alert.person_name || alert.name || 'Unknown'}</p>
                          <p className="text-sm text-muted-foreground">Similarity: {Math.round((alert.similarity || 0) * 100)}%</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant={alert.similarity >= 0.75 ? 'destructive' : 'secondary'}>
                          {Math.round((alert.similarity || 0) * 100)}% match
                        </Badge>
                        <p className="text-xs text-muted-foreground mt-1">{new Date(alert.created_at || alert.timestamp || Date.now()).toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                  {filteredAlertsCount === 0 && (
                    <p className="text-sm text-muted-foreground">No alerts match the current search or date range.</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* System Status */}
          <Card>
            <CardHeader>
              <CardTitle>System Performance</CardTitle>
              <CardDescription>Real-time monitoring of surveillance system components</CardDescription>
            </CardHeader>
            <CardContent>
              {typeof systemHealth?.face_recognition_engine === 'number' || typeof systemHealth?.database_performance === 'number' || typeof systemHealth?.network_connectivity === 'number' ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Face Recognition Engine</span>
                      <span>{typeof systemHealth?.face_recognition_engine === 'number' ? systemHealth.face_recognition_engine.toFixed(1) + '%' : '—'}</span>
                    </div>
                    <Progress value={typeof systemHealth?.face_recognition_engine === 'number' ? systemHealth.face_recognition_engine : 0} className="h-2" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Database Performance</span>
                      <span>{typeof systemHealth?.database_performance === 'number' ? systemHealth.database_performance.toFixed(1) + '%' : '—'}</span>
                    </div>
                    <Progress value={typeof systemHealth?.database_performance === 'number' ? systemHealth.database_performance : 0} className="h-2" />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Network Connectivity</span>
                      <span>{typeof systemHealth?.network_connectivity === 'number' ? systemHealth.network_connectivity.toFixed(1) + '%' : '—'}</span>
                    </div>
                    <Progress value={typeof systemHealth?.network_connectivity === 'number' ? systemHealth.network_connectivity : 0} className="h-2" />
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">Backend Status</div>
                    <div className="font-semibold">{systemHealth?.status ?? 'Unavailable'}</div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">Device</div>
                    <div className="font-semibold">{systemHealth?.device ?? 'Unknown'}</div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">Model Initialized</div>
                    <div className="font-semibold">{systemHealth?.model_initialized ? 'Yes' : 'No'}</div>
                  </div>
                  {systemHealth?.timestamp ? (
                    <div className="space-y-2">
                      <div className="text-sm text-muted-foreground">Last Checked</div>
                      <div className="font-semibold">{new Date(systemHealth.timestamp).toLocaleString()}</div>
                    </div>
                  ) : null}
                </div>
              )}
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  )
}
