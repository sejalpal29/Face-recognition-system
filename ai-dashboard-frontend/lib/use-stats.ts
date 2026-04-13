"use client"

import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api-client"

interface Stats {
  total_persons: number
  total_matches: number
  total_alerts: number
  active_alerts: number
  total_scans: number
  recent_alerts: any[]
}

export function useStats() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.getStats()
      if (response.success) {
        setStats(response.data)
      } else {
        setError(response.error || "Failed to fetch stats")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch stats")
      console.error("[v0] Error fetching stats:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  return { stats, loading, error, refetch: fetchStats }
}
