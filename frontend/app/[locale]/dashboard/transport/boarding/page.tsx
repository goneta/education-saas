"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { ScanLine } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Boarding { id: number; student_id: number; route_id?: number | null; direction: string; event_type: string; method: string; recorded_at?: string | null }
interface Route { id: number; name: string }
interface StudentOption { profileId: number; name: string }

function normalizeStudents(payload: unknown): StudentOption[] {
    const rows = Array.isArray(payload) ? payload : []
    return rows.map(row => {
        const record = row as { full_name?: string; student_profile?: { id?: number } | null }
        const profileId = record.student_profile?.id
        return profileId ? { profileId, name: record.full_name || `#${profileId}` } : null
    }).filter((value): value is StudentOption => value !== null)
}

export default function TransportBoardingPage() {
    const { token } = useAuth()
    const [events, setEvents] = useState<Boarding[]>([])
    const [routes, setRoutes] = useState<Route[]>([])
    const [students, setStudents] = useState<StudentOption[]>([])
    const [form, setForm] = useState({ student_id: "", route_id: "", direction: "morning", event_type: "boarded", method: "manual" })

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const [eventsRes, routesRes, studentsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/transport/boarding`, { headers }),
            fetch(`${API_BASE_URL}/transport/routes`, { headers }),
            fetch(`${API_BASE_URL}/students`, { headers }),
        ])
        if (eventsRes.ok) setEvents(await eventsRes.json())
        if (routesRes.ok) setRoutes(await routesRes.json())
        if (studentsRes.ok) setStudents(normalizeStudents(await studentsRes.json()))
    }, [headers])

    useEffect(() => { void load() }, [load])

    const record = async () => {
        if (!headers || !form.student_id) return
        const body = JSON.stringify({
            student_id: Number(form.student_id),
            route_id: form.route_id ? Number(form.route_id) : null,
            direction: form.direction,
            event_type: form.event_type,
            method: form.method,
        })
        const response = await fetch(`${API_BASE_URL}/transport/boarding`, { method: "POST", headers, body })
        if (response.ok) { setForm({ ...form, student_id: "" }); void load() }
    }

    const studentName = (id: number) => students.find(s => s.profileId === id)?.name || `#${id}`
    const routeName = (id?: number | null) => id ? (routes.find(r => r.id === id)?.name || `#${id}`) : "-"

    const columns = useMemo<FilterColumn<Boarding>[]>(() => [
        { key: "student", label: "Élève", accessor: event => studentName(event.student_id) },
        { key: "direction", label: "Sens", accessor: event => event.direction },
        { key: "type", label: "Type", accessor: event => event.event_type },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    ], [students])
    const filter = useTableFilter(events, columns, { storageKey: "transport-boarding" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">Embarquement</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">Pointage d&apos;embarquement/débarquement (manuel, QR ou RFID) — alimente le contrôle de sécurité et l&apos;attendance.</p>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>Pointer un embarquement</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-6">
                    <select value={form.student_id} onChange={e => setForm({ ...form, student_id: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent md:col-span-2">
                        <option value="">Élève…</option>
                        {students.map(student => <option key={student.profileId} value={student.profileId}>{student.name}</option>)}
                    </select>
                    <select value={form.route_id} onChange={e => setForm({ ...form, route_id: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                        <option value="">Trajet…</option>
                        {routes.map(route => <option key={route.id} value={route.id}>{route.name}</option>)}
                    </select>
                    <select value={form.direction} onChange={e => setForm({ ...form, direction: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                        <option value="morning">Matin</option>
                        <option value="afternoon">Après-midi</option>
                    </select>
                    <select value={form.event_type} onChange={e => setForm({ ...form, event_type: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                        <option value="boarded">Montée</option>
                        <option value="dropped">Descente</option>
                    </select>
                    <Button onClick={record} className="bg-black text-white hover:bg-black/90"><ScanLine className="mr-2 h-4 w-4" /> Pointer</Button>
                </CardContent>
            </Card>

            <div className="max-w-2xl"><TableFilter {...filter.controls} /></div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>Pointages ({filter.filtered.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">Élève</th><th className="px-3 py-2">Trajet</th><th className="px-3 py-2">Sens</th><th className="px-3 py-2">Type</th><th className="px-3 py-2">Méthode</th><th className="px-3 py-2">Heure</th></tr></thead>
                        <tbody>
                            {filter.filtered.length === 0 ? (
                                <tr><td colSpan={6} className="px-3 py-6 text-center text-[#6B7280]">Aucun pointage.</td></tr>
                            ) : filter.filtered.map(event => (
                                <tr key={event.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{studentName(event.student_id)}</td>
                                    <td className="px-3 py-2">{routeName(event.route_id)}</td>
                                    <td className="px-3 py-2">{event.direction === "morning" ? "Matin" : "Après-midi"}</td>
                                    <td className="px-3 py-2">{event.event_type === "boarded" ? "Montée" : "Descente"}</td>
                                    <td className="px-3 py-2">{event.method}</td>
                                    <td className="px-3 py-2">{event.recorded_at ? new Date(event.recorded_at).toLocaleTimeString() : "-"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
