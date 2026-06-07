"use client"

import { useCallback, useEffect, useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface StudentProfile { id: number; registration_number: string; parent_name?: string; user?: { full_name: string } }
interface Assignment { id: number; title: string; due_date: string | null; instructions: string | null }
interface Material { id: number; title: string; content_url: string | null; content_text: string | null }
interface RequestRow { id: number; request_type: string; status: string; details: string | null; response: string | null }
interface PortalDocument { id: number; document_type: string; title: string; reference: string | null; generated_at: string; download_url: string | null }
interface PortalInvoice { id: number; invoice_number: string; title: string; amount_due: number; amount_paid: number; remaining_balance: number; status: string }
interface PortalNotification { id: number; event_type: string; subject: string | null; message: string; channel: string; created_at: string }
interface PortalTimetable { id: number; day_of_week: string; start_time: string; end_time: string; room: string | null; class_id: number; subject_id: number; teacher_id: number | null }

export default function PortalPage() {
    const { token, user } = useAuth()
    const [children, setChildren] = useState<StudentProfile[]>([])
    const [selectedStudentId, setSelectedStudentId] = useState("")
    const [assignments, setAssignments] = useState<Assignment[]>([])
    const [materials, setMaterials] = useState<Material[]>([])
    const [requests, setRequests] = useState<RequestRow[]>([])
    const [portalDocs, setPortalDocs] = useState<PortalDocument[]>([])
    const [portalInvoices, setPortalInvoices] = useState<PortalInvoice[]>([])
    const [portalNotifications, setPortalNotifications] = useState<PortalNotification[]>([])
    const [portalTimetable, setPortalTimetable] = useState<PortalTimetable[]>([])
    const [documentFilter, setDocumentFilter] = useState("")
    const [requestForm, setRequestForm] = useState({ request_type: "report_card", details: "" })
    const [submissionText, setSubmissionText] = useState<Record<number, string>>({})

    const load = useCallback(async () => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        const [childrenRes, assignmentsRes, materialsRes, requestsRes, portalRes, timetableRes] = await Promise.all([
            fetch(`${API_BASE_URL}/pedagogy/portal/children`, { headers }),
            fetch(`${API_BASE_URL}/pedagogy/assignments`, { headers }),
            fetch(`${API_BASE_URL}/pedagogy/materials`, { headers }),
            fetch(`${API_BASE_URL}/pedagogy/requests`, { headers }),
            fetch(`${API_BASE_URL}/documents/portal${selectedStudentId ? `?student_id=${selectedStudentId}${documentFilter ? `&document_type=${documentFilter}` : ""}` : ""}`, { headers }),
            fetch(`${API_BASE_URL}/education/timetables/my`, { headers }),
        ])
        if (childrenRes.ok) {
            const data = await childrenRes.json()
            setChildren(data)
            if (!selectedStudentId && data[0]?.id) setSelectedStudentId(data[0].id.toString())
        }
        if (assignmentsRes.ok) setAssignments(await assignmentsRes.json())
        if (materialsRes.ok) setMaterials(await materialsRes.json())
        if (requestsRes.ok) setRequests(await requestsRes.json())
        if (timetableRes.ok) setPortalTimetable(await timetableRes.json())
        if (portalRes.ok) {
            const data = await portalRes.json()
            setPortalDocs(data.documents || [])
            setPortalInvoices(data.invoices || [])
            setPortalNotifications(data.notifications || [])
        }
    }, [documentFilter, selectedStudentId, token])

    const createRequest = async () => {
        if (!token || !selectedStudentId) return
        const res = await fetch(`${API_BASE_URL}/pedagogy/requests`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ student_id: Number(selectedStudentId), request_type: requestForm.request_type, details: requestForm.details || null })
        })
        if (res.ok) {
            setRequestForm({ request_type: "report_card", details: "" })
            void load()
        }
    }

    const submitAssignment = async (assignmentId: number) => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/pedagogy/assignments/${assignmentId}/submissions`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ content_text: submissionText[assignmentId] || null })
        })
        if (res.ok) setSubmissionText({ ...submissionText, [assignmentId]: "" })
    }

    useEffect(() => { void load() }, [load])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">Parent / Student Portal</h1>
                <p className="text-sm text-[#6B7280] mt-1">Homework, course materials, requests, grades and attendance access for {user?.role}.</p>
            </div>

            <Card><CardHeader><CardTitle>Student Context</CardTitle></CardHeader><CardContent>
                <select value={selectedStudentId} onChange={(e) => setSelectedStudentId(e.target.value)} className="border rounded-md px-3 py-2 text-sm min-w-64">
                    {children.map(child => <option key={child.id} value={child.id}>{child.user?.full_name || child.registration_number}</option>)}
                </select>
            </CardContent></Card>

            <div className="grid gap-4 lg:grid-cols-3">
                <Card><CardHeader><CardTitle>Emploi du temps publié</CardTitle></CardHeader><CardContent className="space-y-3">
                    {portalTimetable.map(row => <div key={row.id} className="rounded-md border p-3 text-sm"><p className="font-medium">{row.day_of_week} • {row.start_time.slice(0, 5)} - {row.end_time.slice(0, 5)}</p><p className="text-[#6B7280]">Classe #{row.class_id} • Matière #{row.subject_id} • Professeur #{row.teacher_id || "-"}</p><p>Salle: {row.room || "-"}</p></div>)}
                    {!portalTimetable.length && <p className="text-sm text-[#6B7280]">Aucun emploi du temps publié.</p>}
                </CardContent></Card>

                <Card><CardHeader><CardTitle>Documents disponibles</CardTitle></CardHeader><CardContent className="space-y-3">
                    <select value={documentFilter} onChange={(event) => setDocumentFilter(event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm">
                        <option value="">Tous les documents</option>
                        <option value="receipt">Reçus</option>
                        <option value="certificate">Attestations</option>
                        <option value="report_card">Bulletins</option>
                        <option value="invoice">Factures</option>
                    </select>
                    {portalDocs.map(doc => <div key={doc.id} className="rounded-md border p-3 text-sm"><div className="flex items-start justify-between gap-3"><div><p className="font-medium">{doc.title}</p><p className="text-[#6B7280]">{doc.document_type} • {doc.reference || "-"}</p><p className="text-xs text-[#6B7280]">{new Date(doc.generated_at).toLocaleString()}</p></div>{doc.download_url && <a className="text-[#0F766E] font-medium" href={`${API_BASE_URL}${doc.download_url}`} target="_blank">Télécharger</a>}</div></div>)}
                    {!portalDocs.length && <p className="text-sm text-[#6B7280]">Aucun document disponible.</p>}
                </CardContent></Card>

                <Card><CardHeader><CardTitle>Factures et soldes</CardTitle></CardHeader><CardContent className="space-y-3">
                    {portalInvoices.map(invoice => <div key={invoice.id} className="rounded-md border p-3 text-sm"><p className="font-medium">{invoice.title}</p><p className="text-[#6B7280]">{invoice.invoice_number} • {invoice.status}</p><p className="mt-1">Payé: {invoice.amount_paid.toLocaleString()} / Dû: {invoice.amount_due.toLocaleString()}</p><p className="font-semibold text-[#0F766E]">Solde: {invoice.remaining_balance.toLocaleString()}</p></div>)}
                    {!portalInvoices.length && <p className="text-sm text-[#6B7280]">Aucune facture disponible.</p>}
                </CardContent></Card>

                <Card><CardHeader><CardTitle>Notifications</CardTitle></CardHeader><CardContent className="space-y-3">
                    {portalNotifications.map(notification => <div key={notification.id} className="rounded-md border p-3 text-sm"><p className="font-medium">{notification.subject || notification.event_type}</p><p className="text-[#6B7280]">{notification.channel} • {new Date(notification.created_at).toLocaleString()}</p><p className="mt-1">{notification.message}</p></div>)}
                    {!portalNotifications.length && <p className="text-sm text-[#6B7280]">Aucune notification enregistrée.</p>}
                </CardContent></Card>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <Card><CardHeader><CardTitle>Assignments</CardTitle></CardHeader><CardContent className="space-y-4">
                    {assignments.map(assignment => <div key={assignment.id} className="border-b pb-4 last:border-0">
                        <div className="flex justify-between gap-3"><div><p className="font-medium">{assignment.title}</p><p className="text-sm text-[#6B7280]">{assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : "No due date"}</p></div></div>
                        <p className="mt-2 text-sm">{assignment.instructions}</p>
                        {user?.role === "student" && <div className="mt-3 flex gap-2"><input placeholder="Submission text" value={submissionText[assignment.id] || ""} onChange={(e) => setSubmissionText({ ...submissionText, [assignment.id]: e.target.value })} className="flex-1 border rounded-md px-3 py-2 text-sm" /><Button variant="outline" onClick={() => submitAssignment(assignment.id)}>Submit</Button></div>}
                    </div>)}
                </CardContent></Card>

                <Card><CardHeader><CardTitle>Course Materials</CardTitle></CardHeader><CardContent className="space-y-3">
                    {materials.map(material => <div key={material.id} className="border-b py-2 last:border-0"><p className="font-medium">{material.title}</p><p className="text-sm text-[#6B7280]">{material.content_text || material.content_url || "-"}</p></div>)}
                </CardContent></Card>
            </div>

            <Card><CardHeader><CardTitle>Administrative Requests</CardTitle></CardHeader><CardContent className="space-y-4">
                <div className="grid gap-3 md:grid-cols-4">
                    <select value={requestForm.request_type} onChange={(e) => setRequestForm({ ...requestForm, request_type: e.target.value })} className="border rounded-md px-3 py-2 text-sm">
                        <option value="report_card">Report card</option>
                        <option value="certificate">Certificate</option>
                        <option value="absence_authorization">Absence authorization</option>
                        <option value="other">Other</option>
                    </select>
                    <input placeholder="Details" value={requestForm.details} onChange={(e) => setRequestForm({ ...requestForm, details: e.target.value })} className="md:col-span-2 border rounded-md px-3 py-2 text-sm" />
                    <Button onClick={createRequest}>Create Request</Button>
                </div>
                <table className="w-full text-sm"><thead><tr className="border-b"><th className="py-2 text-left">Type</th><th className="py-2 text-left">Status</th><th className="py-2 text-left">Details</th><th className="py-2 text-left">Response</th></tr></thead><tbody>{requests.map(r => <tr key={r.id} className="border-b last:border-0"><td className="py-2">{r.request_type}</td><td className="py-2">{r.status}</td><td className="py-2">{r.details || "-"}</td><td className="py-2">{r.response || "-"}</td></tr>)}</tbody></table>
            </CardContent></Card>
        </div>
    )
}
