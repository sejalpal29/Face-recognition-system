"use client"

import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api-client"

interface Alert {
  id: number
  person_id: number
  person_name: string
  similarity: number
  location: string
  created_at: string
}

export function useAlerts(personId?: number) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAlerts = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = personId
        ? await apiClient.getPersonAlerts(personId)
        : await apiClient.getAlerts()
      if (response && response.success) {
        setAlerts(response.data || [])
      } else {
        setAlerts([])
        setError(response?.error || "Failed to fetch alerts")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch alerts")
      console.error("[v0] Error fetching alerts:", err)
    } finally {
      setLoading(false)
    }
  }

  const deleteAlert = async (alertId: number) => {
    try {
      setError(null)
      await apiClient.deleteAlert(alertId)
      setAlerts(alerts.filter((a) => a.id !== alertId))
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to delete alert"
      setError(errorMsg)
      throw err
    }
  }

  useEffect(() => {
    fetchAlerts()
    // Refresh alerts every 10 seconds
    const interval = setInterval(fetchAlerts, 10000)
    return () => clearInterval(interval)
  }, [personId])

  return { alerts, loading, error, refetch: fetchAlerts, deleteAlert }
}
