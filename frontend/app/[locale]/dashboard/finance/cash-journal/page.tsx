"use client"

import { useCallback, useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ExplainedField } from "@/components/ui/explained-field"
import { normalizeLocale } from "@/lib/i18n"
import { tx } from "@/lib/product-copy"

interface Journal {
    total: number
    by_category: Record<string, number>
    by_operator: Record<string, number>
    payments: Array<{ id: number; payment_date: string; receipt_number: string; student_name: string; fee_title: string; amount: number; recorded_by: string }>
}

export default function CashJournalPage() {
    const { token } = useAuth()
    const params = useParams<{ locale: string }>()
    const locale = normalizeLocale(params?.locale)
    const today = new Date().toISOString().slice(0, 10)
    const [filters, setFilters] = useState({ start_date: today, end_date: today, operator_id: "" })
    const [journal, setJournal] = useState<Journal | null>(null)
    const [counted, setCounted] = useState("")
    const [message, setMessage] = useState<string | null>(null)

    const loadJournal = useCallback(async () => {
        if (!token) return
        const qs = new URLSearchParams()
        Object.entries(filters).forEach(([key, value]) => value && qs.set(key, value))
        const res = await fetch(`${API_BASE_URL}/finance/cash-journal?${qs.toString()}`, { headers: { Authorization: `Bearer ${token}` } })
        if (res.ok) setJournal(await res.json())
    }, [filters, token])

    const closeDay = async () => {
        if (!token || !counted) return
        const res = await fetch(`${API_BASE_URL}/finance/cash-closures`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ closure_date: `${filters.end_date || today}T23:59:00`, counted_amount: Number(counted), notes: "Daily closure" })
        })
        setMessage(res.ok ? "Cash closure submitted for management validation." : "Unable to submit closure.")
    }

    useEffect(() => { void loadJournal() }, [loadJournal])

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="apple-page-title">{tx(locale, "cashJournal")}</h1>
                    <p className="apple-page-description">{tx(locale, "cashJournalDescription")}</p>
                </div>
                <Button variant="outline" onClick={() => window.print()}>{tx(locale, "print")}</Button>
            </div>

            <div className="grid gap-3 md:grid-cols-5">
                <ExplainedField label="Date début" help="Première date de la période du journal de caisse. Format attendu: date locale."><input type="date" value={filters.start_date} onChange={(e) => setFilters({ ...filters, start_date: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label="Date fin" help="Dernière date incluse dans le journal. Utilisée pour totaliser les paiements et préparer la clôture."><input type="date" value={filters.end_date} onChange={(e) => setFilters({ ...filters, end_date: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "operatorId")} help="Filtre optionnel: identifiant de l'utilisateur caisse/opérateur qui a enregistré les paiements."><input placeholder={tx(locale, "operatorId")} value={filters.operator_id} onChange={(e) => setFilters({ ...filters, operator_id: e.target.value })} className="apple-input" /></ExplainedField>
                <Button onClick={loadJournal}>{tx(locale, "refresh")}</Button>
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
                <Card><CardContent className="pt-6"><p className="text-sm text-[#6B7280]">{tx(locale, "journalTotal")}</p><p className="text-2xl font-bold text-green-700">{(journal?.total || 0).toLocaleString()} FCFA</p></CardContent></Card>
                <Card className="lg:col-span-2"><CardContent className="pt-6"><div className="grid gap-3 md:grid-cols-[1fr_auto]"><ExplainedField label="Caisse comptée" help="Montant réellement compté physiquement en fin de journée. Il sert au rapprochement avec le total système."><input type="number" placeholder="Montant compté" value={counted} onChange={(e) => setCounted(e.target.value)} className="apple-input" /></ExplainedField><Button onClick={closeDay}>{tx(locale, "submitClosure")}</Button></div>{message && <p className="mt-2 text-sm text-[#6B7280]">{message}</p>}</CardContent></Card>
            </div>

            <div className="grid gap-4">
                <Breakdown title={tx(locale, "byFeeType")} rows={journal?.by_category || {}} />
                <Breakdown title={tx(locale, "byOperator")} rows={journal?.by_operator || {}} />
            </div>

            <Card>
                <CardHeader><CardTitle>{tx(locale, "payments")}</CardTitle></CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead><tr className="border-b"><th className="py-2 text-left">{tx(locale, "date")}</th><th className="py-2 text-left">{tx(locale, "receipt")}</th><th className="py-2 text-left">{tx(locale, "student")}</th><th className="py-2 text-left">{tx(locale, "fee")}</th><th className="py-2 text-left">Opérateur</th><th className="py-2 text-right">{tx(locale, "amount")}</th></tr></thead>
                            <tbody>{(journal?.payments || []).map(p => <tr key={p.id} className="border-b last:border-0"><td className="py-2">{new Date(p.payment_date).toLocaleString()}</td><td className="py-2">{p.receipt_number}</td><td className="py-2">{p.student_name}</td><td className="py-2">{p.fee_title}</td><td className="py-2">{p.recorded_by}</td><td className="py-2 text-right">{p.amount.toLocaleString()} FCFA</td></tr>)}</tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

function Breakdown({ title, rows }: { title: string; rows: Record<string, number> }) {
    return <Card><CardHeader><CardTitle>{title}</CardTitle></CardHeader><CardContent className="space-y-2">{Object.entries(rows).map(([key, value]) => <div key={key} className="flex justify-between border-b py-2 text-sm"><span>{key}</span><span className="font-medium">{value.toLocaleString()} FCFA</span></div>)}</CardContent></Card>
}
