"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { normalizeLocale } from "@/lib/i18n"
import { tx } from "@/lib/product-copy"

type Section = "programs" | "admissions" | "exams" | "inventory" | "payroll" | "canteen"
type OperationRow = Record<string, unknown> & { id?: number }

const SECTION_KEY: Record<Section, string> = {
    programs: "opPrograms", admissions: "opAdmissions", exams: "opExams",
    inventory: "opInventory", payroll: "opPayroll", canteen: "opCanteen",
}

// Column name -> PRODUCT_COPY key (falls back to the raw column name).
const COLUMN_KEY: Record<string, string> = {
    name: "name", sector: "fSector", level: "fLevel", diploma: "fDiploma",
    applicant_name: "fApplicantName", desired_level: "fDesiredLevel", status: "cStatus",
    created_at: "cCreatedAt", exam_type: "cExamType", start_date: "fStartDate",
    category: "fCategory", quantity: "fQuantity", staff_user_id: "fStaffUserId",
    period: "fPeriod", net_amount: "cNetAmount", day_of_week: "cDayOfWeek",
    meal_type: "fMealType", price: "fPrice",
}

export default function OperationsPage() {
    const { token } = useAuth()
    const params = useParams<{ locale: string }>()
    const locale = normalizeLocale(params?.locale)
    const [active, setActive] = useState<Section>("programs")
    const [rows, setRows] = useState<Record<Section, OperationRow[]>>({
        programs: [], admissions: [], exams: [], inventory: [], payroll: [], canteen: []
    })
    const [form, setForm] = useState<Record<string, string>>({})

    const sectionLabel = useCallback((section: Section) => tx(locale, SECTION_KEY[section]), [locale])

    const load = useCallback(async () => {
        if (!token) return
        const endpoints: Record<Section, string> = {
            programs: "programs", admissions: "admissions", exams: "exams",
            inventory: "inventory", payroll: "payroll", canteen: "canteen",
        }
        const loaded: Record<Section, OperationRow[]> = {
            programs: [], admissions: [], exams: [], inventory: [], payroll: [], canteen: []
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
        const email = window.prompt(tx(locale, "promptStudentEmail"))
        if (!email) return
        const classId = window.prompt(tx(locale, "promptClassId"))
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

    const filterColumns = useMemo<FilterColumn<OperationRow>[]>(
        () => columnsFor(active).map(col => ({ key: col, label: tx(locale, COLUMN_KEY[col] || col), accessor: row => formatCell(row, col) })),
        [active, locale],
    )
    const filter = useTableFilter(displayRows, filterColumns, { storageKey: "operations" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">{tx(locale, "operationsTitle")}</h1>
                <p className="text-sm text-[#6B7280] mt-1">{tx(locale, "operationsDescription")}</p>
            </div>

            <div className="flex flex-wrap gap-2">
                {(["programs", "admissions", "exams", "inventory", "payroll", "canteen"] as Section[]).map(section => (
                    <Button key={section} variant={active === section ? "default" : "outline"} onClick={() => { setActive(section); setForm({}) }}>
                        {sectionLabel(section)}
                    </Button>
                ))}
            </div>

            <Card>
                <CardHeader><CardTitle>{tx(locale, "addItem", { name: sectionLabel(active) })}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-4">
                    {fields.map(field => (
                        <input
                            key={field.name}
                            type={field.type || "text"}
                            placeholder={tx(locale, field.labelKey)}
                            value={form[field.name] || ""}
                            onChange={(e) => setForm({ ...form, [field.name]: e.target.value })}
                            className="border rounded-md px-3 py-2 text-sm"
                        />
                    ))}
                    <Button onClick={create}>{tx(locale, "save")}</Button>
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle>{tx(locale, "itemList", { name: sectionLabel(active) })}</CardTitle></CardHeader>
                <CardContent>
                    <div className="mb-4 max-w-2xl">
                        <TableFilter {...filter.controls} />
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b">
                                    {columnsFor(active).map(col => <th key={col} className="py-2 text-left">{tx(locale, COLUMN_KEY[col] || col)}</th>)}
                                    {active === "admissions" && <th className="py-2 text-right">{tx(locale, "actions")}</th>}
                                </tr>
                            </thead>
                            <tbody>
                                {filter.filtered.map(row => (
                                    <tr key={row.id} className="border-b last:border-0">
                                        {columnsFor(active).map(col => <td key={col} className="py-2">{formatCell(row, col)}</td>)}
                                        {active === "admissions" && <td className="py-2 text-right"><Button size="sm" variant="outline" onClick={() => enrollAdmission(row)}>{tx(locale, "enroll")}</Button></td>}
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

function fieldsFor(section: Section) {
    const map: Record<Section, Array<{ name: string; labelKey: string; type?: string }>> = {
        programs: [{ name: "name", labelKey: "fProgramName" }, { name: "sector", labelKey: "fSector" }, { name: "level", labelKey: "fLevel" }, { name: "diploma", labelKey: "fDiploma" }, { name: "duration_years", labelKey: "fDurationYears", type: "number" }],
        admissions: [{ name: "applicant_name", labelKey: "fApplicantName" }, { name: "applicant_phone", labelKey: "fPhone" }, { name: "desired_level", labelKey: "fDesiredLevel" }, { name: "desired_program_id", labelKey: "fProgramId", type: "number" }],
        exams: [{ name: "name", labelKey: "fExamName" }, { name: "exam_type", labelKey: "fType" }, { name: "class_id", labelKey: "fClassId", type: "number" }, { name: "program_id", labelKey: "fProgramId", type: "number" }, { name: "start_date", labelKey: "fStartDate", type: "date" }],
        inventory: [{ name: "name", labelKey: "fItemName" }, { name: "category", labelKey: "fCategory" }, { name: "quantity", labelKey: "fQuantity", type: "number" }, { name: "minimum_quantity", labelKey: "fMinimum", type: "number" }, { name: "location", labelKey: "fLocation" }],
        payroll: [{ name: "staff_user_id", labelKey: "fStaffUserId", type: "number" }, { name: "period", labelKey: "fPeriod" }, { name: "gross_amount", labelKey: "fGross", type: "number" }, { name: "deductions", labelKey: "fDeductions", type: "number" }],
        canteen: [{ name: "name", labelKey: "fPlanName" }, { name: "day_of_week", labelKey: "fDay" }, { name: "meal_type", labelKey: "fMealType" }, { name: "menu", labelKey: "fMenu" }, { name: "price", labelKey: "fPrice", type: "number" }],
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
