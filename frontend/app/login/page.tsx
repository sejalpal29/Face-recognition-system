"use client"

import React, { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useAppContext } from "@/lib/contexts/app-context"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const redirectUrl = searchParams.get('redirectUrl') || '/'
  const { setUser, setIsLoggedIn } = useAppContext()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    
    // simple demo credentials
    const demoEmail = "officer@police.gov"
    const demoPassword = "password123"

    if (email === demoEmail && password === demoPassword) {
      const userData = { name: "Officer", email: demoEmail, badge: "OP-001", department: "Security" }
      
      // Set authentication cookie and context
      setUser(userData)
      setIsLoggedIn(true)
      
      // Set auth token cookie via API (next.js HTTPOnly cookie)
      try {
        await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: demoEmail })
        })
      } catch (err) {
        console.error('Failed to set auth cookie', err)
      }
      
      // Redirect to original page or dashboard
      router.push(redirectUrl)
      return
    }

    setError("Invalid demo credentials. Use officer@police.gov / password123")
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="w-full max-w-md p-8 bg-card rounded-lg shadow-2xl border border-slate-700">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white">AI Surveillance</h1>
          <p className="text-sm text-muted-foreground mt-1">Face Recognition System</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block mb-2 text-sm font-medium">Email</label>
            <Input 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              placeholder="officer@police.gov"
              type="email"
              disabled={email === "" && password === "" ? false : false}
            />
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium">Password</label>
            <Input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-500 px-4 py-3 rounded text-sm">
              {error}
            </div>
          )}

          <div className="pt-2">
            <Button type="submit" className="w-full h-10">Login</Button>
          </div>
        </form>

        <div className="mt-6 pt-6 border-t border-slate-700">
          <p className="text-xs text-muted-foreground text-center">
            <strong>Demo Credentials:</strong><br/>
            Email: officer@police.gov<br/>
            Password: password123
          </p>
        </div>
      </div>
    </div>
  )
}
