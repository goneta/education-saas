"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import { BadgeCheck, BrainCircuit, Landmark, Plus, RefreshCw, ShieldCheck, Wallet } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"

interface AIWallet {
    id: number
    owner_type: string
    school_id?: number | null
    user_id?: number | null
    credits_balance: number
    total_credits_purchased: number
    total_credits_used: number
    is_active: boolean
}

interface AICreditPack {
    id: number
    name: string
    description?: string | null
    credits_amount: number
    price_amount: number
    currency: string
    country_code?: string | null
    region?: string | null
    is_active: boolean
}

interface AIUsageLog {
    id: number
    module: string
    action: string
    credits_used: number
    status: string
    created_at: string
}

interface AITransaction {
    id: number
    transaction_type: string
    credits_amount: number
    amount_money?: number | null
    currency?: string | null
    status: string
    description?: string | null
    created_at: string
}

interface PlatformPayment {
    id: number
    payment_type: string
    status: string
    amount: number
    currency: string
    reference: string
    beneficiary_entity: string
    created_at: string
}

interface SchoolPaymentAccount {
    id: number
    provider: string
    account_name: string
    account_reference?: string | null
    currency: string
    country_code?: string | null
    is_active: boolean
}

interface SchoolPayment {
    id: number
    payment_type: string
    status: string
    amount: number
    currency: string
    reference: string
    beneficiary_account_id?: number | null
    created_at: string
}

interface AIProvider {
    id: number
    name: string
    provider_type: string
    default_model?: string | null
    currency: string
    is_active: boolean
    priority: number
}

interface AnalyticsSummary {
    period: { from?: string | null; to?: string | null }
    total_credits_used: number
    total_requests: number
    blocked_requests: number
    successful_requests: number
    by_module: Record<string, number>
}

const statusColor: Record<string, string> = {
    successful: "text-emerald-700 bg-emerald-50",
    completed: "text-emerald-700 bg-emerald-50",
    active: "text-emerald-700 bg-emerald-50",
    pending: "text-amber-700 bg-amber-50",
    failed: "text-red-700 bg-red-50",
    blocked: "text-red-700 bg-red-50",
}

function money(amount: number, currency: string) {
    return `${Number(amount || 0).toLocaleString("fr-FR")} ${currency}`
}

function CardShell({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
    return (
        <section className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
            <div className="mb-4">
                <h2 className="text-xl font-semibold text-[#111827]">{title}</h2>
                {subtitle && <p className="mt-1 text-sm text-[#6B7280]">{subtitle}</p>}
            </div>
            {children}
        </section>
    )
}

function StatusBadge({ value }: { value: string }) {
    return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusColor[value] || "bg-[#F5F5F7] text-[#111827]"}`}>{value}</span>
}

export default function AICreditsPage() {
    const params = useParams()
    normalizeLocale(params.locale as string)
    const { token, user } = useAuth()
    const [myWallet, setMyWallet] = useState<AIWallet | null>(null)
    const [schoolWallet, setSchoolWallet] = useState<AIWallet | null>(null)
    const [packs, setPacks] = useState<AICreditPack[]>([])
    const [myUsage, setMyUsage] = useState<AIUsageLog[]>([])
    const [schoolUsage, setSchoolUsage] = useState<AIUsageLog[]>([])
    const [myTransactions, setMyTransactions] = useState<AITransaction[]>([])
    const [schoolTransactions, setSchoolTransactions] = useState<AITransaction[]>([])
    const [platformPayments, setPlatformPayments] = useState<PlatformPayment[]>([])
    const [schoolPaymentAccounts, setSchoolPaymentAccounts] = useState<SchoolPaymentAccount[]>([])
    const [schoolPayments, setSchoolPayments] = useState<SchoolPayment[]>([])
    const [providers, setProviders] = useState<AIProvider[]>([])
    const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null)
    const [message, setMessage] = useState("")
    const [loading, setLoading] = useState(false)
    const [accountForm, setAccountForm] = useState({
        provider: "orange_money",
        account_name: "",
        account_reference: "",
        currency: "FCFA",
        country_code: "CI",
    })
    const [providerForm, setProviderForm] = useState({
        name: "",
        provider_type: "openai",
        default_model: "gpt-4.1-mini",
        currency: "USD",
        input_token_cost_per_1k: "0",
        output_token_cost_per_1k: "0",
        priority: "100",
    })

    const isSuperAdmin = user?.role === "super_admin"
    const canManageSchool = useMemo(() => {
        return Boolean(user?.role && ["super_admin", "school_admin", "admin", "direction", "director", "accountant"].includes(user.role))
    }, [user?.role])

    const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!token || !headers) return
        setLoading(true)
        setMessage("")
        try {
            const publicPacks = await fetch(`${API_BASE_URL}/platform/ai/credit-packs?active_only=true`)
            if (publicPacks.ok) setPacks(await publicPacks.json())

            const [walletRes, usageRes, txRes] = await Promise.all([
                fetch(`${API_BASE_URL}/me/ai/wallet`, { headers }),
                fetch(`${API_BASE_URL}/me/ai/usage`, { headers }),
                fetch(`${API_BASE_URL}/me/ai/transactions`, { headers }),
            ])
            if (walletRes.ok) setMyWallet(await walletRes.json())
            if (usageRes.ok) setMyUsage(await usageRes.json())
            if (txRes.ok) setMyTransactions(await txRes.json())

            if (canManageSchool) {
                const [schoolWalletRes, schoolUsageRes, schoolTxRes, accountsRes, paymentsRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/school/ai/wallet`, { headers }),
                    fetch(`${API_BASE_URL}/school/ai/usage`, { headers }),
                    fetch(`${API_BASE_URL}/school/ai/transactions`, { headers }),
                    fetch(`${API_BASE_URL}/school/payment-accounts`, { headers }),
                    fetch(`${API_BASE_URL}/school/payments`, { headers }),
                ])
                if (schoolWalletRes.ok) setSchoolWallet(await schoolWalletRes.json())
                if (schoolUsageRes.ok) setSchoolUsage(await schoolUsageRes.json())
                if (schoolTxRes.ok) setSchoolTransactions(await schoolTxRes.json())
                if (accountsRes.ok) setSchoolPaymentAccounts(await accountsRes.json())
                if (paymentsRes.ok) setSchoolPayments(await paymentsRes.json())
            }

            if (isSuperAdmin) {
                const [providersRes, platformPaymentsRes, analyticsRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/platform/ai/providers`, { headers }),
                    fetch(`${API_BASE_URL}/platform/ai/payments`, { headers }),
                    fetch(`${API_BASE_URL}/platform/ai/analytics`, { headers }),
                ])
                if (providersRes.ok) setProviders(await providersRes.json())
                if (platformPaymentsRes.ok) setPlatformPayments(await platformPaymentsRes.json())
                if (analyticsRes.ok) setAnalytics(await analyticsRes.json())
            }
        } catch {
            setMessage("Chargement impossible. Verifiez votre connexion ou vos permissions.")
        } finally {
            setLoading(false)
        }
    }, [canManageSchool, headers, isSuperAdmin, token])

    useEffect(() => {
        void load()
    }, [load])

    const purchase = async (packId: number, scope: "me" | "school") => {
        if (!token) return
        setMessage("Creation du paiement TeducAI...")
        const endpoint = scope === "school" ? "/school/ai/purchase" : "/me/ai/purchase"
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ pack_id: packId, provider: "manual" }),
        })
        const data = await response.json().catch(() => null)
        if (response.ok) {
            setMessage(`Paiement cree: ${data.reference}. Beneficiaire: ${data.beneficiary_entity}.`)
            void load()
        } else {
            setMessage(data?.detail || "Achat de credits impossible.")
        }
    }

    const createPaymentAccount = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/school/payment-accounts`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify(accountForm),
        })
        if (response.ok) {
            setMessage("Compte de paiement etablissement enregistre.")
            setAccountForm({ provider: "orange_money", account_name: "", account_reference: "", currency: "FCFA", country_code: "CI" })
            void load()
        } else {
            setMessage("Enregistrement du compte de paiement impossible.")
        }
    }

    const createProvider = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/platform/ai/providers`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({
                name: providerForm.name,
                provider_type: providerForm.provider_type,
                default_model: providerForm.default_model,
                currency: providerForm.currency,
                input_token_cost_per_1k: Number(providerForm.input_token_cost_per_1k),
                output_token_cost_per_1k: Number(providerForm.output_token_cost_per_1k),
                priority: Number(providerForm.priority),
                is_active: false,
            }),
        })
        if (response.ok) {
            setMessage("Provider IA cree. Ajoutez la cle API cote plateforme avant activation.")
            setProviderForm({ name: "", provider_type: "openai", default_model: "gpt-4.1-mini", currency: "USD", input_token_cost_per_1k: "0", output_token_cost_per_1k: "0", priority: "100" })
            void load()
        } else {
            setMessage("Creation du provider IA impossible.")
        }
    }

    return (
        <div className="space-y-6 pb-10">
            <div className="flex flex-col gap-4 rounded-[32px] border border-[#E5E7EB] bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between">
                <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-[#F5F5F7] px-3 py-1 text-sm font-medium text-[#111827]">
                        <BrainCircuit className="h-4 w-4" />
                        Credits IA TeducAI
                    </div>
                    <h1 className="mt-3 text-3xl font-semibold tracking-tight text-[#111827]">Credits IA et paiements separes</h1>
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-[#6B7280]">
                        Les credits IA, abonnements et modules premium sont encaisses par TeducAI. Les frais scolaires, cantine,
                        transport et autres paiements metier restent encaisses sur les comptes propres de chaque etablissement.
                    </p>
                </div>
                <button type="button" onClick={() => void load()} className="inline-flex w-fit items-center gap-2 rounded-full bg-black px-5 py-3 text-sm font-medium text-white hover:bg-black/90">
                    <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                    Actualiser
                </button>
            </div>

            {message && <div className="rounded-[22px] border border-[#E5E7EB] bg-[#F5F5F7] p-4 text-sm text-[#111827]">{message}</div>}

            <div className="grid gap-4 lg:grid-cols-4">
                <div className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <div className="flex items-center justify-between"><p className="text-sm text-[#6B7280]">Mes credits</p><Wallet className="h-5 w-5 text-[#6B7280]" /></div>
                    <p className="mt-3 text-3xl font-semibold text-[#111827]">{myWallet?.credits_balance ?? 0}</p>
                    <p className="text-xs text-[#6B7280]">Utilises: {myWallet?.total_credits_used ?? 0}</p>
                </div>
                <div className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <div className="flex items-center justify-between"><p className="text-sm text-[#6B7280]">Credits etablissement</p><Landmark className="h-5 w-5 text-[#6B7280]" /></div>
                    <p className="mt-3 text-3xl font-semibold text-[#111827]">{schoolWallet?.credits_balance ?? "-"}</p>
                    <p className="text-xs text-[#6B7280]">Requetes ecole: {schoolUsage.length}</p>
                </div>
                <div className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <div className="flex items-center justify-between"><p className="text-sm text-[#6B7280]">Requetes IA</p><BrainCircuit className="h-5 w-5 text-[#6B7280]" /></div>
                    <p className="mt-3 text-3xl font-semibold text-[#111827]">{analytics?.total_requests ?? myUsage.length}</p>
                    <p className="text-xs text-[#6B7280]">Bloquees: {analytics?.blocked_requests ?? myUsage.filter(item => item.status === "blocked").length}</p>
                </div>
                <div className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <div className="flex items-center justify-between"><p className="text-sm text-[#6B7280]">Separation paiements</p><ShieldCheck className="h-5 w-5 text-[#6B7280]" /></div>
                    <p className="mt-3 text-lg font-semibold text-[#111827]">TeducAI / Ecole</p>
                    <p className="text-xs text-[#6B7280]">Flux financiers isoles</p>
                </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
                <CardShell title="Acheter des credits IA" subtitle="Ces paiements sont des paiements plateforme TeducAI, encaisses par Thunderfam selon la region.">
                    <div className="grid gap-3 md:grid-cols-2">
                        {packs.map(pack => (
                            <div key={pack.id} className="rounded-[24px] border border-[#E5E7EB] p-4">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <h3 className="font-semibold text-[#111827]">{pack.name}</h3>
                                        <p className="text-sm text-[#6B7280]">{pack.credits_amount.toLocaleString("fr-FR")} credits IA</p>
                                    </div>
                                    <p className="font-semibold text-[#111827]">{money(pack.price_amount, pack.currency)}</p>
                                </div>
                                {pack.description && <p className="mt-2 text-sm text-[#6B7280]">{pack.description}</p>}
                                <div className="mt-4 flex flex-wrap gap-2">
                                    <button type="button" onClick={() => void purchase(pack.id, "me")} className="rounded-full bg-black px-4 py-2 text-sm font-medium text-white hover:bg-black/90">Acheter pour moi</button>
                                    {canManageSchool && <button type="button" onClick={() => void purchase(pack.id, "school")} className="rounded-full border border-[#D1D5DB] px-4 py-2 text-sm hover:bg-[#F5F5F7]">Acheter pour l&apos;ecole</button>}
                                </div>
                            </div>
                        ))}
                    </div>
                </CardShell>

                <CardShell title="Comptes de paiement ecole" subtitle="Utilises uniquement pour les paiements scolaires encaisses par l'etablissement.">
                    {canManageSchool ? (
                        <form onSubmit={createPaymentAccount} className="grid gap-3">
                            <input className="apple-input" placeholder="Nom du compte" value={accountForm.account_name} onChange={event => setAccountForm({ ...accountForm, account_name: event.target.value })} required title="Nom du compte: nom visible par la comptabilite pour identifier le compte d'encaissement de l'etablissement." />
                            <input className="apple-input" placeholder="Reference marchand, telephone ou identifiant" value={accountForm.account_reference} onChange={event => setAccountForm({ ...accountForm, account_reference: event.target.value })} title="Reference: identifiant fournisseur, numero mobile money ou reference bancaire utilisee pour encaisser les paiements scolaires." />
                            <div className="grid gap-3 sm:grid-cols-3">
                                <input className="apple-input" value={accountForm.provider} onChange={event => setAccountForm({ ...accountForm, provider: event.target.value })} title="Provider: Orange Money, MTN, Wave, banque ou autre prestataire de paiement." />
                                <input className="apple-input" value={accountForm.currency} onChange={event => setAccountForm({ ...accountForm, currency: event.target.value })} title="Devise: devise d'encaissement du compte de l'etablissement." />
                                <input className="apple-input" value={accountForm.country_code} onChange={event => setAccountForm({ ...accountForm, country_code: event.target.value })} title="Pays: code pays ISO utilise pour appliquer les regles locales." />
                            </div>
                            <button className="inline-flex w-fit items-center gap-2 rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white hover:bg-black/90"><Plus className="h-4 w-4" /> Enregistrer</button>
                        </form>
                    ) : (
                        <p className="text-sm text-[#6B7280]">Vous n&apos;avez pas les permissions de gestion des comptes de paiement ecole.</p>
                    )}
                    <div className="mt-5 space-y-2">
                        {schoolPaymentAccounts.map(account => (
                            <div key={account.id} className="flex items-center justify-between rounded-[18px] bg-[#F5F5F7] px-3 py-2 text-sm">
                                <span>{account.account_name} - {account.provider}</span>
                                <StatusBadge value={account.is_active ? "active" : "inactive"} />
                            </div>
                        ))}
                    </div>
                </CardShell>
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
                <CardShell title="Historique credits utilisateur">
                    <Table headers={["Date", "Type", "Credits", "Statut"]} rows={myTransactions.map(item => [item.created_at, item.transaction_type, item.credits_amount, item.status])} />
                </CardShell>
                <CardShell title="Usage IA utilisateur">
                    <Table headers={["Date", "Module", "Action", "Credits", "Statut"]} rows={myUsage.map(item => [item.created_at, item.module, item.action, item.credits_used, item.status])} />
                </CardShell>
                {canManageSchool && (
                    <>
                        <CardShell title="Transactions credits ecole">
                            <Table headers={["Date", "Type", "Credits", "Statut"]} rows={schoolTransactions.map(item => [item.created_at, item.transaction_type, item.credits_amount, item.status])} />
                        </CardShell>
                        <CardShell title="Paiements scolaires separes">
                            <Table headers={["Date", "Type", "Reference", "Montant", "Statut"]} rows={schoolPayments.map(item => [item.created_at, item.payment_type, item.reference, money(item.amount, item.currency), item.status])} />
                        </CardShell>
                    </>
                )}
            </div>

            {isSuperAdmin && (
                <div className="grid gap-6 xl:grid-cols-2">
                    <CardShell title="Providers IA plateforme" subtitle="Configuration reservee au Super Administrateur TeducAI. Les cles API ne sont jamais exposees aux ecoles.">
                        <form onSubmit={createProvider} className="mb-5 grid gap-3">
                            <input className="apple-input" placeholder="Nom provider" value={providerForm.name} onChange={event => setProviderForm({ ...providerForm, name: event.target.value })} required title="Nom provider: nom interne du fournisseur IA gere par TeducAI." />
                            <div className="grid gap-3 sm:grid-cols-2">
                                <input className="apple-input" value={providerForm.provider_type} onChange={event => setProviderForm({ ...providerForm, provider_type: event.target.value })} title="Type provider: openai, anthropic, gemini, openrouter, grok ou autre." />
                                <input className="apple-input" value={providerForm.default_model} onChange={event => setProviderForm({ ...providerForm, default_model: event.target.value })} title="Modele par defaut: modele utilise quand aucun autre modele n'est force par le service IA." />
                            </div>
                            <div className="grid gap-3 sm:grid-cols-4">
                                <input className="apple-input" value={providerForm.currency} onChange={event => setProviderForm({ ...providerForm, currency: event.target.value })} title="Devise provider: devise de facturation technique du fournisseur IA." />
                                <input className="apple-input" type="number" value={providerForm.input_token_cost_per_1k} onChange={event => setProviderForm({ ...providerForm, input_token_cost_per_1k: event.target.value })} title="Cout input: cout estime par 1000 tokens entrants." />
                                <input className="apple-input" type="number" value={providerForm.output_token_cost_per_1k} onChange={event => setProviderForm({ ...providerForm, output_token_cost_per_1k: event.target.value })} title="Cout output: cout estime par 1000 tokens sortants." />
                                <input className="apple-input" type="number" value={providerForm.priority} onChange={event => setProviderForm({ ...providerForm, priority: event.target.value })} title="Priorite: plus le nombre est faible, plus le provider est prioritaire." />
                            </div>
                            <button className="inline-flex w-fit items-center gap-2 rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white hover:bg-black/90"><BadgeCheck className="h-4 w-4" /> Creer provider</button>
                        </form>
                        <Table headers={["Nom", "Type", "Modele", "Statut"]} rows={providers.map(item => [item.name, item.provider_type, item.default_model || "-", item.is_active ? "active" : "inactive"])} />
                    </CardShell>
                    <CardShell title="Paiements plateforme TeducAI">
                        <Table headers={["Date", "Type", "Reference", "Montant", "Beneficiaire", "Statut"]} rows={platformPayments.map(item => [item.created_at, item.payment_type, item.reference, money(item.amount, item.currency), item.beneficiary_entity, item.status])} />
                        {analytics && (
                            <div className="mt-5 rounded-[22px] bg-[#F5F5F7] p-4 text-sm">
                                <p className="font-semibold text-[#111827]">Analytics IA plateforme</p>
                                <p className="mt-1 text-[#6B7280]">Credits utilises: {analytics.total_credits_used} | Requetes reussies: {analytics.successful_requests} | Bloquees: {analytics.blocked_requests}</p>
                            </div>
                        )}
                    </CardShell>
                </div>
            )}
        </div>
    )
}

function Table({ headers, rows }: { headers: string[]; rows: Array<Array<string | number>> }) {
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
                <thead>
                    <tr className="border-b border-[#E5E7EB] text-[#6B7280]">
                        {headers.map(header => <th key={header} className="px-3 py-2 font-medium">{header}</th>)}
                    </tr>
                </thead>
                <tbody>
                    {rows.length === 0 ? (
                        <tr><td colSpan={headers.length} className="px-3 py-6 text-center text-[#6B7280]">Aucune donnee disponible.</td></tr>
                    ) : rows.slice(0, 20).map((row, index) => (
                        <tr key={index} className="border-b border-[#F0F1F3]">
                            {row.map((cell, cellIndex) => (
                                <td key={`${index}-${cellIndex}`} className="px-3 py-2 text-[#111827]">
                                    {String(cell).length > 28 ? `${String(cell).slice(0, 28)}...` : cell}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}
