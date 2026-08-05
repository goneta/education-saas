"use client"

// Generic, config-driven CRUD page for the Vie scolaire modules (Discipline,
// Examens, Activités, Santé scolaire, Internat) — backed by the factorized
// /school-life/{slug} API. ONE component provides list + server-side search,
// status/type filters, pagination, create/edit dialog, delete, CSV export and
// print for every module; each page is just a ModuleConfig. Dropdown sources
// (élèves, classes, matières, salles, référentiels globaux 🌐 + locaux 🏫) are
// loaded automatically and wrapped in the shared missing-dependency gates.

import { useCallback, useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import { Download, Pencil, Plus, Printer, RefreshCw, Trash2 } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { parseApiErrorResponse } from "@/lib/api-errors"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { MissingDependency, RequireOptions, missingRequired } from "@/components/ui/missing-dependency"

export interface FieldOption { value: string; label: string }

export interface FieldSpec {
    key: string
    label: string
    type: "text" | "textarea" | "date" | "number" | "checkbox" | "select" | "student" | "class" | "subject" | "room" | "reference"
    required?: boolean
    refCategory?: string
    options?: FieldOption[]
    placeholder?: string
    /** quick-create page for the source list ("/dashboard/…", locale added automatically) */
    createHref?: string
    createLabel?: string
    missingMessage?: string
}

export interface ColumnSpec { key: string; label: string }

export interface ModuleConfig {
    slug: string
    title: string
    subtitle: string
    createLabel: string
    columns: ColumnSpec[]
    fields: FieldSpec[]
    statusOptions: FieldOption[]
    /** field key used by the type_code server filter */
    typeFilterKey?: string
}

interface Row { id: number; student_name?: string | null; [key: string]: unknown }

const PAGE_SIZE = 20

export function SchoolLifeModulePage({ config }: { config: ModuleConfig }) {
    const { token } = useAuth()
    const params = useParams()
    const locale = (params?.locale as string) || "fr"
    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const [rows, setRows] = useState<Row[]>([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(0)
    const [search, setSearch] = useState("")
    const [statusFilter, setStatusFilter] = useState("")
    const [typeFilter, setTypeFilter] = useState("")
    const [loading, setLoading] = useState(true)
    const [message, setMessage] = useState("")

    // Option sources, loaded once per source kind actually used by the config.
    const [sources, setSources] = useState<Record<string, FieldOption[]>>({})
    const [sourcesLoaded, setSourcesLoaded] = useState(false)

    const [dialogOpen, setDialogOpen] = useState(false)
    const [editing, setEditing] = useState<Row | null>(null)
    const [form, setForm] = useState<Record<string, string | boolean>>({})
    const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
    const [saving, setSaving] = useState(false)

    const load = useCallback(async () => {
        if (!headers) return
        setLoading(true)
        try {
            const query = new URLSearchParams({ skip: String(page * PAGE_SIZE), limit: String(PAGE_SIZE) })
            if (search) query.set("search", search)
            if (statusFilter) query.set("status", statusFilter)
            if (typeFilter) query.set("type_code", typeFilter)
            const res = await fetch(`${API_BASE_URL}/school-life/${config.slug}?${query}`, { headers })
            if (res.ok) {
                const payload = await res.json()
                setRows(payload.items || [])
                setTotal(payload.total || 0)
            } else {
                setMessage((await parseApiErrorResponse(res, "Chargement impossible.")).message)
            }
        } finally {
            setLoading(false)
        }
    }, [headers, config.slug, page, search, statusFilter, typeFilter])

    useEffect(() => { void load() }, [load])

    // Load every dropdown source the config declares (students / classes /
    // subjects / rooms / merged reference lists).
    useEffect(() => {
        if (!headers) return
        const kinds = new Set(config.fields.map(field =>
            field.type === "reference" ? `reference:${field.refCategory}` : field.type))
        const jobs: [string, Promise<FieldOption[]>][] = []
        const get = (path: string) => fetch(`${API_BASE_URL}${path}`, { headers }).then(r => r.ok ? r.json() : []).catch(() => [])
        if (kinds.has("student")) jobs.push(["student", get("/students").then((data: { id: number; full_name: string; student_profile?: { id?: number } }[]) =>
            (Array.isArray(data) ? data : []).filter(s => s.student_profile?.id).map(s => ({ value: String(s.student_profile!.id), label: s.full_name })))])
        if (kinds.has("class")) jobs.push(["class", get("/education/classes").then((data: { id: number; name: string }[]) =>
            (Array.isArray(data) ? data : []).map(c => ({ value: String(c.id), label: c.name })))])
        if (kinds.has("subject")) jobs.push(["subject", get("/education/subjects").then((data: { id: number; name: string }[]) =>
            (Array.isArray(data) ? data : []).map(s => ({ value: String(s.id), label: s.name })))])
        if (kinds.has("room")) jobs.push(["room", get("/facilities/rooms").then((data: { id: number; name: string }[]) =>
            (Array.isArray(data) ? data : []).map(r => ({ value: String(r.id), label: r.name })))])
        for (const kind of kinds) {
            if (kind.startsWith("reference:")) {
                const category = kind.split(":")[1]
                jobs.push([kind, get(`/reference-data/${category}`).then((data: { code: string; name: string }[]) =>
                    (Array.isArray(data) ? data : []).map(item => ({ value: item.code, label: item.name })))])
            }
        }
        Promise.all(jobs.map(async ([key, promise]) => [key, await promise] as const)).then(entries => {
            setSources(Object.fromEntries(entries))
            setSourcesLoaded(true)
        })
    }, [headers, config.fields])

    const sourceFor = (field: FieldSpec): FieldOption[] => {
        if (field.type === "select") return field.options || []
        if (field.type === "reference") return sources[`reference:${field.refCategory}`] || []
        return sources[field.type] || []
    }

    const requiredGates = config.fields
        .filter(field => field.required && ["student", "class", "subject", "room", "reference"].includes(field.type))
        .map(field => ({ loaded: sourcesLoaded, count: sourceFor(field).length }))

    const openCreate = () => {
        setEditing(null)
        setForm(Object.fromEntries(config.fields.map(field => [field.key, field.type === "checkbox" ? true : ""])))
        setFieldErrors({})
        setDialogOpen(true)
    }

    const openEdit = (row: Row) => {
        setEditing(row)
        setForm(Object.fromEntries(config.fields.map(field => {
            const value = row[field.key]
            if (field.type === "checkbox") return [field.key, Boolean(value)]
            if (field.type === "date" && typeof value === "string") return [field.key, value.slice(0, 10)]
            return [field.key, value === null || value === undefined ? "" : String(value)]
        })))
        setFieldErrors({})
        setDialogOpen(true)
    }

    const save = async () => {
        if (!headers) return
        const errors: Record<string, string> = {}
        for (const field of config.fields) {
            if (field.required && !form[field.key] && field.type !== "checkbox") errors[field.key] = "Champ obligatoire"
        }
        setFieldErrors(errors)
        if (Object.keys(errors).length) return
        setSaving(true)
        setMessage("")
        try {
            const payload: Record<string, unknown> = {}
            for (const field of config.fields) {
                const value = form[field.key]
                if (field.type === "checkbox") payload[field.key] = Boolean(value)
                else if (value === "") payload[field.key] = null
                else if (field.type === "number") payload[field.key] = Number(value)
                else if (["student", "class", "subject", "room"].includes(field.type)) payload[field.key] = Number(value)
                else payload[field.key] = value
            }
            const url = editing
                ? `${API_BASE_URL}/school-life/${config.slug}/${editing.id}`
                : `${API_BASE_URL}/school-life/${config.slug}`
            const res = await fetch(url, { method: editing ? "PATCH" : "POST", headers, body: JSON.stringify(payload) })
            if (!res.ok) {
                const parsed = await parseApiErrorResponse(res, "Enregistrement impossible.")
                if (Object.keys(parsed.fieldErrors).length) setFieldErrors(previous => ({ ...previous, ...parsed.fieldErrors }))
                setMessage(parsed.message)
                return
            }
            setDialogOpen(false)
            void load()
        } finally {
            setSaving(false)
        }
    }

    const remove = async (row: Row) => {
        if (!headers || !window.confirm("Supprimer cet enregistrement ?")) return
        const res = await fetch(`${API_BASE_URL}/school-life/${config.slug}/${row.id}`, { method: "DELETE", headers })
        if (!res.ok) setMessage((await parseApiErrorResponse(res, "Suppression impossible.")).message)
        void load()
    }

    const exportCsv = async () => {
        if (!headers) return
        const query = new URLSearchParams()
        if (search) query.set("search", search)
        if (statusFilter) query.set("status", statusFilter)
        const res = await fetch(`${API_BASE_URL}/school-life/${config.slug}/export.csv?${query}`, { headers })
        if (!res.ok) { setMessage("Export impossible."); return }
        const blob = await res.blob()
        const link = document.createElement("a")
        link.href = URL.createObjectURL(blob)
        link.download = `${config.slug}.csv`
        link.click()
        URL.revokeObjectURL(link.href)
    }

    const labelFor = (field: FieldSpec | undefined, value: unknown): string => {
        if (value === null || value === undefined || value === "") return "—"
        if (!field) return String(value)
        const options = sourceFor(field)
        const match = options.find(option => option.value === String(value))
        return match ? match.label : String(value)
    }

    const typeField = config.typeFilterKey ? config.fields.find(field => field.key === config.typeFilterKey) : undefined
    const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 print:hidden">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{config.title}</h1>
                    <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{config.subtitle}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <Button variant="outline" onClick={() => window.print()} className="gap-2"><Printer className="h-4 w-4" /> Imprimer</Button>
                    <Button variant="outline" onClick={() => void exportCsv()} className="gap-2"><Download className="h-4 w-4" /> Export CSV</Button>
                    <Button onClick={openCreate} className="gap-2 rounded-lg bg-black text-white hover:bg-black/90"><Plus className="h-4 w-4" /> {config.createLabel}</Button>
                </div>
            </div>

            {message && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 print:hidden dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{message}</div>}

            <div className="flex flex-wrap gap-3 print:hidden">
                <input value={search} onChange={event => { setSearch(event.target.value); setPage(0) }} placeholder="Rechercher…" className="apple-input w-64" />
                <select value={statusFilter} onChange={event => { setStatusFilter(event.target.value); setPage(0) }} className="apple-select w-48">
                    <option value="">Tous les statuts</option>
                    {config.statusOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
                {typeField && (
                    <select value={typeFilter} onChange={event => { setTypeFilter(event.target.value); setPage(0) }} className="apple-select w-56">
                        <option value="">Tous les types</option>
                        {sourceFor(typeField).map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </select>
                )}
                <Button variant="outline" onClick={() => void load()} className="gap-2"><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Actualiser</Button>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle className="text-[#111827] dark:text-white">{config.title} ({total})</CardTitle></CardHeader>
                <CardContent>
                    {loading ? (
                        <p className="py-10 text-center text-[#6B7280]">Chargement…</p>
                    ) : rows.length === 0 ? (
                        <p className="py-10 text-center text-[#6B7280]">Aucun enregistrement. Créez le premier.</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-[#E5E7EB] text-left text-[#6B7280]">
                                        {config.columns.map(column => <th key={column.key} className="px-3 py-2 font-medium">{column.label}</th>)}
                                        <th className="px-3 py-2 text-right font-medium print:hidden">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rows.map(row => (
                                        <tr key={row.id} className="cursor-pointer border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] dark:hover:bg-[#2a3035]" onClick={() => openEdit(row)}>
                                            {config.columns.map(column => (
                                                <td key={column.key} className="px-3 py-2">
                                                    {column.key === "student_name"
                                                        ? (row.student_name || "—")
                                                        : labelFor(config.fields.find(field => field.key === column.key), row[column.key])}
                                                </td>
                                            ))}
                                            <td className="px-3 py-2 text-right print:hidden" onClick={event => event.stopPropagation()}>
                                                <Button size="sm" variant="ghost" title="Modifier" onClick={() => openEdit(row)}><Pencil className="h-4 w-4" /></Button>
                                                <Button size="sm" variant="ghost" className="text-red-600" title="Supprimer" onClick={() => void remove(row)}><Trash2 className="h-4 w-4" /></Button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                    {pages > 1 && (
                        <div className="mt-4 flex items-center justify-between text-sm print:hidden">
                            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>Précédent</Button>
                            <span className="text-[#6B7280]">Page {page + 1} / {pages}</span>
                            <Button variant="outline" size="sm" disabled={page + 1 >= pages} onClick={() => setPage(page + 1)}>Suivant</Button>
                        </div>
                    )}
                </CardContent>
            </Card>

            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-[640px]">
                    <DialogHeader><DialogTitle>{editing ? `Modifier — ${config.title}` : config.createLabel}</DialogTitle></DialogHeader>
                    <div className="grid gap-4 py-2 sm:grid-cols-2">
                        {config.fields.map(field => {
                            const options = sourceFor(field)
                            const isSourceField = ["student", "class", "subject", "room", "reference"].includes(field.type)
                            const control = field.type === "textarea" ? (
                                <textarea value={String(form[field.key] ?? "")} onChange={event => setForm({ ...form, [field.key]: event.target.value })} className="apple-input min-h-20 w-full" placeholder={field.placeholder} />
                            ) : field.type === "checkbox" ? (
                                <label className="flex h-10 items-center gap-2 text-sm">
                                    <input type="checkbox" checked={Boolean(form[field.key])} onChange={event => setForm({ ...form, [field.key]: event.target.checked })} /> {field.placeholder || "Oui"}
                                </label>
                            ) : field.type === "date" ? (
                                <input type="date" value={String(form[field.key] ?? "")} onChange={event => setForm({ ...form, [field.key]: event.target.value })} className="apple-input w-full" />
                            ) : field.type === "number" ? (
                                <input type="number" value={String(form[field.key] ?? "")} onChange={event => setForm({ ...form, [field.key]: event.target.value })} className="apple-input w-full" placeholder={field.placeholder} />
                            ) : field.type === "text" ? (
                                <input value={String(form[field.key] ?? "")} onChange={event => setForm({ ...form, [field.key]: event.target.value })} className="apple-input w-full" placeholder={field.placeholder} />
                            ) : (
                                <select value={String(form[field.key] ?? "")} onChange={event => setForm({ ...form, [field.key]: event.target.value })} className="apple-select w-full">
                                    <option value="">{field.placeholder || "Sélectionner…"}</option>
                                    {options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
                                </select>
                            )
                            return (
                                <div key={field.key} className={`space-y-1 ${field.type === "textarea" ? "sm:col-span-2" : ""}`}>
                                    <label className="text-sm text-[#6B7280]">{field.label}{field.required ? " *" : ""}</label>
                                    {isSourceField ? (
                                        <RequireOptions
                                            loaded={sourcesLoaded}
                                            count={options.length}
                                            message={field.missingMessage || `Impossible de continuer. La liste « ${field.label} » est vide : créez d'abord la donnée manquante.`}
                                            actions={field.createHref ? [{ label: field.createLabel || "Créer", href: `/${locale}${field.createHref}` }] : []}
                                        >
                                            {control}
                                        </RequireOptions>
                                    ) : control}
                                    {fieldErrors[field.key] && <p className="text-xs text-red-600">{fieldErrors[field.key]}</p>}
                                </div>
                            )
                        })}
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDialogOpen(false)}>Annuler</Button>
                        <Button onClick={() => void save()} disabled={saving || missingRequired(requiredGates)} className="bg-black text-white hover:bg-black/90">
                            {saving ? "Enregistrement…" : "Enregistrer"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {sourcesLoaded && requiredGates.some(gate => gate.count === 0) && !dialogOpen && (
                <MissingDependency
                    message="Des données préalables sont manquantes pour créer un enregistrement dans ce module — ouvrez le formulaire pour voir le détail et les actions de création rapide."
                    actions={[]}
                />
            )}
        </div>
    )
}
