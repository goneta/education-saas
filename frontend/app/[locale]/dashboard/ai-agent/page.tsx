"use client"

import { useEffect, useRef, useState } from "react"
import ReactMarkdown from "react-markdown"
import { useTranslations } from "next-intl"
import { ArrowLeft, Download, FileImage, Mic, Paperclip, Printer, RefreshCw, RotateCcw, Send, Share2 } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { formatPreviewContent } from "@/lib/ai-preview"
import { useAuth } from "@/contexts/auth-context"
import { useLayout } from "@/context/layout-context"

type ChatMessage = { role: "user" | "agent"; content: string }

async function readChatError(response: Response) {
    const payload = await response.json().catch(() => null)
    if (typeof payload?.detail === "string") return payload.detail
    if (Array.isArray(payload?.detail) && payload.detail[0]?.msg) return payload.detail[0].msg
    return "Action IA impossible."
}

function downloadText(content: string, extension: "txt" | "csv" | "xls") {
    const type = extension === "txt" ? "text/plain" : extension === "csv" ? "text/csv" : "application/vnd.ms-excel"
    const blob = new Blob([content], { type: `${type};charset=utf-8` })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = `teducai-ai-preview.${extension}`
    anchor.click()
    URL.revokeObjectURL(url)
}

export default function MobileAIAgentPage() {
    const { token } = useAuth()
    const t = useTranslations("layout")
    const { setPreviewContent: setDesktopPreview, setViewMode } = useLayout()
    const [input, setInput] = useState("")
    const [messages, setMessages] = useState<ChatMessage[]>([{ role: "agent", content: t("agentGreeting") }])
    const [preview, setPreview] = useState("")
    const [showPreview, setShowPreview] = useState(false)
    const [loading, setLoading] = useState(false)
    const chatRef = useRef<HTMLDivElement | null>(null)
    const fileRef = useRef<HTMLInputElement | null>(null)
    const imageRef = useRef<HTMLInputElement | null>(null)

    useEffect(() => {
        chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: "smooth" })
    }, [messages, loading, showPreview])

    const resetConversation = () => {
        setInput("")
        setPreview("")
        setShowPreview(false)
        setMessages([{ role: "agent", content: t("agentGreeting") }])
    }

    const send = async () => {
        if (!input.trim() || loading) return
        const prompt = input
        setInput("")
        setMessages(previous => [...previous, { role: "user", content: prompt }])
        setLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(token ? { Authorization: `Bearer ${token}` } : {}),
                },
                body: JSON.stringify({ message: prompt }),
            })
            if (!response.ok) throw new Error(await readChatError(response))
            const data = await response.json().catch(() => null)
            const message = data?.message || "Résultat généré."
            const output = formatPreviewContent(data?.data ?? data?.message)
            setMessages(previous => [...previous, { role: "agent", content: message }])
            if (output) {
                setPreview(output)
                setDesktopPreview(output)
                setViewMode("preview")
                setShowPreview(true)
            }
        } catch (error) {
            setMessages(previous => [...previous, { role: "agent", content: error instanceof Error ? error.message : t("agentCommunicationError") }])
        } finally {
            setLoading(false)
        }
    }

    const printPreview = () => {
        const win = window.open("", "_blank")
        win?.document.write(`<html><head><title>TeducAI Preview</title><style>body{font-family:system-ui;padding:24px;line-height:1.5}</style></head><body>${preview.replace(/\n/g, "<br/>")}</body></html>`)
        win?.document.close()
        win?.print()
    }

    return (
        <div className="relative h-full min-h-[calc(100dvh-144px)] overflow-hidden rounded-none bg-white md:rounded-[28px]">
            <section className={`absolute inset-0 flex flex-col bg-white transition-transform duration-300 ease-out ${showPreview ? "-translate-x-full" : "translate-x-0"}`}>
                <header className="flex h-14 shrink-0 items-center justify-between border-b border-[#E5E7EB] px-4">
                    <div>
                        <h1 className="text-lg font-semibold text-[#111827]">Agent IA</h1>
                        <p className="text-xs text-[#6B7280]">Chat mobile dédié</p>
                    </div>
                    <button type="button" onClick={resetConversation} className="inline-flex h-10 w-10 items-center justify-center rounded-full hover:bg-[#F5F5F7]" title="Réinitialiser la conversation">
                        <RotateCcw className="h-5 w-5" />
                    </button>
                </header>

                <div ref={chatRef} className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4">
                    <div className="space-y-4">
                        {messages.map((message, index) => (
                            <div key={index} className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                                {message.role === "agent" && <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-black text-xs font-semibold text-white">AI</span>}
                                <div className={`max-w-[82%] rounded-[22px] px-4 py-3 text-sm leading-6 ${message.role === "user" ? "bg-black text-white" : "bg-[#F1F2F4] text-[#111827]"}`}>
                                    {message.content}
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex gap-3">
                                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-black text-xs font-semibold text-white">AI</span>
                                <div className="rounded-[22px] bg-[#F1F2F4] px-4 py-3 text-sm italic text-[#6B7280]">{t("agentThinking")}</div>
                            </div>
                        )}
                    </div>
                </div>

                <footer className="sticky bottom-0 shrink-0 border-t border-[#E5E7EB] bg-white p-3 pb-[calc(env(safe-area-inset-bottom)+12px)]">
                    <div className="mb-2 flex gap-2">
                        <input ref={fileRef} type="file" className="hidden" />
                        <input ref={imageRef} type="file" accept="image/*" className="hidden" />
                        <button type="button" onClick={() => fileRef.current?.click()} className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[#E5E7EB]"><Paperclip className="h-5 w-5" /></button>
                        <button type="button" onClick={() => imageRef.current?.click()} className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[#E5E7EB]"><FileImage className="h-5 w-5" /></button>
                        <button type="button" className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[#E5E7EB]"><Mic className="h-5 w-5" /></button>
                    </div>
                    <div className="flex items-end gap-2 rounded-[26px] border border-[#D1D5DB] bg-white p-2">
                        <textarea
                            value={input}
                            onChange={event => setInput(event.target.value)}
                            placeholder={t("agentPlaceholder")}
                            rows={1}
                            className="max-h-28 min-h-10 flex-1 resize-none bg-transparent px-2 py-2 text-[16px] outline-none"
                            onKeyDown={event => {
                                if (event.key === "Enter" && !event.shiftKey) {
                                    event.preventDefault()
                                    void send()
                                }
                            }}
                        />
                        <button type="button" onClick={() => void send()} className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-black text-white disabled:opacity-50" disabled={loading || !input.trim()}>
                            {loading ? <RefreshCw className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                        </button>
                    </div>
                </footer>
            </section>

            <section className={`absolute inset-0 flex flex-col bg-white transition-transform duration-300 ease-out ${showPreview ? "translate-x-0" : "translate-x-full"}`}>
                <header className="flex h-14 shrink-0 items-center justify-between border-b border-[#E5E7EB] px-3">
                    <button type="button" onClick={() => setShowPreview(false)} className="inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium hover:bg-[#F5F5F7]">
                        <ArrowLeft className="h-4 w-4" />
                        Retour à l&apos;Agent IA
                    </button>
                    <div className="flex items-center gap-1">
                        <button type="button" onClick={printPreview} className="inline-flex h-10 w-10 items-center justify-center rounded-full hover:bg-[#F5F5F7]" title="Imprimer"><Printer className="h-5 w-5" /></button>
                        <button type="button" onClick={() => downloadText(preview, "txt")} className="inline-flex h-10 w-10 items-center justify-center rounded-full hover:bg-[#F5F5F7]" title="Télécharger"><Download className="h-5 w-5" /></button>
                        <button type="button" className="inline-flex h-10 w-10 items-center justify-center rounded-full hover:bg-[#F5F5F7]" title="Partager"><Share2 className="h-5 w-5" /></button>
                    </div>
                </header>
                <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4">
                    <div className="prose max-w-none">
                        {preview ? <ReactMarkdown>{preview}</ReactMarkdown> : <p className="text-[#6B7280]">{t("previewEmpty")}</p>}
                    </div>
                </div>
                <footer className="shrink-0 border-t border-[#E5E7EB] bg-white p-3 pb-[calc(env(safe-area-inset-bottom)+12px)]">
                    <div className="grid grid-cols-3 gap-2">
                        <button type="button" onClick={() => downloadText(preview, "csv")} className="rounded-full border border-[#D1D5DB] px-3 py-3 text-sm">CSV</button>
                        <button type="button" onClick={() => downloadText(preview, "xls")} className="rounded-full border border-[#D1D5DB] px-3 py-3 text-sm">Excel</button>
                        <button type="button" onClick={() => setShowPreview(false)} className="rounded-full bg-black px-3 py-3 text-sm text-white">Continuer</button>
                    </div>
                </footer>
            </section>
        </div>
    )
}
