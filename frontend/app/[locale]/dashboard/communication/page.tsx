"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { Megaphone, Send, Plus, AlertTriangle } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Announcement {
    id: number
    title: string
    body: string
    audience: string
    is_emergency: boolean
    status: string
    scheduled_for?: string | null
    published_at?: string | null
}

const AUDIENCES = ["all", "teachers", "students", "parents"]

export default function CommunicationPage() {
    const t = useTranslations("announcements")
    const { token } = useAuth()
    const [items, setItems] = useState<Announcement[]>([])
    const [form, setForm] = useState({ title: "", body: "", audience: "all", is_emergency: false, scheduled_for: "" })
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/communication/announcements`, { headers })
        if (res.ok) setItems(await res.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const create = async () => {
        if (!headers || !form.title.trim() || !form.body.trim()) return
        setError(null)
        const res = await fetch(`${API_BASE_URL}/communication/announcements`, {
            method: "POST", headers,
            body: JSON.stringify({ title: form.title.trim(), body: form.body.trim(), audience: form.audience, is_emergency: form.is_emergency, scheduled_for: form.scheduled_for || null }),
        })
        if (res.ok) { setForm({ title: "", body: "", audience: "all", is_emergency: false, scheduled_for: "" }); void load() }
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const publish = async (a: Announcement) => {
        if (!headers) return
        if ((await fetch(`${API_BASE_URL}/communication/announcements/${a.id}/publish`, { method: "POST", headers })).ok) void load()
    }

    const audienceLabel = (a: string) => AUDIENCES.includes(a) ? t(a as "all") : a
    const statusBadge = (s: string) => <span className={`rounded-full px-2 py-0.5 text-xs ${s === "published" ? "bg-green-100 text-green-800" : s === "scheduled" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-700"}`}>{t(s as "draft")}</span>

    const columns = useMemo<FilterColumn<Announcement>[]>(() => [
        { key: "title", label: t("titleField"), accessor: a => a.title },
        { key: "audience", label: t("audience"), accessor: a => audienceLabel(a.audience) },
        { key: "status", label: t("status"), accessor: a => t(a.status as "draft") },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- labels from a stable translator
    ], [])
    const filter = useTableFilter(items, columns, { storageKey: "announcements" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>{t("create")}</CardTitle></CardHeader>
                <CardContent className="grid gap-3">
                    <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder={t("titleField")} className="apple-input" />
                    <textarea value={form.body} onChange={e => setForm({ ...form, body: e.target.value })} placeholder={t("body")} rows={3} className="apple-input" />
                    <div className="grid gap-3 md:grid-cols-3">
                        <select value={form.audience} onChange={e => setForm({ ...form, audience: e.target.value })} className="apple-select">{AUDIENCES.map(a => <option key={a} value={a}>{t(a as "all")}</option>)}</select>
                        <input type="datetime-local" value={form.scheduled_for} onChange={e => setForm({ ...form, scheduled_for: e.target.value })} className="apple-input" aria-label={t("scheduledFor")} />
                        <label className="flex items-center gap-2 text-sm text-[#111827] dark:text-[#f4f7fb]"><input type="checkbox" checked={form.is_emergency} onChange={e => setForm({ ...form, is_emergency: e.target.checked })} /> <AlertTriangle className="h-4 w-4 text-amber-600" /> {t("emergency")}</label>
                    </div>
                    <Button onClick={create} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> {t("save")}</Button>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle className="flex items-center gap-2"><Megaphone className="h-4 w-4" /> {t("list")} ({filter.filtered.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <div className="mb-3"><TableFilter {...filter.controls} /></div>
                    <table className="w-full text-left text-sm">
                        <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("titleField")}</th><th className="px-3 py-2">{t("audience")}</th><th className="px-3 py-2">{t("status")}</th><th className="px-3 py-2 text-right">{t("actions")}</th></tr></thead>
                        <tbody>
                            {filter.filtered.length === 0 ? <tr><td colSpan={4} className="px-3 py-6 text-center text-[#6B7280]">{t("empty")}</td></tr> : filter.filtered.map(a => (
                                <tr key={a.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{a.is_emergency && <AlertTriangle className="mr-1 inline h-3.5 w-3.5 text-amber-600" />}{a.title}</td>
                                    <td className="px-3 py-2">{audienceLabel(a.audience)}</td>
                                    <td className="px-3 py-2">{statusBadge(a.status)}</td>
                                    <td className="px-3 py-2 text-right">{a.status !== "published" && <Button variant="ghost" size="sm" onClick={() => publish(a)} title={t("publish")}><Send className="h-4 w-4 text-blue-600" /></Button>}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
