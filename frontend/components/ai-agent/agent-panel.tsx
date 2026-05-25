"use client"

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Mic, Paperclip, Send, PanelLeftClose, PanelLeftOpen, BookOpen } from "lucide-react"
import { useLayout } from "@/context/layout-context"
import { useState, useRef, useEffect } from "react"
import { API_BASE_URL } from "@/lib/config"

export function AgentPanel() {
    const { isAgentPanelOpen, toggleAgentPanel, aiStatus, setAiStatus, agentAction, setAgentAction, setViewMode, setPreviewContent } = useLayout()
    const [inputValue, setInputValue] = useState("")
    const [messages, setMessages] = useState<{ role: 'user' | 'agent', content: string }[]>([
        { role: 'agent', content: "Hello! I am your AI assistant. I can help you manage students, create courses, or research information. How can I help you today?" }
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
        setAgentAction("Processing...")

        try {
            // Create a timeout for the fetch
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout


            // IMPORTANT: No trailing slash on the URL to avoid 307 redirects or 404s depending on backend config
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMsg }),
                signal: controller.signal
            })
            clearTimeout(timeoutId);


            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server Error: ${response.status} ${errorText}`);
            }

            const data = await response.json()

            setAiStatus("idle")
            setAgentAction(null)

            if (data.type === 'content') {
                setMessages(prev => [...prev, { role: 'agent', content: data.message }])
                setPreviewContent(data.data) // Set the markdown/data content
                setViewMode("preview")
            } else {
                setMessages(prev => [...prev, { role: 'agent', content: data.message }])
            }

        } catch (error: unknown) {
            console.error("AI Error:", error)
            setAiStatus("idle")
            setAgentAction("Error")

            // Detailed error message for the user
            let errorMessage = "Sorry, I encountered an error communicating with the server.";
            const errorName = error instanceof Error ? error.name : undefined
            const errorText = error instanceof Error ? error.message : String(error)
            if (errorName === 'AbortError') {
                errorMessage = "Request timed out. The server took too long to respond.";
            } else if (errorText) {
                errorMessage = `Error: ${errorText}`;
            }

            setMessages(prev => [...prev, { role: 'agent', content: errorMessage }])
        }
    }

    if (!isAgentPanelOpen) {
        return (
            <div className="h-full flex flex-col items-center py-4 gap-4">
                <Button variant="ghost" size="icon" onClick={toggleAgentPanel}>
                    <PanelLeftOpen className="h-4 w-4" />
                </Button>
            </div>
        )
    }

    return (
        <div className="flex h-full flex-col">
            <div className="flex h-[60px] items-center justify-between border-b border-[#E5E7EB] px-4">
                <div className="flex items-center gap-2 font-semibold">
                    {/* Logo */}
                    <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
                        <BookOpen className="h-5 w-5" />
                    </div>

                    <div className="flex flex-col">
                        <span className="text-sm leading-none">AI Agent</span>
                        {agentAction && (
                            <span className="text-[10px] text-muted-foreground animate-pulse">{agentAction}</span>
                        )}
                    </div>
                </div>
                <Button variant="ghost" size="icon" onClick={toggleAgentPanel} className="h-8 w-8">
                    <PanelLeftClose className="h-4 w-4" />
                </Button>
            </div>

            <div className="flex-1 p-4 flex flex-col gap-4 overflow-hidden">
                <ScrollArea className="flex-1 bg-background rounded-lg border p-4 shadow-sm" ref={scrollRef}>
                    <div className="space-y-4">
                        {messages.map((msg, i) => (
                            <div key={i} className="flex gap-3">
                                <div className={`h-8 w-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs ${msg.role === 'agent' ? 'bg-primary text-primary-foreground' : 'bg-muted-foreground text-secondary'
                                    }`}>
                                    {msg.role === 'agent' ? 'AI' : 'You'}
                                </div>
                                <div className="bg-[#EDEFF2] p-3 rounded-lg text-sm whitespace-pre-wrap text-[#111827]">
                                    {msg.content}
                                </div>
                            </div>
                        ))}
                        {aiStatus === 'working' && (
                            <div className="flex gap-3">
                                <div className="h-8 w-8 rounded-full bg-primary flex-shrink-0 flex items-center justify-center text-primary-foreground text-xs">AI</div>
                                <div className="bg-[#EDEFF2] p-3 rounded-lg text-sm italic text-[#6B7280] flex items-center gap-2">
                                    <span className="animate-pulse">Thinking...</span>
                                </div>
                            </div>
                        )}
                    </div>
                </ScrollArea>

                <div className="bg-background border rounded-lg p-2">
                    <div className="flex gap-2 mb-2">
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Paperclip className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Mic className="h-4 w-4" />
                        </Button>
                    </div>
                    <div className="flex gap-2">
                        <input
                            className="flex-1 bg-transparent border-none text-sm focus:outline-none text-[#111827] placeholder:text-[#6B7280]"
                            placeholder="What would you like to change?"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                        />
                        <Button size="icon" className="h-8 w-8" onClick={handleSendMessage}>
                            <Send className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    )
}
