"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { useAppContext } from "@/lib/contexts/app-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"
import { FileText, Download, TrendingUp, Users, Camera, AlertTriangle } from "lucide-react"
import { addDays, eachDayOfInterval, format, isAfter, isSameDay, parseISO } from "date-fns"
import { apiClient } from "@/lib/api-client"

function formatDate(value?: string) {
  if (!value) return ""
  try {
    return format(parseISO(value), "PPP")
  } catch {
    return value
  }
}

function buildTrendData(alerts: any[], startDate: string, endDate: string) {
  const earliestAlert = alerts.reduce((earliest: Date | null, alert) => {
    const created = alert.created_at ? parseISO(alert.created_at) : null
    if (!created) return earliest
    return earliest === null || created < earliest ? created : earliest
  }, null as Date | null)

  const defaultStart = earliestAlert ?? addDays(new Date(), -6)
  const start = startDate ? parseISO(startDate) : defaultStart
  const end = endDate ? parseISO(endDate) : new Date()

  if (isAfter(start, end)) {
    return []
  }

  const interval = eachDayOfInterval({ start, end })
  return interval.map((day) => ({
    date: format(day, "MMM d"),
    alerts: alerts.filter((alert) => {
      const created = alert.created_at ? parseISO(alert.created_at) : undefined
      return created ? isSameDay(created, day) : false
    }).length
  }))
}

function buildSimilarityDistribution(alerts: any[]) {
  const high = alerts.filter((alert) => (alert.similarity ?? 0) >= 0.8).length
  const medium = alerts.filter((alert) => (alert.similarity ?? 0) >= 0.7 && (alert.similarity ?? 0) < 0.8).length
  const low = alerts.filter((alert) => (alert.similarity ?? 0) < 0.7).length

  return [
    { name: "High Confidence", value: high, color: "#10b981" },
    { name: "Medium Confidence", value: medium, color: "#f59e0b" },
    { name: "Low Confidence", value: low, color: "#6b7280" }
  ]
}

export default function Reports() {
  const router = useRouter()
  const { isLoggedIn, isLoading } = useAppContext()
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [reportType, setReportType] = useState("all")
  const [stats, setStats] = useState<any | null>(null)
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      router.push("/login")
    }
  }, [isLoggedIn, isLoading, router])

  useEffect(() => {
    let mounted = true

    const loadReportData = async () => {
      setLoading(true)
      setError(null)

      try {
        const [statsResp, alertsResp] = await Promise.all([
          apiClient.getStats(startDate || undefined, endDate || undefined),
          apiClient.getAlerts(100, startDate || undefined, endDate || undefined)
        ])

        if (mounted) {
          if (statsResp.success && statsResp.data) {
            setStats(statsResp.data)
          } else {
            setError(statsResp.error || "Failed to load report statistics")
          }

          if (alertsResp.success) {
            setAlerts(alertsResp.data || [])
          } else {
            setError((prev) => prev ? `${prev}; ${alertsResp.error}` : alertsResp.error || "Failed to load alerts")
          }
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load report data")
        }
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadReportData()
    return () => {
      mounted = false
    }
  }, [startDate, endDate])

  const filteredAlerts = useMemo(() => {
    if (reportType === "all") return alerts
    if (reportType === "high") return alerts.filter((alert) => (alert.similarity ?? 0) >= 0.8)
    if (reportType === "medium") return alerts.filter((alert) => (alert.similarity ?? 0) >= 0.7 && (alert.similarity ?? 0) < 0.8)
    if (reportType === "low") return alerts.filter((alert) => (alert.similarity ?? 0) < 0.7)
    return alerts
  }, [alerts, reportType])

  const trendData = useMemo(() => buildTrendData(alerts, startDate, endDate), [alerts, startDate, endDate])
  const statusData = useMemo(() => buildSimilarityDistribution(alerts), [alerts])

  const rangeLabel = startDate && endDate ? `${formatDate(startDate)} — ${formatDate(endDate)}` : "All time"

  const handleExport = () => {
    const content = `
      <html>
        <head>
          <title>Surveillance Report</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 24px; color: #111; }
            h1, h2, h3 { margin: 0 0 12px; }
            .section { margin-bottom: 24px; }
            table { width: 100%; border-collapse: collapse; margin-top: 12px; }
            th, td { border: 1px solid #ddd; padding: 8px; }
            th { background: #f4f4f4; text-align: left; }
            .metric { margin-bottom: 8px; }
            .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #e5e7eb; margin-right: 8px; }
          </style>
        </head>
        <body>
          <h1>Surveillance Report</h1>
          <p>${new Date().toLocaleString()}</p>
          <div class="section">
            <h2>Filters</h2>
            <p>Date range: ${rangeLabel}</p>
            <p>Report type: ${reportType}</p>
          </div>
          <div class="section">
            <h2>Summary</h2>
            <div class="metric">Total matches: ${stats?.total_matches ?? 0}</div>
            <div class="metric">Active cases: ${stats?.total_alerts ?? 0}</div>
            <div class="metric">Resolution rate: ${stats ? Math.round(((stats.total_matches || 0) - (stats.total_alerts || 0)) / Math.max(1, (stats.total_matches || 1)) * 100) : 0}%</div>
            <div class="metric">Missing persons: ${stats?.missing_persons ?? 0}</div>
            <div class="metric">Wanted persons: ${stats?.wanted_persons ?? 0}</div>
          </div>
          <div class="section">
            <h2>Trend Summary</h2>
            ${trendData.length === 0 ? '<p>No trend data available.</p>' : `
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Alerts</th>
                  </tr>
                </thead>
                <tbody>
                  ${trendData.map((point) => `
                    <tr>
                      <td>${point.date}</td>
                      <td>${point.alerts}</td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            `}
          </div>
          <div class="section">
            <h2>Similarity Distribution</h2>
            <ul>
              ${statusData.map((segment) => `<li>${segment.name}: ${segment.value}</li>`).join("")}
            </ul>
          </div>
          <div class="section">
            <h2>Case Details</h2>
            ${alerts.length === 0 ? '<p>No alerts available for the selected range.</p>' : `
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Person</th>
                    <th>Location</th>
                    <th>Similarity</th>
                    <th>Created At</th>
                  </tr>
                </thead>
                <tbody>
                  ${alerts.map((alert) => `
                    <tr>
                      <td>${alert.id}</td>
                      <td>${alert.person_name || 'Unknown'}</td>
                      <td>${alert.location || 'Unknown'}</td>
                      <td>${Math.round((alert.similarity ?? 0) * 100)}%</td>
                      <td>${alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Unknown'}</td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            `}
          </div>
        </body>
      </html>`

    const reportWindow = window.open('', '_blank')
    if (!reportWindow) {
      alert('Unable to open report window')
      return
    }

    reportWindow.document.write(content)
    reportWindow.document.close()
    reportWindow.focus()
    reportWindow.print()
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />

      <div className="flex-1 md:ml-64">
        <Header onSearch={() => {}} onExport={() => {}} onDateRangeChange={() => {}} onNotificationClick={() => {}} />

        <main className="p-6 space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold">Reports</h1>
              <p className="text-muted-foreground">Generate and view surveillance system reports and analytics</p>
            </div>
            <Button onClick={handleExport} disabled={loading}>
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-3 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start-date">Start Date</Label>
                <Input
                  id="start-date"
                  type="date"
                  value={startDate}
                  onChange={(event) => setStartDate(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end-date">End Date</Label>
                <Input
                  id="end-date"
                  type="date"
                  value={endDate}
                  onChange={(event) => setEndDate(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="report-type">Report Type</Label>
                <Select value={reportType} onValueChange={setReportType}>
                  <SelectTrigger id="report-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Alerts</SelectItem>
                    <SelectItem value="high">High Confidence</SelectItem>
                    <SelectItem value="medium">Medium Confidence</SelectItem>
                    <SelectItem value="low">Low Confidence</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Report Range</Label>
                <div className="rounded-lg border border-muted p-3 text-sm text-muted-foreground">{rangeLabel}</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Matches</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{loading ? '—' : stats?.total_matches ?? 0}</div>
                <p className="text-xs text-muted-foreground">Total matches recorded</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Cases</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{loading ? '—' : alerts.length}</div>
                <p className="text-xs text-muted-foreground">Alerts in your selected range</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Resolution Rate</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{loading ? '—' : stats ? `${Math.round(((stats.total_matches || 0) - (stats.total_alerts || 0)) / Math.max(1, (stats.total_matches || 1)) * 100)}%` : '—'}</div>
                <p className="text-xs text-muted-foreground">Estimated resolution rate</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Wanted Persons</CardTitle>
                <Camera className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{loading ? '—' : stats?.wanted_persons ?? 0}</div>
                <p className="text-xs text-muted-foreground">Wanted person records</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Alert Trends</CardTitle>
                <CardDescription>Alerts over your selected period</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="alerts" fill="#10b981" name="Alerts" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Similarity Distribution</CardTitle>
                <CardDescription>Alert confidence levels</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-4 mt-4">
                  {statusData.map((entry) => (
                    <div key={entry.name} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
                      <span className="text-sm">{entry.name}: {entry.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Case Details</CardTitle>
                  <CardDescription>Alert cases within the selected range</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{reportType === 'all' ? 'All alerts' : `${reportType} confidence`}</Badge>
                  <span className="text-sm text-muted-foreground">{rangeLabel}</span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {error ? (
                <div className="rounded-md bg-red-50 border border-red-200 p-4 text-sm text-red-700">{error}</div>
              ) : null}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead>
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Case ID</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Person</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Location</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Similarity</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Created At</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {filteredAlerts.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-sm text-slate-500">No alerts found for the selected period.</td>
                      </tr>
                    ) : filteredAlerts.map((alert) => (
                      <tr key={alert.id}>
                        <td className="px-4 py-3 text-sm text-slate-700">{alert.id}</td>
                        <td className="px-4 py-3 text-sm text-slate-700">{alert.person_name || 'Unknown'}</td>
                        <td className="px-4 py-3 text-sm text-slate-700">{alert.location || 'Unknown'}</td>
                        <td className="px-4 py-3 text-sm text-slate-700">{Math.round((alert.similarity ?? 0) * 100)}%</td>
                        <td className="px-4 py-3 text-sm text-slate-500">{alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Unknown'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  )
}
