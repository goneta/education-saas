"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

type Section = "approvals" | "university" | "credentials" | "hr" | "services" | "accounting" | "inspection" | "notifications"
type EnterpriseRow = Record<string, unknown> & { id?: number }
type DashboardSummary = {
    revenue?: number
    outstanding?: number
    pending_approvals?: number
    low_stock_items?: number
}

const sections: Section[] = ["approvals", "university", "credentials", "hr", "services", "accounting", "inspection", "notifications"]

export default function EnterprisePage() {
    const { token } = useAuth()
    const [active, setActive] = useState<Section>("approvals")
    const [createTarget, setCreateTarget] = useState("approvals")
    const [dashboard, setDashboard] = useState<DashboardSummary | null>(null)
    const [rows, setRows] = useState<Record<string, EnterpriseRow[]>>({})
    const [form, setForm] = useState<Record<string, string>>({})
    const config = useMemo(() => sectionConfig(active), [active])
    const fields = fieldsFor(createTarget)

    const load = useCallback(async () => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        const dash = await fetch(`${API_BASE_URL}/enterprise/direction-dashboard`, { headers })
        if (dash.ok) setDashboard(await dash.json() as DashboardSummary)
        const loaded: Record<string, EnterpriseRow[]> = {}
        for (const endpoint of config.endpoints) {
            const res = await fetch(`${API_BASE_URL}/enterprise/${endpoint}`, { headers })
            if (res.ok) loaded[endpoint] = await res.json() as EnterpriseRow[]
        }
        setRows(loaded)
    }, [config.endpoints, token])

    const create = async () => {
        if (!token) return
        const endpoint = createTarget || config.createEndpoint
        const payload = buildPayload(fields, form)
        if (endpoint === "approvals") payload.steps = [{ step_order: 1, role: "direction" }, { step_order: 2, role: "school_admin" }]
        const res = await fetch(`${API_BASE_URL}/enterprise/${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(payload)
        })
        if (res.ok) {
            setForm({})
            void load()
        }
    }

    useEffect(() => { void load() }, [load])
    useEffect(() => { setCreateTarget(config.createEndpoint); setForm({}) }, [active, config.createEndpoint])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">Enterprise Management</h1>
                <p className="text-sm text-[#6B7280] mt-1">Advanced workflows, LMD/ECTS, HR, accounting, inspection and notifications.</p>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
                <Metric title="Revenue" value={dashboard?.revenue || 0} money />
                <Metric title="Outstanding" value={dashboard?.outstanding || 0} money tone="red" />
                <Metric title="Pending Approvals" value={dashboard?.pending_approvals || 0} />
                <Metric title="Low Stock" value={dashboard?.low_stock_items || 0} tone="red" />
            </div>

            <div className="flex flex-wrap gap-2">
                {sections.map(section => <Button key={section} variant={active === section ? "default" : "outline"} onClick={() => { setActive(section); setForm({}) }}>{label(section)}</Button>)}
            </div>

            <Card>
                <CardHeader><CardTitle>Create {labelForEndpoint(createTarget)}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-4">
                    <select value={createTarget} onChange={(e) => { setCreateTarget(e.target.value); setForm({}) }} className="border rounded-md px-3 py-2 text-sm">
                        {config.endpoints.map(endpoint => <option key={endpoint} value={endpoint}>{labelForEndpoint(endpoint)}</option>)}
                    </select>
                    {fields.map(field => (
                        <input key={field.name} type={field.type || "text"} placeholder={field.label} value={form[field.name] || ""} onChange={(e) => setForm({ ...form, [field.name]: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                    ))}
                    <Button onClick={create}>Save</Button>
                </CardContent>
            </Card>

            <div className="grid gap-4 lg:grid-cols-2">
                {config.endpoints.map(endpoint => <ListCard key={endpoint} title={endpoint} rows={rows[endpoint] || []} />)}
            </div>
        </div>
    )
}

function sectionConfig(section: Section) {
    const map: Record<Section, { title: string; createEndpoint: string; endpoints: string[] }> = {
        approvals: { title: "Approval Workflow", createEndpoint: "approvals", endpoints: ["approvals"] },
        university: { title: "Course Unit", createEndpoint: "course-units", endpoints: ["semesters", "course-units", "university-schedule"] },
        credentials: { title: "Diploma", createEndpoint: "diplomas", endpoints: ["diplomas", "transcripts"] },
        hr: { title: "Staff Contract", createEndpoint: "contracts", endpoints: ["contracts", "leaves"] },
        services: { title: "Transport Assignment", createEndpoint: "transport-assignments", endpoints: ["transport-assignments", "canteen-subscriptions"] },
        accounting: { title: "Chart Account", createEndpoint: "accounts", endpoints: ["accounts", "vendor-invoices", "bank-transactions"] },
        inspection: { title: "Government Export", createEndpoint: "government-exports", endpoints: ["government-exports"] },
        notifications: { title: "Notification", createEndpoint: "notifications", endpoints: ["notification-providers", "notifications"] },
    }
    return map[section]
}

function fieldsFor(endpoint: string): Array<{ name: string; label: string; type?: string; numeric?: boolean }> {
    const map: Record<string, Array<{ name: string; label: string; type?: string; numeric?: boolean }>> = {
        approvals: [{ name: "entity_type", label: "Entity type" }, { name: "entity_id", label: "Entity ID", type: "number", numeric: true }, { name: "title", label: "Title" }],
        semesters: [{ name: "name", label: "Semester" }, { name: "code", label: "Code" }, { name: "academic_year_id", label: "Academic year ID", type: "number", numeric: true }, { name: "start_date", label: "Start date", type: "date" }, { name: "end_date", label: "End date", type: "date" }],
        "course-units": [{ name: "code", label: "Code" }, { name: "name", label: "Unit name" }, { name: "credits", label: "Credits", type: "number", numeric: true }, { name: "semester_id", label: "Semester ID", type: "number", numeric: true }],
        "university-schedule": [{ name: "course_unit_id", label: "Course unit ID", type: "number", numeric: true }, { name: "day_of_week", label: "Day" }, { name: "start_time", label: "Start time", type: "time" }, { name: "end_time", label: "End time", type: "time" }, { name: "room", label: "Room" }],
        diplomas: [{ name: "student_id", label: "Student profile ID", type: "number", numeric: true }, { name: "diploma_name", label: "Diploma" }, { name: "certificate_number", label: "Certificate number" }, { name: "total_credits", label: "Credits", type: "number", numeric: true }],
        transcripts: [{ name: "student_id", label: "Student profile ID", type: "number", numeric: true }, { name: "certificate_number", label: "Certificate number" }, { name: "semester_id", label: "Semester ID", type: "number", numeric: true }, { name: "total_credits", label: "Credits", type: "number", numeric: true }, { name: "gpa", label: "GPA", type: "number", numeric: true }],
        contracts: [{ name: "staff_user_id", label: "Staff user ID", type: "number", numeric: true }, { name: "contract_type", label: "Contract type" }, { name: "start_date", label: "Start date", type: "date" }, { name: "base_salary", label: "Base salary", type: "number", numeric: true }],
        leaves: [{ name: "staff_user_id", label: "Staff user ID", type: "number", numeric: true }, { name: "leave_type", label: "Leave type" }, { name: "start_date", label: "Start date", type: "date" }, { name: "end_date", label: "End date", type: "date" }],
        "transport-assignments": [{ name: "route_id", label: "Route ID", type: "number", numeric: true }, { name: "student_id", label: "Student profile ID", type: "number", numeric: true }, { name: "pickup_stop", label: "Pickup stop" }, { name: "dropoff_stop", label: "Dropoff stop" }],
        "canteen-subscriptions": [{ name: "meal_plan_id", label: "Meal plan ID", type: "number", numeric: true }, { name: "student_id", label: "Student profile ID", type: "number", numeric: true }, { name: "start_date", label: "Start date", type: "date" }, { name: "end_date", label: "End date", type: "date" }],
        accounts: [{ name: "code", label: "Account code" }, { name: "name", label: "Account name" }, { name: "account_type", label: "Type" }],
        "vendor-invoices": [{ name: "vendor_name", label: "Vendor" }, { name: "invoice_number", label: "Invoice number" }, { name: "amount", label: "Amount", type: "number", numeric: true }, { name: "due_date", label: "Due date", type: "date" }],
        "bank-transactions": [{ name: "transaction_date", label: "Transaction date", type: "date" }, { name: "amount", label: "Amount", type: "number", numeric: true }, { name: "direction", label: "Direction" }, { name: "description", label: "Description" }],
        "government-exports": [{ name: "export_type", label: "Export type" }, { name: "period", label: "Period" }],
        "notification-providers": [{ name: "channel", label: "sms/email/whatsapp" }, { name: "provider_name", label: "Webhook URL or provider key" }, { name: "api_key_secret", label: "API key" }, { name: "sender_id", label: "Sender ID" }],
        notifications: [{ name: "channel", label: "sms/email/whatsapp" }, { name: "provider_id", label: "Provider ID", type: "number", numeric: true }, { name: "recipient", label: "Recipient" }, { name: "message", label: "Message" }],
    }
    return map[endpoint] || []
}

function buildPayload(fields: Array<{ name: string; type?: string; numeric?: boolean }>, form: Record<string, string>) {
    const payload: Record<string, unknown> = {}
    for (const field of fields) {
        const value = form[field.name]
        if (!value) continue
        payload[field.name] = field.numeric ? Number(value) : field.type === "date" ? `${value}T00:00:00` : value
    }
    return payload
}

function label(section: Section) {
    return ({ approvals: "Approvals", university: "LMD / ECTS", credentials: "Diplomas", hr: "HR", services: "Transport / Canteen", accounting: "Accounting", inspection: "Inspection", notifications: "Notifications" })[section]
}

function labelForEndpoint(endpoint: string) {
    return endpoint.split("-").map(part => part.charAt(0).toUpperCase() + part.slice(1)).join(" ")
}

function Metric({ title, value, money, tone }: { title: string; value: number; money?: boolean; tone?: "red" }) {
    return <Card><CardContent className="pt-6"><p className="text-sm text-[#6B7280]">{title}</p><p className={`text-2xl font-bold ${tone === "red" ? "text-red-700" : "text-[#111827]"}`}>{value.toLocaleString()}{money ? " FCFA" : ""}</p></CardContent></Card>
}

function ListCard({ title, rows }: { title: string; rows: EnterpriseRow[] }) {
    const keys = rows[0] ? Object.keys(rows[0]).slice(0, 4) : ["id", "name", "status"]
    const { token } = useAuth()
    const [editing, setEditing] = useState<EnterpriseRow | null>(null)
    const [jsonValue, setJsonValue] = useState("")

    const remove = async (id: number) => {
        if (!token || !confirm("Delete this record?")) return
        const res = await fetch(`${API_BASE_URL}/enterprise/${title}/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } })
        if (res.ok) location.reload()
    }

    const update = async () => {
        if (!token || !editing || typeof editing.id !== "number") return
        const res = await fetch(`${API_BASE_URL}/enterprise/${title}/${editing.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: jsonValue
        })
        if (res.ok) location.reload()
    }

    return <Card><CardHeader><CardTitle>{title}</CardTitle></CardHeader><CardContent className="space-y-3"><table className="w-full text-sm"><thead><tr className="border-b">{keys.map(k => <th key={k} className="py-2 text-left">{k}</th>)}<th className="py-2 text-right">Actions</th></tr></thead><tbody>{rows.map((row, idx) => <tr key={row.id || idx} className="border-b last:border-0">{keys.map(k => <td key={k} className="py-2">{format(row[k])}</td>)}<td className="py-2 text-right space-x-2"><Button size="sm" variant="outline" onClick={() => { setEditing(row); setJsonValue(JSON.stringify(row, null, 2)) }}>Edit</Button><Button size="sm" variant="outline" disabled={typeof row.id !== "number"} onClick={() => typeof row.id === "number" && remove(row.id)}>Delete</Button></td></tr>)}</tbody></table>{editing && <div className="space-y-2"><textarea className="min-h-40 w-full border rounded-md p-3 text-xs font-mono" value={jsonValue} onChange={(e) => setJsonValue(e.target.value)} /><div className="flex gap-2"><Button onClick={update}>Save JSON</Button><Button variant="outline" onClick={() => setEditing(null)}>Cancel</Button></div></div>}</CardContent></Card>
}

function format(value: unknown) {
    if (value === null || value === undefined) return "-"
    if (typeof value === "object") return JSON.stringify(value)
    if (typeof value === "number") return value.toLocaleString()
    return String(value)
}
