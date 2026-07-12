"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { useParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { Bot, CircleDot, Plus, Send, Sparkles, Wrench } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { normalizeLocale } from "@/lib/i18n"
import { Button } from "@/components/ui/button"

interface ChatMessage { role: "user" | "assistant"; text: string; agent?: string }
type HistoryItem = Record<string, unknown>

// Streams POST /agents/chat (SSE): start/delta/tool/handoff/done(+history)/error.
export default function AIAgentsPage() {
    const t = useTranslations("aiAgents")
    const params = useParams()
    const locale = normalizeLocale(String(params?.locale || "fr"))
    const { token } = useAuth()
    const [agents, setAgents] = useState<string[]>([])
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [history, setHistory] = useState<HistoryItem[] | null>(null)
    const [input, setInput] = useState("")
    const [busy, setBusy] = useState(false)
    const [activity, setActivity] = useState<string | null>(null) // thinking / tool / handoff line
    const [error, setError] = useState<string | null>(null)
    const bottomRef = useRef<HTMLDivElement | null>(null)

    useEffect(() => {
        if (!token) return
        void (async () => {
            const res = await fetch(`${API_BASE_URL}/agents/capabilities`, { headers: { Authorization: `Bearer ${token}` } })
            if (res.ok) { const d = await res.json(); setAgents(d.agents); if (!d.providers_configured) setError(t("noProvider")) }
        })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token])

    useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }) }, [messages, activity])

    const send = useCallback(async (text: string) => {
        if (!token || !text.trim() || busy) return
        setBusy(true); setError(null); setInput("")
        setMessages(prev => [...prev, { role: "user", text }, { role: "assistant", text: "" }])
        setActivity(t("thinking"))
        try {
            const res = await fetch(`${API_BASE_URL}/agents/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({ message: text, history, language: locale }),
            })
            if (!res.ok || !res.body) { setError((await res.json().catch(() => ({}))).detail || t("error")); return }
            const reader = res.body.getReader()
            const decoder = new TextDecoder()
            let buffer = ""
            for (;;) {
                const { done, value } = await reader.read()
                if (done) break
                buffer += decoder.decode(value, { stream: true })
                const frames = buffer.split("\n\n")
                buffer = frames.pop() || ""
                for (const frame of frames) {
                    const line = frame.split("\n").find(l => l.startsWith("data: "))
                    if (!line) continue
                    const event = JSON.parse(line.slice(6))
                    if (event.type === "delta") {
                        setActivity(null)
                        setMessages(prev => {
                            const next = [...prev]
                            next[next.length - 1] = { ...next[next.length - 1], text: next[next.length - 1].text + event.text }
                            return next
                        })
                    } else if (event.type === "tool" && event.status === "started") {
                        setActivity(`${t("toolRunning")} (${event.name})`)
                    } else if (event.type === "handoff") {
                        setActivity(`${t("handoff")} ${event.agent}`)
                        setMessages(prev => {
                            const next = [...prev]
                            next[next.length - 1] = { ...next[next.length - 1], agent: event.agent }
                            return next
                        })
                    } else if (event.type === "done") {
                        setHistory(event.history || null)
                        setActivity(null)
                    } else if (event.type === "error") {
                        setError(event.message || t("error"))
                        setActivity(null)
                    }
                }
            }
        } catch {
            setError(t("error"))
        } finally { setBusy(false); setActivity(null) }
    }, [token, busy, history, locale, t])

    const reset = () => { setMessages([]); setHistory(null); setError(null) }

    return (
        <div className="flex h-[calc(100vh-8rem)] flex-col space-y-3">
            <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                    <h1 className="flex items-center gap-2 text-2xl font-bold text-[#111827] dark:text-white"><Sparkles className="h-6 w-6" /> {t("title")}</h1>
                    <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
                </div>
                <div className="flex items-center gap-2">
                    <div className="hidden flex-wrap gap-1 sm:flex">
                        {agents.map(a => <span key={a} className="rounded-full border border-[#E5E7EB] px-2 py-0.5 text-xs text-[#6B7280] dark:border-[#3b4248]">{a}</span>)}
                    </div>
                    <Button variant="outline" size="sm" onClick={reset}><Plus className="mr-1 h-4 w-4" /> {t("newChat")}</Button>
                </div>
            </div>

            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <div className="flex-1 space-y-3 overflow-y-auto rounded-2xl border border-[#E5E7EB] bg-white p-4 dark:border-[#3b4248] dark:bg-[#202528]">
                {messages.length === 0 && (
                    <div className="flex flex-wrap gap-2 pt-2">
                        {(["s1", "s2", "s3"] as const).map(k => (
                            <button key={k} onClick={() => send(t(`suggested.${k}` as "suggested.s1"))} className="rounded-full border border-[#E5E7EB] px-3 py-1.5 text-sm text-[#374151] hover:bg-[#F6F7F9] dark:border-[#3b4248] dark:text-[#c7d0da] dark:hover:bg-[#2a3035]">
                                {t(`suggested.${k}` as "suggested.s1")}
                            </button>
                        ))}
                    </div>
                )}
                {messages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                        <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${m.role === "user" ? "bg-black text-white dark:bg-white dark:text-black" : "bg-[#F6F7F9] text-[#111827] dark:bg-[#2a3035] dark:text-[#eef3f8]"}`}>
                            {m.role === "assistant" && (
                                <p className="mb-1 flex items-center gap-1 text-xs font-medium text-[#6B7280] dark:text-[#9aa7b4]"><Bot className="h-3.5 w-3.5" /> {m.agent || "TeducAI"}</p>
                            )}
                            {m.text || (busy && i === messages.length - 1 ? "…" : "")}
                        </div>
                    </div>
                ))}
                {activity && (
                    <p className="flex items-center gap-2 text-xs text-[#6B7280]">
                        {activity.startsWith(t("toolRunning")) ? <Wrench className="h-3.5 w-3.5 animate-pulse" /> : <CircleDot className="h-3.5 w-3.5 animate-pulse" />} {activity}
                    </p>
                )}
                <div ref={bottomRef} />
            </div>

            <div className="flex gap-2">
                <input
                    className="apple-input flex-1"
                    value={input}
                    placeholder={t("placeholder")}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(input) } }}
                    disabled={busy}
                />
                <Button className="bg-black text-white hover:bg-black/90" disabled={busy || !input.trim()} onClick={() => send(input)}>
                    <Send className="mr-1 h-4 w-4" /> {t("send")}
                </Button>
            </div>
        </div>
    )
}
