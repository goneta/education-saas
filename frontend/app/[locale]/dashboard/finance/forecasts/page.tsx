"use client"

import { useCallback, useEffect, useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

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
            <div><h1 className="text-2xl font-bold text-[#111827]">Forecasts</h1><p className="text-sm text-[#6B7280] mt-1">Expected enrollment and revenue versus actual collections.</p></div>
            <div className="grid gap-4 md:grid-cols-3">
                <Metric title="Expected" value={variance?.expected_revenue || 0} />
                <Metric title="Actual" value={variance?.actual_revenue || 0} tone="green" />
                <Metric title="Variance" value={variance?.difference || 0} tone={(variance?.difference || 0) >= 0 ? "green" : "red"} />
            </div>
            <Card><CardHeader><CardTitle>Add Forecast</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-4">
                <input type="number" placeholder="Expected students" value={form.expected_students} onChange={(e) => setForm({ ...form, expected_students: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input type="number" placeholder="Expected revenue" value={form.expected_revenue} onChange={(e) => setForm({ ...form, expected_revenue: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input placeholder="Fee category" value={form.fee_category} onChange={(e) => setForm({ ...form, fee_category: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input placeholder="Level" value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input type="number" placeholder="Class ID" value={form.class_id} onChange={(e) => setForm({ ...form, class_id: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input type="number" placeholder="Academic Year ID" value={form.academic_year_id} onChange={(e) => setForm({ ...form, academic_year_id: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <Button onClick={save}>Save</Button>
            </CardContent></Card>
            <Card><CardHeader><CardTitle>Forecast Rows</CardTitle></CardHeader><CardContent><table className="w-full text-sm"><thead><tr className="border-b"><th className="py-2 text-left">Category</th><th className="py-2 text-left">Level</th><th className="py-2 text-right">Students</th><th className="py-2 text-right">Revenue</th></tr></thead><tbody>{rows.map(row => <tr key={row.id} className="border-b last:border-0"><td className="py-2">{row.fee_category || "Global"}</td><td className="py-2">{row.level || "-"}</td><td className="py-2 text-right">{row.expected_students}</td><td className="py-2 text-right">{row.expected_revenue.toLocaleString()} FCFA</td></tr>)}</tbody></table></CardContent></Card>
        </div>
    )
}

function Metric({ title, value, tone }: { title: string; value: number; tone?: "green" | "red" }) {
    return <Card><CardContent className="pt-6"><p className="text-sm text-[#6B7280]">{title}</p><p className={`text-2xl font-bold ${tone === "green" ? "text-green-700" : tone === "red" ? "text-red-700" : "text-[#111827]"}`}>{value.toLocaleString()} FCFA</p></CardContent></Card>
}
