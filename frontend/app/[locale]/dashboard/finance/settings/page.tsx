"use client"

import { useCallback, useEffect, useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface FeeSchedule {
    id: number
    name: string
    amount: number
    category_order: number
    is_required: boolean
    is_current: boolean
    level: string | null
    class_id: number | null
}

export default function FeeSettingsPage() {
    const { token } = useAuth()
    const [rows, setRows] = useState<FeeSchedule[]>([])
    const [form, setForm] = useState({ name: "", amount: "", category_order: "0", is_required: true, level: "", class_id: "", academic_year_id: "" })
    const [copy, setCopy] = useState({ source: "", target: "" })
    const [message, setMessage] = useState<string | null>(null)

    const loadRows = useCallback(async () => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/finance/fee-schedules`, { headers: { Authorization: `Bearer ${token}` } })
        if (res.ok) setRows(await res.json())
    }, [token])

    const save = async () => {
        if (!token || !form.name || !form.amount) return
        const res = await fetch(`${API_BASE_URL}/finance/fee-schedules`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                name: form.name,
                amount: Number(form.amount),
                category_order: Number(form.category_order || 0),
                is_required: form.is_required,
                level: form.level || null,
                class_id: form.class_id ? Number(form.class_id) : null,
                academic_year_id: form.academic_year_id ? Number(form.academic_year_id) : null
            })
        })
        if (res.ok) {
            setForm({ name: "", amount: "", category_order: "0", is_required: true, level: "", class_id: "", academic_year_id: "" })
            void loadRows()
        }
    }

    const copyYear = async () => {
        if (!token || !copy.source || !copy.target) return
        const res = await fetch(`${API_BASE_URL}/finance/fee-schedules/copy-year?source_academic_year_id=${copy.source}&target_academic_year_id=${copy.target}`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` }
        })
        setMessage(res.ok ? "Previous year amounts copied where missing." : "Copy failed.")
        if (res.ok) void loadRows()
    }

    useEffect(() => { void loadRows() }, [loadRows])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">Fee Settings</h1>
                <p className="text-sm text-[#6B7280] mt-1">Configure fee rubrics by order, amount, year, level and class.</p>
            </div>

            <Card><CardHeader><CardTitle>Add Fee Rubric</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-4">
                <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input type="number" placeholder="Amount" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input type="number" placeholder="Order" value={form.category_order} onChange={(e) => setForm({ ...form, category_order: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input placeholder="Level" value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input type="number" placeholder="Class ID" value={form.class_id} onChange={(e) => setForm({ ...form, class_id: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input type="number" placeholder="Academic Year ID" value={form.academic_year_id} onChange={(e) => setForm({ ...form, academic_year_id: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_required} onChange={(e) => setForm({ ...form, is_required: e.target.checked })} /> Required</label>
                <Button onClick={save}>Save</Button>
            </CardContent></Card>

            <Card><CardHeader><CardTitle>Copy Previous Year</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-4">
                <input type="number" placeholder="Source year ID" value={copy.source} onChange={(e) => setCopy({ ...copy, source: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <input type="number" placeholder="Target year ID" value={copy.target} onChange={(e) => setCopy({ ...copy, target: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                <Button onClick={copyYear}>Copy Amounts</Button>
                {message && <p className="text-sm text-[#6B7280] self-center">{message}</p>}
            </CardContent></Card>

            <Card><CardHeader><CardTitle>Configured Rubrics</CardTitle></CardHeader><CardContent>
                <table className="w-full text-sm"><thead><tr className="border-b"><th className="py-2 text-left">Order</th><th className="py-2 text-left">Name</th><th className="py-2 text-left">Level</th><th className="py-2 text-right">Amount</th><th className="py-2 text-left">Type</th></tr></thead>
                    <tbody>{rows.map(row => <tr key={row.id} className="border-b last:border-0"><td className="py-2">{row.category_order}</td><td className="py-2">{row.name}</td><td className="py-2">{row.level || "-"}</td><td className="py-2 text-right">{row.amount.toLocaleString()} FCFA</td><td className="py-2">{row.is_required ? "Required" : "Optional"}</td></tr>)}</tbody>
                </table>
            </CardContent></Card>
        </div>
    )
}
