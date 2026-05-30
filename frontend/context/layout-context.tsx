"use client"

import React, { createContext, useContext, useState } from "react"

type ViewMode = "dashboard" | "preview"
type AiStatus = "idle" | "working" | string

interface LayoutContextType {
    isAgentPanelOpen: boolean
    toggleAgentPanel: () => void
    viewMode: ViewMode
    setViewMode: (mode: ViewMode) => void
    aiStatus: AiStatus
    setAiStatus: (status: AiStatus) => void
    agentAction: string | null
    setAgentAction: (action: string | null) => void
    previewContent: string | null
    setPreviewContent: (content: string | null) => void
}

const LayoutContext = createContext<LayoutContextType | undefined>(undefined)

export function LayoutProvider({ children }: { children: React.ReactNode }) {
    const [isAgentPanelOpen, setIsAgentPanelOpen] = useState(true)
    const [viewMode, setViewMode] = useState<ViewMode>("dashboard")
    const [aiStatus, setAiStatus] = useState<AiStatus>("idle")
    const [agentAction, setAgentAction] = useState<string | null>(null)
    const [previewContent, setPreviewContent] = useState<string | null>(null)

    const toggleAgentPanel = () => setIsAgentPanelOpen((prev) => !prev)

    return (
        <LayoutContext.Provider
            value={{
                isAgentPanelOpen,
                toggleAgentPanel,
                viewMode,
                setViewMode,
                aiStatus,
                setAiStatus,
                agentAction,
                setAgentAction,
                previewContent,
                setPreviewContent
            }}
        >
            {children}
        </LayoutContext.Provider>
    )
}

export function useLayout() {
    const context = useContext(LayoutContext)
    if (context === undefined) {
        throw new Error("useLayout must be used within a LayoutProvider")
    }
    return context
}
