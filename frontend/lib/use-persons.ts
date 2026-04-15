"use client"

import { useState, useEffect } from "react"
import { apiClient } from "@/lib/api-client"

interface Person {
  id: number
  name: string
  age?: number | null
  case_no: string
  status: string
  face_image_path: string
  embedding_path: string
  created_at: string
  updated_at: string
}

export function usePersons() {
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPersons = async () => {
    try {
      setLoading(true)
      setError(null)
      console.log("[v0] Fetching persons from API...")
      const resp = await apiClient.getPersons()
      if (resp && resp.success) {
        const fetchedPersons = resp.data || []
        console.log(`[v0] Fetched ${fetchedPersons.length} persons from API`)
        setPersons(fetchedPersons)
      } else {
        console.warn("[v0] API returned error:", resp?.error)
        setPersons([])
        setError(resp?.error || 'Failed to fetch persons')
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to fetch persons"
      setError(errorMsg)
      console.error("[v0] Error fetching persons:", err)
    } finally {
      setLoading(false)
    }
  }

  const addPerson = async (name: string, status: string, file: File, caseNo: string, age?: string) => {
    try {
      setError(null)
      const form = new FormData()
      form.append('name', name)
      form.append('status', status)
      form.append('case_no', caseNo)
      form.append('file', file)
      if (age) {
        form.append('age', age)
      }

      const resp: any = await apiClient.addPerson(form)
      if (resp && resp.success) {
        const newPerson = resp.data
        console.log('[v0] Person added successfully, refetching persons list')
        await fetchPersons()
        return newPerson
      }
      throw new Error(resp?.error || 'Failed to add person')
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to add person"
      setError(errorMsg)
      throw err
    }
  }

  const deletePerson = async (personId: number) => {
    try {
      setError(null)
      const resp = await apiClient.deletePerson(personId)
      if (resp && resp.success) {
        setPersons((p) => p.filter((x) => x.id !== personId))
      } else {
        throw new Error(resp?.error || 'Failed to delete person')
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to delete person"
      setError(errorMsg)
      throw err
    }
  }

  useEffect(() => {
    fetchPersons()
  }, [])

  return { persons, loading, error, fetchPersons, addPerson, deletePerson }
}
