"use client"

import ReactMarkdown from 'react-markdown'
import { useTranslations } from 'next-intl'

import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { AgentPanel } from "@/components/ai-agent/agent-panel"
import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { LayoutProvider, useLayout } from "@/context/layout-context"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { LayoutDashboard, Eye } from "lucide-react"
import { FormIntelligence } from "@/components/ui/form-intelligence"

function MainLayoutContent({ children }: { children: React.ReactNode }) {
    const { isAgentPanelOpen, viewMode, setViewMode, previewContent } = useLayout()
    const t = useTranslations("layout")

    return (
        <ResizablePanelGroup direction="horizontal" className="h-screen w-full overflow-hidden font-sans">
            <FormIntelligence />
            {/* Left Panel: AI Agent - Light grey/off-white background */}
            <ResizablePanel
                defaultSize={20}
                minSize={16}
                maxSize={28}
                collapsible={true}
                collapsedSize={4}
                className={cn(
                    "min-h-0 overflow-hidden transition-all duration-300 ease-in-out bg-[#F7F8FA]",
                    !isAgentPanelOpen && "min-w-[50px] max-w-[50px]"
                )}
            >
                <AgentPanel />
            </ResizablePanel>

            <ResizableHandle withHandle className="bg-[#E5E7EB]" />

            {/* Middle Panel: Navigation/Sidebar - Pure white background */}
            <ResizablePanel defaultSize={18} minSize={14} maxSize={24} className="overflow-visible">
                <div className="relative z-40 flex h-full min-h-0 flex-col overflow-visible border-r border-[#E5E7EB] bg-white">
                    {/* Toggle Buttons Area */}
                    <div className="p-2 flex gap-1 border-b border-[#E5E7EB] bg-white">
                        <Button
                            variant={viewMode === 'dashboard' ? 'default' : 'ghost'}
                            size="sm"
                            className="flex-1 h-8 text-xs"
                            onClick={() => setViewMode('dashboard')}
                        >
                            <LayoutDashboard className="h-3 w-3 mr-1" />
                            {t("dashboard")}
                        </Button>
                        <Button
                            variant={viewMode === 'preview' ? 'default' : 'ghost'}
                            size="sm"
                            className="flex-1 h-8 text-xs"
                            onClick={() => setViewMode('preview')}
                        >
                            <Eye className="h-3 w-3 mr-1" />
                            {t("preview")}
                        </Button>
                    </div>
                    <div className="min-h-0 flex-1 overflow-visible">
                        <Sidebar isResizablePanel={true} />
                    </div>
                </div>
            </ResizablePanel>

            <ResizableHandle withHandle className="bg-[#E5E7EB]" />

            {/* Right Panel: Main Content - Very light grey background */}
            <ResizablePanel defaultSize={62} minSize={45} className="min-h-0 overflow-hidden">
                <div className="flex h-full min-h-0 flex-col overflow-hidden bg-[#F6F7F9]">
                    {viewMode === 'dashboard' ? (
                        <>
                            <Header isResizablePanel={true} />
                            <main className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 md:p-6">
                                {children}
                            </main>
                        </>
                    ) : (
                        <div className="h-full flex flex-col bg-white">
                            <div className="h-14 border-b border-[#E5E7EB] flex items-center px-4 font-semibold text-lg bg-white justify-between">
                                <span>{t("previewOutput")}</span>
                                <Button variant="ghost" size="sm" onClick={() => setViewMode('dashboard')}>{t("closePreview")}</Button>
                            </div>
                            <div className="flex-1 overflow-y-auto p-4 md:p-8">
                                {previewContent ? (
                                    <div className="prose dark:prose-invert max-w-none">
                                        <ReactMarkdown>{previewContent}</ReactMarkdown>
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-center text-[#6B7280] flex-col gap-4 h-full">
                                        <div className="p-6 border-2 border-dashed border-[#E5E7EB] rounded-lg bg-[#F6F7F9]">
                                            <Eye className="h-12 w-12 mx-auto mb-2 opacity-20" />
                                            <p>{t("previewTitle")}</p>
                                        </div>
                                        <p className="text-sm max-w-md text-center">
                                            {t("previewEmpty")}
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
