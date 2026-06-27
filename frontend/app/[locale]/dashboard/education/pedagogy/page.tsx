"use client"

import { useCallback, useEffect, useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface ClassItem { id: number; name: string }
interface Assignment { id: number; title: string; class_id: number; due_date: string | null; status: string }
interface Material { id: number; title: string; class_id: number; content_url: string | null }
interface RequestRow { id: number; request_type: string; status: string; student_id: number; details: string | null }

export default function PedagogyPage() {
    const { token } = useAuth()
    const [classes, setClasses] = useState<ClassItem[]>([])
    const [assignments, setAssignments] = useState<Assignment[]>([])
    const [materials, setMaterials] = useState<Material[]>([])
    const [requests, setRequests] = useState<RequestRow[]>([])
    const [assignmentForm, setAssignmentForm] = useState({ title: "", class_id: "", due_date: "", instructions: "" })
    const [materialForm, setMaterialForm] = useState({ title: "", class_id: "", content_url: "", content_text: "" })

    const load = useCallback(async () => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        const [classesRes, assignmentsRes, materialsRes, requestsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/education/classes`, { headers }),
            fetch(`${API_BASE_URL}/pedagogy/assignments`, { headers }),
            fetch(`${API_BASE_URL}/pedagogy/materials`, { headers }),
            fetch(`${API_BASE_URL}/pedagogy/requests`, { headers }),
        ])
        if (classesRes.ok) setClasses(await classesRes.json())
        if (assignmentsRes.ok) setAssignments(await assignmentsRes.json())
        if (materialsRes.ok) setMaterials(await materialsRes.json())
        if (requestsRes.ok) setRequests(await requestsRes.json())
    }, [token])

    const createAssignment = async () => {
        if (!token || !assignmentForm.title || !assignmentForm.class_id) return
        const res = await fetch(`${API_BASE_URL}/pedagogy/assignments`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                title: assignmentForm.title,
                class_id: Number(assignmentForm.class_id),
                due_date: assignmentForm.due_date ? `${assignmentForm.due_date}T23:59:00` : null,
                instructions: assignmentForm.instructions || null,
                status: "published",
            })
        })
        if (res.ok) {
            setAssignmentForm({ title: "", class_id: "", due_date: "", instructions: "" })
            void load()
        }
    }

    const createMaterial = async () => {
        if (!token || !materialForm.title || !materialForm.class_id) return
        const res = await fetch(`${API_BASE_URL}/pedagogy/materials`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                title: materialForm.title,
                class_id: Number(materialForm.class_id),
                content_url: materialForm.content_url || null,
                content_text: materialForm.content_text || null,
            })
        })
        if (res.ok) {
            setMaterialForm({ title: "", class_id: "", content_url: "", content_text: "" })
            void load()
        }
    }

    const updateRequest = async (id: number, status: string) => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/pedagogy/requests/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ status, response: status === "approved" ? "Approved by school office." : "Updated by school office." })
        })
        if (res.ok) void load()
    }

    useEffect(() => { void load() }, [load])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">Pedagogy</h1>
                <p className="text-sm text-[#6B7280] mt-1">Course content, homework, submissions and school office requests.</p>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <Card><CardHeader><CardTitle>Create Assignment</CardTitle></CardHeader><CardContent className="space-y-3">
                    <input placeholder="Title" value={assignmentForm.title} onChange={(e) => setAssignmentForm({ ...assignmentForm, title: e.target.value })} className="w-full border rounded-md px-3 py-2 text-sm" />
                    <select value={assignmentForm.class_id} onChange={(e) => setAssignmentForm({ ...assignmentForm, class_id: e.target.value })} className="w-full border rounded-md px-3 py-2 text-sm"><option value="">Class</option>{classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
                    <input type="date" value={assignmentForm.due_date} onChange={(e) => setAssignmentForm({ ...assignmentForm, due_date: e.target.value })} className="w-full border rounded-md px-3 py-2 text-sm" />
                    <textarea placeholder="Instructions" value={assignmentForm.instructions} onChange={(e) => setAssignmentForm({ ...assignmentForm, instructions: e.target.value })} className="w-full min-h-24 border rounded-md px-3 py-2 text-sm" />
                    <Button onClick={createAssignment}>Publish</Button>
                </CardContent></Card>

                <Card><CardHeader><CardTitle>Share Course Material</CardTitle></CardHeader><CardContent className="space-y-3">
                    <input placeholder="Title" value={materialForm.title} onChange={(e) => setMaterialForm({ ...materialForm, title: e.target.value })} className="w-full border rounded-md px-3 py-2 text-sm" />
                    <select value={materialForm.class_id} onChange={(e) => setMaterialForm({ ...materialForm, class_id: e.target.value })} className="w-full border rounded-md px-3 py-2 text-sm"><option value="">Class</option>{classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
                    <input placeholder="Document URL" value={materialForm.content_url} onChange={(e) => setMaterialForm({ ...materialForm, content_url: e.target.value })} className="w-full border rounded-md px-3 py-2 text-sm" />
                    <textarea placeholder="Content or notes" value={materialForm.content_text} onChange={(e) => setMaterialForm({ ...materialForm, content_text: e.target.value })} className="w-full min-h-24 border rounded-md px-3 py-2 text-sm" />
                    <Button onClick={createMaterial}>Share</Button>
                </CardContent></Card>
            </div>

            <div className="grid gap-4">
                <ListCard title="Assignments" rows={assignments.map(a => [a.title, `Class #${a.class_id}`, a.status])} />
                <ListCard title="Course Materials" rows={materials.map(m => [m.title, `Class #${m.class_id}`, m.content_url || "-"])} />
            </div>

            <Card><CardHeader><CardTitle>Administrative Requests</CardTitle></CardHeader><CardContent>
                <table className="w-full text-sm"><thead><tr className="border-b"><th className="py-2 text-left">Type</th><th className="py-2 text-left">Student</th><th className="py-2 text-left">Status</th><th className="py-2 text-left">Details</th><th className="py-2 text-right">Actions</th></tr></thead>
                    <tbody>{requests.map(r => <tr key={r.id} className="border-b last:border-0"><td className="py-2">{r.request_type}</td><td className="py-2">#{r.student_id}</td><td className="py-2">{r.status}</td><td className="py-2">{r.details || "-"}</td><td className="py-2 text-right space-x-2"><Button size="sm" variant="outline" onClick={() => updateRequest(r.id, "approved")}>Approve</Button><Button size="sm" variant="outline" onClick={() => updateRequest(r.id, "done")}>Done</Button></td></tr>)}</tbody>
                </table>
            </CardContent></Card>
        </div>
    )
}

function ListCard({ title, rows }: { title: string; rows: string[][] }) {
    return <Card><CardHeader><CardTitle>{title}</CardTitle></CardHeader><CardContent className="space-y-2">{rows.map((row, idx) => <div key={idx} className="grid grid-cols-3 gap-3 border-b py-2 text-sm"><span className="font-medium">{row[0]}</span><span>{row[1]}</span><span className="text-[#6B7280]">{row[2]}</span></div>)}</CardContent></Card>
}
