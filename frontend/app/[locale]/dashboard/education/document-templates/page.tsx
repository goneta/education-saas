"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useTranslations } from "next-intl"
import {
    Award, CheckCircle2, Copy, Eye, FileUp, Pencil, Plus, RefreshCw, Sparkles, Star, Trash2,
} from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface Template {
    id: number
    kind: "diploma" | "certificate"
    name: string
    description?: string | null
    title_text?: string | null
    body_text?: string | null
    background_type?: string | null
    background_filename?: string | null
    is_default: boolean
    is_active: boolean
}
interface StudentRow { id: number; full_name?: string | null; student_profile?: { id: number; registration_number?: string | null } | null }

const EMPTY_FORM = { kind: "certificate", name: "", description: "", title_text: "", body_text: "" }

export default function DocumentTemplatesPage() {
    const t = useTranslations("docTemplates")
    const { token } = useAuth()
    const [rows, setRows] = useState<Template[]>([])
    const [placeholders, setPlaceholders] = useState<string[]>([])
    const [students, setStudents] = useState<StudentRow[]>([])
    const [kindFilter, setKindFilter] = useState<string>("all")
    const [editing, setEditing] = useState<Template | null>(null)
    const [creating, setCreating] = useState(false)
    const [form, setForm] = useState({ ...EMPTY_FORM })
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [toast, setToast] = useState<string | null>(null)
    const bodyRef = useRef<HTMLTextAreaElement | null>(null)

    // Generate panel state
    const [genStudent, setGenStudent] = useState("")
    const [genTemplate, setGenTemplate] = useState("")
    const [genKind, setGenKind] = useState<"diploma" | "certificate">("certificate")
    const [genTraining, setGenTraining] = useState("")
    const [genDirector, setGenDirector] = useState("")
    const [genDate, setGenDate] = useState("")

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])
    const authOnly = useMemo(() => token ? { Authorization: `Bearer ${token}` } : undefined, [token])

    const api = useCallback(async (path: string, init?: RequestInit) => {
        if (!headers) return null
        const res = await fetch(`${API_BASE_URL}/document-templates${path}`, { headers, ...init })
        if (!res.ok) { setError((await res.json().catch(() => ({}))).detail || t("error")); return null }
        setError(null)
        return res.json()
    }, [headers, t])

    const load = useCallback(async () => { const d = await api(""); if (d) setRows(d) }, [api])

    useEffect(() => {
        if (!headers) return
        void load()
        void (async () => {
            const p = await api("/placeholders"); if (p) setPlaceholders(p.placeholders)
            const res = await fetch(`${API_BASE_URL}/students`, { headers })
            if (res.ok) setStudents(await res.json())
        })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [headers])

    const flash = (m: string) => { setToast(m); setTimeout(() => setToast(null), 2500) }
    const filtered = rows.filter(r => kindFilter === "all" || r.kind === kindFilter)

    const openCreate = () => { setCreating(true); setEditing(null); setForm({ ...EMPTY_FORM }) }
    const openEdit = (tpl: Template) => {
        setEditing(tpl); setCreating(false)
        setForm({ kind: tpl.kind, name: tpl.name, description: tpl.description || "", title_text: tpl.title_text || "", body_text: tpl.body_text || "" })
    }
    const closeForm = () => { setCreating(false); setEditing(null) }

    const saveForm = async () => {
        setBusy(true)
        try {
            const body = { name: form.name, description: form.description || null, title_text: form.title_text || null, body_text: form.body_text || null }
            const d = editing
                ? await api(`/${editing.id}`, { method: "PATCH", body: JSON.stringify(body) })
                : await api("", { method: "POST", body: JSON.stringify({ ...body, kind: form.kind }) })
            if (d) { closeForm(); flash(t("saved")); void load() }
        } finally { setBusy(false) }
    }

    const insertPlaceholder = (key: string) => {
        const snippet = `{{${key}}}`
        const el = bodyRef.current
        if (el) {
            const start = el.selectionStart ?? form.body_text.length
            const next = form.body_text.slice(0, start) + snippet + form.body_text.slice(el.selectionEnd ?? start)
            setForm({ ...form, body_text: next })
        } else {
            setForm({ ...form, body_text: form.body_text + snippet })
        }
    }

    const act = async (path: string, method = "POST") => {
        setBusy(true)
        try { const d = await api(path, { method }); if (d) { flash(t("saved")); void load() } }
        finally { setBusy(false) }
    }
    const remove = async (tpl: Template) => {
        if (!window.confirm(t("confirmDelete"))) return
        await act(`/${tpl.id}`, "DELETE")
    }

    const uploadBackground = async (tpl: Template, file: File) => {
        if (!authOnly) return
        setBusy(true)
        try {
            const data = new FormData()
            data.append("file", file)
            const res = await fetch(`${API_BASE_URL}/document-templates/${tpl.id}/background`, { method: "POST", headers: authOnly, body: data })
            if (!res.ok) { setError((await res.json().catch(() => ({}))).detail || t("error")); return }
            setError(null); flash(t("saved")); void load()
        } finally { setBusy(false) }
    }

    const fetchPdf = async (path: string, body: unknown, filename: string) => {
        if (!headers) return
        setBusy(true)
        try {
            const res = await fetch(`${API_BASE_URL}/document-templates${path}`, { method: "POST", headers, body: JSON.stringify(body) })
            if (!res.ok) { setError((await res.json().catch(() => ({}))).detail || t("error")); return }
            setError(null)
            const blob = await res.blob()
            const url = URL.createObjectURL(blob)
            const a = document.createElement("a")
            a.href = url; a.download = filename; a.click()
            URL.revokeObjectURL(url)
        } finally { setBusy(false) }
    }

    const preview = (tpl: Template) => fetchPdf(`/${tpl.id}/preview`, { overrides: {} }, `preview-${tpl.kind}-${tpl.id}.pdf`)

    const generate = () => {
        if (!genStudent) return
        const overrides: Record<string, string> = {}
        if (genTraining) overrides.training_name = genTraining
        if (genDirector) overrides.director_name = genDirector
        if (genDate) overrides.graduation_date = genDate
        const body: Record<string, unknown> = { student_id: Number(genStudent), overrides }
        if (genTemplate) body.template_id = Number(genTemplate)
        else body.kind = genKind
        void fetchPdf("/generate", body, `${genTemplate ? "document" : genKind}.pdf`)
    }

    const kindBadge = (kind: Template["kind"]) => (
        <span className="rounded-full bg-[#F1F3F5] px-2 py-0.5 text-xs font-medium text-[#374151] dark:bg-[#2a3035] dark:text-[#c7d0da]">
            {t(`kinds.${kind}` as "kinds.diploma")}
        </span>
    )

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <h1 className="flex items-center gap-2 text-2xl font-bold text-[#111827] dark:text-white"><Award className="h-6 w-6" /> {t("title")}</h1>
                    <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
                </div>
                <Button className="bg-black text-white hover:bg-black/90" onClick={openCreate}><Plus className="mr-1 h-4 w-4" /> {t("newTemplate")}</Button>
            </div>

            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}
            {toast && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-[#0f1f1d] dark:text-emerald-100">{toast}</div>}

            {/* Create / edit form */}
            {(creating || editing) && (
                <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader><CardTitle className="text-base">{editing ? t("editTemplate") : t("newTemplate")}</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-4 sm:grid-cols-2">
                            {!editing && (
                                <label className="text-sm">{t("kind")}
                                    <select className="apple-select mt-1 w-full" value={form.kind} onChange={e => setForm({ ...form, kind: e.target.value })}>
                                        <option value="certificate">{t("kinds.certificate")}</option>
                                        <option value="diploma">{t("kinds.diploma")}</option>
                                    </select>
                                </label>
                            )}
                            <label className="text-sm">{t("name")}<input className="apple-input mt-1 w-full" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label>
                            <label className="text-sm">{t("titleText")}<input className="apple-input mt-1 w-full" value={form.title_text} onChange={e => setForm({ ...form, title_text: e.target.value })} placeholder="DIPLÔME / CERTIFICAT" /></label>
                            <label className="text-sm">{t("description")}<input className="apple-input mt-1 w-full" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></label>
                        </div>
                        <label className="block text-sm">{t("bodyText")}
                            <textarea ref={bodyRef} className="apple-input mt-1 min-h-24 w-full" value={form.body_text} onChange={e => setForm({ ...form, body_text: e.target.value })} />
                            <span className="text-xs text-[#94A3B8]">{t("bodyHint")}</span>
                        </label>
                        <div>
                            <p className="mb-1 text-xs font-semibold uppercase text-[#6B7280]">{t("placeholders")}</p>
                            <div className="flex flex-wrap gap-1.5">
                                {placeholders.map(p => (
                                    <button key={p} type="button" onClick={() => insertPlaceholder(p)} className="rounded-full border border-[#E5E7EB] px-2 py-0.5 font-mono text-xs hover:bg-[#F6F7F9] dark:border-[#3b4248] dark:hover:bg-[#2a3035]">{`{{${p}}}`}</button>
                                ))}
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={closeForm}>{t("cancel")}</Button>
                            <Button className="bg-black text-white hover:bg-black/90" disabled={busy || !form.name.trim()} onClick={saveForm}>{t("save")}</Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Kind filter */}
            <div className="flex gap-1">
                {["all", "diploma", "certificate"].map(k => (
                    <button key={k} onClick={() => setKindFilter(k)} className={`rounded-full px-3 py-1 text-xs font-medium transition ${kindFilter === k ? "bg-black text-white dark:bg-white dark:text-black" : "border border-[#E5E7EB] text-[#6B7280] hover:bg-[#F6F7F9] dark:border-[#3b4248] dark:hover:bg-[#2a3035]"}`}>
                        {k === "all" ? "—" : t(`kinds.${k}` as "kinds.diploma")}
                    </button>
                ))}
            </div>

            {/* Template list */}
            {filtered.length === 0 ? (
                <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardContent className="p-10 text-center text-sm text-[#6B7280]">{t("empty")}</CardContent>
                </Card>
            ) : (
                <div className="grid gap-4 lg:grid-cols-2">
                    {filtered.map(tpl => (
                        <Card key={tpl.id} className={`rounded-2xl border shadow-sm dark:bg-[#202528] ${tpl.is_default ? "border-black ring-1 ring-black dark:border-white dark:ring-white" : "border-[#E5E7EB] dark:border-[#3b4248]"}`}>
                            <CardContent className="space-y-3 p-5">
                                <div className="flex items-start justify-between gap-2">
                                    <div>
                                        <p className="font-semibold text-[#111827] dark:text-white">{tpl.name}</p>
                                        <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs">
                                            {kindBadge(tpl.kind)}
                                            {tpl.is_default && <span className="rounded-full bg-black px-2 py-0.5 font-medium text-white dark:bg-white dark:text-black">{t("default")}</span>}
                                            <span className={`rounded-full px-2 py-0.5 font-medium ${tpl.is_active ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200" : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300"}`}>{tpl.is_active ? t("active") : t("inactive")}</span>
                                        </div>
                                        {tpl.background_filename && <p className="mt-1 text-xs text-[#6B7280]">{t("background")}: {tpl.background_filename}</p>}
                                    </div>
                                </div>
                                <div className="flex flex-wrap gap-1.5">
                                    <Button variant="outline" size="sm" disabled={busy} onClick={() => preview(tpl)}><Eye className="mr-1 h-3.5 w-3.5" /> {t("preview")}</Button>
                                    <Button variant="outline" size="sm" disabled={busy} onClick={() => openEdit(tpl)}><Pencil className="mr-1 h-3.5 w-3.5" /> {t("editTemplate")}</Button>
                                    <Button variant="outline" size="sm" disabled={busy} onClick={() => act(`/${tpl.id}/duplicate`)}><Copy className="mr-1 h-3.5 w-3.5" /> {t("duplicate")}</Button>
                                    {!tpl.is_default && <Button variant="outline" size="sm" disabled={busy} onClick={() => act(`/${tpl.id}/default`)}><Star className="mr-1 h-3.5 w-3.5" /> {t("setDefault")}</Button>}
                                    <Button variant="outline" size="sm" disabled={busy} onClick={() => api(`/${tpl.id}`, { method: "PATCH", body: JSON.stringify({ is_active: !tpl.is_active }) }).then(d => { if (d) { flash(t("saved")); void load() } })}>
                                        <CheckCircle2 className="mr-1 h-3.5 w-3.5" /> {tpl.is_active ? t("deactivate") : t("activate")}
                                    </Button>
                                    <label className="inline-flex">
                                        <input type="file" accept=".pdf,.docx,.png,.jpg,.jpeg" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) void uploadBackground(tpl, f); e.target.value = "" }} />
                                        <span className="inline-flex h-9 cursor-pointer items-center gap-1.5 rounded-full border border-[#E5E7EB] px-4 text-sm hover:bg-[#F6F7F9] dark:border-[#3b4248] dark:hover:bg-[#2a3035]"><FileUp className="h-3.5 w-3.5" /> {t("uploadBackground")}</span>
                                    </label>
                                    <Button variant="outline" size="sm" disabled={busy} onClick={() => remove(tpl)}><Trash2 className="h-3.5 w-3.5" /></Button>
                                </div>
                                <p className="text-xs text-[#94A3B8]">{t("backgroundNote")}</p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Generate panel */}
            <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base"><Sparkles className="h-4 w-4" /> {t("generate")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("generateDesc")}</p>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        <label className="text-sm">{t("student")}
                            <select className="apple-select mt-1 w-full" value={genStudent} onChange={e => setGenStudent(e.target.value)}>
                                <option value="">—</option>
                                {students.filter(s => s.student_profile?.id).map(s => (
                                    <option key={s.student_profile!.id} value={s.student_profile!.id}>
                                        {s.full_name || `#${s.id}`}{s.student_profile?.registration_number ? ` (${s.student_profile.registration_number})` : ""}
                                    </option>
                                ))}
                            </select>
                        </label>
                        <label className="text-sm">{t("template")}
                            <select className="apple-select mt-1 w-full" value={genTemplate} onChange={e => setGenTemplate(e.target.value)}>
                                <option value="">{t("defaultTemplate")}</option>
                                {rows.filter(r => r.is_active).map(r => <option key={r.id} value={r.id}>{r.name} · {t(`kinds.${r.kind}` as "kinds.diploma")}</option>)}
                            </select>
                        </label>
                        {!genTemplate && (
                            <label className="text-sm">{t("kind")}
                                <select className="apple-select mt-1 w-full" value={genKind} onChange={e => setGenKind(e.target.value as "diploma" | "certificate")}>
                                    <option value="certificate">{t("kinds.certificate")}</option>
                                    <option value="diploma">{t("kinds.diploma")}</option>
                                </select>
                            </label>
                        )}
                        <label className="text-sm">{t("trainingName")}<input className="apple-input mt-1 w-full" value={genTraining} onChange={e => setGenTraining(e.target.value)} /></label>
                        <label className="text-sm">{t("directorName")}<input className="apple-input mt-1 w-full" value={genDirector} onChange={e => setGenDirector(e.target.value)} /></label>
                        <label className="text-sm">{t("graduationDate")}<input type="date" className="apple-input mt-1 w-full" value={genDate} onChange={e => setGenDate(e.target.value)} /></label>
                    </div>
                    <Button className="bg-black text-white hover:bg-black/90" disabled={busy || !genStudent} onClick={generate}>
                        {busy ? <RefreshCw className="mr-1 h-4 w-4 animate-spin" /> : <Award className="mr-1 h-4 w-4" />} {t("generateBtn")}
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}
