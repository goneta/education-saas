"use client"

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"

type ThemeMode = "light" | "dark" | "system"

interface ThemeContextValue {
    theme: ThemeMode
    effectiveTheme: "light" | "dark"
    setTheme: (theme: ThemeMode) => void
    toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined)

function systemTheme(): "light" | "dark" {
    if (typeof window === "undefined") return "light"
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
}

function applyTheme(theme: ThemeMode) {
    const effective = theme === "system" ? systemTheme() : theme
    document.documentElement.classList.toggle("dark", effective === "dark")
    document.documentElement.dataset.theme = effective
    return effective
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const { token } = useAuth()
    const [theme, setThemeState] = useState<ThemeMode>("light")
    const [effectiveTheme, setEffectiveTheme] = useState<"light" | "dark">("light")

    useEffect(() => {
        const stored = (localStorage.getItem("teducai_theme") as ThemeMode | null) || "light"
        setThemeState(stored)
        setEffectiveTheme(applyTheme(stored))
    }, [])

    useEffect(() => {
        if (theme !== "system") return
        const media = window.matchMedia("(prefers-color-scheme: dark)")
        const syncSystemTheme = () => setEffectiveTheme(applyTheme("system"))
        media.addEventListener("change", syncSystemTheme)
        return () => media.removeEventListener("change", syncSystemTheme)
    }, [theme])

    useEffect(() => {
        if (!token) return
        fetch(`${API_BASE_URL}/account/preferences`, { headers: { Authorization: `Bearer ${token}` } })
            .then(response => response.ok ? response.json() : null)
            .then(data => {
                if (data?.theme) {
                    setThemeState(data.theme)
                    localStorage.setItem("teducai_theme", data.theme)
                    setEffectiveTheme(applyTheme(data.theme))
                }
            })
            .catch(() => undefined)
    }, [token])

    const setTheme = useCallback((nextTheme: ThemeMode) => {
        setThemeState(nextTheme)
        localStorage.setItem("teducai_theme", nextTheme)
        setEffectiveTheme(applyTheme(nextTheme))
        if (token) {
            void fetch(`${API_BASE_URL}/account/preferences`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({ theme: nextTheme }),
            }).catch(() => undefined)
        }
    }, [token])

    const toggleTheme = useCallback(() => {
        setTheme(effectiveTheme === "dark" ? "light" : "dark")
    }, [effectiveTheme, setTheme])

    const value = useMemo(() => ({ theme, effectiveTheme, setTheme, toggleTheme }), [theme, effectiveTheme, setTheme, toggleTheme])
    return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
    const context = useContext(ThemeContext)
    if (!context) throw new Error("useTheme must be used within ThemeProvider")
    return context
}
