"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import { AlertTriangle, BadgeCheck, Banknote, BrainCircuit, CreditCard, Gift, Landmark, Plus, RefreshCw, ShieldCheck, Smartphone, Wallet } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"
import { requestConfirmation } from "@/lib/confirmation"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"

interface AIWallet {
    id: number
    owner_type: string
    school_id?: number | null
    user_id?: number | null
    balance_credits: number
    total_purchased_credits: number
    total_used_credits: number
    daily_credit_limit?: number | null
    monthly_credit_limit?: number | null
    status: string
}

interface AICreditPack {
    id: number
    name: string
    description?: string | null
    credits_amount: number
    price: number
    currency: string
    country_code?: string | null
    region?: string | null
    target_type: "user" | "school" | "both"
    is_active: boolean
}

interface AIUsageLog {
    id: number
    module_name?: string | null
    action_type?: string | null
    credits_charged: number
    status: string
    created_at: string
    provider_id?: number | null
    model_name?: string | null
    total_tokens?: number
}

interface AITransaction {
    id: number
    transaction_type: string
    credits_amount: number
    balance_before: number
    balance_after: number
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
    provider: string
    created_at: string
}

interface SchoolPaymentAccount {
    id: number
    provider: string
    account_name: string
    merchant_id?: string | null
    phone_number?: string | null
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
    account_label?: string | null
    default_model?: string | null
    currency: string
    available_credits: number
    credits_last_synced_at?: string | null
    is_active: boolean
    priority: number
    has_api_key?: boolean
    balance_api_supported?: boolean
}

interface AnalyticsSummary {
    credits_used: number
    tokens_used: number
    estimated_cost: number
    credits_sold: number
    wallet_balance: number
}

interface AIMonitoring {
    providers: AIProvider[]
    total_provider_credits: number
    total_credits_purchased: number
    total_wallet_balance: number
    remaining_system_credits: number
    low_credit_threshold: number
    notification_enabled: boolean
    low_credit_alert: boolean
}

interface CreditTargetUser {
    id: number
    full_name: string
    email: string
    role: string
    school_id?: number | null
    ai_wallet_status?: string
    ai_credit_balance?: number
}

interface CreditTargetSchool {
    id: number
    name: string
}

interface SchoolCreditAllocation {
    id: number
    user_id: number
    allocated_credits: number
    remaining_credits: number
    consumed_credits: number
    is_active: boolean
    created_at: string
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
        <section className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
            <div className="mb-4">
                <h2 className="text-xl font-semibold text-[#111827] dark:text-white">{title}</h2>
                {subtitle && <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{subtitle}</p>}
            </div>
            {children}
        </section>
    )
}

function StatusBadge({ value }: { value: string }) {
    return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${statusColor[value] || "bg-[#F5F5F7] text-[#111827] dark:bg-[#2a3035] dark:text-white"}`}>{value}</span>
}

function Metric({ label, value, danger = false }: { label: string; value: number; danger?: boolean }) {
    return (
        <div className={`rounded-[20px] border p-4 ${danger ? "border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950/30" : "border-[#E5E7EB] bg-[#F8FAFC] dark:border-[#3b4248] dark:bg-[#252b30]"}`}>
            <p className={`text-xs font-medium ${danger ? "text-red-700 dark:text-red-200" : "text-[#6B7280] dark:text-[#c7d0da]"}`}>{label}</p>
            <p className={`mt-2 text-2xl font-semibold ${danger ? "text-red-800 dark:text-red-100" : "text-[#111827] dark:text-white"}`}>{Number(value || 0).toLocaleString("fr-FR")}</p>
        </div>
    )
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
    const [monitoring, setMonitoring] = useState<AIMonitoring | null>(null)
    const [targetUsers, setTargetUsers] = useState<CreditTargetUser[]>([])
    const [targetSchools, setTargetSchools] = useState<CreditTargetSchool[]>([])
    const [schoolUsers, setSchoolUsers] = useState<CreditTargetUser[]>([])
    const [allocations, setAllocations] = useState<SchoolCreditAllocation[]>([])
    const [message, setMessage] = useState("")
    const [loading, setLoading] = useState(false)
    const [accountForm, setAccountForm] = useState({
        provider: "orange_money",
        account_name: "",
        merchant_id: "",
        phone_number: "",
        country_code: "CI",
    })
    const [providerForm, setProviderForm] = useState({
        name: "",
        provider_type: "openai",
        api_key: "",
        account_label: "",
        available_credits: "0",
        base_url: "",
        default_model: "gpt-4.1-mini",
        currency: "USD",
        cost_per_1k_input_tokens: "0",
        cost_per_1k_output_tokens: "0",
        priority: "100",
    })
    const [packForm, setPackForm] = useState({
        name: "",
        credits_amount: "1500",
        price: "7000",
        currency: "FCFA",
        country_code: "CI",
        region: "africa",
        description: "",
        target_type: "both",
    })
    const [purchaseDialog, setPurchaseDialog] = useState<{ pack: AICreditPack; scope: "me" | "school" } | null>(null)
    const [purchaseProvider, setPurchaseProvider] = useState("cinetpay")
    const [purchaseNetwork, setPurchaseNetwork] = useState("orange_money")
    const [purchaseNote, setPurchaseNote] = useState("")
    const [purchaseLoading, setPurchaseLoading] = useState(false)
    const [manualPaymentForm, setManualPaymentForm] = useState({
        owner_type: "user",
        user_id: "",
        school_id: "",
        pack_id: "",
        payment_method: "cash",
        internal_reference: "",
        note: "",
    })
    const [allocationForm, setAllocationForm] = useState({
        user_id: "",
        credits_amount: "",
        note: "",
    })
    const [adjustForm, setAdjustForm] = useState({
        owner_type: "school",
        user_id: "",
        school_id: "",
        credits_amount: "0",
        description: "",
    })
    const [limitForm, setLimitForm] = useState({
        wallet_id: "",
        daily_credit_limit: "",
        monthly_credit_limit: "",
    })
    const [thresholdForm, setThresholdForm] = useState({ low_credit_threshold: "0", notification_enabled: true })

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
                const [schoolWalletRes, schoolUsageRes, schoolTxRes, accountsRes, paymentsRes, schoolUsersRes, allocationsRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/school/ai/wallet`, { headers }),
                    fetch(`${API_BASE_URL}/school/ai/usage`, { headers }),
                    fetch(`${API_BASE_URL}/school/ai/transactions`, { headers }),
                    fetch(`${API_BASE_URL}/school/payment-accounts`, { headers }),
                    fetch(`${API_BASE_URL}/school/payments`, { headers }),
                    fetch(`${API_BASE_URL}/school/ai/users`, { headers }),
                    fetch(`${API_BASE_URL}/school/ai/allocations`, { headers }),
                ])
                if (schoolWalletRes.ok) setSchoolWallet(await schoolWalletRes.json())
                if (schoolUsageRes.ok) setSchoolUsage(await schoolUsageRes.json())
                if (schoolTxRes.ok) setSchoolTransactions(await schoolTxRes.json())
                if (accountsRes.ok) setSchoolPaymentAccounts(await accountsRes.json())
                if (paymentsRes.ok) setSchoolPayments(await paymentsRes.json())
                if (schoolUsersRes.ok) setSchoolUsers(await schoolUsersRes.json())
                if (allocationsRes.ok) setAllocations(await allocationsRes.json())
            }

            if (isSuperAdmin) {
                const [providersRes, platformPaymentsRes, analyticsRes, targetsRes, monitoringRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/platform/ai/providers`, { headers }),
                    fetch(`${API_BASE_URL}/platform/ai/payments`, { headers }),
                    fetch(`${API_BASE_URL}/platform/ai/analytics`, { headers }),
                    fetch(`${API_BASE_URL}/platform/ai/credit-targets`, { headers }),
                    fetch(`${API_BASE_URL}/platform/ai/monitoring`, { headers }),
                ])
                if (providersRes.ok) setProviders(await providersRes.json())
                if (platformPaymentsRes.ok) setPlatformPayments(await platformPaymentsRes.json())
                if (analyticsRes.ok) setAnalytics(await analyticsRes.json())
                if (monitoringRes.ok) {
                    const data = await monitoringRes.json()
                    setMonitoring(data)
                    setThresholdForm({ low_credit_threshold: String(data.low_credit_threshold ?? 0), notification_enabled: Boolean(data.notification_enabled) })
                }
                if (targetsRes.ok) {
                    const targets = await targetsRes.json()
                    setTargetUsers(targets.users || [])
                    setTargetSchools(targets.schools || [])
                }
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

    const openPurchase = (pack: AICreditPack, scope: "me" | "school") => {
        setPurchaseProvider("cinetpay")
        setPurchaseNetwork("orange_money")
        setPurchaseNote("")
        setPurchaseDialog({ pack, scope })
    }

    const purchase = async () => {
        if (!token || !purchaseDialog) return
        if (purchaseProvider === "free" && !purchaseNote.trim()) {
            setMessage("Veuillez indiquer le motif de la demande gratuite.")
            return
        }
        setPurchaseLoading(true)
        setMessage("Création du paiement TeducAI...")
        try {
            const endpoint = purchaseDialog.scope === "school" ? "/school/ai/purchase" : "/me/ai/purchase"
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: "POST",
                headers: { ...headers, "Content-Type": "application/json" },
                body: JSON.stringify({
                    pack_id: purchaseDialog.pack.id,
                    provider: purchaseProvider,
                    payment_method: purchaseProvider,
                    mobile_money_network: purchaseProvider === "cinetpay" ? purchaseNetwork : undefined,
                    note: purchaseNote || undefined,
                    success_url: `${window.location.origin}/${params.locale}/dashboard/ai-credits`,
                    cancel_url: `${window.location.origin}/${params.locale}/dashboard/ai-credits`,
                }),
            })
            const data = await response.json().catch(() => null)
            if (!response.ok) {
                setMessage(data?.detail || "Achat de crédits impossible.")
                return
            }
            setPurchaseDialog(null)
            if (data.checkout_url) {
                window.location.assign(data.checkout_url)
                return
            }
            const manual = ["cash", "free"].includes(purchaseProvider)
            setMessage(manual
                ? `Demande ${data.reference} enregistrée. Elle attend une validation manuelle.`
                : `Paiement ${data.reference} créé avec le statut ${data.provider_status || data.status}.`
            )
            void load()
        } finally {
            setPurchaseLoading(false)
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
            setAccountForm({ provider: "orange_money", account_name: "", merchant_id: "", phone_number: "", country_code: "CI" })
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
                api_key: providerForm.api_key || undefined,
                account_label: providerForm.account_label || undefined,
                available_credits: Number(providerForm.available_credits || 0),
                base_url: providerForm.base_url || undefined,
                default_model: providerForm.default_model,
                currency: providerForm.currency,
                cost_per_1k_input_tokens: Number(providerForm.cost_per_1k_input_tokens),
                cost_per_1k_output_tokens: Number(providerForm.cost_per_1k_output_tokens),
                priority: Number(providerForm.priority),
                is_active: false,
            }),
        })
        if (response.ok) {
            setMessage("Provider IA cree. La cle API est chiffree en base et n'est jamais affichee.")
            setProviderForm({ name: "", provider_type: "openai", api_key: "", account_label: "", available_credits: "0", base_url: "", default_model: "gpt-4.1-mini", currency: "USD", cost_per_1k_input_tokens: "0", cost_per_1k_output_tokens: "0", priority: "100" })
            void load()
        } else {
            setMessage("Creation du provider IA impossible.")
        }
    }

    const createPack = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/platform/ai/credit-packs`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({
                name: packForm.name,
                description: packForm.description || undefined,
                credits_amount: Number(packForm.credits_amount),
                price: Number(packForm.price),
                currency: packForm.currency,
                country_code: packForm.country_code,
                region: packForm.region,
                target_type: packForm.target_type,
                is_active: true,
            }),
        })
        if (response.ok) {
            setMessage("Pack de credits IA cree.")
            setPackForm({ name: "", credits_amount: "1500", price: "7000", currency: "FCFA", country_code: "CI", region: "africa", description: "", target_type: "both" })
            void load()
        } else {
            setMessage("Creation du pack IA impossible.")
        }
    }

    const adjustCredits = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/platform/ai/wallets/adjust`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({
                owner_type: adjustForm.owner_type,
                user_id: adjustForm.owner_type === "user" && adjustForm.user_id ? Number(adjustForm.user_id) : undefined,
                school_id: adjustForm.owner_type === "school" && adjustForm.school_id ? Number(adjustForm.school_id) : undefined,
                credits_amount: Number(adjustForm.credits_amount),
                description: adjustForm.description || "Ajustement Super Admin",
            }),
        })
        if (response.ok) {
            setMessage("Credits IA ajustes.")
            setAdjustForm({ owner_type: "school", user_id: "", school_id: "", credits_amount: "0", description: "" })
            void load()
        } else {
            setMessage("Ajustement des credits impossible.")
        }
    }

    const updateWalletLimits = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!token || !limitForm.wallet_id) return
        const response = await fetch(`${API_BASE_URL}/platform/ai/wallets/${limitForm.wallet_id}/limits`, {
            method: "PUT",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({
                daily_credit_limit: limitForm.daily_credit_limit ? Number(limitForm.daily_credit_limit) : null,
                monthly_credit_limit: limitForm.monthly_credit_limit ? Number(limitForm.monthly_credit_limit) : null,
            }),
        })
        if (response.ok) {
            setMessage("Limites du wallet IA mises a jour.")
            setLimitForm({ wallet_id: "", daily_credit_limit: "", monthly_credit_limit: "" })
            void load()
        } else {
            setMessage("Mise a jour des limites impossible.")
        }
    }

    const updateMonitoringSettings = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/platform/ai/monitoring/settings`, {
            method: "PUT",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({
                low_credit_threshold: Number(thresholdForm.low_credit_threshold || 0),
                notification_enabled: thresholdForm.notification_enabled,
            }),
        })
        const data = await response.json().catch(() => null)
        if (response.ok) {
            setMonitoring(data)
            setMessage("Seuil d'alerte IA mis a jour.")
        } else {
            setMessage(data?.detail || "Mise a jour du seuil impossible.")
        }
    }

    const syncProviderCredits = async (provider: AIProvider) => {
        if (!token) return
        const value = window.prompt(`Credits disponibles pour ${provider.name}`, String(provider.available_credits ?? 0))
        if (value === null) return
        const response = await fetch(`${API_BASE_URL}/platform/ai/providers/${provider.id}`, {
            method: "PUT",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ available_credits: Number(value) }),
        })
        const data = await response.json().catch(() => null)
        setMessage(response.ok ? "Credits provider mis a jour." : data?.detail || "Mise a jour du provider impossible.")
        if (response.ok) void load()
    }

    const autoSyncProvider = async (provider: AIProvider) => {
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/platform/ai/providers/${provider.id}/sync-credits`, {
            method: "POST",
            headers,
        })
        const data = await response.json().catch(() => null)
        setMessage(response.ok ? `Solde ${provider.name} synchronise via API.` : data?.detail || "Synchronisation API impossible.")
        if (response.ok) void load()
    }

    const autoSyncAll = async () => {
        if (!token) return
        setLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/platform/ai/sync-credits`, { method: "POST", headers })
            const data = await response.json().catch(() => null)
            if (!response.ok) { setMessage(data?.detail || "Synchronisation impossible."); return }
            const unsupported = (data?.results || []).filter((r: { status: string }) => r.status === "unsupported").length
            setMessage(`${data.synced}/${data.total} fournisseur(s) synchronise(s) via API. ${unsupported} sans API de solde (valeur manuelle conservee).`)
            void load()
        } finally {
            setLoading(false)
        }
    }

    const validateManualPayment = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/platform/ai/manual-payments`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({
                owner_type: manualPaymentForm.owner_type,
                user_id: manualPaymentForm.owner_type === "user" ? Number(manualPaymentForm.user_id) : undefined,
                school_id: manualPaymentForm.owner_type === "school" ? Number(manualPaymentForm.school_id) : undefined,
                pack_id: Number(manualPaymentForm.pack_id),
                payment_method: manualPaymentForm.payment_method,
                internal_reference: manualPaymentForm.internal_reference || undefined,
                note: manualPaymentForm.note || undefined,
            }),
        })
        const data = await response.json().catch(() => null)
        if (response.ok) {
            setMessage(`Crédits attribués et paiement ${data.reference} validé.`)
            setManualPaymentForm({ owner_type: "user", user_id: "", school_id: "", pack_id: "", payment_method: "cash", internal_reference: "", note: "" })
            void load()
        } else {
            setMessage(data?.detail || "Validation du paiement impossible.")
        }
    }

    const allocateSchoolCredits = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/school/ai/allocations`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: Number(allocationForm.user_id),
                credits_amount: Number(allocationForm.credits_amount),
                note: allocationForm.note || undefined,
            }),
        })
        const data = await response.json().catch(() => null)
        if (response.ok) {
            setMessage("Crédits de l'établissement attribués à l'utilisateur.")
            setAllocationForm({ user_id: "", credits_amount: "", note: "" })
            void load()
        } else {
            setMessage(data?.detail || "Attribution des crédits impossible.")
        }
    }

    const revokeAllocation = async (allocationId: number) => {
        if (!token || !await requestConfirmation({ title: "Révoquer cette allocation", description: "Les crédits non consommés seront restitués à l'établissement. Cette opération sera auditée.", confirmLabel: "Révoquer l'allocation", destructive: true })) return
        const response = await fetch(`${API_BASE_URL}/school/ai/allocations/${allocationId}`, { method: "DELETE", headers })
        const data = await response.json().catch(() => null)
        setMessage(response.ok ? "Allocation révoquée et solde non consommé restitué." : data?.detail || "Révocation impossible.")
        if (response.ok) void load()
    }

    const updateUserAIAccess = async (userId: number, isActive: boolean) => {
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/school/ai/users/${userId}/access`, {
            method: "PUT",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: isActive }),
        })
        setMessage(response.ok ? (isActive ? "Accès aux crédits IA réactivé." : "Accès aux crédits IA suspendu.") : "Modification de l'accès impossible.")
        if (response.ok) void load()
    }

    const validatePendingPayment = async (paymentId: number) => {
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/platform/ai/payments/${paymentId}/manual-validate`, {
            method: "POST",
            headers,
        })
        const data = await response.json().catch(() => null)
        setMessage(response.ok ? "Paiement manuel validé et crédits ajoutés." : data?.detail || "Validation impossible.")
        if (response.ok) void load()
    }

    const purchaseMethods = [
        { key: "cash", label: "Espèces", icon: Banknote },
        { key: "stripe", label: "Stripe", icon: CreditCard },
        { key: "djamo", label: "Djamo", icon: CreditCard },
        { key: "cinetpay", label: "CinetPay", icon: Smartphone },
        { key: "free", label: "Gratuit", icon: Gift },
    ]

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

            {message && <div className="rounded-[22px] border border-[#E5E7EB] bg-[#F5F5F7] p-4 text-sm text-[#111827] dark:border-[#3b4248] dark:bg-[#2a3035] dark:text-white">{message}</div>}

            <div className="grid gap-4 lg:grid-cols-4">
                <div className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <div className="flex items-center justify-between"><p className="text-sm text-[#6B7280]">Mes credits</p><Wallet className="h-5 w-5 text-[#6B7280]" /></div>
                    <p className="mt-3 text-3xl font-semibold text-[#111827]">{myWallet?.balance_credits ?? 0}</p>
                    <p className="text-xs text-[#6B7280]">Utilises: {myWallet?.total_used_credits ?? 0}</p>
                </div>
                <div className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <div className="flex items-center justify-between"><p className="text-sm text-[#6B7280]">Credits etablissement</p><Landmark className="h-5 w-5 text-[#6B7280]" /></div>
                    <p className="mt-3 text-3xl font-semibold text-[#111827]">{schoolWallet?.balance_credits ?? "-"}</p>
                    <p className="text-xs text-[#6B7280]">Requetes ecole: {schoolUsage.length}</p>
                </div>
                <div className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <div className="flex items-center justify-between"><p className="text-sm text-[#6B7280]">Requetes IA</p><BrainCircuit className="h-5 w-5 text-[#6B7280]" /></div>
                    <p className="mt-3 text-3xl font-semibold text-[#111827]">{analytics?.tokens_used ?? myUsage.reduce((sum, item) => sum + (item.total_tokens || 0), 0)}</p>
                    <p className="text-xs text-[#6B7280]">Crédits utilisés: {analytics?.credits_used ?? myUsage.reduce((sum, item) => sum + item.credits_charged, 0)}</p>
                </div>
                <div className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                    <div className="flex items-center justify-between"><p className="text-sm text-[#6B7280]">Separation paiements</p><ShieldCheck className="h-5 w-5 text-[#6B7280]" /></div>
                    <p className="mt-3 text-lg font-semibold text-[#111827]">TeducAI / Ecole</p>
                    <p className="text-xs text-[#6B7280]">Flux financiers isoles</p>
                </div>
            </div>

            {isSuperAdmin && monitoring && (
                <CardShell title="Monitoring credits IA plateforme" subtitle="Credits provider disponibles, credits vendus ou attribues, et seuil d'alerte Super Admin.">
                    {monitoring.low_credit_alert && (
                        <div className="mb-4 flex items-center gap-2 rounded-[18px] border border-red-300 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800 dark:border-red-800 dark:bg-red-950/40 dark:text-red-200">
                            <AlertTriangle className="h-5 w-5" />
                            Credits IA restants sous le seuil configure.
                        </div>
                    )}
                    <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                        <p className="text-xs text-[#6B7280] dark:text-[#c7d0da]">La synchronisation API met a jour le solde des fournisseurs qui l&apos;exposent (ex: OpenRouter). Les autres conservent la valeur saisie manuellement.</p>
                        <button type="button" onClick={() => void autoSyncAll()} disabled={loading} className="rounded-full bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-white dark:text-black">Synchroniser via API</button>
                    </div>
                    <div className="grid gap-3 md:grid-cols-4">
                        <Metric label="Credits providers" value={monitoring.total_provider_credits} />
                        <Metric label="Credits achetes/alloues" value={monitoring.total_credits_purchased} />
                        <Metric label="Credits restants systeme" value={monitoring.remaining_system_credits} danger={monitoring.low_credit_alert} />
                        <Metric label="Solde wallets" value={monitoring.total_wallet_balance} />
                    </div>
                    <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                        {monitoring.providers.map(provider => (
                            <div key={provider.id} className="rounded-[20px] border border-[#E5E7EB] p-4 dark:border-[#3b4248]">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <p className="font-semibold text-[#111827] dark:text-white">{provider.name}</p>
                                        <p className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{provider.provider_type}{provider.account_label ? ` - ${provider.account_label}` : ""}</p>
                                    </div>
                                    <StatusBadge value={provider.is_active ? "active" : "inactive"} />
                                </div>
                                <p className="mt-4 text-2xl font-semibold text-[#111827] dark:text-white">{provider.available_credits.toLocaleString("fr-FR")}</p>
                                <p className="text-xs text-[#6B7280] dark:text-[#c7d0da]">Derniere synchro: {provider.credits_last_synced_at || "Non renseignee"}</p>
                                <p className="mt-1 text-xs font-medium" style={{ color: provider.balance_api_supported ? "#0F766E" : "#92400E" }}>
                                    {provider.balance_api_supported ? "Solde via API disponible" : "Solde manuel (API non disponible)"}
                                </p>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {provider.balance_api_supported && (
                                        <button type="button" onClick={() => void autoSyncProvider(provider)} className="rounded-full bg-[#0F766E] px-3 py-2 text-sm text-white hover:bg-[#115E59]">Synchroniser (API)</button>
                                    )}
                                    <button type="button" onClick={() => void syncProviderCredits(provider)} className="rounded-full border border-[#D1D5DB] px-3 py-2 text-sm hover:bg-[#F5F5F7] dark:border-[#56616a] dark:hover:bg-[#2a3035]">Saisie manuelle</button>
                                </div>
                            </div>
                        ))}
                    </div>
                    <form onSubmit={updateMonitoringSettings} className="mt-5 flex flex-wrap items-end gap-3 rounded-[20px] border border-[#E5E7EB] p-4 dark:border-[#3b4248]">
                        <label className="grid gap-1 text-sm font-medium text-[#111827] dark:text-white">
                            Seuil minimum
                            <input className="apple-input" type="number" value={thresholdForm.low_credit_threshold} onChange={event => setThresholdForm({ ...thresholdForm, low_credit_threshold: event.target.value })} />
                        </label>
                        <label className="flex min-h-11 items-center gap-2 text-sm text-[#111827] dark:text-white">
                            <input type="checkbox" checked={thresholdForm.notification_enabled} onChange={event => setThresholdForm({ ...thresholdForm, notification_enabled: event.target.checked })} />
                            Notification active
                        </label>
                        <button className="rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white dark:bg-white dark:text-black">Enregistrer le seuil</button>
                    </form>
                </CardShell>
            )}

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
                                    <p className="font-semibold text-[#111827]">{money(pack.price, pack.currency)}</p>
                                </div>
                                {pack.description && <p className="mt-2 text-sm text-[#6B7280]">{pack.description}</p>}
                                <div className="mt-4 flex flex-wrap gap-2">
                                    {pack.target_type !== "school" && <button type="button" onClick={() => openPurchase(pack, "me")} className="rounded-full bg-black px-4 py-2 text-sm font-medium text-white hover:bg-black/90">Acheter pour moi</button>}
                                    {canManageSchool && pack.target_type !== "user" && <button type="button" onClick={() => openPurchase(pack, "school")} className="rounded-full border border-[#D1D5DB] px-4 py-2 text-sm hover:bg-[#F5F5F7]">Acheter pour l&apos;ecole</button>}
                                </div>
                            </div>
                        ))}
                    </div>
                </CardShell>

                <CardShell title="Comptes de paiement ecole" subtitle="Utilises uniquement pour les paiements scolaires encaisses par l'etablissement.">
                    {canManageSchool ? (
                        <form onSubmit={createPaymentAccount} className="grid gap-3">
                            <input className="apple-input" placeholder="Nom du compte" value={accountForm.account_name} onChange={event => setAccountForm({ ...accountForm, account_name: event.target.value })} required title="Nom du compte: nom visible par la comptabilite pour identifier le compte d'encaissement de l'etablissement." />
                            <input className="apple-input" placeholder="Identifiant marchand" value={accountForm.merchant_id} onChange={event => setAccountForm({ ...accountForm, merchant_id: event.target.value })} title="Identifiant marchand: reference fournisseur ou banque utilisee pour encaisser les paiements scolaires." />
                            <input className="apple-input" placeholder="Telephone de paiement" value={accountForm.phone_number} onChange={event => setAccountForm({ ...accountForm, phone_number: event.target.value })} title="Telephone: numero Mobile Money ou contact du compte de paiement ecole." />
                            <div className="grid gap-3 sm:grid-cols-3">
                                <input className="apple-input" value={accountForm.provider} onChange={event => setAccountForm({ ...accountForm, provider: event.target.value })} title="Provider: Orange Money, MTN, Wave, banque ou autre prestataire de paiement." />
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
                    <Table headers={["Date", "Type", "Credits", "Avant", "Après"]} rows={myTransactions.map(item => [item.created_at, item.transaction_type, item.credits_amount, item.balance_before, item.balance_after])} />
                </CardShell>
                <CardShell title="Usage IA utilisateur">
                    <Table headers={["Date", "Module", "Action", "Modele", "Credits", "Statut"]} rows={myUsage.map(item => [item.created_at, item.module_name || "-", item.action_type || "-", item.model_name || "-", item.credits_charged, item.status])} />
                </CardShell>
                {canManageSchool && (
                    <>
                        <CardShell title="Distribuer les crédits de l'établissement" subtitle="Le montant est débité du portefeuille école et crédité à l'utilisateur sélectionné.">
                            <form onSubmit={allocateSchoolCredits} className="grid gap-3">
                                <select className="apple-select" value={allocationForm.user_id} onChange={event => setAllocationForm({ ...allocationForm, user_id: event.target.value })} required>
                                    <option value="">Sélectionner un utilisateur</option>
                                    {schoolUsers.map(item => <option key={item.id} value={item.id}>{item.role} - {item.full_name} ({item.email})</option>)}
                                </select>
                                <input className="apple-input" type="number" min="1" placeholder="Nombre exact de crédits" value={allocationForm.credits_amount} onChange={event => setAllocationForm({ ...allocationForm, credits_amount: event.target.value })} required />
                                <input className="apple-input" placeholder="Motif ou période d'utilisation" value={allocationForm.note} onChange={event => setAllocationForm({ ...allocationForm, note: event.target.value })} />
                                <button className="w-fit rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white">Attribuer</button>
                            </form>
                            <div className="mt-5 space-y-2">
                                {schoolUsers.map(item => (
                                    <div key={`user-${item.id}`} className="flex flex-wrap items-center justify-between gap-3 rounded-[18px] border border-[#E5E7EB] px-3 py-2 text-sm">
                                        <span>{item.role} - {item.full_name} · {item.ai_credit_balance ?? 0} crédits</span>
                                        <button type="button" onClick={() => void updateUserAIAccess(item.id, item.ai_wallet_status !== "active")} className="rounded-full border border-[#D1D5DB] px-3 py-1">
                                            {item.ai_wallet_status === "active" ? "Suspendre l'accès" : "Réactiver l'accès"}
                                        </button>
                                    </div>
                                ))}
                                {allocations.slice(0, 20).map(item => (
                                    <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-[18px] bg-[#F5F5F7] px-3 py-2 text-sm">
                                        <span>{schoolUsers.find(userItem => userItem.id === item.user_id)?.full_name || `Utilisateur #${item.user_id}`} : {item.remaining_credits}/{item.allocated_credits} restants</span>
                                        {item.is_active && <button type="button" onClick={() => void revokeAllocation(item.id)} className="rounded-full border border-red-200 px-3 py-1 text-red-700">Révoquer</button>}
                                    </div>
                                ))}
                            </div>
                        </CardShell>
                        <CardShell title="Transactions credits ecole">
                            <Table headers={["Date", "Type", "Credits", "Avant", "Après"]} rows={schoolTransactions.map(item => [item.created_at, item.transaction_type, item.credits_amount, item.balance_before, item.balance_after])} />
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
                            <div className="grid gap-3 sm:grid-cols-2">
                                <input className="apple-input" type="password" placeholder="Cle API chiffree" value={providerForm.api_key} onChange={event => setProviderForm({ ...providerForm, api_key: event.target.value })} title="Cle API: elle est chiffree en base et n'est jamais renvoyee par l'API." />
                                <input className="apple-input" placeholder="Base URL optionnelle" value={providerForm.base_url} onChange={event => setProviderForm({ ...providerForm, base_url: event.target.value })} title="Base URL: endpoint compatible OpenAI pour OpenRouter, Grok, Custom API ou adaptateur fournisseur." />
                            </div>
                            <div className="grid gap-3 sm:grid-cols-4">
                                <input className="apple-input" value={providerForm.currency} onChange={event => setProviderForm({ ...providerForm, currency: event.target.value })} title="Devise provider: devise de facturation technique du fournisseur IA." />
                                <input className="apple-input" type="number" value={providerForm.cost_per_1k_input_tokens} onChange={event => setProviderForm({ ...providerForm, cost_per_1k_input_tokens: event.target.value })} title="Cout input: cout estime par 1000 tokens entrants." />
                                <input className="apple-input" type="number" value={providerForm.cost_per_1k_output_tokens} onChange={event => setProviderForm({ ...providerForm, cost_per_1k_output_tokens: event.target.value })} title="Cout output: cout estime par 1000 tokens sortants." />
                                <input className="apple-input" type="number" value={providerForm.priority} onChange={event => setProviderForm({ ...providerForm, priority: event.target.value })} title="Priorite: plus le nombre est faible, plus le provider est prioritaire." />
                            </div>
                            <button className="inline-flex w-fit items-center gap-2 rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white hover:bg-black/90"><BadgeCheck className="h-4 w-4" /> Creer provider</button>
                        </form>
                        <Table headers={["Nom", "Type", "Modele", "Statut"]} rows={providers.map(item => [item.name, item.provider_type, item.default_model || "-", item.is_active ? "active" : "inactive"])} />
                    </CardShell>
                    <CardShell title="Créer un pack de crédits IA" subtitle="Définissez les packs vendus par pays, devise et région.">
                        <form onSubmit={createPack} className="grid gap-3">
                            <select className="apple-select" value={packForm.target_type} onChange={event => setPackForm({ ...packForm, target_type: event.target.value })}>
                                <option value="both">Utilisateurs et établissements</option>
                                <option value="user">Utilisateurs uniquement</option>
                                <option value="school">Établissements uniquement</option>
                            </select>
                            <input className="apple-input" placeholder="Nom du pack" value={packForm.name} onChange={event => setPackForm({ ...packForm, name: event.target.value })} required title="Nom du pack: libellé visible aux écoles et utilisateurs." />
                            <textarea className="apple-input min-h-24" placeholder="Description" value={packForm.description} onChange={event => setPackForm({ ...packForm, description: event.target.value })} title="Description: détail facultatif du pack de crédits IA." />
                            <div className="grid gap-3 sm:grid-cols-3">
                                <input className="apple-input" type="number" value={packForm.credits_amount} onChange={event => setPackForm({ ...packForm, credits_amount: event.target.value })} title="Crédits: nombre de crédits IA inclus dans le pack." />
                                <input className="apple-input" type="number" value={packForm.price} onChange={event => setPackForm({ ...packForm, price: event.target.value })} title="Prix: montant facturé pour ce pack." />
                                <input className="apple-input" value={packForm.currency} onChange={event => setPackForm({ ...packForm, currency: event.target.value })} title="Devise: FCFA, GBP, EUR ou USD." />
                            </div>
                            <div className="grid gap-3 sm:grid-cols-2">
                                <input className="apple-input" value={packForm.country_code} onChange={event => setPackForm({ ...packForm, country_code: event.target.value })} title="Pays: code pays cible du pack." />
                                <input className="apple-input" value={packForm.region} onChange={event => setPackForm({ ...packForm, region: event.target.value })} title="Région: africa, uk_europe ou autre segment commercial." />
                            </div>
                            <button className="inline-flex w-fit items-center gap-2 rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white hover:bg-black/90"><Plus className="h-4 w-4" /> Créer le pack</button>
                        </form>
                    </CardShell>
                    <CardShell title="Distribuer ou ajuster des crédits" subtitle="Ajoutez des crédits gratuits, bonus, remboursements ou ajustements administratifs.">
                        <form onSubmit={validateManualPayment} className="mb-6 grid gap-3 rounded-[22px] border border-[#E5E7EB] p-4">
                            <h3 className="font-semibold text-[#111827]">Valider un paiement espèces ou une attribution gratuite</h3>
                            <div className="grid gap-3 sm:grid-cols-2">
                                <select className="apple-select" value={manualPaymentForm.owner_type} onChange={event => setManualPaymentForm({ ...manualPaymentForm, owner_type: event.target.value })}>
                                    <option value="user">Utilisateur</option>
                                    <option value="school">Établissement</option>
                                </select>
                                <select className="apple-select" value={manualPaymentForm.payment_method} onChange={event => setManualPaymentForm({ ...manualPaymentForm, payment_method: event.target.value })}>
                                    <option value="cash">Paiement en espèces</option>
                                    <option value="free">Attribution gratuite</option>
                                </select>
                            </div>
                            {manualPaymentForm.owner_type === "user" ? (
                                <select className="apple-select" value={manualPaymentForm.user_id} onChange={event => setManualPaymentForm({ ...manualPaymentForm, user_id: event.target.value })} required>
                                    <option value="">Sélectionner un utilisateur</option>
                                    {targetUsers.map(item => <option key={item.id} value={item.id}>{item.role} - {item.full_name} ({item.email})</option>)}
                                </select>
                            ) : (
                                <select className="apple-select" value={manualPaymentForm.school_id} onChange={event => setManualPaymentForm({ ...manualPaymentForm, school_id: event.target.value })} required>
                                    <option value="">Sélectionner un établissement</option>
                                    {targetSchools.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
                                </select>
                            )}
                            <select className="apple-select" value={manualPaymentForm.pack_id} onChange={event => setManualPaymentForm({ ...manualPaymentForm, pack_id: event.target.value })} required>
                                <option value="">Sélectionner un pack</option>
                                {packs.filter(pack => pack.target_type === "both" || pack.target_type === manualPaymentForm.owner_type).map(pack => <option key={pack.id} value={pack.id}>{pack.name} - {pack.credits_amount} crédits - {money(pack.price, pack.currency)}</option>)}
                            </select>
                            <input className="apple-input" placeholder="Référence de caisse ou bordereau" value={manualPaymentForm.internal_reference} onChange={event => setManualPaymentForm({ ...manualPaymentForm, internal_reference: event.target.value })} />
                            <textarea className="apple-input min-h-20" placeholder={manualPaymentForm.payment_method === "free" ? "Motif obligatoire de l'attribution gratuite" : "Note facultative"} value={manualPaymentForm.note} onChange={event => setManualPaymentForm({ ...manualPaymentForm, note: event.target.value })} required={manualPaymentForm.payment_method === "free"} />
                            <button className="w-fit rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white">Valider et créditer</button>
                        </form>
                        <form onSubmit={adjustCredits} className="grid gap-3">
                            <select className="apple-select" value={adjustForm.owner_type} onChange={event => setAdjustForm({ ...adjustForm, owner_type: event.target.value })} title="Propriétaire: utilisateur ou école à créditer.">
                                <option value="school">École</option>
                                <option value="user">Utilisateur</option>
                            </select>
                            <div className="grid gap-3 sm:grid-cols-2">
                                <input className="apple-input" placeholder="ID école" value={adjustForm.school_id} onChange={event => setAdjustForm({ ...adjustForm, school_id: event.target.value })} title="ID école: requis si le propriétaire est une école." />
                                <input className="apple-input" placeholder="ID utilisateur" value={adjustForm.user_id} onChange={event => setAdjustForm({ ...adjustForm, user_id: event.target.value })} title="ID utilisateur: requis si le propriétaire est un utilisateur." />
                            </div>
                            <input className="apple-input" type="number" value={adjustForm.credits_amount} onChange={event => setAdjustForm({ ...adjustForm, credits_amount: event.target.value })} title="Crédits: montant positif pour ajouter, négatif pour retirer." />
                            <input className="apple-input" placeholder="Motif" value={adjustForm.description} onChange={event => setAdjustForm({ ...adjustForm, description: event.target.value })} title="Motif: justification visible dans l'historique des transactions." />
                            <button className="inline-flex w-fit items-center gap-2 rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white hover:bg-black/90">Appliquer l&apos;ajustement</button>
                        </form>
                    </CardShell>
                    <CardShell title="Limites de crédits IA" subtitle="Définissez des plafonds quotidiens utilisateur et mensuels école sur un wallet.">
                        <form onSubmit={updateWalletLimits} className="grid gap-3">
                            <input className="apple-input" placeholder="ID wallet" value={limitForm.wallet_id} onChange={event => setLimitForm({ ...limitForm, wallet_id: event.target.value })} required title="ID wallet: identifiant du portefeuille IA à limiter." />
                            <div className="grid gap-3 sm:grid-cols-2">
                                <input className="apple-input" type="number" placeholder="Limite quotidienne utilisateur" value={limitForm.daily_credit_limit} onChange={event => setLimitForm({ ...limitForm, daily_credit_limit: event.target.value })} title="Limite quotidienne: maximum de crédits par utilisateur et par jour." />
                                <input className="apple-input" type="number" placeholder="Limite mensuelle école" value={limitForm.monthly_credit_limit} onChange={event => setLimitForm({ ...limitForm, monthly_credit_limit: event.target.value })} title="Limite mensuelle: maximum de crédits par école et par mois." />
                            </div>
                            <button className="inline-flex w-fit items-center gap-2 rounded-full bg-black px-5 py-2.5 text-sm font-medium text-white hover:bg-black/90">Enregistrer les limites</button>
                        </form>
                    </CardShell>
                    <CardShell title="Paiements plateforme TeducAI">
                        <div className="mb-4 space-y-2">
                            {platformPayments.filter(item => item.status === "pending_manual_validation").map(item => (
                                <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 rounded-[18px] border border-amber-300 bg-amber-50 px-3 py-2 text-sm dark:border-amber-800 dark:bg-[#342f20]">
                                    <span>{item.reference} · {item.provider} · {money(item.amount, item.currency)}</span>
                                    <button type="button" onClick={() => void validatePendingPayment(item.id)} className="rounded-full bg-black px-3 py-1.5 text-white dark:bg-white dark:text-black">Valider</button>
                                </div>
                            ))}
                        </div>
                        <Table headers={["Date", "Type", "Reference", "Montant", "Beneficiaire", "Statut"]} rows={platformPayments.map(item => [item.created_at, item.payment_type, item.reference, money(item.amount, item.currency), item.beneficiary_entity, item.status])} />
                        {analytics && (
                            <div className="mt-5 rounded-[22px] bg-[#F5F5F7] p-4 text-sm">
                                <p className="font-semibold text-[#111827]">Analytics IA plateforme</p>
                                <p className="mt-1 text-[#6B7280]">Credits utilises: {analytics.credits_used} | Tokens: {analytics.tokens_used} | Credits vendus: {analytics.credits_sold}</p>
                            </div>
                        )}
                    </CardShell>
                </div>
            )}
            <Dialog open={Boolean(purchaseDialog)} onOpenChange={open => !open && setPurchaseDialog(null)}>
                <DialogContent className="sm:max-w-[560px] dark:border-[#3b4248] dark:bg-[#202528]">
                    <DialogHeader>
                        <DialogTitle>Paiement des crédits IA</DialogTitle>
                    </DialogHeader>
                    {purchaseDialog && (
                        <div className="space-y-5">
                            <div className="rounded-[20px] bg-[#F5F5F7] p-4 dark:bg-[#2a3035]">
                                <p className="font-semibold">{purchaseDialog.pack.name}</p>
                                <p className="mt-1 text-sm text-[#6B7280]">
                                    {purchaseDialog.pack.credits_amount.toLocaleString("fr-FR")} crédits · {money(purchaseDialog.pack.price, purchaseDialog.pack.currency)} · {purchaseDialog.scope === "school" ? "Établissement" : "Mon compte"}
                                </p>
                            </div>
                            <div className="grid gap-3 sm:grid-cols-2">
                                {purchaseMethods.map(({ key, label, icon: Icon }) => (
                                    <button
                                        key={key}
                                        type="button"
                                        onClick={() => setPurchaseProvider(key)}
                                        className={`flex items-center gap-3 rounded-[18px] border p-4 text-left transition ${purchaseProvider === key ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-[#D1D5DB] hover:bg-[#F5F5F7] dark:border-[#3b4248] dark:hover:bg-[#2a3035]"}`}
                                    >
                                        <Icon className="h-5 w-5" /> {label}
                                    </button>
                                ))}
                            </div>
                            {purchaseProvider === "cinetpay" && (
                                <select className="apple-select" value={purchaseNetwork} onChange={event => setPurchaseNetwork(event.target.value)}>
                                    <option value="orange_money">Orange Money</option>
                                    <option value="wave">Wave</option>
                                    <option value="mtn_money">MTN Money</option>
                                    <option value="moov_money">Moov Money</option>
                                </select>
                            )}
                            {["cash", "free"].includes(purchaseProvider) && (
                                <textarea
                                    className="apple-input min-h-24 py-3"
                                    value={purchaseNote}
                                    onChange={event => setPurchaseNote(event.target.value)}
                                    placeholder={purchaseProvider === "free" ? "Motif obligatoire de la demande gratuite" : "Référence ou note pour la validation en espèces"}
                                />
                            )}
                            <p className="text-sm text-[#6B7280]">
                                Les paiements en espèces et les demandes gratuites restent en attente jusqu&apos;à validation par un Super Administrateur.
                            </p>
                        </div>
                    )}
                    <DialogFooter>
                        <button type="button" onClick={() => setPurchaseDialog(null)} className="rounded-full border border-[#D1D5DB] px-5 py-2.5 dark:border-[#3b4248]">Annuler</button>
                        <button type="button" disabled={purchaseLoading} onClick={() => void purchase()} className="rounded-full bg-black px-5 py-2.5 font-medium text-white disabled:opacity-50 dark:bg-white dark:text-black">
                            {purchaseLoading ? "Initialisation..." : "Continuer le paiement"}
                        </button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
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
