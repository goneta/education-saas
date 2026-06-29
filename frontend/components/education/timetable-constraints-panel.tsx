"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { CalendarOff, Clock, Cpu, Gauge, Plus, Settings2, ShieldCheck, Sparkles, Trash2 } from "lucide-react"

import { API_BASE_URL } from "@/lib/config"

interface RefItem { id: number; name: string }
interface TeacherItem { id: number; full_name: string }
interface ClassItem { id: number; name: string; level?: string | null }

interface Props {
    token: string | null
    subjects: RefItem[]
    teachers: TeacherItem[]
    classes: ClassItem[]
}

interface ConstraintRule {
    id: number
    rule_type: string
    name?: string | null
    parameters: Record<string, unknown>
    severity: string
    is_active: boolean
}
interface Holiday { id: number; date: string; name?: string | null }
interface SubjectRequirement { id: number; subject_id: number; class_id?: number | null; level?: string | null; weekly_sessions: number }
interface TimetableConfig { working_days: string[]; slots: { start: string; end: string; kind: string }[] }
interface Candidate { seed: number; score: number; breakdown?: Record<string, unknown>; unplaced?: unknown }

const DAYS: { value: string; label: string }[] = [
    { value: "monday", label: "Lun" }, { value: "tuesday", label: "Mar" }, { value: "wednesday", label: "Mer" },
    { value: "thursday", label: "Jeu" }, { value: "friday", label: "Ven" }, { value: "saturday", label: "Sam" }, { value: "sunday", label: "Dim" },
]

// The 7 engine rule types (services/timetable_constraints.py) with friendly,
// school-facing labels and the parameters each one needs.
const RULE_TYPES: { value: string; label: string; params: string[] }[] = [
    { value: "subject_time_window", label: "Plage horaire d'une matière (ex. sciences jamais après 16h)", params: ["subject_id", "not_after", "not_before"] },
    { value: "subject_no_consecutive_days", label: "Jamais deux jours de suite (ex. Mathématiques)", params: ["subject_id"] },
    { value: "subject_after_forbidden", label: "Précédence interdite (ex. Physique jamais juste après Sport)", params: ["subject_id", "not_after_subject_id"] },
    { value: "teacher_available_days", label: "Disponibilité d'un enseignant (ex. externe : mardi & jeudi)", params: ["teacher_id", "days"] },
    { value: "subject_max_per_day", label: "Maximum d'heures d'une même matière par jour", params: ["subject_id", "max"] },
    { value: "max_heavy_subjects_per_day", label: "Limiter les matières « lourdes » par jour (ex. primaire ≤ 2)", params: ["max", "min_coefficient"] },
    { value: "room_subject_restriction", label: "Salle / laboratoire réservé à certaines matières", params: ["room", "subject_ids"] },
]

function Section({ icon: Icon, title, subtitle, children }: { icon: typeof Clock; title: string; subtitle?: string; children: React.ReactNode }) {
    return (
        <details className="group rounded-[20px] border border-[#E5E7EB] bg-white open:shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
            <summary className="flex cursor-pointer list-none items-center gap-3 p-4">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#eef1f4] dark:bg-[#343b41]"><Icon className="h-4 w-4" /></span>
                <span className="min-w-0">
                    <span className="block text-sm font-semibold text-[#111827] dark:text-white">{title}</span>
                    {subtitle && <span className="block text-xs text-[#6B7280] dark:text-[#c7d0da]">{subtitle}</span>}
                </span>
                <span className="ml-auto text-[#9aa3ad] transition group-open:rotate-180">▾</span>
            </summary>
            <div className="space-y-3 border-t border-[#E5E7EB] p-4 dark:border-[#3b4248]">{children}</div>
        </details>
    )
}

export function TimetableConstraintsPanel({ token, subjects, teachers, classes }: Props) {
    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])
    const base = `${API_BASE_URL}/education/timetables`

    const [rules, setRules] = useState<ConstraintRule[]>([])
    const [holidays, setHolidays] = useState<Holiday[]>([])
    const [requirements, setRequirements] = useState<SubjectRequirement[]>([])
    const [config, setConfig] = useState<TimetableConfig>({ working_days: ["monday", "tuesday", "wednesday", "thursday", "friday"], slots: [] })
    const [candidates, setCandidates] = useState<Candidate[]>([])
    const [busy, setBusy] = useState<string | null>(null)
    const [message, setMessage] = useState<string | null>(null)

    const subjectName = (id?: number | null) => subjects.find(s => s.id === id)?.name || `#${id}`

    const load = useCallback(async () => {
        if (!headers) return
        const [r, h, q, c] = await Promise.all([
            fetch(`${base}/constraint-rules`, { headers }),
            fetch(`${base}/holidays`, { headers }),
            fetch(`${base}/subject-requirements`, { headers }),
            fetch(`${base}/config`, { headers }),
        ])
        if (r.ok) setRules(await r.json())
        if (h.ok) setHolidays(await h.json())
        if (q.ok) setRequirements(await q.json())
        if (c.ok) {
            const cfg = await c.json()
            setConfig({ working_days: cfg.working_days?.length ? cfg.working_days : ["monday", "tuesday", "wednesday", "thursday", "friday"], slots: cfg.slots || [] })
        }
    }, [headers, base])

    useEffect(() => { void load() }, [load])

    // ----- Optimizer (AI) -----
    const [candidateCount, setCandidateCount] = useState("3")
    const optimize = async () => {
        if (!headers) return
        setBusy("optimize"); setMessage(null); setCandidates([])
        try {
            const res = await fetch(`${base}/optimize`, { method: "POST", headers, body: JSON.stringify({ candidate_count: Number(candidateCount) || 3 }) })
            if (res.ok) setCandidates((await res.json()).candidates || [])
            else setMessage("Optimisation impossible.")
        } finally { setBusy(null) }
    }
    const applyCandidate = async (seed: number) => {
        if (!headers || !window.confirm("Appliquer cet emploi du temps optimisé ?")) return
        setBusy(`apply-${seed}`)
        try {
            const res = await fetch(`${base}/optimize/commit`, { method: "POST", headers, body: JSON.stringify({ seed, candidate_count: Number(candidateCount) || 3 }) })
            setMessage(res.ok ? "Emploi du temps optimisé appliqué." : "Application impossible.")
        } finally { setBusy(null) }
    }

    // ----- Grid config -----
    const toggleDay = (day: string) => setConfig(c => ({ ...c, working_days: c.working_days.includes(day) ? c.working_days.filter(d => d !== day) : [...c.working_days, day] }))
    const addSlot = () => setConfig(c => ({ ...c, slots: [...c.slots, { start: "08:00", end: "09:00", kind: "course" }] }))
    const updateSlot = (i: number, patch: Partial<{ start: string; end: string; kind: string }>) => setConfig(c => ({ ...c, slots: c.slots.map((s, idx) => idx === i ? { ...s, ...patch } : s) }))
    const removeSlot = (i: number) => setConfig(c => ({ ...c, slots: c.slots.filter((_, idx) => idx !== i) }))
    const saveConfig = async () => {
        if (!headers) return
        setBusy("config")
        try {
            const res = await fetch(`${base}/config`, { method: "PUT", headers, body: JSON.stringify({ working_days: config.working_days, slots: config.slots, is_active: true }) })
            setMessage(res.ok ? "Grille enregistrée." : "Enregistrement impossible.")
        } finally { setBusy(null) }
    }

    // ----- Holidays -----
    const [holidayForm, setHolidayForm] = useState({ date: "", name: "" })
    const addHoliday = async () => {
        if (!headers || !holidayForm.date) return
        const res = await fetch(`${base}/holidays`, { method: "POST", headers, body: JSON.stringify({ date: `${holidayForm.date}T00:00:00`, name: holidayForm.name || null }) })
        if (res.ok) { setHolidayForm({ date: "", name: "" }); void load() }
    }
    const removeHoliday = async (id: number) => { if (headers && (await fetch(`${base}/holidays/${id}`, { method: "DELETE", headers })).ok) void load() }

    // ----- Subject weekly hours -----
    const [reqForm, setReqForm] = useState({ subject_id: "", class_id: "", weekly_sessions: "1" })
    const addRequirement = async () => {
        if (!headers || !reqForm.subject_id) return
        const res = await fetch(`${base}/subject-requirements`, {
            method: "POST", headers,
            body: JSON.stringify({ subject_id: Number(reqForm.subject_id), class_id: reqForm.class_id ? Number(reqForm.class_id) : null, weekly_sessions: Number(reqForm.weekly_sessions) || 1 }),
        })
        if (res.ok) { setReqForm({ subject_id: "", class_id: "", weekly_sessions: "1" }); void load() }
    }
    const removeRequirement = async (id: number) => { if (headers && (await fetch(`${base}/subject-requirements/${id}`, { method: "DELETE", headers })).ok) void load() }

    // ----- Constraint rules -----
    const [ruleType, setRuleType] = useState(RULE_TYPES[0].value)
    const [severity, setSeverity] = useState("blocking")
    const [pName, setPName] = useState("")
    const [p, setP] = useState<Record<string, string>>({})
    const [pDays, setPDays] = useState<string[]>([])
    const [pSubjectIds, setPSubjectIds] = useState<number[]>([])
    const activeParams = RULE_TYPES.find(t => t.value === ruleType)?.params || []

    const buildParameters = (): Record<string, unknown> => {
        const out: Record<string, unknown> = {}
        for (const key of activeParams) {
            if (key === "days") out.days = pDays
            else if (key === "subject_ids") out.subject_ids = pSubjectIds
            else if (["subject_id", "teacher_id", "not_after_subject_id", "max", "min_coefficient"].includes(key)) {
                if (p[key]) out[key] = Number(p[key])
            } else if (p[key]) out[key] = p[key]
        }
        return out
    }
    const addRule = async () => {
        if (!headers) return
        const res = await fetch(`${base}/constraint-rules`, {
            method: "POST", headers,
            body: JSON.stringify({ rule_type: ruleType, name: pName || null, parameters: buildParameters(), severity, is_active: true }),
        })
        if (res.ok) { setPName(""); setP({}); setPDays([]); setPSubjectIds([]); void load() }
        else setMessage("Règle invalide ou non supportée.")
    }
    const removeRule = async (id: number) => { if (headers && (await fetch(`${base}/constraint-rules/${id}`, { method: "DELETE", headers })).ok) void load() }
    const ruleLabel = (rt: string) => RULE_TYPES.find(t => t.value === rt)?.label || rt

    return (
        <div className="space-y-4">
            <div>
                <h2 className="text-xl font-bold text-[#111827] dark:text-white">Contraintes & génération IA</h2>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">Configurez le moteur de contraintes : disponibilités, volumes horaires, règles pédagogiques, jours fériés, verrous et génération optimisée.</p>
            </div>
            {message && <div className="rounded-xl border border-[#CCFBF1] bg-[#F0FDFA] px-3 py-2 text-sm text-[#0F766E] dark:border-[#134E4A] dark:bg-[#0f1f1d] dark:text-[#5eead4]">{message}</div>}

            <Section icon={Sparkles} title="Génération optimisée par l'IA" subtitle="Plusieurs emplois du temps notés (score qualité), avec résolution des conflits — appliquez celui qui convient.">
                <div className="flex flex-wrap items-end gap-3">
                    <label className="text-sm">Nombre de propositions
                        <input type="number" min={1} max={8} value={candidateCount} onChange={e => setCandidateCount(e.target.value)} className="apple-input mt-1 w-28" />
                    </label>
                    <button onClick={optimize} disabled={busy === "optimize"} className="inline-flex items-center gap-2 rounded-xl bg-black px-4 py-2 text-sm font-medium text-white hover:bg-black/90 disabled:opacity-50"><Cpu className="h-4 w-4" /> {busy === "optimize" ? "Optimisation…" : "Générer des emplois du temps optimisés"}</button>
                </div>
                <div className="space-y-2">
                    {candidates.map(c => (
                        <div key={c.seed} className="flex items-center justify-between rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm dark:border-[#3b4248]">
                            <span className="flex items-center gap-2"><Gauge className="h-4 w-4 text-[#0F766E]" /> Proposition #{c.seed} · score <strong>{Math.round(c.score)}</strong>/100{Array.isArray(c.unplaced) && c.unplaced.length ? ` · ${c.unplaced.length} non placé(s)` : " · 0 conflit"}</span>
                            <button onClick={() => applyCandidate(c.seed)} disabled={busy === `apply-${c.seed}`} className="rounded-lg border px-3 py-1 text-xs hover:bg-[#F5F5F7] dark:border-[#4a535b] dark:hover:bg-[#2a3035]">Appliquer</button>
                        </div>
                    ))}
                    {candidates.length === 0 && <p className="text-xs text-[#9aa3ad]">Lancez une optimisation pour comparer plusieurs scénarios notés.</p>}
                </div>
            </Section>

            <Section icon={Settings2} title="Configuration de la grille" subtitle="Jours ouvrables, créneaux de cours, pauses, récréations et déjeuner.">
                <div className="flex flex-wrap gap-2">
                    {DAYS.map(d => (
                        <button key={d.value} onClick={() => toggleDay(d.value)} className={`rounded-full border px-3 py-1 text-xs ${config.working_days.includes(d.value) ? "bg-black text-white dark:bg-white dark:text-black" : "dark:border-[#4a535b]"}`}>{d.label}</button>
                    ))}
                </div>
                <div className="space-y-2">
                    {config.slots.map((s, i) => (
                        <div key={i} className="flex flex-wrap items-center gap-2">
                            <input type="time" value={s.start} onChange={e => updateSlot(i, { start: e.target.value })} className="apple-input w-32" />
                            <span>→</span>
                            <input type="time" value={s.end} onChange={e => updateSlot(i, { end: e.target.value })} className="apple-input w-32" />
                            <select value={s.kind} onChange={e => updateSlot(i, { kind: e.target.value })} className="apple-select w-40">
                                <option value="course">Cours</option><option value="break">Récréation / pause</option><option value="lunch">Déjeuner</option>
                            </select>
                            <button onClick={() => removeSlot(i)} className="text-red-600"><Trash2 className="h-4 w-4" /></button>
                        </div>
                    ))}
                    <button onClick={addSlot} className="inline-flex items-center gap-1 text-sm text-[#0F766E]"><Plus className="h-4 w-4" /> Ajouter un créneau</button>
                </div>
                <button onClick={saveConfig} disabled={busy === "config"} className="rounded-xl bg-black px-4 py-2 text-sm font-medium text-white hover:bg-black/90 disabled:opacity-50">Enregistrer la grille</button>
            </Section>

            <Section icon={Clock} title="Volume horaire hebdomadaire par matière" subtitle="Nombre de séances par semaine pour chaque matière (par classe si besoin).">
                <div className="flex flex-wrap items-end gap-2">
                    <select value={reqForm.subject_id} onChange={e => setReqForm({ ...reqForm, subject_id: e.target.value })} className="apple-select"><option value="">Matière…</option>{subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
                    <select value={reqForm.class_id} onChange={e => setReqForm({ ...reqForm, class_id: e.target.value })} className="apple-select"><option value="">Toutes les classes</option>{classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
                    <input type="number" min={1} value={reqForm.weekly_sessions} onChange={e => setReqForm({ ...reqForm, weekly_sessions: e.target.value })} className="apple-input w-28" placeholder="Séances/sem." />
                    <button onClick={addRequirement} className="inline-flex items-center gap-1 rounded-xl bg-black px-3 py-2 text-sm text-white"><Plus className="h-4 w-4" /> Ajouter</button>
                </div>
                <div className="space-y-1">
                    {requirements.map(r => (
                        <div key={r.id} className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-3 py-1.5 text-sm dark:border-[#3b4248]"><span>{subjectName(r.subject_id)} · {r.weekly_sessions} séance(s)/sem.{r.class_id ? ` · ${classes.find(c => c.id === r.class_id)?.name || ""}` : ""}</span><button onClick={() => removeRequirement(r.id)} className="text-red-600"><Trash2 className="h-4 w-4" /></button></div>
                    ))}
                </div>
            </Section>

            <Section icon={CalendarOff} title="Jours fériés & jours non ouvrables" subtitle="Exclus automatiquement de la génération.">
                <div className="flex flex-wrap items-end gap-2">
                    <input type="date" value={holidayForm.date} onChange={e => setHolidayForm({ ...holidayForm, date: e.target.value })} className="apple-input" />
                    <input value={holidayForm.name} onChange={e => setHolidayForm({ ...holidayForm, name: e.target.value })} placeholder="Libellé (facultatif)" className="apple-input" />
                    <button onClick={addHoliday} className="inline-flex items-center gap-1 rounded-xl bg-black px-3 py-2 text-sm text-white"><Plus className="h-4 w-4" /> Ajouter</button>
                </div>
                <div className="space-y-1">
                    {holidays.map(h => (
                        <div key={h.id} className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-3 py-1.5 text-sm dark:border-[#3b4248]"><span>{new Date(h.date).toLocaleDateString("fr-FR")}{h.name ? ` · ${h.name}` : ""}</span><button onClick={() => removeHoliday(h.id)} className="text-red-600"><Trash2 className="h-4 w-4" /></button></div>
                    ))}
                </div>
            </Section>

            <Section icon={ShieldCheck} title="Règles de contraintes pédagogiques" subtitle="Moteur de contraintes : 7 types de règles, bloquantes ou simples avertissements.">
                <div className="grid gap-2 md:grid-cols-2">
                    <label className="text-sm md:col-span-2">Type de règle
                        <select value={ruleType} onChange={e => { setRuleType(e.target.value); setP({}); setPDays([]); setPSubjectIds([]) }} className="apple-select mt-1 w-full">
                            {RULE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                        </select>
                    </label>
                    {activeParams.includes("subject_id") && (
                        <select value={p.subject_id || ""} onChange={e => setP({ ...p, subject_id: e.target.value })} className="apple-select"><option value="">Matière…</option>{subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
                    )}
                    {activeParams.includes("not_after_subject_id") && (
                        <select value={p.not_after_subject_id || ""} onChange={e => setP({ ...p, not_after_subject_id: e.target.value })} className="apple-select"><option value="">Ne pas placer juste après…</option>{subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
                    )}
                    {activeParams.includes("teacher_id") && (
                        <select value={p.teacher_id || ""} onChange={e => setP({ ...p, teacher_id: e.target.value })} className="apple-select"><option value="">Enseignant…</option>{teachers.map(t => <option key={t.id} value={t.id}>{t.full_name}</option>)}</select>
                    )}
                    {activeParams.includes("not_after") && (
                        <label className="text-sm">Jamais après<input type="time" value={p.not_after || ""} onChange={e => setP({ ...p, not_after: e.target.value })} className="apple-input mt-1 w-full" /></label>
                    )}
                    {activeParams.includes("not_before") && (
                        <label className="text-sm">Jamais avant<input type="time" value={p.not_before || ""} onChange={e => setP({ ...p, not_before: e.target.value })} className="apple-input mt-1 w-full" /></label>
                    )}
                    {activeParams.includes("max") && (
                        <label className="text-sm">Maximum<input type="number" min={1} value={p.max || ""} onChange={e => setP({ ...p, max: e.target.value })} className="apple-input mt-1 w-full" /></label>
                    )}
                    {activeParams.includes("min_coefficient") && (
                        <label className="text-sm">Coefficient « lourd » min.<input type="number" min={1} value={p.min_coefficient || ""} onChange={e => setP({ ...p, min_coefficient: e.target.value })} className="apple-input mt-1 w-full" /></label>
                    )}
                    {activeParams.includes("room") && (
                        <input value={p.room || ""} onChange={e => setP({ ...p, room: e.target.value })} placeholder="Salle / laboratoire" className="apple-input" />
                    )}
                    {activeParams.includes("days") && (
                        <div className="flex flex-wrap gap-1 md:col-span-2">{DAYS.map(d => <button key={d.value} type="button" onClick={() => setPDays(days => days.includes(d.value) ? days.filter(x => x !== d.value) : [...days, d.value])} className={`rounded-full border px-3 py-1 text-xs ${pDays.includes(d.value) ? "bg-black text-white dark:bg-white dark:text-black" : "dark:border-[#4a535b]"}`}>{d.label}</button>)}</div>
                    )}
                    {activeParams.includes("subject_ids") && (
                        <div className="flex flex-wrap gap-1 md:col-span-2">{subjects.map(s => <button key={s.id} type="button" onClick={() => setPSubjectIds(ids => ids.includes(s.id) ? ids.filter(x => x !== s.id) : [...ids, s.id])} className={`rounded-full border px-3 py-1 text-xs ${pSubjectIds.includes(s.id) ? "bg-black text-white dark:bg-white dark:text-black" : "dark:border-[#4a535b]"}`}>{s.name}</button>)}</div>
                    )}
                    <input value={pName} onChange={e => setPName(e.target.value)} placeholder="Nom de la règle (facultatif)" className="apple-input" />
                    <select value={severity} onChange={e => setSeverity(e.target.value)} className="apple-select"><option value="blocking">Bloquante</option><option value="warning">Avertissement</option></select>
                </div>
                <button onClick={addRule} className="inline-flex items-center gap-1 rounded-xl bg-black px-4 py-2 text-sm font-medium text-white hover:bg-black/90"><Plus className="h-4 w-4" /> Ajouter la règle</button>
                <div className="space-y-1">
                    {rules.map(r => (
                        <div key={r.id} className="flex items-center justify-between rounded-lg border border-[#E5E7EB] px-3 py-1.5 text-sm dark:border-[#3b4248]">
                            <span><span className={`mr-2 rounded-full px-2 py-0.5 text-[10px] ${r.severity === "blocking" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>{r.severity === "blocking" ? "bloquante" : "avertissement"}</span>{r.name || ruleLabel(r.rule_type)}</span>
                            <button onClick={() => removeRule(r.id)} className="text-red-600"><Trash2 className="h-4 w-4" /></button>
                        </div>
                    ))}
                    {rules.length === 0 && <p className="text-xs text-[#9aa3ad]">Aucune règle définie. Le moteur applique déjà les contraintes structurelles ci-dessous.</p>}
                </div>
            </Section>

            <Section icon={ShieldCheck} title="Contraintes toujours appliquées" subtitle="Garanties par le moteur à la validation et à la génération — aucune configuration requise.">
                <ul className="list-inside list-disc space-y-1 text-sm text-[#4B5563] dark:text-[#c7d0da]">
                    <li>Un professeur ne peut pas être dans deux classes au même moment.</li>
                    <li>Une classe ne peut pas avoir deux cours simultanément.</li>
                    <li>Une salle / un laboratoire ne peut pas être occupé par deux cours en même temps.</li>
                    <li>Professeurs internes vs externes : la disponibilité des externes se définit via la règle « Disponibilité d'un enseignant » ; les affectations multi-établissements sont gérées dans le module Enseignants.</li>
                    <li>Les conflits détectés sont signalés à la validation et résolus par la génération optimisée.</li>
                </ul>
            </Section>
        </div>
    )
}
