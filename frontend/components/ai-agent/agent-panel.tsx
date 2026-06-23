"use client"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Mic, Paperclip, Send, PanelLeftClose, PanelLeftOpen, BookOpen } from "lucide-react"
import { useLayout } from "@/context/layout-context"
import { useState, useRef, useEffect } from "react"
import { API_BASE_URL } from "@/lib/config"
import { formatPreviewContent } from "@/lib/ai-preview"
import { useTranslations } from "next-intl"
import { useAuth } from "@/contexts/auth-context"

async function readChatError(response: Response) {
    const payload = await response.json().catch(() => null)
    if (typeof payload?.detail === "string") return payload.detail
    if (Array.isArray(payload?.detail) && payload.detail[0]?.msg) return payload.detail[0].msg
    return "Action IA impossible."
}

export function AgentPanel() {
    const { isAgentPanelOpen, toggleAgentPanel, aiStatus, setAiStatus, agentAction, setAgentAction, setViewMode, setPreviewContent } = useLayout()
    const { token, user } = useAuth()
    const t = useTranslations("layout")
    const [inputValue, setInputValue] = useState("")
    const [messages, setMessages] = useState<{ role: 'user' | 'agent', content: string }[]>([
        { role: 'agent', content: t("agentGreeting") }
    ])
    const scrollRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        // Auto scroll to bottom
        if (scrollRef.current) {
            const scrollContainer = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollContainer) {
                scrollContainer.scrollTop = scrollContainer.scrollHeight
            }
        }
    }, [messages, aiStatus])

    const handleSendMessage = async () => {
        if (!inputValue.trim()) return

        const userMsg = inputValue
        setMessages(prev => [...prev, { role: 'user', content: userMsg }])
        setInputValue("")

        // Set statuses
        setAiStatus("working")
        setAgentAction(t("agentProcessing"))

        try {
            // Create a timeout for the fetch
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout


            // IMPORTANT: No trailing slash on the URL to avoid 307 redirects or 404s depending on backend config
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ message: userMsg }),
                signal: controller.signal
            })
            clearTimeout(timeoutId);


            if (!response.ok) {
                throw new Error(await readChatError(response));
            }

            const data = await response.json().catch(async () => ({ message: await response.text() }))

            setAiStatus("idle")
            setAgentAction(null)

            if (data.type === 'content') {
                setMessages(prev => [...prev, { role: 'agent', content: data.message }])
                setPreviewContent(formatPreviewContent(data.data ?? data.message))
                setViewMode("preview")
            } else {
                setMessages(prev => [...prev, { role: 'agent', content: data.message }])
            }

        } catch (error: unknown) {
            console.error("AI Error:", error)
            setAiStatus("idle")
            setAgentAction(t("agentError"))

            // Detailed error message for the user
            let errorMessage = t("agentCommunicationError");
            const errorName = error instanceof Error ? error.name : undefined
            const errorText = error instanceof Error ? error.message : String(error)
            if (errorName === 'AbortError') {
                errorMessage = t("agentTimeout");
            } else if (errorText) {
                errorMessage = errorText;
            }

            setMessages(prev => [...prev, { role: 'agent', content: errorMessage }])
        }
    }

    if (!isAgentPanelOpen) {
        return (
            <div className="flex h-full flex-col items-center gap-4 py-4">
                <Button variant="ghost" size="icon" onClick={toggleAgentPanel}>
                    <PanelLeftOpen className="h-4 w-4" />
                </Button>
            </div>
        )
    }

    return (
        <div className="flex h-full min-h-0 flex-col overflow-hidden font-sans">
            <div className="flex h-[60px] items-center justify-between border-b border-[#E5E7EB] px-4 dark:border-[#3b4248] dark:text-white">
                <div className="flex items-center gap-2 font-semibold">
                    {/* Logo */}
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-black text-white dark:bg-[#343b41]">
                        <BookOpen className="h-5 w-5" />
                    </div>

                    <div className="flex flex-col">
                        <span className="text-sm leading-none">Agent IA</span>
                        {agentAction && (
                            <span className="text-[10px] text-muted-foreground animate-pulse">{agentAction}</span>
                        )}
                        {user?.role && (
                            <span className="text-[10px] text-muted-foreground">Rôle: {user.role}</span>
                        )}
                    </div>
                </div>
                <Button variant="ghost" size="icon" onClick={toggleAgentPanel} className="h-8 w-8 dark:text-white dark:hover:bg-[#343b41]">
                    <PanelLeftClose className="h-4 w-4" />
                </Button>
            </div>

            <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden p-4">
                <ScrollArea className="min-h-0 flex-1 rounded-[24px] border bg-background p-4 shadow-sm dark:border-[#56616a] dark:bg-[#202528]" ref={scrollRef}>
                    <div className="space-y-4">
                        {messages.map((msg, i) => (
                            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                                <div className={`h-8 w-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs ${msg.role === 'agent' ? 'bg-black text-white dark:bg-[#343b41]' : 'bg-[#e5e7eb] text-[#111827] dark:bg-[#4a535b] dark:text-white'
                                    }`}>
                                    {msg.role === 'agent' ? 'AI' : t("agentYou")}
                                </div>
                                <div className={`max-w-[82%] whitespace-pre-wrap rounded-[18px] p-3 text-sm ${msg.role === "agent"
                                    ? "bg-[#EDEFF2] text-[#111827] dark:bg-[#30373d] dark:text-[#f4f7fb]"
                                    : "bg-black text-white dark:bg-[#4a535b] dark:text-white"}`}>
                                    {msg.content}
                                </div>
                            </div>
                        ))}
                        {aiStatus === 'working' && (
                            <div className="flex gap-3">
                                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-black text-xs text-white dark:bg-[#343b41]">AI</div>
                                <div className="flex items-center gap-2 rounded-[18px] bg-[#EDEFF2] p-3 text-sm italic text-[#6B7280] dark:bg-[#30373d] dark:text-[#c7d0da]">
                                    <span className="animate-pulse">{t("agentThinking")}</span>
                                </div>
                            </div>
                        )}
                    </div>
                </ScrollArea>

                <div className="rounded-[24px] border bg-background p-3 dark:border-[#56616a] dark:bg-[#202528]">
                    <div className="flex gap-2 mb-2">
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-[#111827] dark:text-white dark:hover:bg-[#343b41]">
                            <Paperclip className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-[#111827] dark:text-white dark:hover:bg-[#343b41]">
                            <Mic className="h-4 w-4" />
                        </Button>
                    </div>
                    <div className="flex gap-2">
                        <input
                            className="flex-1 border-none bg-transparent text-sm text-[#111827] placeholder:text-[#6B7280] focus:outline-none dark:text-white dark:placeholder:text-[#b9c2cd]"
                            placeholder={t("agentPlaceholder")}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                        />
                        <Button size="icon" className="h-9 w-9 bg-black text-white dark:bg-black dark:text-white" onClick={handleSendMessage}>
                            <Send className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    )
}
