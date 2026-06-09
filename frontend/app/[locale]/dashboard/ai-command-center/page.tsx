"use client"

import { useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import { Bot, BrainCircuit, CheckCircle2, Lock, Play, ShieldCheck, Sparkles, TrendingUp } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"
import { cn } from "@/lib/utils"

interface AIAgent {
    key: string
    name: string
    category: string
    actions: string[]
    enabled: boolean
}

interface AutomationResult {
    agent_key: string
    action: string
    executed: boolean
    requires_approval: boolean
    message: string
    data: Record<string, unknown>
    recommendations: string[]
}

const quickCommands = [
    "Give me today's executive summary.",
    "Show unpaid fees and duplicate payment risks.",
    "Identify students at academic risk.",
    "Audit the school for missing data.",
    "Create a lesson plan for Algebra.",
    "Find internships for IT students.",
]

function JsonBlock({ value }: { value: unknown }) {
    return (
        <pre className="max-h-[420px] overflow-auto rounded-[22px] bg-[#111827] p-4 text-xs leading-relaxed text-white">
            {JSON.stringify(value, null, 2)}
        </pre>
    )
}

export default function AICommandCenterPage() {
    const params = useParams()
    const locale = normalizeLocale(params.locale as string)
    const { token } = useAuth()
    const [agents, setAgents] = useState<AIAgent[]>([])
    const [summary, setSummary] = useState<Record<string, unknown> | null>(null)
    const [selectedAgent, setSelectedAgent] = useState("executive_command")
    const [command, setCommand] = useState(quickCommands[0])
    const [result, setResult] = useState<AutomationResult | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState("")

    useEffect(() => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        Promise.all([
            fetch(`${API_BASE_URL}/ai-automation/agents`, { headers }),
            fetch(`${API_BASE_URL}/ai-automation/executive-summary`, { headers }),
        ])
            .then(async ([agentsRes, summaryRes]) => {
                if (agentsRes.ok) setAgents(await agentsRes.json())
                if (summaryRes.ok) setSummary(await summaryRes.json())
            })
            .catch(() => setError("Impossible de charger le centre de commande IA."))
    }, [token])

    const enabledAgents = useMemo(() => agents.filter(agent => agent.enabled), [agents])
    const activeAgent = agents.find(agent => agent.key === selectedAgent) || agents[0]

    const runCommand = async () => {
        if (!token || !command.trim()) return
        setLoading(true)
        setError("")
        setResult(null)
        try {
            const response = await fetch(`${API_BASE_URL}/ai-automation/run`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    agent_key: selectedAgent,
                    command,
                    dry_run: true,
                    parameters: { locale },
                }),
            })
            const data = await response.json()
            if (!response.ok) throw new Error(data?.detail || "Action IA refusee.")
            setResult(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Execution IA impossible.")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6 pb-10">
            <div className="flex flex-col gap-4 rounded-[32px] border border-[#E5E7EB] bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between">
                <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-[#F5F5F7] px-3 py-1 text-sm font-medium text-[#111827]">
                        <Sparkles className="h-4 w-4" />
                        AI-First Education ERP
                    </div>
                    <h1 className="mt-3 text-3xl font-semibold tracking-tight text-[#111827]">AI Command Center</h1>
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-[#6B7280]">
                        Pilotez TeducAI avec des agents IA specialises. Chaque action respecte automatiquement le role actif,
                        les permissions dynamiques et l&apos;isolation des donnees de l&apos;etablissement.
                    </p>
                </div>
                <div className="flex items-center gap-3 rounded-[24px] bg-black px-5 py-4 text-white">
                    <ShieldCheck className="h-6 w-6" />
                    <div>
                        <p className="text-sm font-semibold">RBAC strict</p>
                        <p className="text-xs text-white/70">Suppression uniquement sur validation admin</p>
                    </div>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
                {[
                    { label: "Agents disponibles", value: enabledAgents.length, Icon: BrainCircuit },
                    { label: "Agents configures", value: agents.length, Icon: Bot },
                    { label: "Mode securise", value: "Actif", Icon: ShieldCheck },
                    { label: "Insights", value: summary ? "Pret" : "...", Icon: TrendingUp },
                ].map(({ label, value, Icon }) => (
                    <div key={label} className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                        <div className="flex items-center justify-between">
                            <p className="text-sm text-[#6B7280]">{label}</p>
                            <Icon className="h-5 w-5 text-[#6B7280]" />
                        </div>
                        <p className="mt-3 text-2xl font-semibold text-[#111827]">{value}</p>
                    </div>
                ))}
            </div>

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
                <section className="rounded-[32px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                            <h2 className="text-xl font-semibold text-[#111827]">Agents IA specialises</h2>
                            <p className="text-sm text-[#6B7280]">20 agents couvrent admissions, finance, presence, pedagogie, RH, documents et pilotage.</p>
                        </div>
                        <select
                            value={selectedAgent}
                            onChange={(event) => setSelectedAgent(event.target.value)}
                            className="apple-select max-w-xs"
                            title="Agent IA: choisissez l'agent specialise qui executera la commande selon vos permissions."
                        >
                            {agents.map(agent => (
                                <option key={agent.key} value={agent.key}>{agent.name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="mt-5 grid gap-3 md:grid-cols-2 2xl:grid-cols-3">
                        {agents.map(agent => (
                            <button
                                key={agent.key}
                                type="button"
                                onClick={() => setSelectedAgent(agent.key)}
                                className={cn(
                                    "min-h-[150px] rounded-[26px] border p-4 text-left transition hover:-translate-y-0.5 hover:shadow-md",
                                    selectedAgent === agent.key ? "border-black bg-[#F5F5F7]" : "border-[#E5E7EB] bg-white",
                                    !agent.enabled && "opacity-60"
                                )}
                                title={`${agent.name}: ${agent.enabled ? "agent disponible selon vos permissions." : "agent masque par vos permissions actuelles."}`}
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <p className="text-sm font-medium text-[#6B7280]">{agent.category}</p>
                                        <h3 className="mt-1 text-base font-semibold text-[#111827]">{agent.name}</h3>
                                    </div>
                                    {agent.enabled ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <Lock className="h-5 w-5 text-[#6B7280]" />}
                                </div>
                                <p className="mt-3 line-clamp-3 text-sm leading-5 text-[#6B7280]">
                                    {agent.actions.map(action => action.replace(/_/g, " ")).join(", ")}
                                </p>
                            </button>
                        ))}
                    </div>
                </section>

                <aside className="rounded-[32px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <h2 className="text-xl font-semibold text-[#111827]">Executer une commande</h2>
                    <p className="mt-1 text-sm text-[#6B7280]">
                        Agent actif: <span className="font-medium text-[#111827]">{activeAgent?.name || "Agent IA"}</span>
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2">
                        {quickCommands.map(item => (
                            <button
                                key={item}
                                type="button"
                                onClick={() => setCommand(item)}
                                className="rounded-full border border-[#E5E7EB] px-3 py-1.5 text-xs text-[#111827] hover:bg-[#F5F5F7]"
                            >
                                {item}
                            </button>
                        ))}
                    </div>
                    <textarea
                        value={command}
                        onChange={(event) => setCommand(event.target.value)}
                        rows={7}
                        className="mt-4 w-full resize-none rounded-[24px] border border-[#D1D5DB] bg-white px-4 py-3 text-sm outline-none transition focus:border-black"
                        title="Commande IA: decrivez l'action souhaitee. L'agent verifie votre role, vos permissions et le perimetre de donnees avant toute execution."
                    />
                    <button
                        type="button"
                        onClick={runCommand}
                        disabled={loading || !activeAgent?.enabled}
                        className="mt-4 inline-flex items-center gap-2 rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white transition hover:bg-black/90 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        <Play className="h-4 w-4" />
                        {loading ? "Execution..." : "Executer avec l'IA"}
                    </button>
                    {error && <p className="mt-4 rounded-[18px] bg-red-50 p-3 text-sm text-red-700">{error}</p>}
                    {result && (
                        <div className="mt-5 space-y-3">
                            <div className="rounded-[22px] bg-[#F5F5F7] p-4">
                                <p className="text-sm font-semibold text-[#111827]">{result.message}</p>
                                {result.requires_approval && <p className="mt-2 text-sm text-amber-700">Validation administrateur requise avant execution destructive.</p>}
                            </div>
                            {result.recommendations.length > 0 && (
                                <ul className="space-y-2 text-sm text-[#6B7280]">
                                    {result.recommendations.map(item => <li key={item}>- {item}</li>)}
                                </ul>
                            )}
                            <JsonBlock value={result.data} />
                        </div>
                    )}
                </aside>
            </div>

            {summary && (
                <section className="rounded-[32px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <h2 className="text-xl font-semibold text-[#111827]">Synthese executive IA</h2>
                    <p className="mt-1 text-sm text-[#6B7280]">Vue 360 degres generee depuis les donnees accessibles a votre role.</p>
                    <div className="mt-4">
                        <JsonBlock value={summary} />
                    </div>
                </section>
            )}
        </div>
    )
}
