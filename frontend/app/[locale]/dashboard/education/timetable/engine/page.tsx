"use client"

import { useCallback, useEffect, useState } from "react"
import { Plus, RefreshCw, Trash2, Wand2, FlaskConical, Save } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Button } from "@/components/ui/button"

interface ConstraintRule {
    id: number
    rule_type: string
    name?: string | null
    parameters: Record<string, unknown>
    severity: string
    is_active: boolean
}
interface Candidate {
    seed: number
    score: number
    breakdown: Record<string, unknown>
    placements: unknown[]
}

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

function Section({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) {
    return (
        <section className="rounded-2xl border border-[#E5E7EB] bg-white p-5 dark:border-[#3b4248] dark:bg-[#202528]">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-lg font-semibold text-[#111827] dark:text-white">{title}</h2>
                {action}
            </div>
            {children}
        </section>
    )
}

export default function TimetableEnginePage() {
    const { token } = useAuth()
    const headers = token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined
    const [message, setMessage] = useState("")

    const [ruleTypes, setRuleTypes] = useState<string[]>([])
    const [rules, setRules] = useState<ConstraintRule[]>([])
    const [ruleForm, setRuleForm] = useState({ rule_type: "", name: "", parameters: "{}", severity: "warning" })

    const [workingDays, setWorkingDays] = useState<string[]>([])
    const [slotsText, setSlotsText] = useState("")

    const [candidates, setCandidates] = useState<Candidate[]>([])
    const [busy, setBusy] = useState(false)

    const [scenario, setScenario] = useState("teacher_absent")
    const [scenarioParams, setScenarioParams] = useState('{"teacher_id": 0}')
    const [simResult, setSimResult] = useState<Record<string, unknown> | null>(null)

    const load = useCallback(async () => {
        if (!headers) return
        const [types, rulesRes, config] = await Promise.all([
            fetch(`${API_BASE_URL}/education/timetables/constraint-rule-types`, { headers }),
            fetch(`${API_BASE_URL}/education/timetables/constraint-rules`, { headers }),
            fetch(`${API_BASE_URL}/education/timetables/config`, { headers }),
        ])
        if (types.ok) setRuleTypes((await types.json()).rule_types || [])
        if (rulesRes.ok) setRules(await rulesRes.json())
        if (config.ok) {
            const c = await config.json()
            setWorkingDays(c.working_days || [])
            setSlotsText(JSON.stringify(c.slots || [], null, 2))
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token])

    useEffect(() => { void load() }, [load])

    const createRule = async () => {
        if (!headers) return
        let parameters: Record<string, unknown>
        try { parameters = JSON.parse(ruleForm.parameters || "{}") } catch { setMessage("Paramètres JSON invalides."); return }
        const res = await fetch(`${API_BASE_URL}/education/timetables/constraint-rules`, {
            method: "POST", headers,
            body: JSON.stringify({ rule_type: ruleForm.rule_type, name: ruleForm.name || null, parameters, severity: ruleForm.severity }),
        })
        const data = await res.json().catch(() => null)
        setMessage(res.ok ? "Règle créée." : (typeof data?.detail === "string" ? data.detail : "Création impossible."))
        if (res.ok) void load()
    }

    const deleteRule = async (id: number) => {
        if (!headers) return
        await fetch(`${API_BASE_URL}/education/timetables/constraint-rules/${id}`, { method: "DELETE", headers })
        void load()
    }

    const saveConfig = async () => {
        if (!headers) return
        let slots: unknown
        try { slots = JSON.parse(slotsText || "[]") } catch { setMessage("Créneaux JSON invalides."); return }
        const res = await fetch(`${API_BASE_URL}/education/timetables/config`, {
            method: "PUT", headers, body: JSON.stringify({ working_days: workingDays, slots }),
        })
        setMessage(res.ok ? "Grille enregistrée." : "Enregistrement impossible.")
    }

    const optimize = async () => {
        if (!headers) return
        setBusy(true); setMessage("")
        try {
            const res = await fetch(`${API_BASE_URL}/education/timetables/optimize`, { method: "POST", headers, body: JSON.stringify({ candidate_count: 3 }) })
            const data = await res.json().catch(() => null)
            setCandidates(res.ok ? (data.candidates || []) : [])
            if (!res.ok) setMessage("Optimisation impossible.")
        } finally { setBusy(false) }
    }

    const commit = async (seed: number) => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/education/timetables/optimize/commit`, { method: "POST", headers, body: JSON.stringify({ seed, candidate_count: 3 }) })
        const data = await res.json().catch(() => null)
        setMessage(res.ok ? `Emploi du temps appliqué (${data.created} séances, score ${data.score}).` : "Application impossible.")
    }

    const simulate = async () => {
        if (!headers) return
        let params: Record<string, unknown>
        try { params = JSON.parse(scenarioParams || "{}") } catch { setMessage("Paramètres JSON invalides."); return }
        const res = await fetch(`${API_BASE_URL}/education/timetables/simulate`, { method: "POST", headers, body: JSON.stringify({ scenario, params }) })
        const data = await res.json().catch(() => null)
        setSimResult(res.ok ? data : null)
        if (!res.ok) setMessage(typeof data?.detail === "string" ? data.detail : "Simulation impossible.")
    }

    const inputClass = "w-full rounded-lg border border-[#D1D5DB] bg-white px-3 py-2 text-sm text-[#111827] dark:border-[#56616a] dark:bg-[#252b30] dark:text-white"

    return (
        <div className="space-y-6">
            <header>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">Moteur d&apos;emploi du temps</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">Contraintes configurables, grille horaire, optimisation IA et simulation.</p>
            </header>
            {message && <p className="rounded-lg bg-[#ECFDF5] px-4 py-2 text-sm text-[#0F766E] dark:bg-[#0f3a34] dark:text-[#5eead4]">{message}</p>}

            <Section title="Grille horaire" action={<Button onClick={saveConfig} className="bg-black text-white dark:bg-white dark:text-black"><Save className="h-4 w-4" /> Enregistrer</Button>}>
                <div className="flex flex-wrap gap-2">
                    {DAYS.map(day => (
                        <label key={day} className="flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm dark:border-[#56616a]">
                            <input type="checkbox" checked={workingDays.includes(day)} onChange={e => setWorkingDays(e.target.checked ? [...workingDays, day] : workingDays.filter(d => d !== day))} />
                            {day}
                        </label>
                    ))}
                </div>
                <p className="mt-4 text-sm font-medium text-[#111827] dark:text-white">Créneaux (JSON: start/end/kind course|break|lunch)</p>
                <textarea value={slotsText} onChange={e => setSlotsText(e.target.value)} rows={6} className={`${inputClass} mt-2 font-mono text-xs`} />
            </Section>

            <Section title="Règles de contraintes" action={<Button variant="outline" onClick={() => void load()}><RefreshCw className="h-4 w-4" /></Button>}>
                <div className="grid gap-2 md:grid-cols-[1fr_1fr_2fr_auto_auto]">
                    <select value={ruleForm.rule_type} onChange={e => setRuleForm({ ...ruleForm, rule_type: e.target.value })} className={inputClass}>
                        <option value="">Type de règle…</option>
                        {ruleTypes.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                    <input placeholder="Nom" value={ruleForm.name} onChange={e => setRuleForm({ ...ruleForm, name: e.target.value })} className={inputClass} />
                    <input placeholder='Paramètres JSON, ex {"subject_id": 5, "not_after": "16:00"}' value={ruleForm.parameters} onChange={e => setRuleForm({ ...ruleForm, parameters: e.target.value })} className={`${inputClass} font-mono text-xs`} />
                    <select value={ruleForm.severity} onChange={e => setRuleForm({ ...ruleForm, severity: e.target.value })} className={inputClass}>
                        <option value="warning">warning</option>
                        <option value="blocking">blocking</option>
                    </select>
                    <Button onClick={createRule} disabled={!ruleForm.rule_type} className="bg-black text-white dark:bg-white dark:text-black"><Plus className="h-4 w-4" /></Button>
                </div>
                <div className="mt-4 space-y-2">
                    {rules.map(rule => (
                        <div key={rule.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm dark:border-[#56616a]">
                            <span><strong>{rule.rule_type}</strong>{rule.name ? ` — ${rule.name}` : ""} <span className="text-[#6B7280] dark:text-[#c7d0da]">({rule.severity})</span> <code className="text-xs">{JSON.stringify(rule.parameters)}</code></span>
                            <Button variant="outline" onClick={() => void deleteRule(rule.id)}><Trash2 className="h-4 w-4" /></Button>
                        </div>
                    ))}
                    {!rules.length && <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">Aucune règle configurée.</p>}
                </div>
            </Section>

            <Section title="Optimisation IA" action={<Button onClick={optimize} disabled={busy} className="bg-[#0F766E] text-white"><Wand2 className="h-4 w-4" /> {busy ? "…" : "Générer"}</Button>}>
                <div className="grid gap-3 md:grid-cols-3">
                    {candidates.map(c => (
                        <div key={c.seed} className="rounded-xl border p-4 dark:border-[#56616a]">
                            <p className="text-2xl font-bold text-[#111827] dark:text-white">{c.score}<span className="text-sm font-normal">/100</span></p>
                            <p className="mt-1 text-xs text-[#6B7280] dark:text-[#c7d0da]">{String(c.breakdown.placed_sessions)}/{String(c.breakdown.required_sessions)} séances · {String(c.breakdown.soft_penalty)} pénalité(s)</p>
                            <Button onClick={() => void commit(c.seed)} className="mt-3 w-full bg-black text-white dark:bg-white dark:text-black">Appliquer</Button>
                        </div>
                    ))}
                    {!candidates.length && <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">Lancez l&apos;optimisation pour comparer plusieurs emplois du temps notés.</p>}
                </div>
            </Section>

            <Section title="Simulation (« et si… »)" action={<Button onClick={simulate} variant="outline"><FlaskConical className="h-4 w-4" /> Simuler</Button>}>
                <div className="grid gap-2 md:grid-cols-[1fr_2fr]">
                    <select value={scenario} onChange={e => setScenario(e.target.value)} className={inputClass}>
                        <option value="teacher_absent">Professeur absent</option>
                        <option value="extra_working_day">Jour d&apos;ouverture supplémentaire</option>
                    </select>
                    <input value={scenarioParams} onChange={e => setScenarioParams(e.target.value)} className={`${inputClass} font-mono text-xs`} placeholder='{"teacher_id": 12} ou {"day": "saturday"}' />
                </div>
                {simResult && (
                    <div className="mt-4 rounded-lg bg-[#F8FAFC] p-4 text-sm dark:bg-[#1f2427]">
                        <p className="text-[#111827] dark:text-white">Score: {String((simResult.baseline as Record<string, unknown>)?.score)} → {String((simResult.scenario_result as Record<string, unknown>)?.score)} (Δ {String(simResult.score_delta)})</p>
                        <ul className="mt-2 list-disc pl-5 text-[#6B7280] dark:text-[#c7d0da]">
                            {(simResult.impact as string[] | undefined)?.map((line, i) => <li key={i}>{line}</li>)}
                            {(simResult.explanation as string[] | undefined)?.map((line, i) => <li key={`e${i}`}>{line}</li>)}
                        </ul>
                    </div>
                )}
            </Section>
        </div>
    )
}
