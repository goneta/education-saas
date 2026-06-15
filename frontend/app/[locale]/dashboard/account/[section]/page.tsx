"use client"

import { useEffect, useMemo, useState } from "react"
import type { ElementType } from "react"
import { useParams } from "next/navigation"
import { Bell, CreditCard, Lock, Receipt, RefreshCw, Share2, ShieldCheck, UserCircle, Users, WalletCards } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { useTheme } from "@/contexts/theme-context"

const sectionCopy: Record<string, { title: string; description: string; icon: ElementType }> = {
    overview: { title: "Account Overview", description: "Vue complète de votre compte, rôle, établissement et accès actifs.", icon: UserCircle },
    renewals: { title: "Manage Renewals", description: "Suivez les renouvellements, plans et prochaines échéances.", icon: RefreshCw },
    security: { title: "Security Details", description: "Contrôlez MFA, statut du compte et paramètres de sécurité.", icon: Lock },
    sessions: { title: "Active Sessions", description: "Consultez les sessions actives et l'activité récente.", icon: ShieldCheck },
    contact: { title: "Contact Details", description: "Gérez les informations de contact utilisées par TeducAI.", icon: UserCircle },
    "payment-methods": { title: "Payment Methods", description: "Configurez Stripe, Djamo, CinetPay et Mobile Money.", icon: CreditCard },
    credit: { title: "Account Credit", description: "Consultez vos crédits IA, soldes et transactions.", icon: WalletCards },
    invoices: { title: "Invoices", description: "Retrouvez vos factures, reçus et paiements plateforme/établissement.", icon: Receipt },
    preferences: { title: "Account Preferences", description: "Choisissez le thème, les préférences d'aide et la langue.", icon: UserCircle },
    "email-notifications": { title: "Email Notifications", description: "Activez ou désactivez les notifications email.", icon: Bell },
    "team-members": { title: "Team Members", description: "Consultez et gérez les membres de votre équipe selon permissions.", icon: Users },
    refer: { title: "Refer a Friend", description: "Partagez TeducAI avec un établissement ou un collègue.", icon: Share2 },
}

type ThemeMode = "light" | "dark" | "system"

type UserPreferences = {
    theme?: ThemeMode
    email_notifications_enabled?: boolean
}

type PaymentRow = {
    id: number
    reference: string
    payment_type?: string
    amount?: number
    currency?: string
    status?: string
}

type NotificationRow = {
    id: number
}

export default function AccountSectionPage() {
    const params = useParams()
    const section = String(params.section || "overview")
    const copy = sectionCopy[section] || sectionCopy.overview
    const Icon = copy.icon
    const { token, user } = useAuth()
    const { theme, setTheme } = useTheme()
    const [preferences, setPreferences] = useState<UserPreferences | null>(null)
    const [platformPayments, setPlatformPayments] = useState<PaymentRow[]>([])
    const [schoolPayments, setSchoolPayments] = useState<PaymentRow[]>([])
    const [notifications, setNotifications] = useState<NotificationRow[]>([])

    useEffect(() => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        Promise.all([
            fetch(`${API_BASE_URL}/account/preferences`, { headers }).then(r => r.ok ? r.json() : null),
            fetch(`${API_BASE_URL}/platform/ai/payments`, { headers }).then(r => r.ok ? r.json() : []),
            fetch(`${API_BASE_URL}/school/payments`, { headers }).then(r => r.ok ? r.json() : []),
            fetch(`${API_BASE_URL}/account/notifications`, { headers }).then(r => r.ok ? r.json() : []),
        ]).then(([prefs, platform, school, notif]) => {
            setPreferences(prefs)
            setPlatformPayments(Array.isArray(platform) ? platform : [])
            setSchoolPayments(Array.isArray(school) ? school : [])
            setNotifications(Array.isArray(notif) ? notif : [])
        }).catch(() => undefined)
    }, [token])

    const stats = useMemo(() => [
        { label: "Rôle", value: user?.role || "-" },
        { label: "Paiements", value: String(platformPayments.length + schoolPayments.length) },
        { label: "Notifications", value: String(notifications.length) },
    ], [user?.role, platformPayments.length, schoolPayments.length, notifications.length])

    const savePreferences = async (updates: Record<string, unknown>) => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/account/preferences`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(updates),
        })
        if (res.ok) setPreferences(await res.json())
    }

    return (
        <div className="apple-page">
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <div className="flex items-center gap-3">
                        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-black text-white dark:bg-white dark:text-black"><Icon className="h-6 w-6" /></span>
                        <h1 className="apple-page-title">{copy.title}</h1>
                    </div>
                    <p className="apple-page-description">{copy.description}</p>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                {stats.map(stat => (
                    <section key={stat.label} className="rounded-[24px] border border-[#E5E7EB] bg-white p-5 shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                        <p className="text-sm text-[#6B7280]">{stat.label}</p>
                        <p className="mt-2 text-2xl font-semibold">{stat.value}</p>
                    </section>
                ))}
            </div>

            <section className="rounded-[28px] border border-[#E5E7EB] bg-white p-6 shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                {section === "preferences" || section === "email-notifications" ? (
                    <div className="grid gap-4 md:grid-cols-2">
                        <label className="grid gap-2 text-sm font-medium">
                            Thème
                            <select className="apple-select" value={theme} onChange={event => { setTheme(event.target.value as ThemeMode); void savePreferences({ theme: event.target.value }) }}>
                                <option value="light">Light Mode</option>
                                <option value="dark">Dark Mode</option>
                                <option value="system">Système</option>
                            </select>
                        </label>
                        <label className="grid gap-2 text-sm font-medium">
                            Notifications email
                            <select className="apple-select" value={preferences?.email_notifications_enabled === false ? "off" : "on"} onChange={event => void savePreferences({ email_notifications_enabled: event.target.value === "on" })}>
                                <option value="on">Activées</option>
                                <option value="off">Désactivées</option>
                            </select>
                        </label>
                    </div>
                ) : section === "invoices" || section === "payment-methods" || section === "renewals" ? (
                    <div className="overflow-x-auto">
                        <table className="apple-table">
                            <thead><tr><th>Référence</th><th>Type</th><th>Montant</th><th>Statut</th></tr></thead>
                            <tbody>
                                {[...platformPayments, ...schoolPayments].map(row => (
                                    <tr key={`${row.reference}-${row.id}`}><td>{row.reference}</td><td>{row.payment_type}</td><td>{row.amount?.toLocaleString()} {row.currency}</td><td>{row.status}</td></tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2">
                        <Info label="Nom" value={user?.full_name || "-"} />
                        <Info label="Email" value={user?.email || "-"} />
                        <Info label="ID utilisateur" value={String(user?.id || "-")} />
                        <Info label="Établissement" value={String(user?.school_id || "Plateforme")} />
                    </div>
                )}
            </section>
        </div>
    )
}

function Info({ label, value }: { label: string; value: string }) {
    return <div className="rounded-2xl bg-[#F6F7F9] p-4 dark:bg-[#2a3035]"><p className="text-sm text-[#6B7280]">{label}</p><p className="mt-1 font-semibold">{value}</p></div>
}
