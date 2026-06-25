"use client"

import { useCallback, useEffect, useState } from "react"
import { useRouter, useParams, useSearchParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { CreditCard, Sparkles, Smartphone } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"

type CartItem = {
    id: number
    item_type: string
    title: string
    description?: string
    quantity: number
    unit_amount: number
    currency: string
    line_total: number
    source_type?: string
    source_id?: number
    metadata_json?: Record<string, unknown>
}

type Cart = {
    items: CartItem[]
    total: number
    currency: string
}

type AICreditPack = {
    id: number
    name: string
    description?: string
    credits_amount: number
    price: number
    currency: string
    target_type: "user" | "school" | "both"
}

export default function CheckoutPage() {
    const t = useTranslations("checkout")
    const appT = useTranslations("app")
    const { token } = useAuth()
    const router = useRouter()
    const params = useParams()
    const searchParams = useSearchParams()
    const locale = normalizeLocale(params.locale as string)
    const [cart, setCart] = useState<Cart>({ items: [], total: 0, currency: "FCFA" })
    const [packs, setPacks] = useState<AICreditPack[]>([])
    const [selectedPackId, setSelectedPackId] = useState<number | null>(null)
    const [provider, setProvider] = useState("cinetpay")
    const [network, setNetwork] = useState("orange_money")
    const [status, setStatus] = useState("")

    const loadCart = useCallback(() => {
        if (!token) return
        fetch(`${API_BASE_URL}/account/cart`, { headers: { Authorization: `Bearer ${token}` } })
            .then(response => response.ok ? response.json() : null)
            .then(data => data && setCart(data))
            .catch(() => undefined)
    }, [token])

    useEffect(() => {
        loadCart()
    }, [loadCart])

    const isAICreditCheckout = searchParams.get("purchase") === "ai-credits"
    const requestedCredits = Number(searchParams.get("credits") || 0)
    const selectedPack = packs.find(pack => pack.id === selectedPackId) || null
    const previewItem = selectedPack ? {
        title: selectedPack.name,
        description: selectedPack.description || "Pack de credits IA TeducAI",
        quantity: 1,
        unit_amount: selectedPack.price,
        line_total: selectedPack.price,
        currency: selectedPack.currency,
        metadata_json: {
            credits_amount: selectedPack.credits_amount,
            unit_price: selectedPack.price / selectedPack.credits_amount,
            taxes: 0,
        },
    } : null
    const displayedItems = cart.items.length ? cart.items : previewItem ? [previewItem] : []
    const subtotal = displayedItems.reduce((sum, item) => sum + item.line_total, 0)
    const taxes = displayedItems.reduce((sum, item) => sum + Number(item.metadata_json?.taxes || 0), 0)
    const total = subtotal + taxes
    const currency = displayedItems[0]?.currency || cart.currency

    useEffect(() => {
        if (!isAICreditCheckout) return
        fetch(`${API_BASE_URL}/platform/ai/credit-packs?active_only=true`)
            .then(response => response.ok ? response.json() : [])
            .then((data: AICreditPack[]) => {
                const userPacks = Array.isArray(data) ? data.filter(pack => pack.target_type === "user" || pack.target_type === "both") : []
                setPacks(userPacks)
                const closest = [...userPacks].sort((a, b) => Math.abs(a.credits_amount - requestedCredits) - Math.abs(b.credits_amount - requestedCredits))[0]
                if (closest) setSelectedPackId(closest.id)
            })
            .catch(() => setPacks([]))
    }, [isAICreditCheckout, requestedCredits])

    const ensureSelectedPackInCart = async () => {
        if (!token || !selectedPack) return true
        if (cart.items.some(item => item.item_type === "ai_credits" && item.source_type === "ai_credit_pack" && item.source_id === selectedPack.id)) return true
        const response = await fetch(`${API_BASE_URL}/account/cart/items`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                item_type: "ai_credits",
                title: selectedPack.name,
                description: selectedPack.description || "Pack de credits IA TeducAI",
                quantity: 1,
                unit_amount: selectedPack.price,
                currency: selectedPack.currency,
                provider_scope: "platform",
                source_type: "ai_credit_pack",
                source_id: selectedPack.id,
                metadata_json: {
                    credits_amount: selectedPack.credits_amount,
                    unit_price: selectedPack.price / selectedPack.credits_amount,
                    taxes: 0,
                    pack_id: selectedPack.id,
                    module: "teducai_emploi",
                },
            }),
        })
        if (!response.ok) {
            const payload = await response.json().catch(() => null)
            setStatus(payload?.detail || "Impossible d'ajouter le pack IA au panier.")
            return false
        }
        loadCart()
        return true
    }

    const checkout = async () => {
        if (!token) return
        if (selectedPack && !await ensureSelectedPackInCart()) return
        setStatus(t("creating"))
        const res = await fetch(`${API_BASE_URL}/account/checkout`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                provider,
                mobile_money_network: provider === "cinetpay" ? network : undefined,
                success_url: `${window.location.origin}/${locale}/dashboard/account/invoices`,
                cancel_url: `${window.location.origin}/${locale}/dashboard/checkout`,
            }),
        })
        if (res.ok) {
            const result = await res.json()
            setStatus(t("created"))
            if (result.checkout_url) {
                window.location.assign(result.checkout_url)
            } else {
                const returnPage = searchParams.get("return")
                window.setTimeout(() => router.push(returnPage ? `/${locale}/dashboard/${returnPage}` : `/${locale}/dashboard/account/invoices`), 900)
            }
        } else {
            const text = await res.text()
            setStatus(t("error", { message: text.slice(0, 180) }))
        }
    }

    return (
        <div className="apple-page">
            <div>
                <h1 className="apple-page-title">{t("title")}</h1>
                <p className="apple-page-description">{t("description")}</p>
            </div>
            <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
                <section className="rounded-[28px] border border-[#E5E7EB] bg-white p-6 dark:border-[#3b4248] dark:bg-[#202528]">
                    <h2 className="text-xl font-semibold">{t("items")}</h2>
                    {isAICreditCheckout && (
                        <div className="mt-4 rounded-2xl border border-[#E5E7EB] p-4 dark:border-[#3b4248]">
                            <p className="flex items-center gap-2 font-semibold"><Sparkles className="h-5 w-5 text-[#0F766E]" /> Packs de credits IA</p>
                            <div className="mt-3 grid gap-2">
                                {packs.map(pack => (
                                    <button key={pack.id} type="button" onClick={() => setSelectedPackId(pack.id)} className={`rounded-2xl border p-4 text-left transition ${selectedPackId === pack.id ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-[#E5E7EB] dark:border-[#3b4248]"}`}>
                                        <span className="block font-semibold">{pack.name} - {pack.credits_amount.toLocaleString()} credits</span>
                                        <span className="text-sm opacity-80">{pack.price.toLocaleString()} {pack.currency}</span>
                                    </button>
                                ))}
                                {!packs.length && <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">Aucun pack actif disponible pour le moment.</p>}
                            </div>
                        </div>
                    )}
                    <div className="mt-4 space-y-3">
                        {displayedItems.map((item, index) => (
                            <div key={"id" in item ? item.id : `preview-${index}`} className="flex items-center justify-between rounded-2xl bg-[#F6F7F9] p-4 dark:bg-[#2a3035]">
                                <div><p className="font-semibold">{item.title}</p><p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{item.description || t("quantity", { quantity: item.quantity })}</p>{Number(item.metadata_json?.credits_amount || 0) > 0 && <p className="text-sm text-[#0F766E] dark:text-[#5eead4]">{Number(item.metadata_json?.credits_amount).toLocaleString()} credits - prix unitaire {Number(item.metadata_json?.unit_price || 0).toLocaleString()} {item.currency}</p>}</div>
                                <p className="font-semibold">{item.line_total.toLocaleString()} {item.currency}</p>
                            </div>
                        ))}
                        {!displayedItems.length && <p className="rounded-2xl bg-[#F6F7F9] p-6 text-center text-[#6B7280] dark:bg-[#2a3035] dark:text-[#c7d0da]">{appT("emptyCart")}</p>}
                    </div>
                </section>
                <aside className="rounded-[28px] border border-[#E5E7EB] bg-white p-6 dark:border-[#3b4248] dark:bg-[#202528]">
                    <h2 className="text-xl font-semibold">{t("payment")}</h2>
                    <div className="mt-4 grid gap-3">
                        <button type="button" onClick={() => setProvider("stripe")} className={`flex items-center gap-3 rounded-2xl border p-4 text-left ${provider === "stripe" ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : ""}`}><CreditCard className="h-5 w-5" />{t("stripe")}</button>
                        <button type="button" onClick={() => setProvider("djamo")} className={`flex items-center gap-3 rounded-2xl border p-4 text-left ${provider === "djamo" ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : ""}`}><CreditCard className="h-5 w-5" />{t("djamo")}</button>
                        <button type="button" onClick={() => setProvider("cinetpay")} className={`flex items-center gap-3 rounded-2xl border p-4 text-left ${provider === "cinetpay" ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : ""}`}><Smartphone className="h-5 w-5" />{t("cinetpay")}</button>
                    </div>
                    {provider === "cinetpay" && (
                        <select className="apple-select mt-4" value={network} onChange={event => setNetwork(event.target.value)}>
                            <option value="orange_money">Orange Money</option>
                            <option value="wave">Wave</option>
                            <option value="mtn_money">MTN Money</option>
                            <option value="moov_money">Moov Money</option>
                        </select>
                    )}
                    <div className="mt-6 space-y-2 border-t border-[#E5E7EB] pt-4 dark:border-[#3b4248]">
                        <div className="flex items-center justify-between"><span>Sous-total</span><strong>{subtotal.toLocaleString()} {currency}</strong></div>
                        <div className="flex items-center justify-between text-sm text-[#6B7280] dark:text-[#c7d0da]"><span>Taxes</span><span>{taxes.toLocaleString()} {currency}</span></div>
                        <div className="flex items-center justify-between"><span>{appT("total")}</span><strong>{total.toLocaleString()} {currency}</strong></div>
                    </div>
                    <button type="button" disabled={!displayedItems.length} onClick={checkout} className="mt-4 w-full rounded-full bg-black px-4 py-3 font-semibold text-white disabled:opacity-50 dark:bg-white dark:text-black">{t("payNow")}</button>
                    {status && <p className="mt-3 text-sm text-[#6B7280] dark:text-[#c7d0da]">{status}</p>}
                </aside>
            </div>
        </div>
    )
}
