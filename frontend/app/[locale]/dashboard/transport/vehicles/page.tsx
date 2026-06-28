"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Plus, Trash2 } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Vehicle {
    id: number
    name: string
    vehicle_type: string
    registration?: string | null
    capacity: number
    status: string
    is_active: boolean
}

const TYPES = ["bus", "minibus", "van", "motorcycle", "boat", "electric_bus"]

export default function TransportVehiclesPage() {
    const { token } = useAuth()
    const [vehicles, setVehicles] = useState<Vehicle[]>([])
    const [form, setForm] = useState({ name: "", vehicle_type: "bus", registration: "", capacity: "" })
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/transport/vehicles`, { headers })
        if (response.ok) setVehicles(await response.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const create = async () => {
        if (!headers || !form.name.trim()) return
        setError(null)
        const body = JSON.stringify({ ...form, capacity: Number(form.capacity) || 0 })
        const response = await fetch(`${API_BASE_URL}/transport/vehicles`, { method: "POST", headers, body })
        if (response.ok) { setForm({ name: "", vehicle_type: "bus", registration: "", capacity: "" }); void load() }
        else setError("Enregistrement impossible.")
    }

    const remove = async (id: number) => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/transport/vehicles/${id}`, { method: "DELETE", headers })
        if (response.ok) void load()
    }

    const columns = useMemo<FilterColumn<Vehicle>[]>(() => [
        { key: "name", label: "Nom", accessor: vehicle => vehicle.name },
        { key: "type", label: "Type", accessor: vehicle => vehicle.vehicle_type },
        { key: "registration", label: "Immatriculation", accessor: vehicle => vehicle.registration },
        { key: "status", label: "État", accessor: vehicle => vehicle.status },
    ], [])
    const filter = useTableFilter(vehicles, columns, { storageKey: "transport-vehicles" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">Véhicules</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">Gérez la flotte : bus, minibus, vans et leur capacité.</p>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>Ajouter un véhicule</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-5">
                    <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Nom / N°" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <select value={form.vehicle_type} onChange={e => setForm({ ...form, vehicle_type: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                        {TYPES.map(type => <option key={type} value={type}>{type}</option>)}
                    </select>
                    <input value={form.registration} onChange={e => setForm({ ...form, registration: e.target.value })} placeholder="Immatriculation" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input type="number" value={form.capacity} onChange={e => setForm({ ...form, capacity: e.target.value })} placeholder="Capacité" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <Button onClick={create} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> Ajouter</Button>
                    {error && <p className="text-sm text-red-600 md:col-span-5">{error}</p>}
                </CardContent>
            </Card>

            <div className="max-w-2xl"><TableFilter {...filter.controls} /></div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>Flotte ({filter.filtered.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]">
                                <th className="px-3 py-2">Nom</th><th className="px-3 py-2">Type</th><th className="px-3 py-2">Immatriculation</th><th className="px-3 py-2">Capacité</th><th className="px-3 py-2">État</th><th className="px-3 py-2 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filter.filtered.length === 0 ? (
                                <tr><td colSpan={6} className="px-3 py-6 text-center text-[#6B7280]">Aucun véhicule.</td></tr>
                            ) : filter.filtered.map(vehicle => (
                                <tr key={vehicle.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{vehicle.name}</td>
                                    <td className="px-3 py-2">{vehicle.vehicle_type}</td>
                                    <td className="px-3 py-2">{vehicle.registration || "-"}</td>
                                    <td className="px-3 py-2">{vehicle.capacity}</td>
                                    <td className="px-3 py-2">{vehicle.status}</td>
                                    <td className="px-3 py-2 text-right"><Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => remove(vehicle.id)}><Trash2 className="h-4 w-4" /></Button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
