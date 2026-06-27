"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ExplainedField } from "@/components/ui/explained-field"
import { normalizeLocale } from "@/lib/i18n"
import { tx } from "@/lib/product-copy"

interface FinanceReport {
    total_expected: number
    total_paid: number
    total_remaining: number
    payments_by_class: Record<string, number>
    payments_by_category: Record<string, number>
    debtors: Array<{ student_name: string; registration_number: string; class_name: string; fee_title: string; paid: number; remaining: number }>
}

export default function FinanceReportsPage() {
    const { token } = useAuth()
    const params = useParams<{ locale: string }>()
    const locale = normalizeLocale(params?.locale)
    const [report, setReport] = useState<FinanceReport | null>(null)
    const [filters, setFilters] = useState({ start_date: "", end_date: "", fee_category: "", operator_id: "" })

    const loadReport = async () => {
        if (!token) return
        const qs = new URLSearchParams()
        Object.entries(filters).forEach(([key, value]) => value && qs.set(key, value))
        const res = await fetch(`${API_BASE_URL}/finance/reports?${qs.toString()}`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) setReport(await res.json())
    }

    useEffect(() => {
        loadReport()
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token])

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="apple-page-title">{tx(locale, "financeReports")}</h1>
                    <p className="apple-page-description">{tx(locale, "financeReportsDescription")}</p>
                </div>
                <Button variant="outline" onClick={() => window.print()}>{tx(locale, "print")}</Button>
            </div>

            <div className="grid gap-3 md:grid-cols-5">
                <ExplainedField label="Date début" help="Début de la période de rapport. Les paiements hors période sont exclus."><input type="date" value={filters.start_date} onChange={(e) => setFilters({ ...filters, start_date: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label="Date fin" help="Fin de la période de rapport. Utilisée pour calculer encaissé, dû et restant."><input type="date" value={filters.end_date} onChange={(e) => setFilters({ ...filters, end_date: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "feeCategory")} help="Filtre optionnel par rubrique: inscription, scolarité, assurance, annexe, etc."><input placeholder={tx(locale, "feeCategory")} value={filters.fee_category} onChange={(e) => setFilters({ ...filters, fee_category: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "operatorId")} help="Filtre optionnel pour auditer les opérations enregistrées par un caissier ou opérateur."><input placeholder={tx(locale, "operatorId")} value={filters.operator_id} onChange={(e) => setFilters({ ...filters, operator_id: e.target.value })} className="apple-input" /></ExplainedField>
                <Button onClick={loadReport}>{tx(locale, "apply")}</Button>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
                <Metric title={tx(locale, "expected")} value={report?.total_expected || 0} />
                <Metric title={tx(locale, "collected")} value={report?.total_paid || 0} tone="green" />
                <Metric title={tx(locale, "remaining")} value={report?.total_remaining || 0} tone="red" />
            </div>

            <div className="grid gap-4">
                <Breakdown title={tx(locale, "byClass")} rows={report?.payments_by_class || {}} />
                <Breakdown title={tx(locale, "byFeeType")} rows={report?.payments_by_category || {}} />
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader><CardTitle>{tx(locale, "debtors")}</CardTitle></CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead><tr className="border-b"><th className="py-2 text-left">{tx(locale, "student")}</th><th className="py-2 text-left">{tx(locale, "class")}</th><th className="py-2 text-left">{tx(locale, "fee")}</th><th className="py-2 text-right">{tx(locale, "paid")}</th><th className="py-2 text-right">{tx(locale, "remaining")}</th></tr></thead>
                            <tbody>
                                {(report?.debtors || []).map((row, idx) => (
                                    <tr key={idx} className="border-b last:border-0">
                                        <td className="py-2">{row.student_name} <span className="text-[#6B7280]">({row.registration_number})</span></td>
                                        <td className="py-2">{row.class_name}</td>
                                        <td className="py-2">{row.fee_title}</td>
                                        <td className="py-2 text-right">{row.paid.toLocaleString()} FCFA</td>
                                        <td className="py-2 text-right text-red-700">{row.remaining.toLocaleString()} FCFA</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

function Metric({ title, value, tone }: { title: string; value: number; tone?: "green" | "red" }) {
    return <Card><CardContent className="pt-6"><p className="text-sm text-[#6B7280]">{title}</p><p className={`text-2xl font-bold ${tone === "green" ? "text-green-700" : tone === "red" ? "text-red-700" : "text-[#111827]"}`}>{value.toLocaleString()} FCFA</p></CardContent></Card>
}

function Breakdown({ title, rows }: { title: string; rows: Record<string, number> }) {
    return <Card><CardHeader><CardTitle>{title}</CardTitle></CardHeader><CardContent className="space-y-2">{Object.entries(rows).map(([key, value]) => <div key={key} className="flex justify-between border-b py-2 text-sm"><span>{key}</span><span className="font-medium">{value.toLocaleString()} FCFA</span></div>)}</CardContent></Card>
}
