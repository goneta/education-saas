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

export default function PortalPage() {
    const { token, user } = useAuth()
    const [children, setChildren] = useState<StudentProfile[]>([])
    const [selectedStudentId, setSelectedStudentId] = useState("")
    const [assignments, setAssignments] = useState<Assignment[]>([])
    const [materials, setMaterials] = useState<Material[]>([])
    const [requests, setRequests] = useState<RequestRow[]>([])
    const [requestForm, setRequestForm] = useState({ request_type: "report_card", details: "" })
    const [submissionText, setSubmissionText] = useState<Record<number, string>>({})

    const load = useCallback(async () => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        const [childrenRes, assignmentsRes, materialsRes, requestsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/pedagogy/portal/children`, { headers }),
            fetch(`${API_BASE_URL}/pedagogy/assignments`, { headers }),
            fetch(`${API_BASE_URL}/pedagogy/materials`, { headers }),
            fetch(`${API_BASE_URL}/pedagogy/requests`, { headers }),
        ])
        if (childrenRes.ok) {
            const data = await childrenRes.json()
            setChildren(data)
            if (!selectedStudentId && data[0]?.id) setSelectedStudentId(data[0].id.toString())
        }
        if (assignmentsRes.ok) setAssignments(await assignmentsRes.json())
        if (materialsRes.ok) setMaterials(await materialsRes.json())
        if (requestsRes.ok) setRequests(await requestsRes.json())
    }, [selectedStudentId, token])

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
