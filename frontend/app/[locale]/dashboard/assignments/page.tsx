"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useLocale, useTranslations } from "next-intl"
import { BookMarked, CheckCircle2, ClipboardList, RefreshCw, Send, Sparkles, Wand2 } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface Stats { students: number; submitted: number; missing: number; graded: number; late: number; average?: number | null; success_rate?: number | null; max_score: number }
interface Assignment { id: number; title: string; assignment_type: string; mode: string; status: string; class_id: number; subject_id?: number | null; max_score: number; due_date?: string | null; ai_generated: boolean; stats?: Stats }
interface RosterRow { student_id: number; student_name?: string | null; submission_id?: number | null; status: string; is_late: boolean; score?: number | null; ai_graded: boolean }
interface ClassOption { id: number; name: string }
interface SubjectOption { id: number; name: string }

const TYPES = ["devoir", "exercice", "interrogation", "controle", "evaluation", "examen", "quiz", "devoir_maison", "tp", "projet", "expose"]

export default function AssignmentsPage() {
    const t = useTranslations("assignments")
    const locale = useLocale()
    const { token } = useAuth()
    const [rows, setRows] = useState<Assignment[]>([])
    const [classes, setClasses] = useState<ClassOption[]>([])
    const [subjects, setSubjects] = useState<SubjectOption[]>([])
    const [statusFilter, setStatusFilter] = useState("")
    const [error, setError] = useState<string | null>(null)
    const [busy, setBusy] = useState<string | null>(null)
    const [form, setForm] = useState({ title: "", assignment_type: "devoir", mode: "online", class_id: "", subject_id: "", instructions: "", max_score: "20", due_date: "", answer_key_release: "after_due" })
    const [ai, setAi] = useState({ subject: "", level: "", chapter: "", num_questions: "8", difficulty: "moyen" })
    const [aiPreview, setAiPreview] = useState<{ content: unknown; answer_key: unknown; max_score: number } | null>(null)
    const [roster, setRoster] = useState<{ assignment: Assignment; roster: RosterRow[]; stats: Stats } | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/assignments/teaching${statusFilter ? `?status=${statusFilter}` : ""}`, { headers })
        if (res.ok) setRows(await res.json())
        const [c, s] = await Promise.all([
            fetch(`${API_BASE_URL}/education/classes`, { headers }),
            fetch(`${API_BASE_URL}/education/subjects`, { headers }),
        ])
        if (c.ok) setClasses((await c.json()).map((x: ClassOption) => ({ id: x.id, name: x.name })))
        if (s.ok) setSubjects((await s.json()).map((x: SubjectOption) => ({ id: x.id, name: x.name })))
    }, [headers, statusFilter])

    useEffect(() => { void load() }, [load])

    const post = async (url: string, body?: unknown) => {
        const res = await fetch(`${API_BASE_URL}${url}`, { method: "POST", headers, body: body ? JSON.stringify(body) : undefined })
        if (!res.ok) { setError((await res.json().catch(() => ({}))).detail || "—"); return null }
        return res.json()
    }

    const create = async (publish: boolean) => {
        if (!headers || !form.class_id) return
        setBusy("create"); setError(null)
        try {
            const created = await post("/assignments", {
                ...form, class_id: Number(form.class_id), subject_id: form.subject_id ? Number(form.subject_id) : null,
                max_score: Number(form.max_score) || 20, due_date: form.due_date ? new Date(form.due_date).toISOString() : null,
                content: aiPreview?.content, answer_key: aiPreview?.answer_key, ai_generated: Boolean(aiPreview),
            })
            if (created && publish) await post(`/assignments/${created.id}/publish`)
            if (created) { setForm({ ...form, title: "", instructions: "" }); setAiPreview(null); void load() }
        } finally { setBusy(null) }
    }

    const generate = async () => {
        if (!headers || !ai.subject) return
        setBusy("ai"); setError(null)
        try {
            const out = await post("/assignments/ai-generate", { ...ai, num_questions: Number(ai.num_questions) || 8, language: locale })
            if (out) { setAiPreview(out); setForm(f => ({ ...f, title: f.title || `${f.assignment_type} — ${ai.subject}`, subject_id: f.subject_id, max_score: String(out.max_score || 20) })) }
        } finally { setBusy(null) }
    }

    const openRoster = async (a: Assignment) => {
        const res = await fetch(`${API_BASE_URL}/assignments/${a.id}/roster`, { headers })
        if (res.ok) setRoster(await res.json())
    }

    const gradeRow = async (row: RosterRow, useAi: boolean) => {
        if (!row.submission_id) return
        setBusy(`grade-${row.submission_id}`); setError(null)
        try {
            if (useAi) {
                await post(`/assignments/submissions/${row.submission_id}/ai-grade?language=${locale}`)
            } else {
                const score = window.prompt(t("enterScore", { max: roster?.stats.max_score ?? 20 }))
                if (score === null) return
                await post(`/assignments/submissions/${row.submission_id}/grade`, { score: Number(score), publish: true })
            }
            if (roster) void openRoster(roster.assignment)
        } finally { setBusy(null) }
    }

    const statusBadge = (status: string) => {
        const map: Record<string, string> = { draft: "bg-gray-100 text-gray-700", published: "bg-blue-100 text-blue-800", closed: "bg-gray-100 text-gray-700", submitted: "bg-amber-100 text-amber-800", graded: "bg-emerald-100 text-emerald-800", absent: "bg-red-100 text-red-800", late: "bg-orange-100 text-orange-800", returned: "bg-emerald-100 text-emerald-800" }
        return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${map[status] || "bg-gray-100 text-gray-700"}`}>{t(`status.${status}` as "status.draft")}</span>
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle className="flex items-center gap-2"><Wand2 className="h-4 w-4" /> {t("create")}</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-3 md:grid-cols-3">
                        <label className="text-xs text-[#6B7280]">{t("titleField")}<input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className="apple-input mt-1 w-full" /></label>
                        <label className="text-xs text-[#6B7280]">{t("type")}<select value={form.assignment_type} onChange={e => setForm({ ...form, assignment_type: e.target.value })} className="apple-select mt-1 w-full">{TYPES.map(x => <option key={x} value={x}>{t(`types.${x}` as "types.devoir")}</option>)}</select></label>
                        <label className="text-xs text-[#6B7280]">{t("mode")}<select value={form.mode} onChange={e => setForm({ ...form, mode: e.target.value })} className="apple-select mt-1 w-full"><option value="online">{t("modeOnline")}</option><option value="paper">{t("modePaper")}</option></select></label>
                        <label className="text-xs text-[#6B7280]">{t("class")}<select value={form.class_id} onChange={e => setForm({ ...form, class_id: e.target.value })} className="apple-select mt-1 w-full"><option value="">—</option>{classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
                        <label className="text-xs text-[#6B7280]">{t("subject")}<select value={form.subject_id} onChange={e => setForm({ ...form, subject_id: e.target.value })} className="apple-select mt-1 w-full"><option value="">—</option>{subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select></label>
                        <label className="text-xs text-[#6B7280]">{t("maxScore")}<input type="number" value={form.max_score} onChange={e => setForm({ ...form, max_score: e.target.value })} className="apple-input mt-1 w-full" /></label>
                        <label className="text-xs text-[#6B7280]">{t("dueDate")}<input type="datetime-local" value={form.due_date} onChange={e => setForm({ ...form, due_date: e.target.value })} className="apple-input mt-1 w-full" /></label>
                        <label className="text-xs text-[#6B7280]">{t("answerKeyRelease")}<select value={form.answer_key_release} onChange={e => setForm({ ...form, answer_key_release: e.target.value })} className="apple-select mt-1 w-full"><option value="never">{t("release.never")}</option><option value="after_due">{t("release.after_due")}</option><option value="immediate">{t("release.immediate")}</option></select></label>
                    </div>
                    <label className="block text-xs text-[#6B7280]">{t("instructions")}<textarea value={form.instructions} onChange={e => setForm({ ...form, instructions: e.target.value })} className="apple-input mt-1 min-h-20 w-full" /></label>

                    <div className="rounded-xl border border-[#E5E7EB] p-3 dark:border-[#3b4248]">
                        <p className="mb-2 flex items-center gap-2 text-sm font-semibold"><Sparkles className="h-4 w-4" /> {t("aiHelper")}</p>
                        <div className="grid gap-2 md:grid-cols-5">
                            <input value={ai.subject} onChange={e => setAi({ ...ai, subject: e.target.value })} placeholder={t("subject")} className="apple-input" />
                            <input value={ai.level} onChange={e => setAi({ ...ai, level: e.target.value })} placeholder={t("level")} className="apple-input" />
                            <input value={ai.chapter} onChange={e => setAi({ ...ai, chapter: e.target.value })} placeholder={t("chapter")} className="apple-input" />
                            <input type="number" value={ai.num_questions} onChange={e => setAi({ ...ai, num_questions: e.target.value })} placeholder={t("numQuestions")} className="apple-input" />
                            <Button onClick={generate} disabled={busy !== null || !ai.subject} variant="outline">{busy === "ai" ? <RefreshCw className="mr-1 h-4 w-4 animate-spin" /> : <Sparkles className="mr-1 h-4 w-4" />}{t("generate")}</Button>
                        </div>
                        {aiPreview && <p className="mt-2 text-xs text-emerald-700">{t("aiReady")}</p>}
                        <p className="mt-1 text-xs text-[#94A3B8]">{t("aiHint")}</p>
                    </div>

                    <div className="flex gap-2">
                        <Button onClick={() => create(false)} disabled={busy !== null || !form.class_id} variant="outline">{t("saveDraft")}</Button>
                        <Button onClick={() => create(true)} disabled={busy !== null || !form.class_id} className="bg-black text-white hover:bg-black/90"><Send className="mr-1 h-4 w-4" /> {t("publish")}</Button>
                    </div>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><ClipboardList className="h-4 w-4" /> {t("myAssignments")}</CardTitle>
                    <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="apple-select mt-2 w-48"><option value="">{t("allStatuses")}</option><option value="draft">{t("status.draft")}</option><option value="published">{t("status.published")}</option><option value="closed">{t("status.closed")}</option></select>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("titleField")}</th><th className="px-3 py-2">{t("type")}</th><th className="px-3 py-2">{t("status.label")}</th><th className="px-3 py-2">{t("submittedCol")}</th><th className="px-3 py-2">{t("average")}</th><th className="px-3 py-2"></th></tr></thead>
                            <tbody>
                                {rows.length === 0 ? <tr><td colSpan={6} className="px-3 py-6 text-center text-[#6B7280]">{t("empty")}</td></tr> : rows.map(a => (
                                    <tr key={a.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                        <td className="px-3 py-2 font-medium">{a.title}{a.ai_generated && <Sparkles className="ml-1 inline h-3 w-3 text-[#0F766E]" />}</td>
                                        <td className="px-3 py-2">{t(`types.${a.assignment_type}` as "types.devoir")}</td>
                                        <td className="px-3 py-2">{statusBadge(a.status)}</td>
                                        <td className="px-3 py-2">{a.stats ? `${a.stats.submitted}/${a.stats.students}` : "—"}</td>
                                        <td className="px-3 py-2">{a.stats?.average ?? "—"}</td>
                                        <td className="px-3 py-2 text-right">
                                            {a.status === "draft" && <Button size="sm" variant="outline" onClick={() => post(`/assignments/${a.id}/publish`).then(() => load())}>{t("publish")}</Button>}
                                            <Button size="sm" variant="outline" className="ml-2" onClick={() => openRoster(a)}><CheckCircle2 className="mr-1 h-3 w-3" /> {t("grade")}</Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            {roster && (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><BookMarked className="h-4 w-4" /> {t("gradeTitle", { title: roster.assignment.title })}</CardTitle>
                        <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("gradeStats", { submitted: roster.stats.submitted, students: roster.stats.students, graded: roster.stats.graded, average: String(roster.stats.average ?? "—") })}</p>
                        <div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => post(`/assignments/${roster.assignment.id}/push-to-gradebook`).then(() => setError(null))}>{t("pushGradebook")}</Button></div>
                    </CardHeader>
                    <CardContent>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("student")}</th><th className="px-3 py-2">{t("status.label")}</th><th className="px-3 py-2">{t("score")}</th><th className="px-3 py-2"></th></tr></thead>
                                <tbody>
                                    {roster.roster.map(r => (
                                        <tr key={r.student_id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                            <td className="px-3 py-2 font-medium">{r.student_name}{r.is_late && <span className="ml-1 text-xs text-orange-600">({t("status.late")})</span>}</td>
                                            <td className="px-3 py-2">{statusBadge(r.status)}</td>
                                            <td className="px-3 py-2">{r.score != null ? `${r.score}/${roster.stats.max_score}` : "—"}{r.ai_graded && <Sparkles className="ml-1 inline h-3 w-3 text-[#0F766E]" />}</td>
                                            <td className="px-3 py-2 text-right">
                                                {r.submission_id ? (
                                                    <>
                                                        <Button size="sm" variant="outline" disabled={busy !== null} onClick={() => gradeRow(r, true)}><Sparkles className="mr-1 h-3 w-3" /> {t("aiGrade")}</Button>
                                                        <Button size="sm" variant="outline" className="ml-2" disabled={busy !== null} onClick={() => gradeRow(r, false)}>{t("gradeManual")}</Button>
                                                    </>
                                                ) : <span className="text-xs text-[#94A3B8]">{t("noSubmission")}</span>}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
