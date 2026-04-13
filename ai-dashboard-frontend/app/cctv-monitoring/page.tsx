"use client"

import { type ChangeEvent, useEffect, useMemo, useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { useAppContext } from "@/lib/contexts/app-context"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { apiClient } from "@/lib/api-client"

interface CCTVCamera {
  id: number
  name: string
  location: string
  stream_url: string
  enabled: boolean
  connected: boolean
  status: string
  last_seen?: string | null
}

const getStatusVariant = (status: string) => {
  switch (status) {
    case "streaming":
      return "default"
    case "offline":
      return "destructive"
    case "disconnected":
      return "outline"
    case "stopped":
      return "secondary"
    default:
      return "secondary"
  }
}

export default function CCTVMonitoringPage() {
  const { isLoggedIn, isLoading } = useAppContext()
  const [cameras, setCameras] = useState<CCTVCamera[]>([])
  const [loading, setLoading] = useState(false)
  const [connectOpen, setConnectOpen] = useState(false)
  const [cameraName, setCameraName] = useState("")
  const [cameraLocation, setCameraLocation] = useState("")
  const [streamUrl, setStreamUrl] = useState("")
  const [connectError, setConnectError] = useState<string | null>(null)
  const [connecting, setConnecting] = useState(false)
  const [systemHealth, setSystemHealth] = useState<any>(null)
  const [healthLoading, setHealthLoading] = useState(false)

  const apiUrl = useMemo(() => process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, '') ?? '', [])

  const fetchCameras = async () => {
    setLoading(true)
    const response = await apiClient.getCCTVs()
    if (response.success && Array.isArray(response.data)) {
      setCameras(response.data)
    }
    setLoading(false)
  }

  const fetchSystemHealth = async () => {
    setHealthLoading(true)
    const response = await apiClient.getSystemHealth()
    if (response.success) {
      setSystemHealth(response.data)
    }
    setHealthLoading(false)
  }

  useEffect(() => {
    fetchCameras()
    fetchSystemHealth()
  }, [])

  if (!isLoading && !isLoggedIn) {
    return null
  }

  const handleConnectCamera = async () => {
    setConnecting(true)
    setConnectError(null)
    if (!cameraName || !cameraLocation || !streamUrl) {
      setConnectError('Please provide a camera name, location, and stream URL.')
      setConnecting(false)
      return
    }

    const response = await apiClient.connectCCTV({
      name: cameraName,
      location: cameraLocation,
      stream_url: streamUrl
    })

    if (!response.success) {
      setConnectError(response.error || 'Unable to connect CCTV camera.')
      setConnecting(false)
      return
    }

    await fetchCameras()
    setCameraName('')
    setCameraLocation('')
    setStreamUrl('')
    setConnectOpen(false)
    setConnecting(false)
  }

  const handleToggleCamera = async (camera: CCTVCamera) => {
    setLoading(true)
    const response = await apiClient.updateCCTV(camera.id, {
      enabled: !camera.enabled,
      connected: camera.connected
    })
    if (response.success) {
      await fetchCameras()
    }
    setLoading(false)
  }

  const handleDisconnectCamera = async (camera: CCTVCamera) => {
    setLoading(true)
    const response = await apiClient.disconnectCCTV(camera.id)
    if (response.success) {
      await fetchCameras()
    }
    setLoading(false)
  }

  const connectedCount = cameras.filter((camera) => camera.connected).length
  const activeStreams = cameras.filter((camera) => camera.enabled && camera.connected && camera.status === 'streaming').length

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 md:ml-64">
        <Header onSearch={() => {}} onExport={() => {}} onDateRangeChange={() => {}} onNotificationClick={() => {}} />

        <main className="p-6 space-y-6 overflow-auto">
          <div>
            <h1 className="text-3xl font-bold">CCTV Monitoring</h1>
            <p className="text-muted-foreground">Connect cameras, view live feeds, and track recognition status.</p>
          </div>

          <div className="grid gap-6 lg:grid-cols-[0.75fr_0.45fr]">
            <Card>
              <CardHeader>
                <CardTitle>Camera Dashboard</CardTitle>
                <CardDescription>Manage connected CCTV cameras and preview live feeds with recognition overlays.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Add a camera and start monitoring feeds in real time.</p>
                    <p className="text-sm text-muted-foreground">Camera status updates automatically after each action.</p>
                  </div>
                  <Dialog open={connectOpen} onOpenChange={setConnectOpen}>
                    <DialogTrigger asChild>
                      <Button>Connect CCTV</Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[520px]">
                      <DialogHeader>
                        <DialogTitle>Connect CCTV Camera</DialogTitle>
                        <DialogDescription>Enter camera details and stream URL to register the source.</DialogDescription>
                      </DialogHeader>
                      <div className="grid gap-4 py-4">
                        <div className="grid gap-2">
                          <Label htmlFor="camera-name">Camera Name</Label>
                          <Input id="camera-name" value={cameraName} onChange={(event) => setCameraName(event.target.value)} placeholder="Front gate camera" />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor="camera-location">Location</Label>
                          <Input id="camera-location" value={cameraLocation} onChange={(event) => setCameraLocation(event.target.value)} placeholder="Main entrance" />
                        </div>
                        <div className="grid gap-2">
                          <Label htmlFor="stream-url">Stream URL</Label>
                          <Textarea id="stream-url" value={streamUrl} onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setStreamUrl(event.target.value)} placeholder="rtsp://... or http://..." />
                        </div>
                        {connectError ? <p className="text-sm text-red-600">{connectError}</p> : null}
                      </div>
                      <DialogFooter className="flex flex-col gap-3 sm:flex-row sm:justify-end">
                        <Button variant="secondary" onClick={() => setConnectOpen(false)}>Cancel</Button>
                        <Button disabled={connecting} onClick={handleConnectCamera}>{connecting ? 'Connecting...' : 'Save & Activate'}</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>

                {loading ? (
                  <div className="rounded-lg border border-muted p-6 text-center text-sm text-muted-foreground">Refreshing camera list...</div>
                ) : cameras.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-muted p-6 text-center text-sm text-muted-foreground">
                    No cameras connected yet. Add a camera to begin monitoring.
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {cameras.map((camera) => (
                      <Card key={camera.id} className="border">
                        <CardHeader>
                          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                            <div>
                              <CardTitle>{camera.name}</CardTitle>
                              <CardDescription>{camera.location}</CardDescription>
                            </div>
                            <Badge variant={getStatusVariant(camera.status) as "default" | "destructive" | "outline" | "secondary"}>{camera.status}</Badge>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          {camera.enabled && camera.connected ? (
                            <div className="overflow-hidden rounded-md border border-slate-200 bg-slate-950">
                              <img
                                alt={`Live feed for ${camera.name}`}
                                src={`${apiUrl}/api/video-feed/${camera.id}`}
                                className="h-60 w-full object-cover"
                              />
                            </div>
                          ) : (
                            <div className="flex h-60 items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 text-sm text-slate-600">
                              {camera.connected ? 'Stream stopped. Start camera to preview.' : 'Camera disconnected.'}
                            </div>
                          )}

                          <div className="grid gap-2 sm:grid-cols-2">
                            <Button onClick={() => handleToggleCamera(camera)}>
                              {camera.enabled ? 'Stop stream' : 'Start stream'}
                            </Button>
                            <Button variant="destructive" onClick={() => handleDisconnectCamera(camera)}>
                              Disconnect
                            </Button>
                          </div>

                          <div className="grid gap-1 text-sm text-muted-foreground">
                            <p className="truncate">Stream URL: {camera.stream_url}</p>
                            <p>Last seen: {camera.last_seen ? new Date(camera.last_seen).toLocaleString() : 'N/A'}</p>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Status</CardTitle>
                <CardDescription>Health metrics and live camera connectivity.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="grid gap-4">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm font-medium text-slate-700">Connected Cameras</p>
                    <p className="mt-2 text-3xl font-semibold text-slate-900">{connectedCount}</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm font-medium text-slate-700">Active Streams</p>
                    <p className="mt-2 text-3xl font-semibold text-slate-900">{activeStreams}</p>
                  </div>
                </div>
                <Separator />
                <div className="space-y-3">
                  <p className="text-sm font-medium text-slate-700">Backend Health</p>
                  {healthLoading ? (
                    <p className="text-sm text-slate-500">Checking system health...</p>
                  ) : systemHealth ? (
                    <div className="space-y-2 text-sm text-slate-700">
                      <p>Status: <span className="font-semibold">{systemHealth.status ?? 'online'}</span></p>
                      <p>CPU: <span className="font-semibold">{systemHealth.cpu_usage ?? 'n/a'}</span></p>
                      <p>Memory: <span className="font-semibold">{systemHealth.memory_usage ?? 'n/a'}</span></p>
                      <p>Uptime: <span className="font-semibold">{systemHealth.uptime ?? 'n/a'}</span></p>
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">System health unavailable.</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}
