"use client"

import { useEffect, useState } from "react"
import ReactMarkdown from 'react-markdown'
import { useTranslations } from 'next-intl'
import Link from "next/link"
import { useParams, usePathname } from "next/navigation"

import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { AgentPanel } from "@/components/ai-agent/agent-panel"
import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { LayoutProvider, useLayout } from "@/context/layout-context"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Bell, Bot, Eye, Home, LayoutDashboard, Menu, Search, X } from "lucide-react"
import { FormIntelligence } from "@/components/ui/form-intelligence"
import { DashboardUxEnhancer } from "@/components/dashboard/dashboard-ux-enhancer"
import { normalizeLocale } from "@/lib/i18n"
import { LanguageSwitcher } from "@/components/layout/language-switcher"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"

function MainLayoutContent({ children }: { children: React.ReactNode }) {
    const { isAgentPanelOpen, viewMode, setViewMode, previewContent } = useLayout()
    const t = useTranslations("layout")

    return (
        <div className="fixed inset-0 h-dvh w-dvw overflow-hidden bg-[#F6F7F9] font-sans">
            <DashboardUxEnhancer />
            <div className="hidden h-full w-full lg:block">
            <ResizablePanelGroup direction="horizontal" className="h-full w-full overflow-hidden">
                <FormIntelligence />
                {/* Left Panel: AI Agent - Light grey/off-white background */}
                <ResizablePanel
                    defaultSize={20}
                    minSize={16}
                    maxSize={28}
                    collapsible={true}
                    collapsedSize={4}
                    className={cn(
                        "h-full min-h-0 overflow-hidden transition-all duration-300 ease-in-out bg-[#F7F8FA]",
                        !isAgentPanelOpen && "min-w-[50px] max-w-[50px]"
                    )}
                >
                    <AgentPanel />
                </ResizablePanel>

                <ResizableHandle withHandle className="bg-[#E5E7EB]" />

                {/* Middle Panel: Navigation/Sidebar - Pure white background */}
                <ResizablePanel defaultSize={18} minSize={14} maxSize={24} className="h-full overflow-visible">
                    <div className="relative z-40 flex h-full min-h-0 flex-col overflow-visible border-r border-[#E5E7EB] bg-white">
                        {/* Toggle Buttons Area */}
                        <div className="flex shrink-0 gap-1 border-b border-[#E5E7EB] bg-white p-2">
                            <Button
                                variant={viewMode === 'dashboard' ? 'default' : 'ghost'}
                                size="sm"
                                className="h-8 flex-1 text-xs"
                                onClick={() => setViewMode('dashboard')}
                            >
                                <LayoutDashboard className="mr-1 h-3 w-3" />
                                {t("dashboard")}
                            </Button>
                            <Button
                                variant={viewMode === 'preview' ? 'default' : 'ghost'}
                                size="sm"
                                className="h-8 flex-1 text-xs"
                                onClick={() => setViewMode('preview')}
                            >
                                <Eye className="mr-1 h-3 w-3" />
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
                <ResizablePanel defaultSize={62} minSize={45} className="h-full min-h-0 overflow-hidden">
                    <div className="flex h-full min-h-0 flex-col overflow-hidden bg-[#F6F7F9]">
                        {viewMode === 'dashboard' ? (
                            <>
                                <Header isResizablePanel={true} />
                                <main className="min-h-0 flex-1 overflow-y-auto overscroll-contain bg-[#F6F7F9] p-4 md:p-6">
                                    {children}
                                </main>
                            </>
                        ) : (
                            <div className="flex h-full min-h-0 flex-col bg-white">
                                <div className="flex h-14 shrink-0 items-center justify-between border-b border-[#E5E7EB] bg-white px-4 text-lg font-semibold">
                                    <span>{t("previewOutput")}</span>
                                    <Button variant="ghost" size="sm" onClick={() => setViewMode('dashboard')}>{t("closePreview")}</Button>
                                </div>
                                <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 md:p-8">
                                    {previewContent ? (
                                        <div className="prose dark:prose-invert max-w-none">
                                            <ReactMarkdown>{previewContent}</ReactMarkdown>
                                        </div>
                                    ) : (
                                        <div className="flex h-full flex-col items-center justify-center gap-4 text-[#6B7280]">
                                            <div className="rounded-lg border-2 border-dashed border-[#E5E7EB] bg-[#F6F7F9] p-6">
                                                <Eye className="mx-auto mb-2 h-12 w-12 opacity-20" />
                                                <p>{t("previewTitle")}</p>
                                            </div>
                                            <p className="max-w-md text-center text-sm">
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
            </div>
            <MobileDashboardShell>{children}</MobileDashboardShell>
        </div>
    )
}

function MobileDashboardShell({ children }: { children: React.ReactNode }) {
    const params = useParams()
    const pathname = usePathname()
    const locale = normalizeLocale(params.locale as string)
    const t = useTranslations("app")
    const { token, user } = useAuth()
    const [drawerOpen, setDrawerOpen] = useState(false)
    const [schoolName, setSchoolName] = useState("")

    useEffect(() => {
        if (!token || !user?.school_id) {
            setSchoolName("")
            return
        }
        setSchoolName(`Établissement #${user.school_id}`)
        let cancelled = false
        fetch(`${API_BASE_URL}/system/school-settings`, {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then(response => response.ok ? response.json() : null)
            .then(data => {
                if (!cancelled && data?.name) setSchoolName(data.name)
            })
            .catch(() => undefined)
        return () => {
            cancelled = true
        }
    }, [token, user?.school_id])

    const navItems = [
        { href: `/${locale}/dashboard`, label: "Accueil", Icon: Home },
        { href: `/${locale}/dashboard/ai-agent`, label: "Agent IA", Icon: Bot },
        { href: `/${locale}/dashboard/enterprise`, label: "Alertes", Icon: Bell },
        { href: `/${locale}/dashboard`, label: "Recherche", Icon: Search },
    ]

    const isAgentPage = pathname?.includes("/dashboard/ai-agent")

    return (
        <div className="flex h-full min-h-0 flex-col overflow-hidden bg-[#F6F7F9] lg:hidden">
            <header className="sticky top-0 z-[70] flex h-[64px] shrink-0 items-center gap-3 border-b border-[#E5E7EB] bg-white px-3">
                <button
                    type="button"
                    onClick={() => setDrawerOpen(true)}
                    className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-[#E5E7EB] bg-white text-[#111827]"
                    aria-label="Ouvrir le menu"
                >
                    <Menu className="h-5 w-5" />
                </button>
                <div className="min-w-0 flex-1">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6B7280]" />
                        <input
                            type="search"
                            placeholder={t("search")}
                            className="h-11 w-full rounded-full border border-[#D1D5DB] bg-white pl-10 pr-3 text-[16px] outline-none focus:border-black"
                        />
                    </div>
                </div>
                {schoolName && <div className="hidden max-w-[28vw] truncate text-sm font-bold text-black sm:block">{schoolName}</div>}
                <LanguageSwitcher />
            </header>

            <main className={cn(
                "min-h-0 flex-1 overflow-y-auto overflow-x-hidden overscroll-contain px-3 pb-24 pt-4",
                isAgentPage && "p-0 pb-20"
            )}>
                {children}
            </main>

            <nav className="fixed inset-x-0 bottom-0 z-[75] border-t border-[#E5E7EB] bg-white/95 px-2 pb-[env(safe-area-inset-bottom)] pt-1 shadow-[0_-12px_34px_rgba(15,23,42,0.08)] backdrop-blur">
                <div className="grid grid-cols-5 gap-1">
                    {navItems.map(({ href, label, Icon }) => {
                        const active = pathname === href || (href.includes("ai-agent") && pathname?.includes("ai-agent"))
                        return (
                            <Link
                                key={label}
                                href={href}
                                className={cn(
                                    "flex min-h-[56px] flex-col items-center justify-center rounded-2xl text-[11px] font-medium text-[#6B7280]",
                                    active && "bg-black text-white"
                                )}
                            >
                                <Icon className="mb-1 h-5 w-5" />
                                {label}
                            </Link>
                        )
                    })}
                    <button
                        type="button"
                        onClick={() => setDrawerOpen(true)}
                        className="flex min-h-[56px] flex-col items-center justify-center rounded-2xl text-[11px] font-medium text-[#6B7280]"
                    >
                        <Menu className="mb-1 h-5 w-5" />
                        Menu
                    </button>
                </div>
            </nav>

            {drawerOpen && (
                <div className="fixed inset-0 z-[1300] lg:hidden">
                    <button
                        type="button"
                        aria-label="Fermer le menu"
                        className="absolute inset-0 bg-black/45"
                        onClick={() => setDrawerOpen(false)}
                    />
                    <aside className="absolute inset-y-0 left-0 flex w-[85vw] max-w-[360px] flex-col overflow-hidden rounded-r-[28px] bg-white shadow-[24px_0_80px_rgba(15,23,42,0.25)]">
                        <div className="flex h-14 shrink-0 items-center justify-between border-b border-[#E5E7EB] px-4">
                            <span className="font-semibold text-[#111827]">Menu TeducAI</span>
                            <button type="button" onClick={() => setDrawerOpen(false)} className="rounded-full p-2 hover:bg-[#F5F5F7]">
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
                            <Sidebar forceVisible isResizablePanel onNavigate={() => setDrawerOpen(false)} />
                        </div>
                    </aside>
                </div>
            )}
        </div>
    )
}

export function MainLayout({ children }: { children: React.ReactNode }) {
    return (
        <LayoutProvider>
            <MainLayoutContent>{children}</MainLayoutContent>
        </LayoutProvider>
    )
}
