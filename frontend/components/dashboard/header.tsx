"use client"

import { useCallback, useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { Bell, Moon, Search, ShoppingBasket, Sun, Trash2 } from "lucide-react"
import { useParams, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { LanguageSwitcher } from "@/components/layout/language-switcher"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { useTheme } from "@/contexts/theme-context"
import { normalizeLocale } from "@/lib/i18n"
import { ContextSelector } from "@/components/dashboard/context-selector"

interface HeaderProps {
    isResizablePanel?: boolean;
}

export function Header({ isResizablePanel = false }: HeaderProps) {
    const t = useTranslations("app")
    const { token } = useAuth()
    const { effectiveTheme, toggleTheme } = useTheme()
    const params = useParams()
    const router = useRouter()
    const locale = normalizeLocale(params.locale as string)
    const [notificationsOpen, setNotificationsOpen] = useState(false)
    const [cartOpen, setCartOpen] = useState(false)
    const [notifications, setNotifications] = useState<Array<{ id: number; subject?: string; message: string; created_at?: string; read_at?: string; event_type?: string; source_type?: string; source_id?: number }>>([])
    const [actionBusyId, setActionBusyId] = useState<number | null>(null)
    const [unreadCount, setUnreadCount] = useState(0)
    const [cart, setCart] = useState<{ items: Array<{ id: number; title: string; quantity: number; unit_amount: number; currency: string; line_total: number }>; total: number; currency: string }>({ items: [], total: 0, currency: "FCFA" })

    const loadTopbarData = useCallback(() => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        fetch(`${API_BASE_URL}/account/notifications`, { headers })
            .then(response => response.ok ? response.json() : [])
            .then(data => {
                const rows = Array.isArray(data) ? data : []
                setNotifications(rows)
                setUnreadCount(rows.filter(item => !item.read_at).length)
            })
            .catch(() => undefined)
        fetch(`${API_BASE_URL}/account/cart`, { headers })
            .then(response => response.ok ? response.json() : null)
            .then(data => data && setCart(data))
            .catch(() => undefined)
    }, [token])

    useEffect(() => {
        loadTopbarData()
        if (!token) return
        const timer = window.setInterval(loadTopbarData, 60000)
        return () => window.clearInterval(timer)
    }, [loadTopbarData, token])

    const updateQuantity = async (itemId: number, quantity: number) => {
        if (!token || quantity < 1) return
        await fetch(`${API_BASE_URL}/account/cart/items/${itemId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ quantity }),
        })
        loadTopbarData()
    }

    const removeCartItem = async (itemId: number) => {
        if (!token) return
        await fetch(`${API_BASE_URL}/account/cart/items/${itemId}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
        })
        loadTopbarData()
    }

    const markNotificationRead = async (notificationId: number) => {
        if (!token) return
        await fetch(`${API_BASE_URL}/account/notifications/${notificationId}/read`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
        })
        loadTopbarData()
    }

    // One-tap actions: some notification types carry an inline action for parents.
    const justifyAbsence = async (notification: { id: number; source_id?: number }) => {
        if (!token || !notification.source_id) return
        setActionBusyId(notification.id)
        try {
            const response = await fetch(`${API_BASE_URL}/automations/absence/${notification.source_id}/justify`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
            })
            if (response.ok) await markNotificationRead(notification.id)
        } finally {
            setActionBusyId(null)
        }
    }

    const notificationAction = (item: { event_type?: string; source_type?: string; source_id?: number; read_at?: string }) => {
        if (item.event_type === "absence.followup" && item.source_type === "attendance" && item.source_id && !item.read_at) return "justify"
        if (item.event_type?.startsWith("fee.reminder") || item.event_type === "parent.digest") return "pay"
        return null
    }

    return (
        <header className={cn(
            "sticky top-0 z-30 flex h-14 shrink-0 items-center gap-4 border-b border-[#E5E7EB] bg-white px-4 lg:h-[60px] lg:px-6 dark:border-[#3a4248] dark:bg-[#1f2427]",
            !isResizablePanel && "fixed top-0 right-0 left-0 md:left-64 z-20",
            isResizablePanel && "w-full"
        )}>
            <div className="flex min-w-0 flex-1 items-center gap-4">
                <form className="min-w-[180px] flex-1 md:max-w-sm">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <input
                            type="search"
                            placeholder={t("search")}
                            className="w-full appearance-none rounded-full border border-input bg-background px-3 py-1.5 pl-8 text-sm shadow-none ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-[#444c54] dark:bg-[#1b2024] dark:text-[#f4f7fb] dark:placeholder:text-[#9aa5b1]"
                        />
                    </div>
                </form>
                <ContextSelector />
            </div>
            <div className="relative">
                <button type="button" onClick={() => { setNotificationsOpen(prev => !prev); setCartOpen(false) }} className="relative flex h-10 w-10 items-center justify-center rounded-full text-[#555] transition hover:bg-[#F5F5F7] dark:text-white dark:hover:bg-[#2b3136]" aria-label={t("notifications")} aria-expanded={notificationsOpen}>
                    <Bell className="h-5 w-5" />
                    {unreadCount > 0 && <span className="absolute -right-0.5 -top-1 rounded-full bg-[#0A84FF] px-1.5 py-0.5 text-[11px] font-bold text-white">{unreadCount}</span>}
                </button>
                {notificationsOpen && (
                    <div className="absolute right-0 top-12 z-[1200] w-[340px] rounded-[22px] border border-[#E5E7EB] bg-white p-3 shadow-[0_24px_80px_rgba(15,23,42,0.22)] dark:border-[#3b4248] dark:bg-[#202528]">
                        <h3 className="px-2 pb-2 text-base font-semibold text-[#111827] dark:text-white">{t("notifications")}</h3>
                        <div className="max-h-[360px] space-y-2 overflow-y-auto">
                            {notifications.length ? notifications.map(item => (
                                <div key={item.id} className={cn("rounded-2xl p-3 text-left text-sm transition", item.read_at ? "bg-[#F6F7F9] dark:bg-[#2a3035]" : "bg-[#EAF4FF] dark:bg-[#243545]")}>
                                    <button type="button" onClick={() => void markNotificationRead(item.id)} className="block w-full text-left">
                                        <p className="font-semibold">{item.subject || t("notification")}</p>
                                        <p className="mt-1 text-[#6B7280] dark:text-[#b9c2cd]">{item.message}</p>
                                    </button>
                                    {notificationAction(item) === "justify" && (
                                        <button type="button" disabled={actionBusyId !== null} onClick={() => void justifyAbsence(item)} className="mt-2 rounded-full bg-black px-3 py-1 text-xs font-medium text-white hover:bg-black/90 disabled:opacity-50 dark:bg-white dark:text-black">
                                            {actionBusyId === item.id ? "…" : t("justifyAbsence")}
                                        </button>
                                    )}
                                    {notificationAction(item) === "pay" && (
                                        <button type="button" onClick={() => { setNotificationsOpen(false); router.push(`/${locale}/dashboard/finance`) }} className="mt-2 rounded-full bg-black px-3 py-1 text-xs font-medium text-white hover:bg-black/90 dark:bg-white dark:text-black">
                                            {t("payFee")}
                                        </button>
                                    )}
                                </div>
                            )) : <p className="px-2 py-6 text-center text-sm text-[#6B7280]">{t("noNotifications")}</p>}
                        </div>
                    </div>
                )}
            </div>
            <button type="button" onClick={toggleTheme} className="relative flex h-9 w-[76px] items-center rounded-full border border-[#D1D5DB] bg-white px-1 transition dark:border-[#3b4248] dark:bg-[#2a3035]" aria-label={t("themeToggle")} title={t("themeToggle")}>
                <span className={cn("absolute left-2 text-[#555] transition dark:text-white", effectiveTheme === "dark" ? "opacity-100" : "opacity-0")}><Sun className="h-4 w-4" /></span>
                <span className={cn("absolute right-2 text-[#555] transition dark:text-white", effectiveTheme === "dark" ? "opacity-0" : "opacity-100")}><Moon className="h-4 w-4" /></span>
                <span className={cn("relative z-10 flex h-7 w-7 items-center justify-center rounded-full transition", effectiveTheme === "dark" ? "translate-x-9 bg-white text-black" : "translate-x-0 bg-[#666] text-white")}>
                    {effectiveTheme === "dark" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
                </span>
            </button>
            <div className="relative">
                <button type="button" onClick={() => { setCartOpen(prev => !prev); setNotificationsOpen(false) }} className="relative flex h-10 w-10 items-center justify-center rounded-full text-[#555] transition hover:bg-[#F5F5F7] dark:text-white dark:hover:bg-[#2b3136]" aria-label={t("cart")} aria-expanded={cartOpen}>
                    <ShoppingBasket className="h-5 w-5" />
                    {cart.items.length > 0 && <span className="absolute -right-0.5 -top-1 rounded-full bg-black px-1.5 py-0.5 text-[11px] font-bold text-white dark:bg-white dark:text-black">{cart.items.length}</span>}
                </button>
                {cartOpen && (
                    <div className="absolute right-0 top-12 z-[1200] w-[380px] rounded-[22px] border border-[#E5E7EB] bg-white p-4 shadow-[0_24px_80px_rgba(15,23,42,0.22)] dark:border-[#3b4248] dark:bg-[#202528]">
                        <h3 className="text-base font-semibold text-[#111827] dark:text-white">{t("cart")}</h3>
                        <div className="mt-3 max-h-[360px] space-y-2 overflow-y-auto">
                            {cart.items.length ? cart.items.map(item => (
                                <div key={item.id} className="rounded-2xl bg-[#F6F7F9] p-3 dark:bg-[#2a3035]">
                                    <div className="flex items-start justify-between gap-3">
                                        <div>
                                            <p className="font-semibold">{item.title}</p>
                                            <p className="text-sm text-[#6B7280] dark:text-[#b9c2cd]">{item.line_total.toLocaleString()} {item.currency}</p>
                                        </div>
                                        <button type="button" onClick={() => removeCartItem(item.id)} className="rounded-full p-2 hover:bg-white/70 dark:hover:bg-black/20" aria-label={t("remove")} title={t("remove")}><Trash2 className="h-4 w-4" /></button>
                                    </div>
                                    <div className="mt-2 flex items-center gap-2">
                                        <button type="button" onClick={() => updateQuantity(item.id, item.quantity - 1)} className="h-8 w-8 rounded-full border">-</button>
                                        <span className="w-8 text-center">{item.quantity}</span>
                                        <button type="button" onClick={() => updateQuantity(item.id, item.quantity + 1)} className="h-8 w-8 rounded-full border">+</button>
                                    </div>
                                </div>
                            )) : <p className="py-6 text-center text-sm text-[#6B7280]">{t("emptyCart")}</p>}
                        </div>
                        <div className="mt-4 flex items-center justify-between border-t border-[#E5E7EB] pt-3 dark:border-[#3b4248]">
                            <span className="font-semibold">{t("total")}</span>
                            <span className="font-bold">{cart.total.toLocaleString()} {cart.currency}</span>
                        </div>
                        <button type="button" disabled={!cart.items.length} onClick={() => router.push(`/${locale}/dashboard/checkout`)} className="mt-3 w-full rounded-full bg-black px-4 py-3 font-semibold text-white disabled:opacity-50 dark:bg-white dark:text-black">{t("checkout")}</button>
                    </div>
                )}
            </div>
            <LanguageSwitcher />
        </header>
    )
}
