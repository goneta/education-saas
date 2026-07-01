"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { KeyRound, Webhook, Plus, Trash2, RotateCw, Copy, Check, BookOpen } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { normalizeLocale } from "@/lib/i18n"

interface ApiKey { id: number; name: string; prefix: string; is_active: boolean; created_at: string; last_used_at?: string | null }
interface WebhookEndpoint { id: number; url: string; event_types?: string[] | null; is_active: boolean; created_at: string }
interface Delivery { id: number; endpoint_id: number; event_type: string; status: string; attempts: number; max_attempts: number; created_at: string; last_error?: string | null }

export default function IntegrationsPage() {
    const t = useTranslations("integrations")
    const { token } = useAuth()
    const params = useParams<{ locale: string }>()
    const locale = normalizeLocale(params?.locale)

    const [keys, setKeys] = useState<ApiKey[]>([])
    const [hooks, setHooks] = useState<WebhookEndpoint[]>([])
    const [deliveries, setDeliveries] = useState<Delivery[]>([])
    const [keyName, setKeyName] = useState("")
    const [newKey, setNewKey] = useState<string | null>(null)
    const [copied, setCopied] = useState(false)
    const [hookForm, setHookForm] = useState({ url: "", events: "", secret: "" })
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const [k, w, d] = await Promise.all([
            fetch(`${API_BASE_URL}/extensibility/api-keys`, { headers }),
            fetch(`${API_BASE_URL}/extensibility/webhooks`, { headers }),
            fetch(`${API_BASE_URL}/extensibility/deliveries?limit=25`, { headers }),
        ])
        if (k.ok) setKeys(await k.json())
        if (w.ok) setHooks(await w.json())
        if (d.ok) setDeliveries(await d.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const createKey = async () => {
        if (!headers || !keyName.trim()) return
        setError(null)
        const res = await fetch(`${API_BASE_URL}/extensibility/api-keys`, { method: "POST", headers, body: JSON.stringify({ name: keyName.trim() }) })
        if (res.ok) { const data = await res.json(); setNewKey(data.api_key); setKeyName(""); void load() }
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const revokeKey = async (key: ApiKey) => {
        if (!headers || !window.confirm(t("confirmRevoke"))) return
        if ((await fetch(`${API_BASE_URL}/extensibility/api-keys/${key.id}`, { method: "DELETE", headers })).ok) void load()
    }

    const copyKey = async () => {
        if (!newKey) return
        try { await navigator.clipboard.writeText(newKey); setCopied(true); setTimeout(() => setCopied(false), 1600) } catch { /* ignore */ }
    }

    const addHook = async () => {
        if (!headers || !hookForm.url.trim()) return
        setError(null)
        const events = hookForm.events.split(",").map(e => e.trim()).filter(Boolean)
        const res = await fetch(`${API_BASE_URL}/extensibility/webhooks`, {
            method: "POST", headers,
            body: JSON.stringify({ url: hookForm.url.trim(), event_types: events.length ? events : null, secret: hookForm.secret || null }),
        })
        if (res.ok) { setHookForm({ url: "", events: "", secret: "" }); void load() }
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const deleteHook = async (hook: WebhookEndpoint) => {
        if (!headers || !window.confirm(t("confirmDeleteWebhook"))) return
        if ((await fetch(`${API_BASE_URL}/extensibility/webhooks/${hook.id}`, { method: "DELETE", headers })).ok) void load()
    }

    const retryDelivery = async (delivery: Delivery) => {
        if (!headers) return
        if ((await fetch(`${API_BASE_URL}/extensibility/deliveries/${delivery.id}/retry`, { method: "POST", headers })).ok) void load()
    }

    const fmtDate = (value?: string | null) => value ? new Date(value).toLocaleString() : "—"
    const statusBadge = (s: string) => <span className={`rounded-full px-2 py-0.5 text-xs ${s === "delivered" ? "bg-green-100 text-green-800" : s === "failed" ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"}`}>{t(s as "pending")}</span>

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                    <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
                </div>
                <Link href={`/${locale}/docs/api-webhooks`} className="flex items-center gap-2 rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm text-[#374151] hover:bg-[#F8FAFC] dark:border-[#3b4248] dark:text-[#c7d0da] dark:hover:bg-[#1c2227]">
                    <BookOpen className="h-4 w-4" /> {t("docsLink")}
                </Link>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><KeyRound className="h-4 w-4" /> {t("apiKeys")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("apiKeysHint")}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex flex-wrap gap-2">
                        <input value={keyName} onChange={e => setKeyName(e.target.value)} placeholder={t("keyName")} className="apple-input max-w-xs" />
                        <Button onClick={createKey} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> {t("createKey")}</Button>
                    </div>
                    {newKey && (
                        <div className="rounded-xl border border-[#CCFBF1] bg-[#F0FDFA] p-3 dark:border-[#134E4A] dark:bg-[#0f1f1d]">
                            <p className="text-sm font-medium text-[#134E4A] dark:text-[#5eead4]">{t("keyCreated")}</p>
                            <div className="mt-2 flex flex-wrap items-center gap-2">
                                <code className="rounded-md bg-white px-2 py-1 font-mono text-sm text-[#0F766E] dark:bg-[#1c2a28]">{newKey}</code>
                                <Button variant="outline" size="sm" onClick={copyKey}>{copied ? <Check className="mr-1 h-3.5 w-3.5 text-[#0F766E]" /> : <Copy className="mr-1 h-3.5 w-3.5" />}{copied ? t("copied") : t("copy")}</Button>
                            </div>
                        </div>
                    )}
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("name")}</th><th className="px-3 py-2">{t("prefix")}</th><th className="px-3 py-2">{t("lastUsed")}</th><th className="px-3 py-2">{t("status")}</th><th className="px-3 py-2 text-right">{t("actions")}</th></tr></thead>
                            <tbody>
                                {keys.length === 0 ? <tr><td colSpan={5} className="px-3 py-6 text-center text-[#6B7280]">{t("noKeys")}</td></tr> : keys.map(key => (
                                    <tr key={key.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                        <td className="px-3 py-2 font-medium">{key.name}</td>
                                        <td className="px-3 py-2"><code className="rounded bg-[#F1F3F5] px-1.5 py-0.5 font-mono text-xs dark:bg-[#2a3035]">{key.prefix}…</code></td>
                                        <td className="px-3 py-2">{key.last_used_at ? fmtDate(key.last_used_at) : t("never")}</td>
                                        <td className="px-3 py-2"><span className={`rounded-full px-2 py-0.5 text-xs ${key.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-700"}`}>{key.is_active ? t("active") : t("revoked")}</span></td>
                                        <td className="px-3 py-2 text-right">{key.is_active && <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => revokeKey(key)}>{t("revoke")}</Button>}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><Webhook className="h-4 w-4" /> {t("webhooks")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("webhooksHint")}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-2 md:grid-cols-4">
                        <input value={hookForm.url} onChange={e => setHookForm({ ...hookForm, url: e.target.value })} placeholder={t("url")} className="apple-input md:col-span-2" />
                        <input value={hookForm.events} onChange={e => setHookForm({ ...hookForm, events: e.target.value })} placeholder={t("events")} className="apple-input" />
                        <input value={hookForm.secret} onChange={e => setHookForm({ ...hookForm, secret: e.target.value })} placeholder={t("secret")} className="apple-input" />
                        <Button onClick={addHook} className="bg-black text-white hover:bg-black/90 md:col-span-4"><Plus className="mr-2 h-4 w-4" /> {t("addWebhook")}</Button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">URL</th><th className="px-3 py-2">{t("events")}</th><th className="px-3 py-2">{t("status")}</th><th className="px-3 py-2 text-right">{t("actions")}</th></tr></thead>
                            <tbody>
                                {hooks.length === 0 ? <tr><td colSpan={4} className="px-3 py-6 text-center text-[#6B7280]">{t("noWebhooks")}</td></tr> : hooks.map(hook => (
                                    <tr key={hook.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                        <td className="px-3 py-2 font-mono text-xs">{hook.url}</td>
                                        <td className="px-3 py-2">{hook.event_types && hook.event_types.length ? hook.event_types.join(", ") : t("allEvents")}</td>
                                        <td className="px-3 py-2"><span className={`rounded-full px-2 py-0.5 text-xs ${hook.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-700"}`}>{hook.is_active ? t("active") : "—"}</span></td>
                                        <td className="px-3 py-2 text-right"><Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => deleteHook(hook)}><Trash2 className="h-4 w-4" /></Button></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div>
                        <p className="mb-2 text-sm font-semibold text-[#111827] dark:text-white">{t("deliveries")}</p>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("event")}</th><th className="px-3 py-2">{t("status")}</th><th className="px-3 py-2">{t("attempts")}</th><th className="px-3 py-2">{t("date")}</th><th className="px-3 py-2 text-right">{t("actions")}</th></tr></thead>
                                <tbody>
                                    {deliveries.length === 0 ? <tr><td colSpan={5} className="px-3 py-6 text-center text-[#6B7280]">{t("noDeliveries")}</td></tr> : deliveries.map(delivery => (
                                        <tr key={delivery.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                            <td className="px-3 py-2 font-mono text-xs">{delivery.event_type}</td>
                                            <td className="px-3 py-2">{statusBadge(delivery.status)}</td>
                                            <td className="px-3 py-2">{delivery.attempts}/{delivery.max_attempts}</td>
                                            <td className="px-3 py-2">{fmtDate(delivery.created_at)}</td>
                                            <td className="px-3 py-2 text-right">{delivery.status === "failed" && <Button variant="ghost" size="sm" onClick={() => retryDelivery(delivery)} title={t("retry")}><RotateCw className="h-4 w-4" /></Button>}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
