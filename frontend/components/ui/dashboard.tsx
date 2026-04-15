"use client"

import { useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useFetchAlerts, useFetchPersons, useFetchStats, useFetchSystemHealth } from "@/lib/api"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { Users, AlertTriangle, ShieldCheck, Activity, Download, Search, Eye, BarChart3 } from "lucide-react"
import { addDays, eachDayOfInterval, format, isAfter, isBefore, isSameDay, parseISO } from "date-fns"

function formatDate(value: Date) {
  return format(value, "yyyy-MM-dd")
}

function getDateValue(value?: string) {
  return value ? parseISO(value) : undefined
}

export default function Dashboard() {
  const { stats, loading: statsLoading, error: statsError } = useFetchStats()
  const { health, loading: healthLoading, error: healthError } = useFetchSystemHealth()
  const { alerts, loading: alertsLoading, error: alertsError } = useFetchAlerts(100)
  const { persons, loading: personsLoading, error: personsError } = useFetchPersons(200)

  const [query, setQuery] = useState("")
  const [fromDate, setFromDate] = useState("")
  const [toDate, setToDate] = useState("")

  const queryLower = query.trim().toLowerCase()
  const dateFrom = getDateValue(fromDate)
  const dateTo = getDateValue(toDate)
  const useDateFilter = Boolean(dateFrom && dateTo)
  const dateRangeLabel = useDateFilter ? `${format(dateFrom!, "MMM d, yyyy")} → ${format(dateTo!, "MMM d, yyyy")}` : "All time"

  const filteredPersons = useMemo(() => {
    return persons.filter((person: any) => {
      const matchesQuery = queryLower === "" || [person.name, person.case_no, person.status]
        .some((value) => value?.toString().toLowerCase().includes(queryLower))
      const createdAt = person.created_at ? parseISO(person.created_at) : undefined
      const matchesDate = !useDateFilter || (!createdAt || (createdAt && !isAfter(createdAt, dateTo!) && !isBefore(createdAt, dateFrom!)))
      return matchesQuery && matchesDate
    })
  }, [persons, queryLower, dateFrom, dateTo, useDateFilter])

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert: any) => {
      const matchesQuery = queryLower === "" || [alert.person_name, alert.location]
        .some((value) => value?.toString().toLowerCase().includes(queryLower))
      const createdAt = alert.created_at ? parseISO(alert.created_at) : undefined
      const matchesDate = !useDateFilter || (!createdAt || (createdAt && !isAfter(createdAt, dateTo!) && !isBefore(createdAt, dateFrom!)))
      return matchesQuery && matchesDate
    })
  }, [alerts, queryLower, dateFrom, dateTo, useDateFilter])

  const summaryMetrics = useMemo(() => {
    const personsInRange = useDateFilter ? filteredPersons.length : stats?.total_persons ?? persons.length
    const missingInRange = useDateFilter ? filteredPersons.filter((person:any) => person.status?.toLowerCase() === "missing").length : stats?.missing_persons ?? persons.filter((person:any) => person.status?.toLowerCase() === "missing").length
    const wantedInRange = useDateFilter ? filteredPersons.filter((person:any) => person.status?.toLowerCase() === "wanted").length : stats?.wanted_persons ?? persons.filter((person:any) => person.status?.toLowerCase() === "wanted").length
    const matchesInRange = useDateFilter ? filteredAlerts.length : stats?.total_matches ?? stats?.total_facial_embeddings ?? 0
    const activeAlertsInRange = useDateFilter ? filteredAlerts.length : alerts.length
    const totalAlertsInRange = useDateFilter ? filteredAlerts.length : stats?.total_alerts ?? alerts.length

    return {
      totalPersons: personsInRange,
      missingPersons: missingInRange,
      wantedPersons: wantedInRange,
      matchesFound: matchesInRange,
      activeAlerts: activeAlertsInRange,
      totalAlerts: totalAlertsInRange
    }
  }, [filteredAlerts, filteredPersons, stats, persons, alerts.length, useDateFilter])

  const trendRangeStart = useMemo(() => {
    if (useDateFilter) return dateFrom!
    return addDays(new Date(), -6)
  }, [dateFrom, useDateFilter])

  const trendRangeEnd = useMemo(() => {
    if (useDateFilter) return dateTo!
    return new Date()
  }, [dateTo, useDateFilter])

  const isAlertTrend = alerts.length > 0
  const trendSource = useMemo(() => {
    return isAlertTrend ? filteredAlerts : filteredPersons
  }, [alerts.length, filteredAlerts, filteredPersons])

  const trendLoading = isAlertTrend ? alertsLoading : personsLoading

  const trendWindow = useMemo(() => {
    const intervalStart = trendRangeStart
    const intervalEnd = trendRangeEnd
    const days = eachDayOfInterval({ start: intervalStart, end: intervalEnd })
    return days.map((day) => ({
      date: format(day, "MMM d"),
      matches: trendSource.filter((item:any) => {
        const createdAt = item.created_at ? parseISO(item.created_at) : undefined
        return createdAt ? isSameDay(createdAt, day) : false
      }).length
    }))
  }, [trendSource, trendRangeEnd, trendRangeStart])

  const hasTrendData = trendWindow.some((point) => point.matches > 0)

  const exportDashboardPdf = () => {
    const html = `
      <html>
        <head>
          <title>Dashboard Report</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 24px; color: #111; }
            h1, h2 { margin: 0 0 12px; }
            table { width: 100%; border-collapse: collapse; margin-top: 12px; }
            th, td { border: 1px solid #ddd; padding: 8px; }
            th { background: #f4f4f4; }
            .metric { margin-bottom: 10px; }
          </style>
        </head>
        <body>
          <h1>AI Surveillance Dashboard Report</h1>
          <p>${new Date().toLocaleString()}</p>
          <h2>Summary</h2>
          <div class="metric">Total Persons: ${summaryMetrics.totalPersons}</div>
          <div class="metric">Missing Persons: ${summaryMetrics.missingPersons}</div>
          <div class="metric">Wanted Persons: ${summaryMetrics.wantedPersons}</div>
          <div class="metric">Matches Found: ${summaryMetrics.matchesFound}</div>
          <div class="metric">Active Alerts: ${summaryMetrics.activeAlerts}</div>
          <div class="metric">Date filter: ${dateRangeLabel}</div>
          <h2>Weekly Match Trends</h2>
          ${hasTrendData ? `
            <table>
              <thead><tr><th>Date</th><th>Matches</th></tr></thead>
              <tbody>
                ${trendWindow.map((row) => `<tr><td>${row.date}</td><td>${row.matches}</td></tr>`).join('')}
              </tbody>
            </table>
          ` : `<p>No data available</p>`}
        </body>
      </html>`
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(html)
      printWindow.document.close()
      printWindow.focus()
      printWindow.print()
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard Overview</h1>
          <p className="text-muted-foreground">Live metrics from your surveillance database</p>
        </div>
        <Button onClick={exportDashboardPdf} className="w-full md:w-auto">
          <Download className="mr-2 h-4 w-4" /> Export PDF
        </Button>
      </div>
      {(statsError || alertsError || personsError || healthError) ? (
        <div className="rounded-lg border border-yellow-400 bg-yellow-50 p-4 text-sm text-yellow-900">
          {statsError && <div>Stats error: {statsError}</div>}
          {alertsError && <div>Alerts error: {alertsError}</div>}
          {personsError && <div>Persons error: {personsError}</div>}
          {healthError && <div>Health error: {healthError}</div>}
        </div>
      ) : null}

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <div className="xl:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Users className="h-5 w-5" /> Total Persons</CardTitle>
              <CardDescription>{dateRangeLabel}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">{statsLoading ? '—' : summaryMetrics.totalPersons}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> Total Matches Found</CardTitle>
              <CardDescription>{useDateFilter ? 'Within selected date range' : 'Historical matches'}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">{statsLoading ? '—' : summaryMetrics.matchesFound}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5" /> Active Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">{statsLoading ? '—' : summaryMetrics.activeAlerts}</p>
              <p className="text-sm text-muted-foreground">Live alerts from the backend</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Eye className="h-5 w-5" /> Wanted Persons</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">{statsLoading ? '—' : summaryMetrics.wantedPersons}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5" /> Missing Persons</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">{statsLoading ? '—' : summaryMetrics.missingPersons}</p>
            </CardContent>
          </Card>
        </div>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Eye className="h-5 w-5" /> Active CCTV Feed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">No live feeds</p>
            <p className="text-sm text-muted-foreground">Live CCTV integration is not configured yet. This section will show active feeds when available.</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Search className="h-5 w-5" /> Search & Filter</CardTitle>
          <CardDescription>Search persons, case numbers, and alerts; filter metrics by date range</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Input
                placeholder="Search persons, cases, alerts..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </div>
            <div>
              <Input
                type="date"
                value={fromDate}
                onChange={(event) => setFromDate(event.target.value)}
                placeholder="From"
              />
            </div>
            <div>
              <Input
                type="date"
                value={toDate}
                onChange={(event) => setToDate(event.target.value)}
                placeholder="To"
              />
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle>Persons Found</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{personsLoading ? '—' : filteredPersons.length}</p>
                <p className="text-sm text-muted-foreground">Matched by search and date</p>
              </CardContent>
            </Card>
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle>Alerts Found</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{alertsLoading ? '—' : filteredAlerts.length}</p>
                <p className="text-sm text-muted-foreground">Matches returned by alerts</p>
              </CardContent>
            </Card>
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle>Case Matches</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{personsLoading ? '—' : filteredPersons.filter((person:any) => person.case_no?.toLowerCase().includes(queryLower)).length}</p>
                <p className="text-sm text-muted-foreground">Search across case numbers</p>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" /> {isAlertTrend ? 'Weekly Alert Trends' : 'Weekly Person Activity'}
            </CardTitle>
            <CardDescription>{useDateFilter ? dateRangeLabel : 'Last 7 days'}</CardDescription>
          </CardHeader>
          <CardContent>
            {trendLoading ? (
              <p>Loading trend data…</p>
            ) : !hasTrendData ? (
              <p className="text-sm text-muted-foreground">No data available</p>
            ) : (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendWindow} margin={{ top: 16, right: 16, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Line type="monotone" dataKey="matches" stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5" /> System Performance</CardTitle>
            <CardDescription>Real backend and model status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-muted-foreground">Backend Status</div>
                <div className="font-semibold">{healthLoading ? 'Loading…' : health?.status ?? 'Unavailable'}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Device</div>
                <div className="font-semibold">{healthLoading ? 'Loading…' : health?.device ?? 'Unknown'}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Model Initialized</div>
                <div className="font-semibold">{healthLoading ? 'Loading…' : health?.model_initialized ? 'Yes' : 'No'}</div>
              </div>
              {health?.timestamp ? (
                <div>
                  <div className="text-sm text-muted-foreground">Last Checked</div>
                  <div className="font-semibold">{new Date(health.timestamp).toLocaleString()}</div>
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
          <CardDescription>Shows real-time alert data from the backend</CardDescription>
        </CardHeader>
        <CardContent>
          {alertsLoading ? (
            <p>Loading alerts…</p>
          ) : alerts.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recent alerts available</p>
          ) : (
            <div className="grid gap-3">
              {filteredAlerts.slice(0, 5).map((alert:any) => (
                <div key={alert.id} className="rounded-lg border p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold">{alert.person_name || 'Unknown'}</p>
                      <p className="text-sm text-muted-foreground">{alert.location || 'Unknown location'}</p>
                    </div>
                    <Badge variant={(alert.similarity ?? 0) >= 0.9 ? 'destructive' : 'secondary'}>
                      {Math.round((alert.similarity ?? 0) * 100)}% Match
                    </Badge>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{alert.created_at ? format(parseISO(alert.created_at), 'PP p') : 'Unknown time'}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
