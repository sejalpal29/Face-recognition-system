"use client"

import React, { useEffect } from "react"
import { useRouter } from "next/navigation"
import { Sidebar } from "@/components/sidebar"
import { useAppContext } from "lib/contexts/app-context"
import CCTVMonitoring from "@/components/ui/cctv-monitoring"

export default function CCTVPage() {
  const router = useRouter()
  const { isLoggedIn, isLoading } = useAppContext()

  useEffect(() => {
    if (!isLoading && !isLoggedIn) {
      console.log("[v0] User not authenticated, redirecting to login")
      router.push("/login")
    }
  }, [isLoggedIn, isLoading, router])

  if (isLoading || !isLoggedIn) {
    return null
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex-1 md:ml-64">
        <main className="p-6">
          <CCTVMonitoring />
        </main>
      </div>
    </div>
  )
}

