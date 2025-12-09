"use client"

import ReactMarkdown from 'react-markdown'

import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { AgentPanel } from "@/components/ai-agent/agent-panel"
import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { LayoutProvider, useLayout } from "@/context/layout-context"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { LayoutDashboard, Eye } from "lucide-react"

function MainLayoutContent({ children }: { children: React.ReactNode }) {
    const { isAgentPanelOpen, viewMode, setViewMode, previewContent } = useLayout()

    return (
        <ResizablePanelGroup direction="horizontal" className="min-h-screen w-full rounded-lg border">
            {/* Left Panel: AI Agent */}
            <ResizablePanel
                defaultSize={20}
                minSize={15}
                maxSize={30}
                collapsible={true}
                collapsedSize={4}
                // We control the size via the context state in a real app ideally, 
                // but for now we let the panel handle resize and we just react to state for rendering content
                className={cn(
                    "transition-all duration-300 ease-in-out",
                    !isAgentPanelOpen && "min-w-[50px] max-w-[50px]"
                )}
            >
                <AgentPanel />
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Middle Panel: Navigation/Sidebar */}
            <ResizablePanel defaultSize={15} minSize={12} maxSize={20}>
                <div className="h-full border-r bg-muted/40 flex flex-col">
                    {/* Toggle Buttons Area */}
                    <div className="p-2 flex gap-1 border-b bg-background">
                        <Button
                            variant={viewMode === 'dashboard' ? 'default' : 'ghost'}
                            size="sm"
                            className="flex-1 h-8 text-xs"
                            onClick={() => setViewMode('dashboard')}
                        >
                            <LayoutDashboard className="h-3 w-3 mr-1" />
                            Dash
                        </Button>
                        <Button
                            variant={viewMode === 'preview' ? 'default' : 'ghost'}
                            size="sm"
                            className="flex-1 h-8 text-xs"
                            onClick={() => setViewMode('preview')}
                        >
                            <Eye className="h-3 w-3 mr-1" />
                            Prev
                        </Button>
                    </div>
                    <div className="flex-1 overflow-hidden">
                        <Sidebar isResizablePanel={true} />
                    </div>
                </div>
            </ResizablePanel>

            <ResizableHandle withHandle />

            {/* Right Panel: Main Content */}
            <ResizablePanel defaultSize={65}>
                <div className="flex flex-col h-full overflow-hidden">
                    {viewMode === 'dashboard' ? (
                        <>
                            <Header isResizablePanel={true} />
                            <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-muted/20">
                                {children}
                            </main>
                        </>
                    ) : (
                        <div className="h-full flex flex-col bg-background">
                            <div className="h-14 border-b flex items-center px-4 font-semibold text-lg bg-muted/40 justify-between">
                                <span>Preview Output</span>
                                <Button variant="ghost" size="sm" onClick={() => setViewMode('dashboard')}>Close Preview</Button>
                            </div>
                            <div className="flex-1 overflow-y-auto p-4 md:p-8">
                                {previewContent ? (
                                    <div className="prose dark:prose-invert max-w-none">
                                        <ReactMarkdown>{previewContent}</ReactMarkdown>
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-center text-muted-foreground flex-col gap-4 h-full">
                                        <div className="p-6 border-2 border-dashed rounded-lg bg-muted/20">
                                            <Eye className="h-12 w-12 mx-auto mb-2 opacity-20" />
                                            <p>AI Generated Content Preview</p>
                                        </div>
                                        <p className="text-sm max-w-md text-center">
                                            Use the AI Agent to generate courses, reports, or lists. The content will appear here.
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </ResizablePanel>
        </ResizablePanelGroup>
    )
}

export function MainLayout({ children }: { children: React.ReactNode }) {
    return (
        <LayoutProvider>
            <MainLayoutContent>{children}</MainLayoutContent>
        </LayoutProvider>
    )
}
