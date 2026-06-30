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

interface ForecastRow {
    id: number
    expected_students: number
    expected_revenue: number
    fee_category: string | null
    level: string | null
    class_id: number | null
}

interface Variance {
    expected_revenue: number
    actual_revenue: number
    difference: number
}

export default function ForecastsPage() {
    const { token } = useAuth()
    const params = useParams<{ locale: string }>()
    const locale = normalizeLocale(params?.locale)
    const [rows, setRows] = useState<ForecastRow[]>([])
    const [variance, setVariance] = useState<Variance | null>(null)
    const [form, setForm] = useState({ expected_students: "", expected_revenue: "", fee_category: "", level: "", class_id: "", academic_year_id: "" })

    const load = useCallback(async () => {
        if (!token) return
        const [rowsRes, varianceRes] = await Promise.all([
            fetch(`${API_BASE_URL}/finance/forecasts`, { headers: { Authorization: `Bearer ${token}` } }),
            fetch(`${API_BASE_URL}/finance/forecast-vs-actual`, { headers: { Authorization: `Bearer ${token}` } })
        ])
        if (rowsRes.ok) setRows(await rowsRes.json())
        if (varianceRes.ok) setVariance(await varianceRes.json())
    }, [token])

    const save = async () => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/finance/forecasts`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                expected_students: Number(form.expected_students || 0),
                expected_revenue: Number(form.expected_revenue || 0),
                fee_category: form.fee_category || null,
                level: form.level || null,
                class_id: form.class_id ? Number(form.class_id) : null,
                academic_year_id: form.academic_year_id ? Number(form.academic_year_id) : null
            })
        })
        if (res.ok) {
            setForm({ expected_students: "", expected_revenue: "", fee_category: "", level: "", class_id: "", academic_year_id: "" })
            void load()
        }
    }

    useEffect(() => { void load() }, [load])

    return (
        <div className="space-y-6">
            <div><h1 className="apple-page-title">{tx(locale, "forecasts")}</h1><p className="apple-page-description">{tx(locale, "forecastsDescription")}</p></div>
            <div className="grid gap-4 md:grid-cols-3">
                <Metric title={tx(locale, "expected")} value={variance?.expected_revenue || 0} />
                <Metric title={tx(locale, "actual")} value={variance?.actual_revenue || 0} tone="green" />
                <Metric title={tx(locale, "variance")} value={variance?.difference || 0} tone={(variance?.difference || 0) >= 0 ? "green" : "red"} />
            </div>
            <Card><CardHeader><CardTitle>{tx(locale, "addForecast")}</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-4">
                <ExplainedField label={tx(locale, "expectedStudents")} help={tx(locale, "helpExpectedStudents")}><input type="number" placeholder={tx(locale, "expectedStudents")} value={form.expected_students} onChange={(e) => setForm({ ...form, expected_students: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "expectedRevenue")} help={tx(locale, "helpExpectedRevenue")}><input type="number" placeholder={tx(locale, "expectedRevenue")} value={form.expected_revenue} onChange={(e) => setForm({ ...form, expected_revenue: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "feeCategory")} help={tx(locale, "helpFeeCategory")}><input placeholder={tx(locale, "feeCategory")} value={form.fee_category} onChange={(e) => setForm({ ...form, fee_category: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "level")} help={tx(locale, "helpLevel")}><input placeholder={tx(locale, "level")} value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "classId")} help={tx(locale, "helpClassId")}><input type="number" placeholder={tx(locale, "classId")} value={form.class_id} onChange={(e) => setForm({ ...form, class_id: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "academicYearId")} help={tx(locale, "helpAcademicYearId")}><input type="number" placeholder={tx(locale, "academicYearId")} value={form.academic_year_id} onChange={(e) => setForm({ ...form, academic_year_id: e.target.value })} className="apple-input" /></ExplainedField>
                <Button onClick={save}>{tx(locale, "save")}</Button>
            </CardContent></Card>
            <Card><CardHeader><CardTitle>{tx(locale, "forecastRows")}</CardTitle></CardHeader><CardContent><table className="apple-table"><thead><tr><th>{tx(locale, "category")}</th><th>{tx(locale, "level")}</th><th className="text-right">{tx(locale, "students")}</th><th className="text-right">{tx(locale, "revenue")}</th></tr></thead><tbody>{rows.map(row => <tr key={row.id}><td>{row.fee_category || tx(locale, "global")}</td><td>{row.level || "-"}</td><td className="text-right">{row.expected_students}</td><td className="text-right">{row.expected_revenue.toLocaleString()} FCFA</td></tr>)}</tbody></table></CardContent></Card>
        </div>
    )
}

function Metric({ title, value, tone }: { title: string; value: number; tone?: "green" | "red" }) {
    return <Card><CardContent className="pt-6"><p className="text-sm text-[#6B7280]">{title}</p><p className={`text-2xl font-bold ${tone === "green" ? "text-green-700" : tone === "red" ? "text-red-700" : "text-[#111827]"}`}>{value.toLocaleString()} FCFA</p></CardContent></Card>
}
