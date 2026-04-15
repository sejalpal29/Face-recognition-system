"use client"

/**
 * Custom React hooks for API communication
 * Provides data fetching and mutation capabilities
 */

import { useState, useCallback, useEffect } from "react"
import { apiClient } from "./api-client"

export function useFetchPersons(limit = 50, status?: string) {
  const [persons, setPersons] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPersons = useCallback(async () => {
    setLoading(true)
    setError(null)
    const response = await apiClient.getPersons(limit, 0, status)
    if (response && response.success) {
      setPersons(response.data || [])
    } else {
      setError(response?.error || "Failed to fetch persons")
    }
    setLoading(false)
  }, [limit, status])

  useEffect(() => {
    fetchPersons()
  }, [fetchPersons])

  return { persons, loading, error, refetch: fetchPersons }
}

export function useFetchAlerts(limit = 50, personId?: number, days = 7) {
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAlerts = useCallback(async () => {
    setLoading(true)
    setError(null)
    const response = await apiClient.getAlerts(limit)
    if (response && response.success) {
      setAlerts(response.data || [])
    } else {
      setError(response?.error || "Failed to fetch alerts")
    }
    setLoading(false)
  }, [limit, personId, days])

  useEffect(() => {
    fetchAlerts()
  }, [fetchAlerts])

  return { alerts, loading, error, refetch: fetchAlerts }
}

export function useFetchStats() {
  const [stats, setStats] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = useCallback(async () => {
    setLoading(true)
    setError(null)
    const response = await apiClient.getStats()
    if (response.success) {
      setStats(response.data)
    } else {
      setError(response.error || "Failed to fetch stats")
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchStats()
    // Refresh stats every 30 seconds
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [fetchStats])

  return { stats, loading, error, refetch: fetchStats }
}

export function useFetchSystemHealth() {
  const [health, setHealth] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = useCallback(async () => {
    setLoading(true)
    setError(null)
    const response = await apiClient.getSystemHealth()
    if (response.success) {
      setHealth(response.data)
    } else {
      setError(response.error || "Failed to fetch system health")
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    fetchHealth()
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  return { health, loading, error, refetch: fetchHealth }
}

export function useAddPerson() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addPerson = useCallback(async (formData: FormData) => {
    setLoading(true)
    setError(null)
    const response: any = await apiClient.addPerson(formData)
    if (!response.success) {
      setError(response.error || "Failed to add person")
    }
    setLoading(false)
    return response
  }, [])

  return { addPerson, loading, error }
}

export function useUploadVideo() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)

  const uploadVideo = useCallback(async (file: File) => {
    setLoading(true)
    setError(null)
    setProgress(0)
    const response: any = await apiClient.processVideo(file)
    if (!response.success) {
      setError(response.error || "Failed to upload video")
    } else {
      setProgress(100)
    }
    setLoading(false)
    return response
  }, [])
  

  return { uploadVideo, loading, error, progress }
}
