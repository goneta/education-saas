"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Plus, Trash2 } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Stop {
    id: number
    route_id: number
    name: string
    sequence: number
    latitude?: number | null
    longitude?: number | null
    radius_m: number
    scheduled_arrival?: string | null
    address?: string | null
}
interface Route { id: number; name: string }

export default function TransportStopsPage() {
    const { token } = useAuth()
    const [stops, setStops] = useState<Stop[]>([])
    const [routes, setRoutes] = useState<Route[]>([])
    const [form, setForm] = useState({ route_id: "", name: "", sequence: "", latitude: "", longitude: "", scheduled_arrival: "" })
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const [stopsRes, routesRes] = await Promise.all([
            fetch(`${API_BASE_URL}/transport/stops`, { headers }),
            fetch(`${API_BASE_URL}/transport/routes`, { headers }),
        ])
        if (stopsRes.ok) setStops(await stopsRes.json())
        if (routesRes.ok) setRoutes(await routesRes.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const create = async () => {
        if (!headers || !form.route_id || !form.name.trim()) return
        setError(null)
        const body = JSON.stringify({
            route_id: Number(form.route_id),
            name: form.name,
            sequence: Number(form.sequence) || 0,
            latitude: form.latitude ? Number(form.latitude) : null,
            longitude: form.longitude ? Number(form.longitude) : null,
            scheduled_arrival: form.scheduled_arrival || null,
        })
        const response = await fetch(`${API_BASE_URL}/transport/stops`, { method: "POST", headers, body })
        if (response.ok) { setForm({ route_id: "", name: "", sequence: "", latitude: "", longitude: "", scheduled_arrival: "" }); void load() }
        else setError("Enregistrement impossible.")
    }

    const remove = async (id: number) => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/transport/stops/${id}`, { method: "DELETE", headers })
        if (response.ok) void load()
    }

    const routeName = (id: number) => routes.find(r => r.id === id)?.name || `#${id}`

    const columns = useMemo<FilterColumn<Stop>[]>(() => [
        { key: "name", label: "Arrêt", accessor: stop => stop.name },
        { key: "route", label: "Trajet", accessor: stop => routeName(stop.route_id) },
        { key: "address", label: "Adresse", accessor: stop => stop.address },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- routeName derives from routes
    ], [routes])
    const filter = useTableFilter(stops, columns, { storageKey: "transport-stops" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">Arrêts de bus</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">Arrêts géolocalisés (GPS + ETA) le long de chaque trajet — base du suivi en temps réel et de l&apos;attendance d&apos;embarquement.</p>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>Ajouter un arrêt</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-6">
                    <select value={form.route_id} onChange={e => setForm({ ...form, route_id: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                        <option value="">Trajet…</option>
                        {routes.map(route => <option key={route.id} value={route.id}>{route.name}</option>)}
                    </select>
                    <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Nom de l'arrêt" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input type="number" value={form.sequence} onChange={e => setForm({ ...form, sequence: e.target.value })} placeholder="Ordre" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input value={form.latitude} onChange={e => setForm({ ...form, latitude: e.target.value })} placeholder="Latitude" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input value={form.longitude} onChange={e => setForm({ ...form, longitude: e.target.value })} placeholder="Longitude" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input value={form.scheduled_arrival} onChange={e => setForm({ ...form, scheduled_arrival: e.target.value })} placeholder="ETA (07:15)" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <Button onClick={create} className="bg-black text-white hover:bg-black/90 md:col-span-6"><Plus className="mr-2 h-4 w-4" /> Ajouter l&apos;arrêt</Button>
                    {error && <p className="text-sm text-red-600 md:col-span-6">{error}</p>}
                </CardContent>
            </Card>

            <div className="max-w-2xl"><TableFilter {...filter.controls} /></div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>Arrêts ({filter.filtered.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]">
                                <th className="px-3 py-2">#</th><th className="px-3 py-2">Arrêt</th><th className="px-3 py-2">Trajet</th><th className="px-3 py-2">GPS</th><th className="px-3 py-2">ETA</th><th className="px-3 py-2 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filter.filtered.length === 0 ? (
                                <tr><td colSpan={6} className="px-3 py-6 text-center text-[#6B7280]">Aucun arrêt.</td></tr>
                            ) : filter.filtered.map(stop => (
                                <tr key={stop.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2">{stop.sequence}</td>
                                    <td className="px-3 py-2 font-medium">{stop.name}</td>
                                    <td className="px-3 py-2">{routeName(stop.route_id)}</td>
                                    <td className="px-3 py-2">{stop.latitude != null && stop.longitude != null ? `${stop.latitude}, ${stop.longitude}` : "-"}</td>
                                    <td className="px-3 py-2">{stop.scheduled_arrival || "-"}</td>
                                    <td className="px-3 py-2 text-right"><Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => remove(stop.id)}><Trash2 className="h-4 w-4" /></Button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
