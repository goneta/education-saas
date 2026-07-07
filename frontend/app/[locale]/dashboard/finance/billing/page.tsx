"use client"

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { useTranslations } from "next-intl"
import {
    AlertTriangle, BadgePercent, Bot, CreditCard, Download, FileText,
    Gauge, Landmark, Plus, ReceiptText, Send, Settings2, ShieldCheck, Sparkles, Star, Trash2, Wallet,
} from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { normalizeLocale } from "@/lib/i18n"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

type TabId =
    | "overview" | "subscription" | "paymentMethods" | "invoices" | "credits"
    | "usage" | "transactions" | "promotions" | "preferences" | "tax" | "audit"

const TABS: TabId[] = [
    "overview", "subscription", "paymentMethods", "invoices", "credits",
    "usage", "transactions", "promotions", "preferences", "tax", "audit",
]

interface Overview {
    subscription: { plan: string; plan_name: string; billing_cycle: string; amount: number; currency: string; status: string; next_renewal_at?: string | null }
    wallet: { balance_credits: number; total_purchased_credits: number; total_used_credits: number; status: string }
    auto_recharge: { enabled: boolean; threshold_credits: number; recharge_credits: number; recharge_amount: number; monthly_max_amount?: number | null }
    usage: { credits_used: number; tokens_used: number; estimated_cost: number; credits_sold: number; wallet_balance: number }
    recent_transactions: Txn[]
    currency: string
}
interface Plan { key: string; name: string; monthly: number | null; yearly: number | null; credits: number | null; storage_gb: number | null; users: number | null; schools: number | null; support: string; features: string[]; contact_sales?: boolean }
interface Invoice { id: number; number: string; date: string; description: string; plan?: string | null; credits: number; amount: number; currency: string; provider: string; status: string }
type Txn = Invoice
interface Preferences { currency: string; timezone?: string | null; invoice_language: string; email_invoices: boolean; payment_reminders: boolean; renewal_reminders: boolean; auto_renew: boolean; invoice_recipients?: string[] | null }
interface Tax { tax_type: string; tax_id?: string | null; business_number?: string | null; company_registration?: string | null; legal_name?: string | null; tax_rate: number; tax_exempt: boolean; billing_address?: Record<string, string> | null }
interface AuditRow { id: number; action: string; entity_type?: string | null; details?: Record<string, unknown> | null; ip_address?: string | null; created_at?: string | null }
interface Revenue { total_revenue: number; mrr: number; arr: number; total_schools: number; outstanding: number; failed_payments: number; revenue_by_country: { country: string; amount: number }[] }
interface PaymentMethod { id: number; method_type: string; provider: string; nickname?: string | null; holder_name?: string | null; brand?: string | null; last4?: string | null; expiry_month?: number | null; expiry_year?: number | null; is_default: boolean; expiry_state: string }

const PROVIDERS = ["CinetPay · Orange · Wave · MTN · Moov", "Djamo", "Stripe", "Visa", "Mastercard", "American Express", "PayPal", "Apple Pay", "Google Pay", "Bank transfer"]
const STATUS_STYLES: Record<string, string> = {
    active: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200",
    paid: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200",
    pending: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-200",
    pending_payment: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-200",
    failed: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-200",
    refunded: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-200",
    cancelled: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-200",
}

export default function BillingPage() {
    const t = useTranslations("billing")
    const params = useParams()
    const locale = normalizeLocale(String(params?.locale || "fr"))
    const { token, user } = useAuth()
    const isSuperAdmin = String(user?.role || "").toLowerCase() === "super_admin"

    const [tab, setTab] = useState<TabId>("overview")
    const [overview, setOverview] = useState<Overview | null>(null)
    const [plans, setPlans] = useState<Plan[]>([])
    const [invoices, setInvoices] = useState<Invoice[]>([])
    const [txns, setTxns] = useState<Txn[]>([])
    const [prefs, setPrefs] = useState<Preferences | null>(null)
    const [tax, setTax] = useState<Tax | null>(null)
    const [audit, setAudit] = useState<AuditRow[]>([])
    const [revenue, setRevenue] = useState<Revenue | null>(null)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [toast, setToast] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])
    const currency = overview?.currency || prefs?.currency || "FCFA"
    const fmtMoney = useCallback((n: number, cur = currency) => `${new Intl.NumberFormat(locale).format(Math.round(n || 0))} ${cur}`, [currency, locale])
    const fmtDate = useCallback((d?: string | null) => d ? new Date(d).toLocaleDateString(locale) : "—", [locale])

    const api = useCallback(async (path: string, init?: RequestInit) => {
        if (!headers) return null
        const res = await fetch(`${API_BASE_URL}/billing${path}`, { headers, ...init })
        if (!res.ok) { setError((await res.json().catch(() => ({}))).detail || t("error")); return null }
        setError(null)
        return res.json()
    }, [headers, t])

    const loadOverview = useCallback(async () => { const d = await api("/overview"); if (d) setOverview(d) }, [api])

    useEffect(() => { void loadOverview() }, [loadOverview])
    useEffect(() => {
        if (!headers) return
        void (async () => {
            if (tab === "subscription" && !plans.length) { const d = await api("/plans"); if (d) setPlans(d.plans) }
            if (tab === "invoices") { const d = await api("/invoices"); if (d) setInvoices(d.invoices) }
            if (tab === "transactions") { const d = await api("/transactions"); if (d) setTxns(d.transactions) }
            if (tab === "preferences" && !prefs) { const d = await api("/preferences"); if (d) setPrefs(d) }
            if (tab === "tax" && !tax) { const d = await api("/tax"); if (d) setTax(d) }
            if (tab === "audit") { const d = await api("/audit"); if (d) setAudit(d) }
            if (tab === "overview" && isSuperAdmin && !revenue) { const d = await api("/admin/revenue"); if (d) setRevenue(d) }
        })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [tab, headers])

    const flash = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2500) }

    const switchPlan = async (planKey: string, cycle: string) => {
        if (!headers) return
        setBusy(true)
        try {
            const res = await fetch(`${API_BASE_URL}/system/subscription/change`, {
                method: "POST", headers, body: JSON.stringify({ plan: planKey, billing_cycle: cycle, payment_provider: "manual" }),
            })
            if (!res.ok) { setError((await res.json().catch(() => ({}))).detail || t("error")); return }
            const data = await res.json().catch(() => ({}))
            if (data?.checkout_url) { window.location.href = data.checkout_url; return }
            flash(t("saved")); void loadOverview()
        } finally { setBusy(false) }
    }

    const downloadPdf = async (id: number, number: string) => {
        if (!token) return
        setBusy(true)
        try {
            const res = await fetch(`${API_BASE_URL}/billing/invoices/${id}/pdf`, { headers: { Authorization: `Bearer ${token}` } })
            if (!res.ok) { setError(t("error")); return }
            const blob = await res.blob()
            const url = URL.createObjectURL(blob)
            const a = document.createElement("a")
            a.href = url; a.download = `invoice-${number}.pdf`; a.click()
            URL.revokeObjectURL(url)
            setError(null)
        } finally { setBusy(false) }
    }

    const badge = (status: string) => (
        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[status] || "bg-slate-100 text-slate-600"}`}>
            {t(`status.${status}` as "status.active")}
        </span>
    )

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>

            {/* Tabs */}
            <div className="flex flex-wrap gap-1 border-b border-[#E5E7EB] dark:border-[#3b4248]">
                {TABS.map(id => (
                    <button key={id} onClick={() => setTab(id)}
                        className={`relative -mb-px rounded-t-lg px-3 py-2 text-sm font-medium transition ${tab === id ? "border-b-2 border-black text-[#111827] dark:border-white dark:text-white" : "text-[#6B7280] hover:text-[#111827] dark:hover:text-white"}`}>
                        {t(`tabs.${id}` as "tabs.overview")}
                    </button>
                ))}
            </div>

            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}
            {toast && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-[#0f1f1d] dark:text-emerald-100">{toast}</div>}

            {/* --- OVERVIEW --- */}
            {tab === "overview" && (
                <div className="space-y-4">
                    {isSuperAdmin && revenue && (
                        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
                            {[["revenue", fmtMoney(revenue.total_revenue)], ["mrr", fmtMoney(revenue.mrr)], ["arr", fmtMoney(revenue.arr)], ["totalSchools", String(revenue.total_schools)], ["outstanding", fmtMoney(revenue.outstanding)], ["failedPayments", String(revenue.failed_payments)]].map(([k, v]) => (
                                <Card key={k} className="rounded-xl border border-[#E5E7EB] dark:border-[#3b4248] dark:bg-[#202528]">
                                    <CardContent className="p-4"><p className="text-xs text-[#6B7280]">{t(`admin.${k}` as "admin.revenue")}</p><p className="mt-1 text-lg font-bold">{v}</p></CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                    <div className="grid gap-4 lg:grid-cols-2">
                        {/* Current plan */}
                        <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                            <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Sparkles className="h-4 w-4" /> {t("overview.currentPlan")}</CardTitle></CardHeader>
                            <CardContent className="space-y-3">
                                <div className="flex items-end justify-between">
                                    <div>
                                        <p className="text-2xl font-bold">{overview?.subscription.plan_name || "—"}</p>
                                        <p className="text-sm text-[#6B7280]">{overview ? `${fmtMoney(overview.subscription.amount)} · ${overview.subscription.billing_cycle === "yearly" ? t("overview.yearly") : t("overview.monthly")}` : ""}</p>
                                    </div>
                                    {overview && badge(overview.subscription.status)}
                                </div>
                                {overview?.subscription.next_renewal_at && <p className="text-xs text-[#6B7280]">{t("overview.renews")} {fmtDate(overview.subscription.next_renewal_at)}</p>}
                                <div className="flex flex-wrap gap-2 pt-1">
                                    <Button variant="outline" onClick={() => setTab("subscription")}>{t("overview.upgrade")}</Button>
                                    <Button variant="outline" onClick={() => setTab("subscription")}>{t("overview.manage")}</Button>
                                </div>
                            </CardContent>
                        </Card>
                        {/* Credit balance */}
                        <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                            <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Wallet className="h-4 w-4" /> {t("overview.creditBalance")}</CardTitle></CardHeader>
                            <CardContent className="space-y-3">
                                <p className="text-4xl font-bold tracking-tight">{new Intl.NumberFormat(locale).format(overview?.wallet.balance_credits || 0)}</p>
                                <p className="text-sm text-[#6B7280]">{t("overview.creditDesc")}</p>
                                <div className="flex flex-wrap gap-2 pt-1">
                                    <Link href={`/${locale}/dashboard/ai-credits`}><Button className="bg-black text-white hover:bg-black/90">{t("overview.addCredits")}</Button></Link>
                                    <Button variant="outline" onClick={() => setTab("usage")}>{t("overview.creditHistory")}</Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                    {/* Auto recharge */}
                    <Card className={`rounded-2xl border shadow-sm ${overview?.auto_recharge.enabled ? "border-[#E5E7EB] dark:border-[#3b4248]" : "border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-[#2a2418]"} dark:bg-[#202528]`}>
                        <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
                            <div className="flex items-start gap-3">
                                {overview?.auto_recharge.enabled ? <ShieldCheck className="mt-0.5 h-5 w-5 text-emerald-600" /> : <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-600" />}
                                <div>
                                    <p className="font-semibold">{overview?.auto_recharge.enabled ? t("overview.autoOn") : t("overview.autoOff")}</p>
                                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{overview?.auto_recharge.enabled
                                        ? `${t("overview.autoRecharge")}: +${overview.auto_recharge.recharge_credits} @ ≤ ${overview.auto_recharge.threshold_credits}`
                                        : t("overview.autoWarning")}</p>
                                </div>
                            </div>
                            <Button variant="outline" onClick={() => setTab("preferences")}>{overview?.auto_recharge.enabled ? t("overview.configure") : t("overview.enableAuto")}</Button>
                        </CardContent>
                    </Card>
                    {/* Quick access */}
                    <div>
                        <h2 className="mb-2 text-sm font-semibold text-[#6B7280]">{t("overview.quickAccess")}</h2>
                        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                            {([["paymentMethods", CreditCard], ["invoices", FileText], ["usage", Gauge], ["tax", Landmark], ["promotions", BadgePercent], ["preferences", Settings2]] as [TabId, typeof CreditCard][]).map(([id, Icon]) => (
                                <button key={id} onClick={() => setTab(id)} className="flex items-center gap-3 rounded-xl border border-[#E5E7EB] p-4 text-left transition hover:bg-[#F6F7F9] dark:border-[#3b4248] dark:hover:bg-[#2a3035]">
                                    <span className="rounded-lg bg-[#F1F3F5] p-2 dark:bg-[#2a3035]"><Icon className="h-5 w-5" /></span>
                                    <span className="font-medium">{t(`tabs.${id}` as "tabs.overview")}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                    {/* Recent activity */}
                    <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                        <CardHeader><CardTitle className="text-base">{t("overview.recentActivity")}</CardTitle></CardHeader>
                        <CardContent>
                            {overview && overview.recent_transactions.length ? (
                                <div className="divide-y divide-[#EEF0F2] dark:divide-[#2a3035]">
                                    {overview.recent_transactions.map(x => (
                                        <div key={x.id} className="flex items-center justify-between py-2 text-sm">
                                            <span>{x.description}</span>
                                            <span className="flex items-center gap-3"><span className="text-[#6B7280]">{fmtDate(x.date)}</span><span className="font-semibold">{fmtMoney(x.amount, x.currency)}</span>{badge(x.status)}</span>
                                        </div>
                                    ))}
                                </div>
                            ) : <p className="py-3 text-sm text-[#6B7280]">{t("overview.noActivity")}</p>}
                        </CardContent>
                    </Card>
                    {/* AI billing assistant */}
                    <BillingAssistant api={api} locale={locale} />
                </div>
            )}

            {/* --- SUBSCRIPTION --- */}
            {tab === "subscription" && (
                <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
                    {plans.map(p => {
                        const isCurrent = overview?.subscription.plan === p.key
                        return (
                            <Card key={p.key} className={`flex flex-col rounded-2xl border shadow-sm dark:bg-[#202528] ${isCurrent ? "border-black ring-1 ring-black dark:border-white dark:ring-white" : "border-[#E5E7EB] dark:border-[#3b4248]"}`}>
                                <CardHeader>
                                    <CardTitle className="flex items-center justify-between text-lg">{p.name}{isCurrent && <span className="rounded-full bg-black px-2 py-0.5 text-xs font-medium text-white dark:bg-white dark:text-black">{t("subscription.currentBadge")}</span>}</CardTitle>
                                    <p className="text-2xl font-bold">{p.contact_sales || p.monthly == null ? "—" : fmtMoney(p.monthly)}<span className="text-sm font-normal text-[#6B7280]">{p.contact_sales ? "" : t("subscription.perMonth")}</span></p>
                                </CardHeader>
                                <CardContent className="flex flex-1 flex-col gap-3">
                                    <ul className="space-y-1 text-sm text-[#374151] dark:text-[#c7d0da]">
                                        {p.credits != null && <li>{t("subscription.includedCredits")}: <b>{p.credits}</b></li>}
                                        {p.storage_gb != null && <li>{t("subscription.storage")}: <b>{p.storage_gb} GB</b></li>}
                                        {p.users != null && <li>{t("subscription.users")}: <b>{p.users}</b></li>}
                                        {p.schools != null && <li>{t("subscription.schools")}: <b>{p.schools}</b></li>}
                                        <li>{t("subscription.support")}: <b>{p.support.replace(/_/g, " ")}</b></li>
                                    </ul>
                                    <div className="mt-auto pt-2">
                                        {p.contact_sales ? (
                                            <Button variant="outline" className="w-full">{t("subscription.contactSales")}</Button>
                                        ) : isCurrent ? (
                                            <Button variant="outline" className="w-full" disabled>{t("subscription.currentBadge")}</Button>
                                        ) : (
                                            <Button className="w-full bg-black text-white hover:bg-black/90" disabled={busy} onClick={() => switchPlan(p.key, "monthly")}>{t("subscription.switch")}</Button>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>
                        )
                    })}
                </div>
            )}

            {/* --- PAYMENT METHODS --- */}
            {tab === "paymentMethods" && <PaymentMethodsTab api={api} locale={locale} />}

            {/* --- INVOICES --- */}
            {tab === "invoices" && (
                <BillingTable
                    rows={invoices} empty={t("invoices.empty")}
                    cols={[t("invoices.number"), t("invoices.date"), t("invoices.description"), t("invoices.amount"), t("invoices.method"), t("invoices.status"), t("invoices.actions")]}
                    render={(x: Invoice) => (
                        <tr key={x.id} className="border-b border-[#EEF0F2] last:border-0 dark:border-[#2a3035]">
                            <td className="px-4 py-3 font-mono text-xs">{x.number}</td>
                            <td className="px-4 py-3">{fmtDate(x.date)}</td>
                            <td className="px-4 py-3">{x.description}</td>
                            <td className="px-4 py-3 font-semibold">{fmtMoney(x.amount, x.currency)}</td>
                            <td className="px-4 py-3 capitalize">{x.provider}</td>
                            <td className="px-4 py-3">{badge(x.status)}</td>
                            <td className="px-4 py-3"><Button variant="outline" size="sm" disabled={busy} onClick={() => downloadPdf(x.id, x.number)}><Download className="mr-1 h-3.5 w-3.5" /> {t("invoices.download")}</Button></td>
                        </tr>
                    )}
                />
            )}

            {/* --- CREDITS --- */}
            {tab === "credits" && (
                <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader><CardTitle className="text-base">{t("credits.title")}</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-4xl font-bold">{new Intl.NumberFormat(locale).format(overview?.wallet.balance_credits || 0)}</p>
                        <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("credits.desc")}</p>
                        <Link href={`/${locale}/dashboard/ai-credits`}><Button className="bg-black text-white hover:bg-black/90"><Sparkles className="mr-1 h-4 w-4" /> {t("credits.openStore")}</Button></Link>
                    </CardContent>
                </Card>
            )}

            {/* --- USAGE --- */}
            {tab === "usage" && overview && (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {[["balance", overview.wallet.balance_credits], ["creditsUsed", overview.usage.credits_used], ["tokens", overview.usage.tokens_used], ["creditsSold", overview.usage.credits_sold], ["estimatedCost", overview.usage.estimated_cost]].map(([k, v]) => (
                        <Card key={String(k)} className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                            <CardContent className="p-5"><p className="text-xs uppercase text-[#6B7280]">{t(`usage.${k}` as "usage.balance")}</p><p className="mt-1 text-2xl font-bold">{k === "estimatedCost" ? fmtMoney(Number(v)) : new Intl.NumberFormat(locale).format(Number(v))}</p></CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* --- TRANSACTIONS --- */}
            {tab === "transactions" && (
                <div className="space-y-3">
                    <div className="flex justify-end"><Button variant="outline" size="sm" onClick={() => exportCsv(txns)}><Download className="mr-1 h-3.5 w-3.5" /> {t("transactions.export")}</Button></div>
                    <BillingTable
                        rows={txns} empty={t("transactions.empty")}
                        cols={[t("invoices.number"), t("invoices.date"), t("invoices.description"), t("invoices.amount"), t("invoices.method"), t("invoices.status")]}
                        render={(x: Txn) => (
                            <tr key={x.id} className="border-b border-[#EEF0F2] last:border-0 dark:border-[#2a3035]">
                                <td className="px-4 py-3 font-mono text-xs">{x.number}</td>
                                <td className="px-4 py-3">{fmtDate(x.date)}</td>
                                <td className="px-4 py-3">{x.description}</td>
                                <td className="px-4 py-3 font-semibold">{fmtMoney(x.amount, x.currency)}</td>
                                <td className="px-4 py-3 capitalize">{x.provider}</td>
                                <td className="px-4 py-3">{badge(x.status)}</td>
                            </tr>
                        )}
                    />
                </div>
            )}

            {/* --- PROMOTIONS --- */}
            {tab === "promotions" && <PromotionsTab api={api} onRedeemed={loadOverview} />}

            {/* --- PREFERENCES --- */}
            {tab === "preferences" && prefs && (
                <Card className="max-w-2xl rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader><CardTitle className="text-base">{t("preferences.title")}</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-4 sm:grid-cols-2">
                            <label className="text-sm">{t("preferences.currency")}<input className="apple-input mt-1 w-full" value={prefs.currency} onChange={e => setPrefs({ ...prefs, currency: e.target.value })} /></label>
                            <label className="text-sm">{t("preferences.timezone")}<input className="apple-input mt-1 w-full" value={prefs.timezone || ""} onChange={e => setPrefs({ ...prefs, timezone: e.target.value })} /></label>
                            <label className="text-sm">{t("preferences.invoiceLanguage")}
                                <select className="apple-select mt-1 w-full" value={prefs.invoice_language} onChange={e => setPrefs({ ...prefs, invoice_language: e.target.value })}>
                                    <option value="fr">Français</option><option value="en">English</option><option value="es">Español</option><option value="sw">Kiswahili</option>
                                </select>
                            </label>
                            <label className="text-sm">{t("preferences.recipients")}<input className="apple-input mt-1 w-full" value={(prefs.invoice_recipients || []).join(", ")} onChange={e => setPrefs({ ...prefs, invoice_recipients: e.target.value.split(",").map(s => s.trim()).filter(Boolean) })} /></label>
                        </div>
                        <div className="space-y-2">
                            {([["email_invoices", "emailInvoices"], ["payment_reminders", "paymentReminders"], ["renewal_reminders", "renewalReminders"], ["auto_renew", "autoRenew"]] as [keyof Preferences, string][]).map(([field, label]) => (
                                <label key={String(field)} className="flex items-center gap-2 text-sm">
                                    <input type="checkbox" checked={Boolean(prefs[field])} onChange={e => setPrefs({ ...prefs, [field]: e.target.checked } as Preferences)} />
                                    {t(`preferences.${label}` as "preferences.emailInvoices")}
                                </label>
                            ))}
                        </div>
                        <Button className="bg-black text-white hover:bg-black/90" disabled={busy} onClick={async () => { setBusy(true); const d = await api("/preferences", { method: "PUT", body: JSON.stringify(prefs) }); setBusy(false); if (d) { setPrefs(d); flash(t("saved")) } }}>{t("save")}</Button>
                    </CardContent>
                </Card>
            )}

            {/* --- TAX --- */}
            {tab === "tax" && tax && (
                <Card className="max-w-2xl rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader><CardTitle className="text-base">{t("tax.title")}</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-4 sm:grid-cols-2">
                            <label className="text-sm">{t("tax.taxType")}
                                <select className="apple-select mt-1 w-full" value={tax.tax_type} onChange={e => setTax({ ...tax, tax_type: e.target.value })}>
                                    <option value="vat">VAT</option><option value="gst">GST</option><option value="sales_tax">Sales tax</option><option value="none">—</option>
                                </select>
                            </label>
                            <label className="text-sm">{t("tax.taxId")}<input className="apple-input mt-1 w-full" value={tax.tax_id || ""} onChange={e => setTax({ ...tax, tax_id: e.target.value })} /></label>
                            <label className="text-sm">{t("tax.legalName")}<input className="apple-input mt-1 w-full" value={tax.legal_name || ""} onChange={e => setTax({ ...tax, legal_name: e.target.value })} /></label>
                            <label className="text-sm">{t("tax.businessNumber")}<input className="apple-input mt-1 w-full" value={tax.business_number || ""} onChange={e => setTax({ ...tax, business_number: e.target.value })} /></label>
                            <label className="text-sm">{t("tax.companyRegistration")}<input className="apple-input mt-1 w-full" value={tax.company_registration || ""} onChange={e => setTax({ ...tax, company_registration: e.target.value })} /></label>
                            <label className="text-sm">{t("tax.taxRate")}<input type="number" className="apple-input mt-1 w-full" value={tax.tax_rate} onChange={e => setTax({ ...tax, tax_rate: Number(e.target.value) })} /></label>
                        </div>
                        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={tax.tax_exempt} onChange={e => setTax({ ...tax, tax_exempt: e.target.checked })} /> {t("tax.taxExempt")}</label>
                        <div className="grid gap-4 sm:grid-cols-3">
                            <label className="text-sm">{t("tax.line1")}<input className="apple-input mt-1 w-full" value={tax.billing_address?.line1 || ""} onChange={e => setTax({ ...tax, billing_address: { ...(tax.billing_address || {}), line1: e.target.value } })} /></label>
                            <label className="text-sm">{t("tax.city")}<input className="apple-input mt-1 w-full" value={tax.billing_address?.city || ""} onChange={e => setTax({ ...tax, billing_address: { ...(tax.billing_address || {}), city: e.target.value } })} /></label>
                            <label className="text-sm">{t("tax.country")}<input className="apple-input mt-1 w-full" value={tax.billing_address?.country || ""} onChange={e => setTax({ ...tax, billing_address: { ...(tax.billing_address || {}), country: e.target.value } })} /></label>
                        </div>
                        <Button className="bg-black text-white hover:bg-black/90" disabled={busy} onClick={async () => { setBusy(true); const d = await api("/tax", { method: "PUT", body: JSON.stringify(tax) }); setBusy(false); if (d) { setTax(d); flash(t("saved")) } }}>{t("save")}</Button>
                    </CardContent>
                </Card>
            )}

            {/* --- AUDIT --- */}
            {tab === "audit" && (
                <BillingTable
                    rows={audit} empty={t("audit.empty")}
                    cols={[t("audit.date"), t("audit.action"), t("audit.details"), t("audit.ip")]}
                    render={(x: AuditRow) => (
                        <tr key={x.id} className="border-b border-[#EEF0F2] last:border-0 dark:border-[#2a3035]">
                            <td className="px-4 py-3">{fmtDate(x.created_at)}</td>
                            <td className="px-4 py-3 font-mono text-xs">{x.action}</td>
                            <td className="px-4 py-3 text-xs text-[#6B7280]">{x.details ? JSON.stringify(x.details) : "—"}</td>
                            <td className="px-4 py-3 text-xs">{x.ip_address || "—"}</td>
                        </tr>
                    )}
                />
            )}
        </div>
    )
}

function BillingTable<T>({ rows, cols, render, empty }: { rows: T[]; cols: string[]; render: (x: T) => ReactNode; empty: string }) {
    return (
        <Card className="overflow-hidden rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
            {rows.length === 0 ? (
                <div className="flex items-center gap-2 p-8 text-sm text-[#6B7280]"><ReceiptText className="h-5 w-5" /> {empty}</div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="border-b border-[#E5E7EB] bg-[#F8FAFC] text-xs uppercase text-[#6B7280] dark:border-[#3b4248] dark:bg-[#252b30]">
                            <tr>{cols.map(c => <th key={c} className="px-4 py-3 font-medium">{c}</th>)}</tr>
                        </thead>
                        <tbody>{rows.map(render)}</tbody>
                    </table>
                </div>
            )}
        </Card>
    )
}

function PromotionsTab({ api, onRedeemed }: { api: (p: string, i?: RequestInit) => Promise<Record<string, unknown> | null>; onRedeemed: () => void }) {
    const t = useTranslations("billing")
    const [code, setCode] = useState("")
    const [result, setResult] = useState<Record<string, unknown> | null>(null)
    const [busy, setBusy] = useState(false)

    const act = async (redeem: boolean) => {
        if (!code.trim()) return
        setBusy(true)
        const d = await api(redeem ? "/promos/redeem" : "/promos/validate", { method: "POST", body: JSON.stringify({ code, context: "any", base_amount: 0 }) })
        setBusy(false)
        if (d) { setResult(d); if (redeem && d.redeemed) onRedeemed() }
    }

    return (
        <Card className="max-w-xl rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
            <CardHeader><CardTitle className="flex items-center gap-2 text-base"><BadgePercent className="h-4 w-4" /> {t("promotions.title")}</CardTitle></CardHeader>
            <CardContent className="space-y-3">
                <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("promotions.enterCode")}</p>
                <div className="flex gap-2">
                    <input className="apple-input flex-1 uppercase" value={code} onChange={e => setCode(e.target.value)} placeholder="WELCOME100" />
                    <Button variant="outline" disabled={busy} onClick={() => act(false)}>{t("promotions.validate")}</Button>
                    <Button className="bg-black text-white hover:bg-black/90" disabled={busy} onClick={() => act(true)}>{t("promotions.apply")}</Button>
                </div>
                {result && (result.valid ? (
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-[#0f1f1d] dark:text-emerald-100">
                        {result.redeemed ? t("promotions.applied") : t("promotions.discount")}
                        {Number(result.credits) > 0 && ` · ${t("promotions.creditsGranted")}: ${Number(result.credits)}`}
                        {Number(result.discount_amount) > 0 && ` · ${t("promotions.discount")}: ${Number(result.discount_amount)}`}
                    </div>
                ) : (
                    <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">
                        {t(`promotions.reason.${String(result.reason)}` as "promotions.reason.not_found")}
                    </div>
                ))}
            </CardContent>
        </Card>
    )
}

const ASSISTANT_SUGGESTIONS = ["why_higher", "estimate_next", "cheaper_plan", "why_failed", "last_year"] as const

function BillingAssistant({ api, locale }: { api: (p: string, i?: RequestInit) => Promise<Record<string, unknown> | null>; locale: string }) {
    const t = useTranslations("billing")
    const [question, setQuestion] = useState("")
    const [answer, setAnswer] = useState<string | null>(null)
    const [busy, setBusy] = useState(false)

    const ask = async (q: string) => {
        if (!q.trim() || busy) return
        setBusy(true); setAnswer(null); setQuestion(q)
        const d = await api("/assistant", { method: "POST", body: JSON.stringify({ question: q, language: locale }) })
        setBusy(false)
        if (d) setAnswer(String(d.answer || ""))
    }

    return (
        <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base"><Bot className="h-4 w-4" /> {t("assistant.title")}</CardTitle>
                <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("assistant.subtitle")}</p>
            </CardHeader>
            <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                    {ASSISTANT_SUGGESTIONS.map(k => {
                        const label = t(`assistant.suggestions.${k}` as "assistant.suggestions.why_higher")
                        return <button key={k} disabled={busy} onClick={() => ask(label)} className="rounded-full border border-[#E5E7EB] px-3 py-1 text-xs transition hover:bg-[#F6F7F9] disabled:opacity-50 dark:border-[#3b4248] dark:hover:bg-[#2a3035]">{label}</button>
                    })}
                </div>
                <div className="flex gap-2">
                    <input className="apple-input flex-1" value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === "Enter") ask(question) }} placeholder={t("assistant.placeholder")} />
                    <Button className="bg-black text-white hover:bg-black/90" disabled={busy || !question.trim()} onClick={() => ask(question)}><Send className="mr-1 h-4 w-4" /> {t("assistant.ask")}</Button>
                </div>
                {busy && <p className="text-sm text-[#6B7280]">{t("assistant.thinking")}</p>}
                {answer && <div className="whitespace-pre-wrap rounded-xl border border-[#E5E7EB] bg-[#F8FAFC] p-3 text-sm text-[#111827] dark:border-[#3b4248] dark:bg-[#252b30] dark:text-[#eef3f8]">{answer}</div>}
                <p className="text-xs text-[#94A3B8]">{t("assistant.creditNote")}</p>
            </CardContent>
        </Card>
    )
}

const PROVIDER_OPTIONS = ["visa", "mastercard", "amex", "cinetpay", "djamo", "stripe", "paypal", "applepay", "googlepay", "bank"]

function PaymentMethodsTab({ api, locale }: { api: (p: string, i?: RequestInit) => Promise<Record<string, unknown> | null>; locale: string }) {
    const t = useTranslations("billing")
    const emptyForm = { provider: "visa", method_type: "card", nickname: "", holder_name: "", last4: "", expiry_month: "", expiry_year: "", is_default: false }
    const [methods, setMethods] = useState<PaymentMethod[]>([])
    const [adding, setAdding] = useState(false)
    const [busy, setBusy] = useState(false)
    const [form, setForm] = useState(emptyForm)

    const load = useCallback(async () => {
        const d = await api("/payment-methods")
        if (d) setMethods((d.methods as PaymentMethod[]) || [])
    }, [api])
    useEffect(() => { void load() }, [load])

    const typeLabel: Record<string, string> = { card: t("payments.typeCard"), mobile_money: t("payments.typeMobile"), bank: t("payments.typeBank"), wallet: t("payments.typeWallet") }

    const add = async () => {
        setBusy(true)
        const body = { ...form, brand: form.provider, expiry_month: form.expiry_month ? Number(form.expiry_month) : null, expiry_year: form.expiry_year ? Number(form.expiry_year) : null }
        const d = await api("/payment-methods", { method: "POST", body: JSON.stringify(body) })
        setBusy(false)
        if (d) { setAdding(false); setForm(emptyForm); void load() }
    }
    const setDefault = async (id: number) => { await api(`/payment-methods/${id}/default`, { method: "POST" }); void load() }
    const remove = async (id: number) => { if (!window.confirm(t("payments.confirmRemove"))) return; await api(`/payment-methods/${id}`, { method: "DELETE" }); void load() }

    return (
        <div className="space-y-4">
            <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-base">{t("payments.saved")}</CardTitle>
                    <Button size="sm" onClick={() => setAdding(v => !v)}><Plus className="mr-1 h-4 w-4" /> {t("payments.add")}</Button>
                </CardHeader>
                <CardContent className="space-y-3">
                    {adding && (
                        <div className="space-y-3 rounded-xl border border-[#E5E7EB] p-4 dark:border-[#3b4248]">
                            <p className="text-sm font-semibold">{t("payments.addTitle")}</p>
                            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                                <label className="text-sm">{t("payments.provider")}
                                    <select className="apple-select mt-1 w-full" value={form.provider} onChange={e => setForm({ ...form, provider: e.target.value })}>
                                        {PROVIDER_OPTIONS.map(p => <option key={p} value={p} className="capitalize">{p}</option>)}
                                    </select>
                                </label>
                                <label className="text-sm">{t("payments.methodType")}
                                    <select className="apple-select mt-1 w-full" value={form.method_type} onChange={e => setForm({ ...form, method_type: e.target.value })}>
                                        <option value="card">{t("payments.typeCard")}</option>
                                        <option value="mobile_money">{t("payments.typeMobile")}</option>
                                        <option value="bank">{t("payments.typeBank")}</option>
                                        <option value="wallet">{t("payments.typeWallet")}</option>
                                    </select>
                                </label>
                                <label className="text-sm">{t("payments.nickname")}<input className="apple-input mt-1 w-full" value={form.nickname} onChange={e => setForm({ ...form, nickname: e.target.value })} /></label>
                                <label className="text-sm">{t("payments.holder")}<input className="apple-input mt-1 w-full" value={form.holder_name} onChange={e => setForm({ ...form, holder_name: e.target.value })} /></label>
                                <label className="text-sm">{t("payments.last4")}<input className="apple-input mt-1 w-full" maxLength={4} inputMode="numeric" value={form.last4} onChange={e => setForm({ ...form, last4: e.target.value.replace(/\D/g, "").slice(0, 4) })} /></label>
                                <div className="grid grid-cols-2 gap-2">
                                    <label className="text-sm">{t("payments.expMonth")}<input className="apple-input mt-1 w-full" inputMode="numeric" value={form.expiry_month} onChange={e => setForm({ ...form, expiry_month: e.target.value.replace(/\D/g, "").slice(0, 2) })} /></label>
                                    <label className="text-sm">{t("payments.expYear")}<input className="apple-input mt-1 w-full" inputMode="numeric" value={form.expiry_year} onChange={e => setForm({ ...form, expiry_year: e.target.value.replace(/\D/g, "").slice(0, 4) })} /></label>
                                </div>
                            </div>
                            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_default} onChange={e => setForm({ ...form, is_default: e.target.checked })} /> {t("payments.setDefault")}</label>
                            <p className="text-xs text-[#6B7280]">{t("payments.secureNote")}</p>
                            <div className="flex gap-2">
                                <Button variant="outline" onClick={() => { setAdding(false); setForm(emptyForm) }}>{t("cancel")}</Button>
                                <Button className="bg-black text-white hover:bg-black/90" disabled={busy || !form.provider} onClick={add}>{t("payments.save")}</Button>
                            </div>
                        </div>
                    )}

                    {methods.length === 0 && !adding ? (
                        <p className="py-4 text-sm text-[#6B7280]">{t("payments.noMethods")}</p>
                    ) : methods.map(m => (
                        <div key={m.id} className="flex flex-col gap-2 rounded-xl border border-[#E5E7EB] p-3 sm:flex-row sm:items-center sm:justify-between dark:border-[#3b4248]">
                            <div className="flex items-center gap-3">
                                <span className="rounded-lg bg-[#F1F3F5] p-2 dark:bg-[#2a3035]"><CreditCard className="h-5 w-5" /></span>
                                <div>
                                    <p className="font-medium capitalize">{m.nickname || m.brand || m.provider}{m.last4 && <span className="ml-2 font-mono text-sm text-[#6B7280]">•••• {m.last4}</span>}</p>
                                    <p className="text-xs text-[#6B7280]">
                                        {typeLabel[m.method_type] || m.method_type}
                                        {m.expiry_month && m.expiry_year ? ` · ${String(m.expiry_month).padStart(2, "0")}/${m.expiry_year}` : ""}
                                        {m.is_default && <span className="ml-2 rounded-full bg-black px-2 py-0.5 text-[10px] font-medium text-white dark:bg-white dark:text-black">{t("payments.default")}</span>}
                                        {m.expiry_state === "expired" && <span className="ml-2 rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-medium text-red-700">{t("payments.expired")}</span>}
                                        {m.expiry_state === "expiring_soon" && <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700">{t("payments.expiringSoon")}</span>}
                                    </p>
                                </div>
                            </div>
                            <div className="flex gap-1">
                                {!m.is_default && <Button variant="outline" size="sm" onClick={() => setDefault(m.id)}><Star className="mr-1 h-3.5 w-3.5" /> {t("payments.setDefault")}</Button>}
                                <Button variant="outline" size="sm" onClick={() => remove(m.id)}><Trash2 className="h-3.5 w-3.5" /></Button>
                            </div>
                        </div>
                    ))}
                </CardContent>
            </Card>

            <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardContent className="space-y-3 p-5">
                    <p className="text-xs font-semibold uppercase text-[#6B7280]">{t("payments.supported")}</p>
                    <div className="flex flex-wrap gap-2">{PROVIDERS.map(p => <span key={p} className="rounded-lg border border-[#E5E7EB] px-2.5 py-1 text-xs dark:border-[#3b4248]">{p}</span>)}</div>
                    <Link href={`/${locale}/dashboard/account/payment-methods`}><Button variant="outline" size="sm"><CreditCard className="mr-1 h-4 w-4" /> {t("payments.manageInAccount")}</Button></Link>
                </CardContent>
            </Card>
        </div>
    )
}

function exportCsv(rows: Txn[]) {
    const header = ["number", "date", "description", "amount", "currency", "provider", "status"]
    const lines = [header.join(",")].concat(rows.map(r => [r.number, r.date, `"${r.description}"`, r.amount, r.currency, r.provider, r.status].join(",")))
    const blob = new Blob([lines.join("\n")], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url; a.download = "transactions.csv"; a.click()
    URL.revokeObjectURL(url)
}
