"use client"

import React, { createContext, useContext, useState, useCallback, useEffect } from "react"

export interface UserProfile {
  name: string
  email: string
  badge: string
  department: string
  profileImage?: string
}

export interface AppContextType {
  user: UserProfile | null
  setUser: (user: UserProfile | null) => void
  isLoggedIn: boolean
  setIsLoggedIn: (value: boolean) => void
  isLoading: boolean
  notifications: Array<{ id: number; message: string; read: boolean; timestamp: Date }>
  addNotification: (message: string) => void
  markNotificationAsRead: (id: number) => void
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [notifications, setNotifications] = useState([
    { id: 1, message: "Face match found - John Doe (95% confidence)", read: false, timestamp: new Date(Date.now() - 2 * 60000) },
    { id: 2, message: "High priority alert - Person of interest detected", read: false, timestamp: new Date(Date.now() - 15 * 60000) },
    { id: 3, message: "System backup completed successfully", read: false, timestamp: new Date(Date.now() - 60 * 60000) },
  ])

  // Load auth state from localStorage on mount
  useEffect(() => {
    try {
      const savedAuth = localStorage.getItem("auth_state")
      if (savedAuth) {
        const authData = JSON.parse(savedAuth)
        console.log("[v0] Restoring auth state from localStorage:", authData.user?.email)
        setUser(authData.user)
        setIsLoggedIn(true)
      }
    } catch (error) {
      console.error("[v0] Error loading auth state:", error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleSetUser = useCallback((newUser: UserProfile | null) => {
    setUser(newUser)
    if (newUser) {
      console.log("[v0] Saving user to localStorage:", newUser.email)
      localStorage.setItem("auth_state", JSON.stringify({ user: newUser, savedAt: Date.now() }))
      setIsLoggedIn(true)
    } else {
      localStorage.removeItem("auth_state")
      setIsLoggedIn(false)
    }
  }, [])

  const handleSetIsLoggedIn = useCallback((value: boolean) => {
    setIsLoggedIn(value)
    console.log("[v0] Login state changed to:", value)
    if (!value) {
      handleSetUser(null)
      // Call logout API to clear auth cookie
      fetch('/api/auth/logout', { method: 'POST' }).catch(err => console.error('Logout API error:', err))
    }
  }, [handleSetUser])

  const addNotification = useCallback((message: string) => {
    const newNotification = {
      id: Date.now(),
      message,
      read: false,
      timestamp: new Date(),
    }
    setNotifications((prev) => [newNotification, ...prev])
    console.log("[v0] New notification added:", message)
  }, [])

  const markNotificationAsRead = useCallback((id: number) => {
    setNotifications((prev) =>
      prev.map((notif) => (notif.id === id ? { ...notif, read: true } : notif))
    )
  }, [])

  const value: AppContextType = {
    user,
    setUser: handleSetUser,
    isLoggedIn,
    setIsLoggedIn: handleSetIsLoggedIn,
    isLoading,
    notifications,
    addNotification,
    markNotificationAsRead,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export const useAppContext = () => {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error("useAppContext must be used within AppProvider")
  }
  return context
}
