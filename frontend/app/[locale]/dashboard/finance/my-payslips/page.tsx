"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { Eye, FileText } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"
import { PayslipModal } from "../payroll/page"

interface PayslipLine { type: string; label: string; amount: number; is_taxable: boolean }
interface Payslip {
    id: number; staff_user_id: number; full_name?: string | null; period: string; currency?: string | null
    base_amount?: number | null; allowances_total?: number | null; bonus_total?: number | null
    overtime_total?: number | null; advances_total?: number | null; other_deductions_total?: number | null
    gross_amount: number; social_contributions?: number | null; tax_amount?: number | null
    deductions: number; net_amount: number; status: string; payment_method?: string | null
    payment_reference?: string | null; lines: PayslipLine[]
}

export default function MyPayslipsPage() {
    const t = useTranslations("payroll")
    const { token } = useAuth()
    const [payslips, setPayslips] = useState<Payslip[]>([])
    const [detail, setDetail] = useState<Payslip | null>(null)

    const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/finance/payroll/payslips/me`, { headers })
        if (res.ok) setPayslips(await res.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const money = (v?: number | null, cur?: string | null) => `${(v ?? 0).toLocaleString()} ${cur || "XOF"}`
    const columns = useMemo<FilterColumn<Payslip>[]>(() => [
        { key: "period", label: t("period"), accessor: p => p.period },
        { key: "status", label: t("status"), accessor: p => t(p.status as "draft") },
    ], [t])
    const filter = useTableFilter(payslips, columns, { storageKey: "my-payslips" })
    const statusBadge = (s: string) => <span className={`rounded-full px-2 py-0.5 text-xs ${s === "paid" ? "bg-green-100 text-green-800" : s === "approved" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-700"}`}>{t(s as "draft")}</span>

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("myTitle")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("mySubtitle")}</p>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle className="flex items-center gap-2"><FileText className="h-4 w-4" /> {t("myTitle")} ({filter.filtered.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <div className="mb-3"><TableFilter {...filter.controls} /></div>
                    <table className="w-full text-left text-sm">
                        <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("period")}</th><th className="px-3 py-2">{t("gross")}</th><th className="px-3 py-2">{t("net")}</th><th className="px-3 py-2">{t("status")}</th><th className="px-3 py-2 text-right">{t("actions")}</th></tr></thead>
                        <tbody>
                            {filter.filtered.length === 0 ? <tr><td colSpan={5} className="px-3 py-6 text-center text-[#6B7280]">{t("noPayslips")}</td></tr> : filter.filtered.map(p => (
                                <tr key={p.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{p.period}</td>
                                    <td className="px-3 py-2">{money(p.gross_amount, p.currency)}</td>
                                    <td className="px-3 py-2 font-medium">{money(p.net_amount, p.currency)}</td>
                                    <td className="px-3 py-2">{statusBadge(p.status)}</td>
                                    <td className="px-3 py-2 text-right"><Button variant="ghost" size="sm" onClick={() => setDetail(p)} title={t("view")}><Eye className="h-4 w-4" /></Button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>

            {detail && <PayslipModal payslip={detail} onClose={() => setDetail(null)} t={t} money={money} />}
        </div>
    )
}
