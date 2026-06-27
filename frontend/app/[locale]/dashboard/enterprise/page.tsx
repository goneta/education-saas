"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { requestConfirmation } from "@/lib/confirmation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ExplainedField, fieldHelp } from "@/components/ui/explained-field"
import { tx, humanizeKey } from "@/lib/product-copy"
import { normalizeLocale } from "@/lib/i18n"

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
    const params = useParams<{ locale: string }>()
    const locale = normalizeLocale(params?.locale)
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
                <h1 className="apple-page-title">{tx(locale, "enterpriseTitle")}</h1>
                <p className="apple-page-description">{tx(locale, "enterpriseDescription")}</p>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
                <Metric title={tx(locale, "revenue")} value={dashboard?.revenue || 0} money />
                <Metric title={tx(locale, "outstanding")} value={dashboard?.outstanding || 0} money tone="red" />
                <Metric title={tx(locale, "pendingApprovals")} value={dashboard?.pending_approvals || 0} />
                <Metric title={tx(locale, "lowStock")} value={dashboard?.low_stock_items || 0} tone="red" />
            </div>

            <div className="flex flex-wrap gap-2">
                {sections.map(section => <Button key={section} variant={active === section ? "default" : "outline"} onClick={() => { setActive(section); setForm({}) }}>{label(section, locale)}</Button>)}
            </div>

            <Card>
                <CardHeader><CardTitle>{tx(locale, "createRecord", { name: labelForEndpoint(createTarget, locale) })}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-4">
                    <ExplainedField label={tx(locale, "category")} help="Choisissez le sous-module à créer. Les champs du formulaire se mettent à jour automatiquement selon cette sélection.">
                    <select value={createTarget} onChange={(e) => { setCreateTarget(e.target.value); setForm({}) }} className="apple-select">
                        {config.endpoints.map(endpoint => <option key={endpoint} value={endpoint}>{labelForEndpoint(endpoint, locale)}</option>)}
                    </select>
                    </ExplainedField>
                    {fields.map(field => (
                        <ExplainedField key={field.name} label={field.label} help={field.help || fieldHelp(field.label, field.numeric ? "Saisissez un nombre valide. Cet identifiant ou montant relie l'enregistrement aux données existantes et aux rapports." : "Saisissez une valeur claire et vérifiable. Cette donnée sera visible dans les listes, workflows et documents générés.")}>
                            <input type={field.type || "text"} placeholder={field.label} value={form[field.name] || ""} onChange={(e) => setForm({ ...form, [field.name]: e.target.value })} className="apple-input" />
                        </ExplainedField>
                    ))}
                    <Button onClick={create}>{tx(locale, "save")}</Button>
                </CardContent>
            </Card>

            <div className="grid gap-4">
                {config.endpoints.map(endpoint => <ListCard key={endpoint} title={endpoint} displayTitle={labelForEndpoint(endpoint, locale)} rows={rows[endpoint] || []} locale={locale} />)}
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

function fieldsFor(endpoint: string): Array<{ name: string; label: string; help?: string; type?: string; numeric?: boolean }> {
    const map: Record<string, Array<{ name: string; label: string; help?: string; type?: string; numeric?: boolean }>> = {
        approvals: [{ name: "entity_type", label: "Type d'entité", help: "Type de dossier à faire approuver: inscription, attestation, congé, facture ou diplôme." }, { name: "entity_id", label: "ID entité", type: "number", numeric: true, help: "Identifiant numérique du dossier concerné. Il provient de l'enregistrement créé dans le module source." }, { name: "title", label: "Titre", help: "Titre lisible du workflow d'approbation." }],
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

function label(section: Section, locale: string) {
    return ({ approvals: tx(locale, "approvals"), university: tx(locale, "lmdEcts"), credentials: tx(locale, "diplomas"), hr: tx(locale, "hr"), services: tx(locale, "transportCanteen"), accounting: tx(locale, "accounting"), inspection: tx(locale, "inspection"), notifications: tx(locale, "notifications") })[section]
}

function labelForEndpoint(endpoint: string, locale: string) {
    const labels: Record<string, string> = {
        approvals: tx(locale, "approvals"),
        semesters: "Semestres",
        "course-units": "Unités d'enseignement",
        "university-schedule": "Emploi du temps universitaire",
        diplomas: tx(locale, "diplomas"),
        transcripts: "Relevés certifiés",
        contracts: "Contrats",
        leaves: "Congés",
        "transport-assignments": "Affectations transport",
        "canteen-subscriptions": "Abonnements cantine",
        accounts: "Comptes",
        "vendor-invoices": "Factures fournisseurs",
        "bank-transactions": "Transactions bancaires",
        "government-exports": tx(locale, "governmentExports"),
        "notification-providers": "Fournisseurs de notification",
        notifications: tx(locale, "notifications"),
    }
    return labels[endpoint] || humanizeKey(endpoint)
}

function Metric({ title, value, money, tone }: { title: string; value: number; money?: boolean; tone?: "red" }) {
    return <Card><CardContent className="pt-6"><p className="text-sm text-[#6B7280]">{title}</p><p className={`text-2xl font-bold ${tone === "red" ? "text-red-700" : "text-[#111827]"}`}>{value.toLocaleString()}{money ? " FCFA" : ""}</p></CardContent></Card>
}

function ListCard({ title, displayTitle, rows, locale }: { title: string; displayTitle: string; rows: EnterpriseRow[]; locale: string }) {
    const keys = rows[0] ? Object.keys(rows[0]).slice(0, 4) : ["id", "name", "status"]
    const { token } = useAuth()
    const [editing, setEditing] = useState<EnterpriseRow | null>(null)
    const [jsonValue, setJsonValue] = useState("")

    const remove = async (id: number) => {
        if (!token || !await requestConfirmation({ title: "Supprimer cet enregistrement", description: "Cette action est irréversible et reste soumise aux règles métier du module.", confirmLabel: "Supprimer définitivement", destructive: true })) return
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

    return <Card><CardHeader><CardTitle>{displayTitle}</CardTitle></CardHeader><CardContent className="space-y-3"><table className="apple-table"><thead><tr>{keys.map(k => <th key={k}>{humanizeKey(k)}</th>)}<th className="text-right">{tx(locale, "actions")}</th></tr></thead><tbody>{rows.map((row, idx) => <tr key={row.id || idx}>{keys.map(k => <td key={k}>{format(row[k])}</td>)}<td className="space-x-2 text-right"><Button size="sm" variant="outline" onClick={() => { setEditing(row); setJsonValue(JSON.stringify(row, null, 2)) }}>{tx(locale, "edit")}</Button><Button size="sm" variant="outline" disabled={typeof row.id !== "number"} onClick={() => typeof row.id === "number" && remove(row.id)}>{tx(locale, "delete")}</Button></td></tr>)}</tbody></table>{editing && <div className="space-y-2"><textarea className="min-h-40 w-full rounded-[18px] border border-[#e0e0e0] p-4 text-xs font-mono" value={jsonValue} onChange={(e) => setJsonValue(e.target.value)} /><div className="flex gap-2"><Button onClick={update}>Enregistrer JSON</Button><Button variant="outline" onClick={() => setEditing(null)}>{tx(locale, "cancel")}</Button></div></div>}</CardContent></Card>
}

function format(value: unknown) {
    if (value === null || value === undefined) return "-"
    if (typeof value === "object") return JSON.stringify(value)
    if (typeof value === "number") return value.toLocaleString()
    return String(value)
}
