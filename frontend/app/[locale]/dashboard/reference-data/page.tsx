"use client"

// Listes de référence hiérarchiques : données GLOBALES TeducAI (🌐, gérées par
// le Super Admin, lecture seule pour les établissements) + données LOCALES de
// l'établissement (🏫, gérées par ses admins, invisibles ailleurs). Les
// formulaires de l'application consomment la vue FUSIONNÉE de ces listes.

import { useCallback, useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { Globe2, Pencil, Plus, School, Trash2 } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { parseApiErrorResponse } from "@/lib/api-errors"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface Category { key: string; label_fr: string; label_en: string }
interface RefItem {
    id: number
    category: string
    code: string
    name: string
    description?: string | null
    sort_order: number
    is_active: boolean
    scope: "global" | "school"
    school_id: number | null
    source: "reference" | "levels"
}

export default function ReferenceDataPage() {
    const t = useTranslations("referenceData")
    const { token, user } = useAuth()
    const params = useParams()
    const router = useRouter()
    const searchParams = useSearchParams()
    const locale = params.locale as string
    const isSuperAdmin = String(user?.role || "").toLowerCase() === "super_admin"
    const canManageLocal = ["super_admin", "school_admin", "direction"].includes(String(user?.role || "").toLowerCase())

    const [categories, setCategories] = useState<Category[]>([])
    const [category, setCategory] = useState(searchParams.get("category") || "fee_type")
    const [items, setItems] = useState<RefItem[]>([])
    const [loading, setLoading] = useState(true)
    const [message, setMessage] = useState("")
    const [newName, setNewName] = useState("")
    const [newCode, setNewCode] = useState("")
    const [editing, setEditing] = useState<RefItem | null>(null)
    const [editName, setEditName] = useState("")

    const headers = { Authorization: `Bearer ${token}` }

    const load = useCallback(async () => {
        if (!token) return
        setLoading(true)
        try {
            const [cats, rows] = await Promise.all([
                fetch(`${API_BASE_URL}/reference-data/categories`, { headers }).then(r => r.ok ? r.json() : []),
                fetch(`${API_BASE_URL}/reference-data/${category}?include_inactive=true`, { headers }).then(r => r.ok ? r.json() : []),
            ])
            setCategories(Array.isArray(cats) ? cats : [])
            setItems(Array.isArray(rows) ? rows : [])
        } finally {
            setLoading(false)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps -- headers derived from token
    }, [token, category])

    useEffect(() => { void load() }, [load])

    const create = async () => {
        if (!token || !newName.trim()) return
        const response = await fetch(`${API_BASE_URL}/reference-data/${category}`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ name: newName.trim(), code: newCode.trim() || undefined }),
        })
        if (!response.ok) {
            const parsed = await parseApiErrorResponse(response, t("createError"))
            setMessage(parsed.message)
            return
        }
        setNewName(""); setNewCode("")
        setMessage(t("created"))
        void load()
    }

    const saveEdit = async () => {
        if (!token || !editing || !editName.trim()) return
        const response = await fetch(`${API_BASE_URL}/reference-data/items/${editing.id}`, {
            method: "PATCH",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ name: editName.trim() }),
        })
        if (!response.ok) {
            const parsed = await parseApiErrorResponse(response, t("updateError"))
            setMessage(parsed.message)
            return
        }
        setEditing(null)
        void load()
    }

    const toggleActive = async (item: RefItem) => {
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/reference-data/items/${item.id}`, {
            method: "PATCH",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: !item.is_active }),
        })
        if (!response.ok) setMessage((await parseApiErrorResponse(response, t("updateError"))).message)
        void load()
    }

    const remove = async (item: RefItem) => {
        if (!token) return
        if (!window.confirm(t("deleteConfirm", { name: item.name }))) return
        const response = await fetch(`${API_BASE_URL}/reference-data/items/${item.id}`, { method: "DELETE", headers })
        if (!response.ok) setMessage((await parseApiErrorResponse(response, t("deleteError"))).message)
        void load()
    }

    const canEdit = (item: RefItem) => {
        if (item.source === "levels") return false // géré sur la page Niveaux
        if (item.scope === "global") return isSuperAdmin
        return canManageLocal
    }

    const categoryLabel = (cat: Category) => (locale === "fr" ? cat.label_fr : cat.label_en)

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">{t("title")}</h1>
                <p className="mt-1 max-w-3xl text-sm text-[#6B7280]">{t("subtitle")}</p>
            </div>

            <div className="flex flex-wrap gap-2">
                {categories.map(cat => (
                    <button key={cat.key} type="button"
                        onClick={() => { setCategory(cat.key); router.replace(`/${locale}/dashboard/reference-data?category=${cat.key}`) }}
                        className={`rounded-full border px-4 py-1.5 text-sm transition ${category === cat.key ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-[#E5E7EB] hover:bg-[#F6F7F9] dark:border-[#3b4248] dark:hover:bg-[#2a3035]"}`}>
                        {categoryLabel(cat)}
                    </button>
                ))}
            </div>

            {message && <div className="rounded-lg border border-[#E5E7EB] bg-[#F6F7F9] px-4 py-3 text-sm dark:border-[#3b4248] dark:bg-[#2a3035]">{message}</div>}

            {canManageLocal && (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader><CardTitle className="text-base">{isSuperAdmin ? t("addGlobal") : t("addLocal")}</CardTitle></CardHeader>
                    <CardContent>
                        <div className="flex flex-wrap items-end gap-3">
                            <div className="min-w-56 flex-1">
                                <label className="text-sm text-[#6B7280]">{t("nameLabel")}</label>
                                <Input value={newName} onChange={e => setNewName(e.target.value)} placeholder={t("namePh")} />
                            </div>
                            <div className="w-44">
                                <label className="text-sm text-[#6B7280]">{t("codeLabel")}</label>
                                <Input value={newCode} onChange={e => setNewCode(e.target.value)} placeholder={t("codePh")} />
                            </div>
                            <Button onClick={() => void create()} disabled={!newName.trim()} className="bg-black text-white hover:bg-black/90">
                                <Plus className="mr-2 h-4 w-4" /> {t("addBtn")}
                            </Button>
                        </div>
                        {!isSuperAdmin && <p className="mt-2 text-xs text-[#6B7280]">{t("localNote")}</p>}
                    </CardContent>
                </Card>
            )}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle className="text-base">{t("listTitle")} ({items.length})</CardTitle></CardHeader>
                <CardContent>
                    {loading ? (
                        <p className="py-8 text-center text-[#6B7280]">{t("loading")}</p>
                    ) : items.length === 0 ? (
                        <p className="py-8 text-center text-[#6B7280]">{t("empty")}</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-[#E5E7EB] text-left text-sm text-[#6B7280]">
                                        <th className="px-3 py-2">{t("scope")}</th>
                                        <th className="px-3 py-2">{t("codeLabel")}</th>
                                        <th className="px-3 py-2">{t("nameLabel")}</th>
                                        <th className="px-3 py-2">{t("status")}</th>
                                        <th className="px-3 py-2">{t("actions")}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {items.map(item => (
                                        <tr key={`${item.source}-${item.id}`} className="border-b border-[#E5E7EB] text-sm last:border-0">
                                            <td className="px-3 py-2">
                                                {item.scope === "global" ? (
                                                    <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-950 dark:text-blue-200">
                                                        <Globe2 className="h-3.5 w-3.5" /> {t("globalBadge")}
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
                                                        <School className="h-3.5 w-3.5" /> {t("schoolBadge")}
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-3 py-2 font-mono text-xs">{item.code}</td>
                                            <td className="px-3 py-2">
                                                {editing?.id === item.id && editing.source === item.source ? (
                                                    <div className="flex items-center gap-2">
                                                        <Input value={editName} onChange={e => setEditName(e.target.value)} className="h-8 w-56" />
                                                        <Button size="sm" onClick={() => void saveEdit()}>{t("save")}</Button>
                                                        <Button size="sm" variant="outline" onClick={() => setEditing(null)}>{t("cancel")}</Button>
                                                    </div>
                                                ) : item.name}
                                            </td>
                                            <td className="px-3 py-2">
                                                <span className={`rounded-full px-2 py-0.5 text-xs ${item.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-700"}`}>
                                                    {item.is_active ? t("active") : t("inactive")}
                                                </span>
                                            </td>
                                            <td className="px-3 py-2">
                                                {item.source === "levels" ? (
                                                    <Button size="sm" variant="ghost" onClick={() => router.push(`/${locale}/dashboard/levels`)}>{t("manageOnLevels")}</Button>
                                                ) : canEdit(item) ? (
                                                    <div className="flex items-center gap-1">
                                                        <Button size="sm" variant="ghost" title={t("edit")} onClick={() => { setEditing(item); setEditName(item.name) }}><Pencil className="h-4 w-4" /></Button>
                                                        <Button size="sm" variant="ghost" onClick={() => void toggleActive(item)}>{item.is_active ? t("deactivate") : t("activate")}</Button>
                                                        <Button size="sm" variant="ghost" className="text-red-600" title={t("delete")} onClick={() => void remove(item)}><Trash2 className="h-4 w-4" /></Button>
                                                    </div>
                                                ) : (
                                                    <span className="text-xs text-[#6B7280]">{t("readOnly")}</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
