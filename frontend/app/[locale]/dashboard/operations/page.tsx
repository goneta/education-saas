"use client"

import { useCallback, useEffect, useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

type Section = "programs" | "admissions" | "exams" | "inventory" | "payroll" | "transport" | "canteen"
type OperationRow = Record<string, unknown> & { id?: number }

export default function OperationsPage() {
    const { token } = useAuth()
    const [active, setActive] = useState<Section>("programs")
    const [rows, setRows] = useState<Record<Section, OperationRow[]>>({
        programs: [], admissions: [], exams: [], inventory: [], payroll: [], transport: [], canteen: []
    })
    const [form, setForm] = useState<Record<string, string>>({})

    const load = useCallback(async () => {
        if (!token) return
        const endpoints: Record<Section, string> = {
            programs: "programs",
            admissions: "admissions",
            exams: "exams",
            inventory: "inventory",
            payroll: "payroll",
            transport: "transport",
            canteen: "canteen",
        }
        const loaded: Record<Section, OperationRow[]> = {
            programs: [], admissions: [], exams: [], inventory: [], payroll: [], transport: [], canteen: []
        }
        for (const key of Object.keys(endpoints) as Section[]) {
            const res = await fetch(`${API_BASE_URL}/operations/${endpoints[key]}`, { headers: { Authorization: `Bearer ${token}` } })
            if (res.ok) loaded[key] = await res.json() as OperationRow[]
        }
        setRows(loaded)
    }, [token])

    const create = async () => {
        if (!token) return
        const payload = buildPayload(active, form)
        const res = await fetch(`${API_BASE_URL}/operations/${active}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(payload)
        })
        if (res.ok) {
            setForm({})
            void load()
        }
    }

    const enrollAdmission = async (row: OperationRow) => {
        if (!token || typeof row.id !== "number") return
        const email = window.prompt("Student email")
        if (!email) return
        const classId = window.prompt("Class ID for assignment")
        const res = await fetch(`${API_BASE_URL}/operations/admissions/${row.id}/enroll`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                email,
                full_name: typeof row.applicant_name === "string" ? row.applicant_name : undefined,
                class_id: classId ? Number(classId) : undefined,
            })
        })
        if (res.ok) void load()
    }

    useEffect(() => { void load() }, [load])

    const fields = fieldsFor(active)
    const displayRows = rows[active] || []

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">Institution Operations</h1>
                <p className="text-sm text-[#6B7280] mt-1">Admissions, programs, exams, inventory, payroll, transport and canteen.</p>
            </div>

            <div className="flex flex-wrap gap-2">
                {(["programs", "admissions", "exams", "inventory", "payroll", "transport", "canteen"] as Section[]).map(section => (
                    <Button key={section} variant={active === section ? "default" : "outline"} onClick={() => { setActive(section); setForm({}) }}>
                        {label(section)}
                    </Button>
                ))}
            </div>

            <Card>
                <CardHeader><CardTitle>Add {label(active)}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-4">
                    {fields.map(field => (
                        <input
                            key={field.name}
                            type={field.type || "text"}
                            placeholder={field.label}
                            value={form[field.name] || ""}
                            onChange={(e) => setForm({ ...form, [field.name]: e.target.value })}
                            className="border rounded-md px-3 py-2 text-sm"
                        />
                    ))}
                    <Button onClick={create}>Save</Button>
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle>{label(active)} List</CardTitle></CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b">
                                    {columnsFor(active).map(col => <th key={col} className="py-2 text-left">{col}</th>)}
                                    {active === "admissions" && <th className="py-2 text-right">Actions</th>}
                                </tr>
                            </thead>
                            <tbody>
                                {displayRows.map(row => (
                                    <tr key={row.id} className="border-b last:border-0">
                                        {columnsFor(active).map(col => <td key={col} className="py-2">{formatCell(row, col)}</td>)}
                                        {active === "admissions" && <td className="py-2 text-right"><Button size="sm" variant="outline" onClick={() => enrollAdmission(row)}>Enroll</Button></td>}
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

function label(section: Section) {
    return ({ programs: "Programs", admissions: "Admissions", exams: "Exams", inventory: "Inventory", payroll: "Payroll", transport: "Transport", canteen: "Canteen" })[section]
}

function fieldsFor(section: Section) {
    const map: Record<Section, Array<{ name: string; label: string; type?: string }>> = {
        programs: [{ name: "name", label: "Program name" }, { name: "sector", label: "Sector" }, { name: "level", label: "Level" }, { name: "diploma", label: "Diploma" }, { name: "duration_years", label: "Duration years", type: "number" }],
        admissions: [{ name: "applicant_name", label: "Applicant name" }, { name: "applicant_phone", label: "Phone" }, { name: "desired_level", label: "Desired level" }, { name: "desired_program_id", label: "Program ID", type: "number" }],
        exams: [{ name: "name", label: "Exam name" }, { name: "exam_type", label: "Type" }, { name: "class_id", label: "Class ID", type: "number" }, { name: "program_id", label: "Program ID", type: "number" }, { name: "start_date", label: "Start date", type: "date" }],
        inventory: [{ name: "name", label: "Item name" }, { name: "category", label: "Category" }, { name: "quantity", label: "Quantity", type: "number" }, { name: "minimum_quantity", label: "Minimum", type: "number" }, { name: "location", label: "Location" }],
        payroll: [{ name: "staff_user_id", label: "Staff user ID", type: "number" }, { name: "period", label: "Period" }, { name: "gross_amount", label: "Gross", type: "number" }, { name: "deductions", label: "Deductions", type: "number" }],
        transport: [{ name: "name", label: "Route name" }, { name: "vehicle_identifier", label: "Vehicle" }, { name: "driver_name", label: "Driver" }, { name: "driver_phone", label: "Phone" }, { name: "monthly_fee", label: "Monthly fee", type: "number" }],
        canteen: [{ name: "name", label: "Plan name" }, { name: "day_of_week", label: "Day" }, { name: "meal_type", label: "Meal type" }, { name: "menu", label: "Menu" }, { name: "price", label: "Price", type: "number" }],
    }
    return map[section]
}

function columnsFor(section: Section) {
    const map: Record<Section, string[]> = {
        programs: ["name", "sector", "level", "diploma"],
        admissions: ["applicant_name", "desired_level", "status", "created_at"],
        exams: ["name", "exam_type", "status", "start_date"],
        inventory: ["name", "category", "quantity", "status"],
        payroll: ["staff_user_id", "period", "net_amount", "status"],
        transport: ["name", "vehicle_identifier", "driver_name", "monthly_fee"],
        canteen: ["name", "day_of_week", "meal_type", "price"],
    }
    return map[section]
}

function buildPayload(section: Section, form: Record<string, string>) {
    const numeric = new Set(["duration_years", "desired_program_id", "class_id", "program_id", "quantity", "minimum_quantity", "staff_user_id", "gross_amount", "deductions", "monthly_fee", "price"])
    const payload: Record<string, unknown> = {}
    for (const field of fieldsFor(section)) {
        const value = form[field.name]
        if (!value) continue
        payload[field.name] = numeric.has(field.name) ? Number(value) : field.type === "date" ? `${value}T00:00:00` : value
    }
    return payload
}

function formatCell(row: OperationRow, col: string) {
    const value = row[col]
    if (value === null || value === undefined) return "-"
    if (typeof value === "number") return value.toLocaleString()
    if ((col.includes("date") || col === "created_at") && (typeof value === "string" || value instanceof Date)) {
        return new Date(value).toLocaleDateString()
    }
    return String(value)
}
