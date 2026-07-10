"use client"

import { Suspense, useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useParams, useSearchParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { AlertTriangle, CheckCircle2, Clock, RefreshCw, ReceiptText } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { normalizeLocale } from "@/lib/i18n"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

type State = "checking" | "pending" | "successful" | "failed" | "unknown"

function PaymentStatusInner() {
    const t = useTranslations("payStatus")
    const params = useParams()
    const locale = normalizeLocale(String(params?.locale || "fr"))
    const searchParams = useSearchParams()
    const { token } = useAuth()
    // CinetPay appends ?transaction_id=… on return; internal links use ?ref=….
    const initialRef = searchParams.get("transaction_id") || searchParams.get("ref") || ""
    const [reference, setReference] = useState(initialRef)
    const [state, setState] = useState<State>(initialRef ? "checking" : "unknown")
    const [busy, setBusy] = useState(false)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const check = useCallback(async (ref: string) => {
        if (!headers || !ref.trim()) return
        setBusy(true)
        try {
            // Gateway-backed verification: the backend re-checks CinetPay and
            // applies the VERIFIED status idempotently before answering.
            const res = await fetch(`${API_BASE_URL}/payments/${encodeURIComponent(ref.trim())}/refresh`, { method: "POST", headers })
            if (res.status === 503) { setState("unknown"); return }
            if (!res.ok) { setState("failed"); return }
            const d = await res.json()
            setState(d.status === "successful" ? "successful" : d.status === "failed" || d.status === "cancelled" ? "failed" : "pending")
        } catch { setState("unknown") } finally { setBusy(false) }
    }, [headers])

    useEffect(() => { if (initialRef && headers) void check(initialRef) }, [initialRef, headers, check])

    // Poll while pending (mobile-money validation happens on the payer's phone).
    useEffect(() => {
        if (state !== "pending" || !reference) return
        const timer = setInterval(() => { void check(reference) }, 7000)
        return () => clearInterval(timer)
    }, [state, reference, check])

    const visuals: Record<State, { icon: typeof Clock; tone: string; text: string }> = {
        checking: { icon: RefreshCw, tone: "text-[#6B7280]", text: t("checking") },
        pending: { icon: Clock, tone: "text-amber-600", text: t("pending") },
        successful: { icon: CheckCircle2, tone: "text-emerald-600", text: t("successful") },
        failed: { icon: AlertTriangle, tone: "text-red-600", text: t("failed") },
        unknown: { icon: AlertTriangle, tone: "text-[#6B7280]", text: reference ? t("unknown") : t("enterRef") },
    }
    const v = visuals[state]
    const Icon = v.icon

    return (
        <div className="mx-auto max-w-xl space-y-6 py-8">
            <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
            <Card className="rounded-2xl border border-[#E5E7EB] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardContent className="space-y-4 p-8 text-center">
                    <Icon className={`mx-auto h-12 w-12 ${v.tone} ${state === "checking" || busy ? "animate-spin" : ""}`} />
                    <p className="text-sm text-[#374151] dark:text-[#c7d0da]">{v.text}</p>
                    <div className="flex items-center justify-center gap-2">
                        <input className="apple-input w-64" value={reference} placeholder="SCH-…" onChange={e => setReference(e.target.value)} />
                        <Button variant="outline" disabled={busy || !reference.trim()} onClick={() => { setState("checking"); void check(reference) }}>
                            <RefreshCw className="mr-1 h-4 w-4" /> {t("recheck")}
                        </Button>
                    </div>
                    {reference && <p className="font-mono text-xs text-[#94A3B8]">{t("reference")}: {reference}</p>}
                    <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
                        {state === "failed" && (
                            <Link href={`/${locale}/dashboard/checkout`}><Button className="bg-black text-white hover:bg-black/90">{t("retry")}</Button></Link>
                        )}
                        <Link href={`/${locale}/dashboard/my-documents`}><Button variant="outline"><ReceiptText className="mr-1 h-4 w-4" /> {t("receipts")}</Button></Link>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

export default function PaymentStatusPage() {
    return <Suspense fallback={null}><PaymentStatusInner /></Suspense>
}
