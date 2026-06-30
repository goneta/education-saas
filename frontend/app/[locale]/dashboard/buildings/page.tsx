"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { Building2, Plus, Power, Trash2 } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Building { id: number; name: string; description?: string | null; campus_id?: number | null; is_active: boolean }
interface Campus { id: number; name: string }

export default function BuildingsPage() {
    const t = useTranslations("facilities")
    const { token } = useAuth()
    const [buildings, setBuildings] = useState<Building[]>([])
    const [campuses, setCampuses] = useState<Campus[]>([])
    const [form, setForm] = useState({ name: "", description: "", campus_id: "" })
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const [b, c] = await Promise.all([
            fetch(`${API_BASE_URL}/facilities/buildings`, { headers }),
            fetch(`${API_BASE_URL}/facilities/campuses`, { headers }),
        ])
        if (b.ok) setBuildings(await b.json())
        if (c.ok) setCampuses(await c.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const create = async () => {
        if (!headers || !form.name.trim()) return
        setError(null)
        const res = await fetch(`${API_BASE_URL}/facilities/buildings`, {
            method: "POST", headers,
            body: JSON.stringify({ name: form.name.trim(), description: form.description || null, campus_id: form.campus_id ? Number(form.campus_id) : null }),
        })
        if (res.ok) { setForm({ name: "", description: "", campus_id: "" }); void load() }
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const toggle = async (b: Building) => {
        if (!headers) return
        if ((await fetch(`${API_BASE_URL}/facilities/buildings/${b.id}`, { method: "PATCH", headers, body: JSON.stringify({ is_active: !b.is_active }) })).ok) void load()
    }
    const remove = async (b: Building) => {
        if (!headers || !window.confirm(t("confirmDelete"))) return
        const res = await fetch(`${API_BASE_URL}/facilities/buildings/${b.id}`, { method: "DELETE", headers })
        if (res.ok) void load()
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }
    const campusName = (id?: number | null) => campuses.find(c => c.id === id)?.name || t("noCampus")

    const columns: FilterColumn<Building>[] = [
        { key: "name", label: t("name"), accessor: b => b.name },
        { key: "description", label: t("description"), accessor: b => b.description },
        { key: "campus", label: t("campus"), accessor: b => campusName(b.campus_id) },
    ]
    const filter = useTableFilter(buildings, columns, { storageKey: "buildings" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("buildingsTitle")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("buildingsSubtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>{t("addBuilding")}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-4">
                    <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder={t("name")} className="apple-input" />
                    <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder={t("description")} className="apple-input md:col-span-2" />
                    <select value={form.campus_id} onChange={e => setForm({ ...form, campus_id: e.target.value })} className="apple-select"><option value="">{t("noCampus")}</option>{campuses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
                    <Button onClick={create} className="bg-black text-white hover:bg-black/90 md:col-span-4"><Plus className="mr-2 h-4 w-4" /> {t("add")}</Button>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle className="flex items-center gap-2"><Building2 className="h-4 w-4" /> {t("buildingsTitle")} ({buildings.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <div className="mb-3"><TableFilter {...filter.controls} /></div>
                    <table className="w-full text-left text-sm">
                        <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("name")}</th><th className="px-3 py-2">{t("description")}</th><th className="px-3 py-2">{t("campus")}</th><th className="px-3 py-2">{t("state")}</th><th className="px-3 py-2 text-right">{t("actions")}</th></tr></thead>
                        <tbody>
                            {filter.filtered.length === 0 ? <tr><td colSpan={5} className="px-3 py-6 text-center text-[#6B7280]">{t("empty")}</td></tr> : filter.filtered.map(b => (
                                <tr key={b.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{b.name}</td>
                                    <td className="px-3 py-2">{b.description || "—"}</td>
                                    <td className="px-3 py-2">{campusName(b.campus_id)}</td>
                                    <td className="px-3 py-2"><span className={`rounded-full px-2 py-0.5 text-xs ${b.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-700"}`}>{b.is_active ? t("active") : t("inactive")}</span></td>
                                    <td className="px-3 py-2 text-right"><div className="flex justify-end gap-1"><Button variant="ghost" size="sm" onClick={() => toggle(b)}><Power className="h-4 w-4" /></Button><Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => remove(b)}><Trash2 className="h-4 w-4" /></Button></div></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
