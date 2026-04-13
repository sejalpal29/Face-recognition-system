"use client"

import { useState } from "react"
import { apiClient } from "@/lib/api-client"

interface ScanResult {
  match: boolean
  name: string | null
  person_id: number | null
  similarity: number | null
  alert: boolean
  location: string
  timestamp: string
}

export function useScan() {
  const [result, setResult] = useState<ScanResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const scanFrame = async (file: File, location = "CCTV-01") => {
    try {
      setLoading(true)
      setError(null)
      const response = await apiClient.scanFrame(file, location)
      if (response.success) {
        setResult(response.data)
        return response.data
      } else {
        throw new Error(response.error || "Failed to scan frame")
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to scan frame"
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return { result, loading, error, scanFrame }
}
