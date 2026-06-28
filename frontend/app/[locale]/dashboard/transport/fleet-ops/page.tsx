"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Plus, Trash2, Fuel, ShieldAlert } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface Vehicle { id: number; name: string }
interface Incident { id: number; vehicle_id?: number | null; incident_type: string; severity: string; status: string; description?: string | null; occurred_at?: string | null }
interface FuelLog { id: number; vehicle_id: number; liters: number; cost: number; odometer?: number | null; logged_at?: string | null }

export default function TransportFleetOpsPage() {
    const { token } = useAuth()
    const [vehicles, setVehicles] = useState<Vehicle[]>([])
    const [incidents, setIncidents] = useState<Incident[]>([])
    const [fuelLogs, setFuelLogs] = useState<FuelLog[]>([])
    const [incidentForm, setIncidentForm] = useState({ vehicle_id: "", incident_type: "breakdown", severity: "low", description: "" })
    const [fuelForm, setFuelForm] = useState({ vehicle_id: "", liters: "", cost: "", odometer: "" })

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const [vehRes, incRes, fuelRes] = await Promise.all([
            fetch(`${API_BASE_URL}/transport/vehicles`, { headers }),
            fetch(`${API_BASE_URL}/transport/incidents`, { headers }),
            fetch(`${API_BASE_URL}/transport/fuel-logs`, { headers }),
        ])
        if (vehRes.ok) setVehicles(await vehRes.json())
        if (incRes.ok) setIncidents(await incRes.json())
        if (fuelRes.ok) setFuelLogs(await fuelRes.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const createIncident = async () => {
        if (!headers) return
        const body = JSON.stringify({
            vehicle_id: incidentForm.vehicle_id ? Number(incidentForm.vehicle_id) : null,
            incident_type: incidentForm.incident_type,
            severity: incidentForm.severity,
            description: incidentForm.description || null,
        })
        const response = await fetch(`${API_BASE_URL}/transport/incidents`, { method: "POST", headers, body })
        if (response.ok) { setIncidentForm({ vehicle_id: "", incident_type: "breakdown", severity: "low", description: "" }); void load() }
    }
    const removeIncident = async (id: number) => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/transport/incidents/${id}`, { method: "DELETE", headers })
        if (response.ok) void load()
    }

    const createFuel = async () => {
        if (!headers || !fuelForm.vehicle_id) return
        const body = JSON.stringify({
            vehicle_id: Number(fuelForm.vehicle_id),
            liters: Number(fuelForm.liters) || 0,
            cost: Number(fuelForm.cost) || 0,
            odometer: fuelForm.odometer ? Number(fuelForm.odometer) : null,
        })
        const response = await fetch(`${API_BASE_URL}/transport/fuel-logs`, { method: "POST", headers, body })
        if (response.ok) { setFuelForm({ vehicle_id: "", liters: "", cost: "", odometer: "" }); void load() }
    }

    const vehicleName = (id?: number | null) => id ? (vehicles.find(v => v.id === id)?.name || `#${id}`) : "-"

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">Maintenance &amp; carburant</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">Incidents de sécurité/opérationnels et consommation de carburant — alimentent les KPI du tableau de bord.</p>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader><CardTitle className="flex items-center gap-2"><ShieldAlert className="h-4 w-4" /> Incidents</CardTitle></CardHeader>
                    <CardContent className="space-y-3">
                        <div className="grid gap-2">
                            <select value={incidentForm.vehicle_id} onChange={e => setIncidentForm({ ...incidentForm, vehicle_id: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                                <option value="">Véhicule (optionnel)…</option>
                                {vehicles.map(vehicle => <option key={vehicle.id} value={vehicle.id}>{vehicle.name}</option>)}
                            </select>
                            <div className="grid grid-cols-2 gap-2">
                                <select value={incidentForm.incident_type} onChange={e => setIncidentForm({ ...incidentForm, incident_type: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                                    {["breakdown", "accident", "delay", "behavior", "other"].map(type => <option key={type} value={type}>{type}</option>)}
                                </select>
                                <select value={incidentForm.severity} onChange={e => setIncidentForm({ ...incidentForm, severity: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                                    {["low", "medium", "high"].map(level => <option key={level} value={level}>{level}</option>)}
                                </select>
                            </div>
                            <input value={incidentForm.description} onChange={e => setIncidentForm({ ...incidentForm, description: e.target.value })} placeholder="Description" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                            <Button onClick={createIncident} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> Signaler</Button>
                        </div>
                        <div className="space-y-2">
                            {incidents.length === 0 ? <p className="text-sm text-[#6B7280]">Aucun incident.</p> : incidents.map(incident => (
                                <div key={incident.id} className="flex items-center justify-between rounded-md border border-[#E5E7EB] px-3 py-2 text-sm dark:border-[#3b4248]">
                                    <span><span className="font-medium">{incident.incident_type}</span> · {incident.severity} · {vehicleName(incident.vehicle_id)}</span>
                                    <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => removeIncident(incident.id)}><Trash2 className="h-4 w-4" /></Button>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader><CardTitle className="flex items-center gap-2"><Fuel className="h-4 w-4" /> Carburant</CardTitle></CardHeader>
                    <CardContent className="space-y-3">
                        <div className="grid gap-2">
                            <select value={fuelForm.vehicle_id} onChange={e => setFuelForm({ ...fuelForm, vehicle_id: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                                <option value="">Véhicule…</option>
                                {vehicles.map(vehicle => <option key={vehicle.id} value={vehicle.id}>{vehicle.name}</option>)}
                            </select>
                            <div className="grid grid-cols-3 gap-2">
                                <input value={fuelForm.liters} onChange={e => setFuelForm({ ...fuelForm, liters: e.target.value })} placeholder="Litres" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                                <input value={fuelForm.cost} onChange={e => setFuelForm({ ...fuelForm, cost: e.target.value })} placeholder="Coût" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                                <input value={fuelForm.odometer} onChange={e => setFuelForm({ ...fuelForm, odometer: e.target.value })} placeholder="Km" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                            </div>
                            <Button onClick={createFuel} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> Enregistrer</Button>
                        </div>
                        <div className="space-y-2">
                            {fuelLogs.length === 0 ? <p className="text-sm text-[#6B7280]">Aucun plein.</p> : fuelLogs.map(log => (
                                <div key={log.id} className="rounded-md border border-[#E5E7EB] px-3 py-2 text-sm dark:border-[#3b4248]">
                                    <span className="font-medium">{vehicleName(log.vehicle_id)}</span> · {log.liters} L · {log.cost.toLocaleString()} FCFA
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
