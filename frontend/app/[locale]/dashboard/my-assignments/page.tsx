"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { BookOpenCheck, ClipboardList, RefreshCw, Save, Send } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface Question { id: number | string; type: string; prompt: string; options?: string[] | null; points?: number }
interface AnswerKeyItem { id: number | string; expected_answer: string; explanation?: string; points?: number }
interface Submission { id: number; status: string; score?: number | null; feedback?: string | null; is_late: boolean; answers?: Record<string, string> | null; submitted_at?: string | null }
interface Assignment { id: number; title: string; assignment_type: string; mode: string; max_score: number; due_date?: string | null; instructions?: string | null; content?: { questions?: Question[] } | null; answer_key?: { items?: AnswerKeyItem[]; rubric?: string } | null; submission?: Submission | null; answer_key_visible: boolean }

interface Child { student_id: number; full_name?: string | null }

export default function MyAssignmentsPage() {
    const t = useTranslations("assignments")
    const { token, user } = useAuth()
    const isParent = String(user?.role || "").toLowerCase() === "parent"
    const [children, setChildren] = useState<Child[]>([])
    const [studentId, setStudentId] = useState<number | null>(null)
    const [rows, setRows] = useState<Assignment[]>([])
    const [open, setOpen] = useState<Assignment | null>(null)
    const [answers, setAnswers] = useState<Record<string, string>>({})
    const [busy, setBusy] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])
    const sidQs = isParent && studentId ? `?student_id=${studentId}` : ""

    useEffect(() => {
        if (!headers || !isParent) return
        void (async () => {
            const res = await fetch(`${API_BASE_URL}/self-documents/children`, { headers })
            if (res.ok) { const c: Child[] = await res.json(); setChildren(c); if (c.length) setStudentId(c[0].student_id) }
        })()
    }, [headers, isParent])

    const load = useCallback(async () => {
        if (!headers || (isParent && studentId === null)) return
        const res = await fetch(`${API_BASE_URL}/assignments/mine${sidQs}`, { headers })
        if (res.ok) setRows(await res.json())
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }, [headers, isParent, studentId, sidQs])

    useEffect(() => { void load() }, [load])

    const openAssignment = (a: Assignment) => {
        setOpen(a); setError(null)
        setAnswers((a.submission?.answers as Record<string, string>) || {})
    }

    const save = async (submit: boolean) => {
        if (!headers || !open || isParent) return
        setBusy(submit ? "submit" : "save"); setError(null)
        try {
            const url = submit ? `/assignments/${open.id}/submit` : `/assignments/${open.id}/autosave`
            const res = await fetch(`${API_BASE_URL}${url}`, { method: "POST", headers, body: JSON.stringify({ answers }) })
            if (!res.ok) { setError((await res.json().catch(() => ({}))).detail || "—"); return }
            if (submit) setOpen(null)
            void load()
        } finally { setBusy(null) }
    }

    const bucket = (a: Assignment) => {
        const s = a.submission?.status
        if (s === "graded" || s === "returned") return "graded"
        if (s === "submitted") return "done"
        return "todo"
    }
    const grouped = useMemo(() => ({
        todo: rows.filter(a => bucket(a) === "todo"),
        done: rows.filter(a => bucket(a) === "done"),
        graded: rows.filter(a => bucket(a) === "graded"),
    }), [rows])

    const card = (a: Assignment) => (
        <button key={a.id} onClick={() => openAssignment(a)} className="w-full rounded-xl border border-[#E5E7EB] p-3 text-left hover:bg-[#F6F7F9] dark:border-[#3b4248] dark:hover:bg-[#2a3035]">
            <div className="flex items-center justify-between gap-2">
                <span className="font-medium">{a.title}</span>
                <span className="text-xs text-[#6B7280]">{t(`types.${a.assignment_type}` as "types.devoir")}</span>
            </div>
            <div className="mt-1 flex items-center justify-between text-xs text-[#6B7280]">
                <span>{a.due_date ? `${t("dueDate")}: ${new Date(a.due_date).toLocaleDateString()}` : ""}</span>
                {a.submission?.score != null && <span className="font-semibold text-emerald-700">{a.submission.score}/{a.max_score}</span>}
            </div>
        </button>
    )

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("studentTitle")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("studentSubtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            {isParent && children.length > 1 && (
                <div className="max-w-sm"><label className="text-xs text-[#6B7280]">{t("child")}<select value={studentId ?? ""} onChange={e => setStudentId(Number(e.target.value))} className="apple-select mt-1 w-full">{children.map(c => <option key={c.student_id} value={c.student_id}>{c.full_name || `#${c.student_id}`}</option>)}</select></label></div>
            )}

            {open ? (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><BookOpenCheck className="h-4 w-4" /> {open.title}</CardTitle>
                        <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t(`types.${open.assignment_type}` as "types.devoir")} · {open.mode === "paper" ? t("modePaper") : t("modeOnline")} · /{open.max_score}</p>
                        {open.instructions && <p className="text-sm text-[#374151] dark:text-[#c7d0da]">{open.instructions}</p>}
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {open.submission?.feedback && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-[#0f1f1d] dark:text-emerald-100"><strong>{t("feedback")}:</strong> {open.submission.feedback}</div>}

                        {open.mode === "paper" ? (
                            <p className="text-sm text-[#6B7280]">{t("paperNote")}</p>
                        ) : (open.content?.questions || []).map(q => {
                            const key = String(q.id)
                            const graded = bucket(open) === "graded"
                            return (
                                <div key={key} className="rounded-xl border border-[#E5E7EB] p-3 dark:border-[#3b4248]">
                                    <p className="text-sm font-medium">{q.prompt} {q.points ? <span className="text-xs text-[#94A3B8]">({q.points} pts)</span> : null}</p>
                                    {q.type === "mcq" && q.options ? (
                                        <div className="mt-2 space-y-1">
                                            {q.options.map(opt => (
                                                <label key={opt} className="flex items-center gap-2 text-sm">
                                                    <input type="radio" name={key} disabled={graded || isParent} checked={answers[key] === opt} onChange={() => setAnswers({ ...answers, [key]: opt })} /> {opt}
                                                </label>
                                            ))}
                                        </div>
                                    ) : (
                                        <textarea disabled={graded || isParent} value={answers[key] || ""} onChange={e => setAnswers({ ...answers, [key]: e.target.value })} className="apple-input mt-2 min-h-16 w-full" />
                                    )}
                                    {open.answer_key_visible && (open.answer_key?.items || []).find(i => String(i.id) === key) && (
                                        <p className="mt-2 rounded-lg bg-[#F0FDFA] px-2 py-1 text-xs text-[#0F766E]"><strong>{t("correction")}:</strong> {(open.answer_key!.items!.find(i => String(i.id) === key))!.expected_answer}</p>
                                    )}
                                </div>
                            )
                        })}

                        <div className="flex gap-2">
                            <Button variant="outline" onClick={() => setOpen(null)}>{t("back")}</Button>
                            {!isParent && bucket(open) === "todo" && open.mode === "online" && (
                                <>
                                    <Button variant="outline" disabled={busy !== null} onClick={() => save(false)}>{busy === "save" ? <RefreshCw className="mr-1 h-4 w-4 animate-spin" /> : <Save className="mr-1 h-4 w-4" />} {t("saveDraftStudent")}</Button>
                                    <Button className="bg-black text-white hover:bg-black/90" disabled={busy !== null} onClick={() => save(true)}><Send className="mr-1 h-4 w-4" /> {t("submit")}</Button>
                                </>
                            )}
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4 lg:grid-cols-3">
                    {([["todo", grouped.todo], ["done", grouped.done], ["graded", grouped.graded]] as [string, Assignment[]][]).map(([k, list]) => (
                        <Card key={k} className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                            <CardHeader><CardTitle className="flex items-center gap-2 text-base"><ClipboardList className="h-4 w-4" /> {t(`bucket.${k}` as "bucket.todo")} ({list.length})</CardTitle></CardHeader>
                            <CardContent className="space-y-2">
                                {list.length === 0 ? <p className="py-4 text-center text-sm text-[#6B7280]">{t("nothing")}</p> : list.map(card)}
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    )
}
