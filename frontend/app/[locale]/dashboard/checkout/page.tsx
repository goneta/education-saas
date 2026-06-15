"use client"

import { useCallback, useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { CreditCard, Smartphone } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"

type CartItem = {
    id: number
    title: string
    quantity: number
    unit_amount: number
    currency: string
    line_total: number
}

type Cart = {
    items: CartItem[]
    total: number
    currency: string
}

export default function CheckoutPage() {
    const { token } = useAuth()
    const router = useRouter()
    const params = useParams()
    const locale = normalizeLocale(params.locale as string)
    const [cart, setCart] = useState<Cart>({ items: [], total: 0, currency: "FCFA" })
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

    const checkout = async () => {
        if (!token) return
        setStatus("Création de la transaction...")
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
            setStatus("Paiement créé. Vous pouvez suivre son statut dans Factures.")
            window.setTimeout(() => router.push(`/${locale}/dashboard/account/invoices`), 900)
        } else {
            const text = await res.text()
            setStatus(`Erreur checkout: ${text.slice(0, 180)}`)
        }
    }

    return (
        <div className="apple-page">
            <div>
                <h1 className="apple-page-title">Checkout</h1>
                <p className="apple-page-description">Choisissez le mode de paiement. Les paiements plateforme vont vers Thunderfam Group; les paiements scolaires vont vers le compte de l&apos;établissement.</p>
            </div>
            <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
                <section className="rounded-[28px] border border-[#E5E7EB] bg-white p-6 dark:border-[#3b4248] dark:bg-[#202528]">
                    <h2 className="text-xl font-semibold">Articles</h2>
                    <div className="mt-4 space-y-3">
                        {cart.items.map((item) => (
                            <div key={item.id} className="flex items-center justify-between rounded-2xl bg-[#F6F7F9] p-4 dark:bg-[#2a3035]">
                                <div><p className="font-semibold">{item.title}</p><p className="text-sm text-[#6B7280]">Quantité {item.quantity}</p></div>
                                <p className="font-semibold">{item.line_total.toLocaleString()} {item.currency}</p>
                            </div>
                        ))}
                        {!cart.items.length && <p className="rounded-2xl bg-[#F6F7F9] p-6 text-center text-[#6B7280] dark:bg-[#2a3035]">Votre panier est vide.</p>}
                    </div>
                </section>
                <aside className="rounded-[28px] border border-[#E5E7EB] bg-white p-6 dark:border-[#3b4248] dark:bg-[#202528]">
                    <h2 className="text-xl font-semibold">Paiement</h2>
                    <div className="mt-4 grid gap-3">
                        <button type="button" onClick={() => setProvider("stripe")} className={`flex items-center gap-3 rounded-2xl border p-4 text-left ${provider === "stripe" ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : ""}`}><CreditCard className="h-5 w-5" />Stripe - carte bancaire</button>
                        <button type="button" onClick={() => setProvider("djamo")} className={`flex items-center gap-3 rounded-2xl border p-4 text-left ${provider === "djamo" ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : ""}`}><CreditCard className="h-5 w-5" />Djamo - carte bancaire</button>
                        <button type="button" onClick={() => setProvider("cinetpay")} className={`flex items-center gap-3 rounded-2xl border p-4 text-left ${provider === "cinetpay" ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : ""}`}><Smartphone className="h-5 w-5" />CinetPay Mobile Money</button>
                    </div>
                    {provider === "cinetpay" && (
                        <select className="apple-select mt-4" value={network} onChange={event => setNetwork(event.target.value)}>
                            <option value="orange_money">Orange Money</option>
                            <option value="wave">Wave</option>
                            <option value="mtn_money">MTN Money</option>
                            <option value="moov_money">Moov Money</option>
                        </select>
                    )}
                    <div className="mt-6 flex items-center justify-between border-t border-[#E5E7EB] pt-4 dark:border-[#3b4248]"><span>Total</span><strong>{cart.total.toLocaleString()} {cart.currency}</strong></div>
                    <button type="button" disabled={!cart.items.length} onClick={checkout} className="mt-4 w-full rounded-full bg-black px-4 py-3 font-semibold text-white disabled:opacity-50 dark:bg-white dark:text-black">Payer maintenant</button>
                    {status && <p className="mt-3 text-sm text-[#6B7280]">{status}</p>}
                </aside>
            </div>
        </div>
    )
}
