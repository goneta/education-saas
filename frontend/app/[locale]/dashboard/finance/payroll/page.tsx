"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { Plus, Wallet, Eye, CheckCircle2, X, Trash2, Printer } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface SalaryProfile {
    id: number; user_id: number; full_name?: string | null; email?: string | null
    employee_type: string; pay_type: string; base_rate: number; currency: string
    cotisation_rate: number; tax_rate: number; is_active: boolean
}
interface PayslipLine { type: string; label: string; amount: number; is_taxable: boolean }
interface Payslip {
    id: number; staff_user_id: number; full_name?: string | null; period: string; period_type?: string | null
    pay_type?: string | null; currency?: string | null; base_amount?: number | null
    allowances_total?: number | null; bonus_total?: number | null; overtime_total?: number | null
    advances_total?: number | null; other_deductions_total?: number | null; gross_amount: number
    social_contributions?: number | null; tax_amount?: number | null; deductions: number; net_amount: number
    status: string; payment_method?: string | null; payment_reference?: string | null; lines: PayslipLine[]
}
interface Employee { user_id: number; full_name: string }

const EMPLOYEE_TYPES = ["permanent", "contract", "vacataire", "consultant"]
const PAY_TYPES = ["hourly", "daily", "weekly", "monthly"]
const LINE_TYPES = ["allowance", "bonus", "overtime", "deduction", "advance"]
const PAYMENT_METHODS = ["bank_transfer", "cash", "stripe", "cinetpay", "djamo"]

export default function PayrollPage() {
    const t = useTranslations("payroll")
    const { token } = useAuth()
    const [tab, setTab] = useState<"profiles" | "payslips">("payslips")
    const [profiles, setProfiles] = useState<SalaryProfile[]>([])
    const [payslips, setPayslips] = useState<Payslip[]>([])
    const [employees, setEmployees] = useState<Employee[]>([])
    const [error, setError] = useState<string | null>(null)
    const [profileForm, setProfileForm] = useState({ user_id: "", employee_type: "permanent", pay_type: "monthly", base_rate: "", currency: "XOF", cotisation_rate: "", tax_rate: "" })
    const [genOpen, setGenOpen] = useState(false)
    const [gen, setGen] = useState<{ staff_user_id: string; period: string; period_type: string; units: string; lines: PayslipLine[] }>({ staff_user_id: "", period: "", period_type: "monthly", units: "1", lines: [] })
    const [detail, setDetail] = useState<Payslip | null>(null)
    const [payFor, setPayFor] = useState<Payslip | null>(null)
    const [payForm, setPayForm] = useState({ payment_method: "bank_transfer", payment_reference: "" })

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const [pr, ps, staff, teachers] = await Promise.all([
            fetch(`${API_BASE_URL}/finance/payroll/salary-profiles`, { headers }),
            fetch(`${API_BASE_URL}/finance/payroll/payslips`, { headers }),
            fetch(`${API_BASE_URL}/personnel`, { headers }),
            fetch(`${API_BASE_URL}/teachers`, { headers }),
        ])
        if (pr.ok) setProfiles(await pr.json())
        if (ps.ok) setPayslips(await ps.json())
        const emp: Employee[] = []
        if (staff.ok) (await staff.json()).forEach((s: { user_id: number; full_name?: string }) => emp.push({ user_id: s.user_id, full_name: s.full_name || `#${s.user_id}` }))
        if (teachers.ok) {
            const rows = await teachers.json()
            ;(Array.isArray(rows) ? rows : []).forEach((tch: { id: number; full_name?: string }) => { if (!emp.some(e => e.user_id === tch.id)) emp.push({ user_id: tch.id, full_name: tch.full_name || `#${tch.id}` }) })
        }
        setEmployees(emp)
    }, [headers])

    useEffect(() => { void load() }, [load])

    const money = (v?: number | null, cur?: string | null) => `${(v ?? 0).toLocaleString()} ${cur || "XOF"}`
    const employeeName = (id: number) => employees.find(e => e.user_id === id)?.full_name || `#${id}`

    const createProfile = async () => {
        if (!headers || !profileForm.user_id || !profileForm.base_rate) return
        setError(null)
        const res = await fetch(`${API_BASE_URL}/finance/payroll/salary-profiles`, {
            method: "POST", headers,
            body: JSON.stringify({
                user_id: Number(profileForm.user_id), employee_type: profileForm.employee_type, pay_type: profileForm.pay_type,
                base_rate: Number(profileForm.base_rate), currency: profileForm.currency,
                cotisation_rate: (Number(profileForm.cotisation_rate) || 0) / 100, tax_rate: (Number(profileForm.tax_rate) || 0) / 100,
            }),
        })
        if (res.ok) { setProfileForm({ user_id: "", employee_type: "permanent", pay_type: "monthly", base_rate: "", currency: "XOF", cotisation_rate: "", tax_rate: "" }); void load() }
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const addGenLine = () => setGen(g => ({ ...g, lines: [...g.lines, { type: "allowance", label: "", amount: 0, is_taxable: true }] }))
    const updateGenLine = (i: number, patch: Partial<PayslipLine>) => setGen(g => ({ ...g, lines: g.lines.map((l, idx) => idx === i ? { ...l, ...patch } : l) }))
    const removeGenLine = (i: number) => setGen(g => ({ ...g, lines: g.lines.filter((_, idx) => idx !== i) }))

    const generate = async () => {
        if (!headers || !gen.staff_user_id || !gen.period.trim()) return
        setError(null)
        const res = await fetch(`${API_BASE_URL}/finance/payroll/payslips/generate`, {
            method: "POST", headers,
            body: JSON.stringify({
                staff_user_id: Number(gen.staff_user_id), period: gen.period.trim(), period_type: gen.period_type,
                units: Number(gen.units) || 1, lines: gen.lines.filter(l => l.label.trim()),
            }),
        })
        if (res.ok) { setGenOpen(false); setGen({ staff_user_id: "", period: "", period_type: "monthly", units: "1", lines: [] }); void load() }
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const approve = async (p: Payslip) => {
        if (!headers) return
        if ((await fetch(`${API_BASE_URL}/finance/payroll/payslips/${p.id}/approve`, { method: "POST", headers })).ok) void load()
    }
    const confirmPay = async () => {
        if (!headers || !payFor) return
        const res = await fetch(`${API_BASE_URL}/finance/payroll/payslips/${payFor.id}/pay`, { method: "POST", headers, body: JSON.stringify(payForm) })
        if (res.ok) { setPayFor(null); setPayForm({ payment_method: "bank_transfer", payment_reference: "" }); void load() }
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const columns = useMemo<FilterColumn<Payslip>[]>(() => [
        { key: "employee", label: t("employee"), accessor: p => p.full_name || employeeName(p.staff_user_id) },
        { key: "period", label: t("period"), accessor: p => p.period },
        { key: "status", label: t("status"), accessor: p => t(p.status as "draft") },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- labels stable; names from employees
    ], [employees])
    const filter = useTableFilter(payslips, columns, { storageKey: "payroll-payslips" })

    const statusBadge = (s: string) => <span className={`rounded-full px-2 py-0.5 text-xs ${s === "paid" ? "bg-green-100 text-green-800" : s === "approved" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-700"}`}>{t(s as "draft")}</span>

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <div className="flex gap-2">
                {(["payslips", "profiles"] as const).map(k => (
                    <button key={k} onClick={() => setTab(k)} className={`rounded-full px-4 py-1.5 text-sm font-medium ${tab === k ? "bg-black text-white dark:bg-white dark:text-black" : "border border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"}`}>{k === "payslips" ? t("tabPayslips") : t("tabProfiles")}</button>
                ))}
            </div>

            {tab === "profiles" && (
                <>
                    <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                        <CardHeader><CardTitle>{t("addProfile")}</CardTitle></CardHeader>
                        <CardContent className="grid gap-3 md:grid-cols-4">
                            <select value={profileForm.user_id} onChange={e => setProfileForm({ ...profileForm, user_id: e.target.value })} className="apple-select"><option value="">{t("selectEmployee")}</option>{employees.map(e => <option key={e.user_id} value={e.user_id}>{e.full_name}</option>)}</select>
                            <select value={profileForm.employee_type} onChange={e => setProfileForm({ ...profileForm, employee_type: e.target.value })} className="apple-select">{EMPLOYEE_TYPES.map(x => <option key={x} value={x}>{t(x as "permanent")}</option>)}</select>
                            <select value={profileForm.pay_type} onChange={e => setProfileForm({ ...profileForm, pay_type: e.target.value })} className="apple-select">{PAY_TYPES.map(x => <option key={x} value={x}>{t(x as "monthly")}</option>)}</select>
                            <input type="number" value={profileForm.base_rate} onChange={e => setProfileForm({ ...profileForm, base_rate: e.target.value })} placeholder={t("baseRate")} className="apple-input" />
                            <input value={profileForm.currency} onChange={e => setProfileForm({ ...profileForm, currency: e.target.value })} placeholder={t("currency")} className="apple-input" />
                            <input type="number" value={profileForm.cotisation_rate} onChange={e => setProfileForm({ ...profileForm, cotisation_rate: e.target.value })} placeholder={t("cotisationRate")} className="apple-input" />
                            <input type="number" value={profileForm.tax_rate} onChange={e => setProfileForm({ ...profileForm, tax_rate: e.target.value })} placeholder={t("taxRate")} className="apple-input" />
                            <Button onClick={createProfile} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> {t("save")}</Button>
                        </CardContent>
                    </Card>

                    <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                        <CardHeader><CardTitle>{t("profilesList")} ({profiles.length})</CardTitle></CardHeader>
                        <CardContent className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("employee")}</th><th className="px-3 py-2">{t("employeeType")}</th><th className="px-3 py-2">{t("payType")}</th><th className="px-3 py-2">{t("baseRate")}</th><th className="px-3 py-2">{t("cotisationRate")}</th><th className="px-3 py-2">{t("taxRate")}</th></tr></thead>
                                <tbody>
                                    {profiles.length === 0 ? <tr><td colSpan={6} className="px-3 py-6 text-center text-[#6B7280]">{t("noProfiles")}</td></tr> : profiles.map(p => (
                                        <tr key={p.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                            <td className="px-3 py-2 font-medium">{p.full_name}</td>
                                            <td className="px-3 py-2">{t(p.employee_type as "permanent")}</td>
                                            <td className="px-3 py-2">{t(p.pay_type as "monthly")}</td>
                                            <td className="px-3 py-2">{money(p.base_rate, p.currency)}</td>
                                            <td className="px-3 py-2">{Math.round((p.cotisation_rate || 0) * 100)}%</td>
                                            <td className="px-3 py-2">{Math.round((p.tax_rate || 0) * 100)}%</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </CardContent>
                    </Card>
                </>
            )}

            {tab === "payslips" && (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader className="flex flex-row items-center justify-between gap-3">
                        <CardTitle>{t("payslipsList")} ({filter.filtered.length})</CardTitle>
                        <Button onClick={() => setGenOpen(true)} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> {t("generate")}</Button>
                    </CardHeader>
                    <CardContent className="overflow-x-auto">
                        <div className="mb-3"><TableFilter {...filter.controls} /></div>
                        <table className="w-full text-left text-sm">
                            <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("employee")}</th><th className="px-3 py-2">{t("period")}</th><th className="px-3 py-2">{t("gross")}</th><th className="px-3 py-2">{t("net")}</th><th className="px-3 py-2">{t("status")}</th><th className="px-3 py-2 text-right">{t("actions")}</th></tr></thead>
                            <tbody>
                                {filter.filtered.length === 0 ? <tr><td colSpan={6} className="px-3 py-6 text-center text-[#6B7280]">{t("noPayslips")}</td></tr> : filter.filtered.map(p => (
                                    <tr key={p.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                        <td className="px-3 py-2 font-medium">{p.full_name || employeeName(p.staff_user_id)}</td>
                                        <td className="px-3 py-2">{p.period}</td>
                                        <td className="px-3 py-2">{money(p.gross_amount, p.currency)}</td>
                                        <td className="px-3 py-2 font-medium">{money(p.net_amount, p.currency)}</td>
                                        <td className="px-3 py-2">{statusBadge(p.status)}</td>
                                        <td className="px-3 py-2 text-right">
                                            <div className="flex justify-end gap-1">
                                                <Button variant="ghost" size="sm" onClick={() => setDetail(p)} title={t("view")}><Eye className="h-4 w-4" /></Button>
                                                {p.status === "draft" && <Button variant="ghost" size="sm" onClick={() => approve(p)} title={t("approve")}><CheckCircle2 className="h-4 w-4 text-blue-600" /></Button>}
                                                {p.status !== "paid" && <Button variant="ghost" size="sm" onClick={() => setPayFor(p)} title={t("pay")}><Wallet className="h-4 w-4 text-green-600" /></Button>}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </CardContent>
                </Card>
            )}

            {genOpen && (
                <div className="fixed inset-0 z-[1300] flex items-center justify-center bg-black/40 p-4" onClick={() => setGenOpen(false)}>
                    <div className="w-full max-w-2xl rounded-[20px] bg-white p-5 shadow-xl dark:bg-[#202528] max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                        <div className="mb-3 flex items-center justify-between"><h3 className="font-semibold text-[#111827] dark:text-white">{t("generate")}</h3><button onClick={() => setGenOpen(false)} aria-label={t("close")}><X className="h-4 w-4" /></button></div>
                        <div className="grid gap-3 md:grid-cols-2">
                            <select value={gen.staff_user_id} onChange={e => setGen({ ...gen, staff_user_id: e.target.value })} className="apple-select"><option value="">{t("selectEmployee")}</option>{profiles.map(p => <option key={p.user_id} value={p.user_id}>{p.full_name}</option>)}</select>
                            <select value={gen.period_type} onChange={e => setGen({ ...gen, period_type: e.target.value })} className="apple-select"><option value="monthly">{t("monthly")}</option><option value="weekly">{t("weekly")}</option></select>
                            <input value={gen.period} onChange={e => setGen({ ...gen, period: e.target.value })} placeholder={gen.period_type === "weekly" ? "2026-W23" : "2026-06"} className="apple-input" />
                            <input type="number" value={gen.units} onChange={e => setGen({ ...gen, units: e.target.value })} placeholder={t("units")} className="apple-input" />
                        </div>
                        <div className="mt-4">
                            <div className="mb-2 flex items-center justify-between"><p className="text-sm font-medium">{t("lines")}</p><Button variant="outline" size="sm" onClick={addGenLine}><Plus className="mr-1 h-3 w-3" /> {t("addLine")}</Button></div>
                            <div className="space-y-2">
                                {gen.lines.map((l, i) => (
                                    <div key={i} className="grid grid-cols-12 gap-2">
                                        <select value={l.type} onChange={e => updateGenLine(i, { type: e.target.value })} className="apple-select col-span-4">{LINE_TYPES.map(x => <option key={x} value={x}>{t(x as "allowance")}</option>)}</select>
                                        <input value={l.label} onChange={e => updateGenLine(i, { label: e.target.value })} placeholder={t("lineLabel")} className="apple-input col-span-4" />
                                        <input type="number" value={l.amount} onChange={e => updateGenLine(i, { amount: Number(e.target.value) })} placeholder={t("lineAmount")} className="apple-input col-span-3" />
                                        <button onClick={() => removeGenLine(i)} className="col-span-1 text-red-600" aria-label="remove"><Trash2 className="h-4 w-4" /></button>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="mt-4 flex justify-end gap-2">
                            <Button variant="outline" onClick={() => setGenOpen(false)}>{t("close")}</Button>
                            <Button onClick={generate} className="bg-black text-white hover:bg-black/90">{t("generate")}</Button>
                        </div>
                    </div>
                </div>
            )}

            {detail && <PayslipModal payslip={detail} onClose={() => setDetail(null)} t={t} money={money} />}

            {payFor && (
                <div className="fixed inset-0 z-[1300] flex items-center justify-center bg-black/40 p-4" onClick={() => setPayFor(null)}>
                    <div className="w-full max-w-sm rounded-[20px] bg-white p-5 shadow-xl dark:bg-[#202528]" onClick={e => e.stopPropagation()}>
                        <div className="mb-3 flex items-center justify-between"><h3 className="font-semibold">{t("pay")} — {payFor.full_name || employeeName(payFor.staff_user_id)}</h3><button onClick={() => setPayFor(null)} aria-label={t("close")}><X className="h-4 w-4" /></button></div>
                        <div className="space-y-3">
                            <select value={payForm.payment_method} onChange={e => setPayForm({ ...payForm, payment_method: e.target.value })} className="apple-select w-full">{PAYMENT_METHODS.map(m => <option key={m} value={m}>{["bank_transfer", "cash"].includes(m) ? t(m as "cash") : m}</option>)}</select>
                            <input value={payForm.payment_reference} onChange={e => setPayForm({ ...payForm, payment_reference: e.target.value })} placeholder={t("paymentReference")} className="apple-input w-full" />
                            <Button onClick={confirmPay} className="w-full bg-black text-white hover:bg-black/90">{t("confirmPay")} · {money(payFor.net_amount, payFor.currency)}</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export function PayslipModal({ payslip, onClose, t, money }: { payslip: Payslip; onClose: () => void; t: (k: string) => string; money: (v?: number | null, c?: string | null) => string }) {
    const row = (label: string, value: string, strong = false) => (
        <div className={`flex justify-between py-1 ${strong ? "font-semibold" : ""}`}><span className="text-[#6B7280] dark:text-[#c7d0da]">{label}</span><span>{value}</span></div>
    )
    return (
        <div className="fixed inset-0 z-[1300] flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
            <div className="w-full max-w-md rounded-[20px] bg-white p-6 shadow-xl dark:bg-[#202528] max-h-[90vh] overflow-y-auto print:max-h-full print:shadow-none" onClick={e => e.stopPropagation()} id="payslip-print">
                <div className="mb-4 flex items-start justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-[#111827] dark:text-white">{t("payslip")}</h3>
                        <p className="text-sm text-[#6B7280]">{payslip.full_name} · {payslip.period}</p>
                    </div>
                    <button onClick={onClose} aria-label={t("close")} className="print:hidden"><X className="h-4 w-4" /></button>
                </div>
                <div className="text-sm">
                    {row(t("base"), money(payslip.base_amount, payslip.currency))}
                    {(payslip.allowances_total || 0) > 0 && row(t("allowance"), money(payslip.allowances_total, payslip.currency))}
                    {(payslip.bonus_total || 0) > 0 && row(t("bonus"), money(payslip.bonus_total, payslip.currency))}
                    {(payslip.overtime_total || 0) > 0 && row(t("overtime"), money(payslip.overtime_total, payslip.currency))}
                    {row(t("gross"), money(payslip.gross_amount, payslip.currency), true)}
                    {(payslip.social_contributions || 0) > 0 && row(t("contributions"), `- ${money(payslip.social_contributions, payslip.currency)}`)}
                    {(payslip.tax_amount || 0) > 0 && row(t("tax"), `- ${money(payslip.tax_amount, payslip.currency)}`)}
                    {(payslip.other_deductions_total || 0) > 0 && row(t("deduction"), `- ${money(payslip.other_deductions_total, payslip.currency)}`)}
                    {(payslip.advances_total || 0) > 0 && row(t("advance"), `- ${money(payslip.advances_total, payslip.currency)}`)}
                    <div className="my-2 border-t border-[#E5E7EB] dark:border-[#3b4248]" />
                    {row(t("net"), money(payslip.net_amount, payslip.currency), true)}
                </div>
                <div className="mt-5 flex justify-end gap-2 print:hidden">
                    <Button variant="outline" onClick={() => window.print()}><Printer className="mr-2 h-4 w-4" /> {t("print")}</Button>
                    <Button onClick={onClose}>{t("close")}</Button>
                </div>
            </div>
        </div>
    )
}
