"use client"

import { useEffect, useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

type Section = "approvals" | "university" | "credentials" | "hr" | "services" | "accounting" | "inspection" | "notifications"

const sections: Section[] = ["approvals", "university", "credentials", "hr", "services", "accounting", "inspection", "notifications"]

export default function EnterprisePage() {
    const { token } = useAuth()
    const [active, setActive] = useState<Section>("approvals")
    const [dashboard, setDashboard] = useState<any>(null)
    const [rows, setRows] = useState<Record<string, any[]>>({})
    const [form, setForm] = useState<Record<string, string>>({})
    const config = sectionConfig(active)

    const headers = token ? { Authorization: `Bearer ${token}` } : undefined

    const load = async () => {
        if (!token) return
        const dash = await fetch(`${API_BASE_URL}/enterprise/direction-dashboard`, { headers })
        if (dash.ok) setDashboard(await dash.json())
        const loaded: Record<string, any[]> = {}
        for (const endpoint of config.endpoints) {
            const res = await fetch(`${API_BASE_URL}/enterprise/${endpoint}`, { headers })
            if (res.ok) loaded[endpoint] = await res.json()
        }
        setRows(loaded)
    }

    const create = async () => {
        if (!token) return
        const endpoint = config.createEndpoint
        const payload = buildPayload(config.fields, form)
        if (endpoint === "approvals") payload.steps = [{ step_order: 1, role: "direction" }, { step_order: 2, role: "school_admin" }]
        const res = await fetch(`${API_BASE_URL}/enterprise/${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(payload)
        })
        if (res.ok) {
            setForm({})
            load()
        }
    }

    useEffect(() => { load() /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [token, active])

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
                <CardHeader><CardTitle>Create {config.title}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-4">
                    {config.fields.map(field => (
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
    const map: Record<Section, { title: string; createEndpoint: string; endpoints: string[]; fields: Array<{ name: string; label: string; type?: string; numeric?: boolean }> }> = {
        approvals: { title: "Approval Workflow", createEndpoint: "approvals", endpoints: ["approvals"], fields: [{ name: "entity_type", label: "Entity type" }, { name: "entity_id", label: "Entity ID", type: "number", numeric: true }, { name: "title", label: "Title" }] },
        university: { title: "Course Unit", createEndpoint: "course-units", endpoints: ["semesters", "course-units", "university-schedule"], fields: [{ name: "code", label: "Code" }, { name: "name", label: "Unit name" }, { name: "credits", label: "Credits", type: "number", numeric: true }, { name: "semester_id", label: "Semester ID", type: "number", numeric: true }] },
        credentials: { title: "Diploma", createEndpoint: "diplomas", endpoints: ["diplomas", "transcripts"], fields: [{ name: "student_id", label: "Student profile ID", type: "number", numeric: true }, { name: "diploma_name", label: "Diploma" }, { name: "certificate_number", label: "Certificate number" }, { name: "total_credits", label: "Credits", type: "number", numeric: true }] },
        hr: { title: "Staff Contract", createEndpoint: "contracts", endpoints: ["contracts", "leaves"], fields: [{ name: "staff_user_id", label: "Staff user ID", type: "number", numeric: true }, { name: "contract_type", label: "Contract type" }, { name: "start_date", label: "Start date", type: "date" }, { name: "base_salary", label: "Base salary", type: "number", numeric: true }] },
        services: { title: "Transport Assignment", createEndpoint: "transport-assignments", endpoints: ["transport-assignments", "canteen-subscriptions"], fields: [{ name: "route_id", label: "Route ID", type: "number", numeric: true }, { name: "student_id", label: "Student profile ID", type: "number", numeric: true }, { name: "pickup_stop", label: "Pickup stop" }, { name: "dropoff_stop", label: "Dropoff stop" }] },
        accounting: { title: "Chart Account", createEndpoint: "accounts", endpoints: ["accounts", "vendor-invoices", "bank-transactions"], fields: [{ name: "code", label: "Account code" }, { name: "name", label: "Account name" }, { name: "account_type", label: "Type" }] },
        inspection: { title: "Government Export", createEndpoint: "government-exports", endpoints: ["government-exports"], fields: [{ name: "export_type", label: "Export type" }, { name: "period", label: "Period" }] },
        notifications: { title: "Notification", createEndpoint: "notifications", endpoints: ["notifications"], fields: [{ name: "channel", label: "sms/email/whatsapp" }, { name: "recipient", label: "Recipient" }, { name: "subject", label: "Subject" }, { name: "message", label: "Message" }] },
    }
    return map[section]
}

function buildPayload(fields: Array<{ name: string; type?: string; numeric?: boolean }>, form: Record<string, string>) {
    const payload: Record<string, any> = {}
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

function Metric({ title, value, money, tone }: { title: string; value: number; money?: boolean; tone?: "red" }) {
    return <Card><CardContent className="pt-6"><p className="text-sm text-[#6B7280]">{title}</p><p className={`text-2xl font-bold ${tone === "red" ? "text-red-700" : "text-[#111827]"}`}>{value.toLocaleString()}{money ? " FCFA" : ""}</p></CardContent></Card>
}

function ListCard({ title, rows }: { title: string; rows: any[] }) {
    const keys = rows[0] ? Object.keys(rows[0]).slice(0, 4) : ["id", "name", "status"]
    return <Card><CardHeader><CardTitle>{title}</CardTitle></CardHeader><CardContent><table className="w-full text-sm"><thead><tr className="border-b">{keys.map(k => <th key={k} className="py-2 text-left">{k}</th>)}</tr></thead><tbody>{rows.map((row, idx) => <tr key={row.id || idx} className="border-b last:border-0">{keys.map(k => <td key={k} className="py-2">{format(row[k])}</td>)}</tr>)}</tbody></table></CardContent></Card>
}

function format(value: any) {
    if (value === null || value === undefined) return "-"
    if (typeof value === "object") return JSON.stringify(value)
    if (typeof value === "number") return value.toLocaleString()
    return String(value)
}
