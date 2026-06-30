"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { CalendarDays, Check, X, Plus } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface LeaveRequest {
    id: number
    staff_user_id: number
    leave_type: string
    start_date: string
    end_date: string
    reason?: string | null
    status: string
}
interface Person { user_id: number; full_name: string }

const LEAVE_TYPES = ["annual", "sick", "unpaid", "maternity", "other"]
const APPROVER_ROLES = ["super_admin", "school_admin", "admin", "director", "principal"]

export default function LeavePage() {
    const t = useTranslations("leave")
    const { token, user } = useAuth()
    const [requests, setRequests] = useState<LeaveRequest[]>([])
    const [people, setPeople] = useState<Person[]>([])
    const [form, setForm] = useState({ leave_type: "annual", start_date: "", end_date: "", reason: "" })
    const [error, setError] = useState<string | null>(null)

    const isApprover = APPROVER_ROLES.includes(String(user?.role || "").toLowerCase())
    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/hr/leave-requests`, { headers })
        if (res.ok) setRequests(await res.json())
        if (isApprover) {
            const [staff, teachers] = await Promise.all([
                fetch(`${API_BASE_URL}/personnel`, { headers }),
                fetch(`${API_BASE_URL}/teachers`, { headers }),
            ])
            const list: Person[] = []
            if (staff.ok) (await staff.json()).forEach((s: { user_id: number; full_name?: string }) => list.push({ user_id: s.user_id, full_name: s.full_name || `#${s.user_id}` }))
            if (teachers.ok) { const rows = await teachers.json(); (Array.isArray(rows) ? rows : []).forEach((te: { id: number; full_name?: string }) => { if (!list.some(p => p.user_id === te.id)) list.push({ user_id: te.id, full_name: te.full_name || `#${te.id}` }) }) }
            setPeople(list)
        }
    }, [headers, isApprover])

    useEffect(() => { void load() }, [load])

    const submit = async () => {
        if (!headers || !form.start_date || !form.end_date) return
        setError(null)
        if (form.end_date < form.start_date) { setError(t("dateError")); return }
        const res = await fetch(`${API_BASE_URL}/hr/leave-requests`, {
            method: "POST", headers,
            body: JSON.stringify({ leave_type: form.leave_type, start_date: form.start_date, end_date: form.end_date, reason: form.reason || null }),
        })
        if (res.ok) { setForm({ leave_type: "annual", start_date: "", end_date: "", reason: "" }); void load() }
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const decide = async (req: LeaveRequest, status: "approved" | "rejected") => {
        if (!headers) return
        if ((await fetch(`${API_BASE_URL}/hr/leave-requests/${req.id}/decide`, { method: "POST", headers, body: JSON.stringify({ status }) })).ok) void load()
    }

    const personName = (id: number) => id === user?.id ? (user?.full_name || `#${id}`) : (people.find(p => p.user_id === id)?.full_name || `#${id}`)
    const typeLabel = (lt: string) => LEAVE_TYPES.includes(lt) ? t(lt as "annual") : lt
    const fmt = (d: string) => d ? new Date(d).toLocaleDateString() : "—"
    const statusBadge = (s: string) => <span className={`rounded-full px-2 py-0.5 text-xs ${s === "approved" ? "bg-green-100 text-green-800" : s === "rejected" ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"}`}>{t(s as "pending")}</span>

    const columns = useMemo<FilterColumn<LeaveRequest>[]>(() => [
        { key: "employee", label: t("employee"), accessor: r => personName(r.staff_user_id) },
        { key: "type", label: t("type"), accessor: r => typeLabel(r.leave_type) },
        { key: "status", label: t("status"), accessor: r => t(r.status as "pending") },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- labels stable; names from people/user
    ], [people, user])
    const filter = useTableFilter(requests, columns, { storageKey: "leave" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>{t("request")}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-4">
                    <select value={form.leave_type} onChange={e => setForm({ ...form, leave_type: e.target.value })} className="apple-select">{LEAVE_TYPES.map(lt => <option key={lt} value={lt}>{t(lt as "annual")}</option>)}</select>
                    <input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} className="apple-input" aria-label={t("startDate")} />
                    <input type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} className="apple-input" aria-label={t("endDate")} />
                    <input value={form.reason} onChange={e => setForm({ ...form, reason: e.target.value })} placeholder={t("reason")} className="apple-input" />
                    <Button onClick={submit} className="bg-black text-white hover:bg-black/90 md:col-span-4"><Plus className="mr-2 h-4 w-4" /> {t("submit")}</Button>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle className="flex items-center gap-2"><CalendarDays className="h-4 w-4" /> {t("list")} ({filter.filtered.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <div className="mb-3"><TableFilter {...filter.controls} /></div>
                    <table className="w-full text-left text-sm">
                        <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("employee")}</th><th className="px-3 py-2">{t("type")}</th><th className="px-3 py-2">{t("dates")}</th><th className="px-3 py-2">{t("reason")}</th><th className="px-3 py-2">{t("status")}</th>{isApprover && <th className="px-3 py-2 text-right">{t("actions")}</th>}</tr></thead>
                        <tbody>
                            {filter.filtered.length === 0 ? <tr><td colSpan={isApprover ? 6 : 5} className="px-3 py-6 text-center text-[#6B7280]">{t("empty")}</td></tr> : filter.filtered.map(r => (
                                <tr key={r.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{personName(r.staff_user_id)}</td>
                                    <td className="px-3 py-2">{typeLabel(r.leave_type)}</td>
                                    <td className="px-3 py-2">{fmt(r.start_date)} → {fmt(r.end_date)}</td>
                                    <td className="px-3 py-2 text-[#6B7280]">{r.reason || "—"}</td>
                                    <td className="px-3 py-2">{statusBadge(r.status)}</td>
                                    {isApprover && <td className="px-3 py-2 text-right">{r.status === "pending" && (
                                        <div className="flex justify-end gap-1">
                                            <Button variant="ghost" size="sm" onClick={() => decide(r, "approved")} title={t("approve")}><Check className="h-4 w-4 text-green-600" /></Button>
                                            <Button variant="ghost" size="sm" onClick={() => decide(r, "rejected")} title={t("reject")}><X className="h-4 w-4 text-red-600" /></Button>
                                        </div>
                                    )}</td>}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
