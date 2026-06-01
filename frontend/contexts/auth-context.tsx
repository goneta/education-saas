"use client"

import React, { createContext, useContext, useState, useEffect, useCallback } from "react"
import { API_BASE_URL } from "@/lib/config"

interface User {
    id: number
    email: string
    full_name: string
    role: string
    school_id: number
}

interface AuthContextType {
    user: User | null
    token: string | null
    isAuthenticated: boolean
    isLoading: boolean
    login: (email: string, password: string, otpCode?: string) => Promise<void>
    logout: () => void
    error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)
const IDLE_TIMEOUT_MS = 30 * 60 * 1000

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [token, setToken] = useState<string | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const clearSession = useCallback((authToken: string | null) => {
        if (authToken) {
            void fetch(`${API_BASE_URL}/auth/logout`, {
                method: "POST",
                headers: { Authorization: `Bearer ${authToken}` },
            }).catch(() => undefined)
        }
        localStorage.removeItem("access_token")
        setToken(null)
        setUser(null)
        setError(null)
    }, [])

    // Check for existing token on mount
    useEffect(() => {
        const storedToken = localStorage.getItem("access_token")
        if (storedToken) {
            setToken(storedToken)
            // Fetch user info
            fetchUserInfo(storedToken)
        } else {
            setIsLoading(false)
        }
    }, [])

    useEffect(() => {
        if (!token) return
        let timeout: ReturnType<typeof setTimeout>
        const reset = () => {
            clearTimeout(timeout)
            timeout = setTimeout(() => clearSession(token), IDLE_TIMEOUT_MS)
        }
        const events = ["mousemove", "keydown", "click", "scroll", "touchstart"]
        events.forEach(event => window.addEventListener(event, reset, { passive: true }))
        reset()
        return () => {
            clearTimeout(timeout)
            events.forEach(event => window.removeEventListener(event, reset))
        }
    }, [token, clearSession])

    const fetchUserInfo = async (authToken: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/me`, {
                headers: {
                    Authorization: `Bearer ${authToken}`,
                },
            })

            if (response.ok) {
                const userData = await response.json()
                setUser(userData)
            } else {
                // Token invalid, clear it
                localStorage.removeItem("access_token")
                setToken(null)
            }
        } catch (err) {
            console.error("Failed to fetch user info:", err)
            localStorage.removeItem("access_token")
            setToken(null)
        } finally {
            setIsLoading(false)
        }
    }

    const login = async (email: string, password: string, otpCode?: string) => {
        setError(null)
        setIsLoading(true)

        try {
            // Create form data for OAuth2PasswordRequestForm
            const formData = new URLSearchParams()
            formData.append("username", email) // Backend expects 'username' field
            formData.append("password", password)
            if (otpCode) formData.append("otp_code", otpCode)

            const response = await fetch(`${API_BASE_URL}/auth/token`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: formData.toString(),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || "Login failed")
            }

            const data = await response.json()
            const accessToken = data.access_token

            // Store token
            localStorage.setItem("access_token", accessToken)
            setToken(accessToken)

            // Fetch user info
            await fetchUserInfo(accessToken)
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred")
            setIsLoading(false)
            throw err
        }
    }

    const logout = () => {
        clearSession(token)
    }

    const value: AuthContextType = {
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
        error,
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider")
    }
    return context
}
