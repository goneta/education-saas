"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Plus, Trash2 } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Assignment {
    id: number
    route_id: number
    student_id: number
    pickup_stop?: string | null
    dropoff_stop?: string | null
    is_active: boolean
}
interface Route { id: number; name: string }
interface StudentOption { profileId: number; name: string }

function normalizeStudents(payload: unknown): StudentOption[] {
    const rows = Array.isArray(payload) ? payload : []
    return rows
        .map(row => {
            const record = row as { full_name?: string; student_profile?: { id?: number } | null }
            const profileId = record.student_profile?.id
            return profileId ? { profileId, name: record.full_name || `#${profileId}` } : null
        })
        .filter((value): value is StudentOption => value !== null)
}

export default function TransportAssignmentsPage() {
    const { token } = useAuth()
    const [assignments, setAssignments] = useState<Assignment[]>([])
    const [routes, setRoutes] = useState<Route[]>([])
    const [students, setStudents] = useState<StudentOption[]>([])
    const [form, setForm] = useState({ route_id: "", student_id: "", pickup_stop: "", dropoff_stop: "" })
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const [assignmentsRes, routesRes, studentsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/transport/assignments`, { headers }),
            fetch(`${API_BASE_URL}/transport/routes`, { headers }),
            fetch(`${API_BASE_URL}/students`, { headers }),
        ])
        if (assignmentsRes.ok) setAssignments(await assignmentsRes.json())
        if (routesRes.ok) setRoutes(await routesRes.json())
        if (studentsRes.ok) setStudents(normalizeStudents(await studentsRes.json()))
    }, [headers])

    useEffect(() => { void load() }, [load])

    const create = async () => {
        if (!headers || !form.route_id || !form.student_id) return
        setError(null)
        const body = JSON.stringify({
            route_id: Number(form.route_id),
            student_id: Number(form.student_id),
            pickup_stop: form.pickup_stop || null,
            dropoff_stop: form.dropoff_stop || null,
        })
        const response = await fetch(`${API_BASE_URL}/transport/assignments`, { method: "POST", headers, body })
        if (response.ok) { setForm({ route_id: "", student_id: "", pickup_stop: "", dropoff_stop: "" }); void load() }
        else setError("Affectation impossible (élève ou trajet invalide).")
    }

    const remove = async (id: number) => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/transport/assignments/${id}`, { method: "DELETE", headers })
        if (response.ok) void load()
    }

    const studentName = (id: number) => students.find(s => s.profileId === id)?.name || `#${id}`
    const routeName = (id: number) => routes.find(r => r.id === id)?.name || `#${id}`

    const columns = useMemo<FilterColumn<Assignment>[]>(() => [
        { key: "student", label: "Élève", accessor: assignment => studentName(assignment.student_id) },
        { key: "route", label: "Trajet", accessor: assignment => routeName(assignment.route_id) },
        { key: "pickup", label: "Arrêt montée", accessor: assignment => assignment.pickup_stop },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- name lookups derive from students/routes
    ], [students, routes])
    const filter = useTableFilter(assignments, columns, { storageKey: "transport-assignments" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">Affectations élèves</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">Affectez chaque élève à un trajet — relié directement aux dossiers élèves (source unique de données).</p>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>Nouvelle affectation</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-5">
                    <select value={form.student_id} onChange={e => setForm({ ...form, student_id: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                        <option value="">Élève…</option>
                        {students.map(student => <option key={student.profileId} value={student.profileId}>{student.name}</option>)}
                    </select>
                    <select value={form.route_id} onChange={e => setForm({ ...form, route_id: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                        <option value="">Trajet…</option>
                        {routes.map(route => <option key={route.id} value={route.id}>{route.name}</option>)}
                    </select>
                    <input value={form.pickup_stop} onChange={e => setForm({ ...form, pickup_stop: e.target.value })} placeholder="Arrêt montée" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input value={form.dropoff_stop} onChange={e => setForm({ ...form, dropoff_stop: e.target.value })} placeholder="Arrêt descente" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <Button onClick={create} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> Affecter</Button>
                    {error && <p className="text-sm text-red-600 md:col-span-5">{error}</p>}
                </CardContent>
            </Card>

            <div className="max-w-2xl"><TableFilter {...filter.controls} /></div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>Affectations ({filter.filtered.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]">
                                <th className="px-3 py-2">Élève</th><th className="px-3 py-2">Trajet</th><th className="px-3 py-2">Montée</th><th className="px-3 py-2">Descente</th><th className="px-3 py-2 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filter.filtered.length === 0 ? (
                                <tr><td colSpan={5} className="px-3 py-6 text-center text-[#6B7280]">Aucune affectation.</td></tr>
                            ) : filter.filtered.map(assignment => (
                                <tr key={assignment.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{studentName(assignment.student_id)}</td>
                                    <td className="px-3 py-2">{routeName(assignment.route_id)}</td>
                                    <td className="px-3 py-2">{assignment.pickup_stop || "-"}</td>
                                    <td className="px-3 py-2">{assignment.dropoff_stop || "-"}</td>
                                    <td className="px-3 py-2 text-right"><Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => remove(assignment.id)}><Trash2 className="h-4 w-4" /></Button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
