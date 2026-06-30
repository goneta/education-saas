"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { GraduationCap, Plus, Power, Trash2 } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Level {
    id: number
    code: string
    name: string
    category?: string | null
    sort_order: number
    is_active: boolean
}

const CATEGORIES = ["primaire", "college", "lycee", "superieur", "autre"]

export default function SchoolLevelsPage() {
    const t = useTranslations("schoolLevels")
    const { token } = useAuth()
    const [levels, setLevels] = useState<Level[]>([])
    const [form, setForm] = useState({ code: "", name: "", category: "primaire", sort_order: "" })
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/levels`, { headers })
        if (res.ok) setLevels(await res.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const create = async () => {
        if (!headers || !form.code.trim() || !form.name.trim()) return
        setError(null)
        const res = await fetch(`${API_BASE_URL}/levels`, {
            method: "POST", headers,
            body: JSON.stringify({ code: form.code.trim(), name: form.name.trim(), category: form.category, sort_order: Number(form.sort_order) || 0 }),
        })
        if (res.ok) { setForm({ code: "", name: "", category: "primaire", sort_order: "" }); void load() }
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const toggle = async (level: Level) => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/levels/${level.id}`, { method: "PATCH", headers, body: JSON.stringify({ is_active: !level.is_active }) })
        if (res.ok) void load()
    }

    const remove = async (level: Level) => {
        if (!headers || !window.confirm(t("confirmDelete"))) return
        const res = await fetch(`${API_BASE_URL}/levels/${level.id}`, { method: "DELETE", headers })
        if (res.ok) void load()
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const categoryLabel = (c?: string | null) => c && CATEGORIES.includes(c) ? t(c as "primaire") : (c || "—")

    const columns: FilterColumn<Level>[] = [
        { key: "code", label: t("code"), accessor: r => r.code },
        { key: "name", label: t("name"), accessor: r => r.name },
        { key: "category", label: t("category"), accessor: r => categoryLabel(r.category) },
    ]
    const filter = useTableFilter(levels, columns, { storageKey: "levels" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>{t("addLevel")}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-5">
                    <input value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} placeholder={t("code")} className="apple-input" />
                    <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder={t("name")} className="apple-input md:col-span-2" />
                    <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className="apple-select">{CATEGORIES.map(c => <option key={c} value={c}>{t(c as "primaire")}</option>)}</select>
                    <input type="number" value={form.sort_order} onChange={e => setForm({ ...form, sort_order: e.target.value })} placeholder={t("order")} className="apple-input" />
                    <Button onClick={create} className="bg-black text-white hover:bg-black/90 md:col-span-5"><Plus className="mr-2 h-4 w-4" /> {t("add")}</Button>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle className="flex items-center gap-2"><GraduationCap className="h-4 w-4" /> {t("list")} ({levels.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <div className="mb-3"><TableFilter {...filter.controls} /></div>
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]">
                                <th className="px-3 py-2">{t("order")}</th><th className="px-3 py-2">{t("code")}</th><th className="px-3 py-2">{t("name")}</th><th className="px-3 py-2">{t("category")}</th><th className="px-3 py-2">{t("status")}</th><th className="px-3 py-2 text-right">{t("actions")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filter.filtered.length === 0 ? (
                                <tr><td colSpan={6} className="px-3 py-6 text-center text-[#6B7280]">{t("empty")}</td></tr>
                            ) : filter.filtered.map(level => (
                                <tr key={level.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2">{level.sort_order}</td>
                                    <td className="px-3 py-2 font-medium">{level.code}</td>
                                    <td className="px-3 py-2">{level.name}</td>
                                    <td className="px-3 py-2">{categoryLabel(level.category)}</td>
                                    <td className="px-3 py-2"><span className={`rounded-full px-2 py-0.5 text-xs ${level.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-700"}`}>{level.is_active ? t("active") : t("inactive")}</span></td>
                                    <td className="px-3 py-2 text-right">
                                        <div className="flex justify-end gap-1">
                                            <Button variant="ghost" size="sm" title={level.is_active ? t("deactivate") : t("activate")} onClick={() => toggle(level)}><Power className="h-4 w-4" /></Button>
                                            <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => remove(level)}><Trash2 className="h-4 w-4" /></Button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
