"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Plus, Trash2 } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Driver {
    id: number
    full_name: string
    phone?: string | null
    license_number?: string | null
    employment_status: string
    medical_clearance: boolean
    is_active: boolean
}

export default function TransportDriversPage() {
    const { token } = useAuth()
    const [drivers, setDrivers] = useState<Driver[]>([])
    const [form, setForm] = useState({ full_name: "", phone: "", license_number: "" })
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/transport/drivers`, { headers })
        if (response.ok) setDrivers(await response.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const create = async () => {
        if (!headers || !form.full_name.trim()) return
        setError(null)
        const response = await fetch(`${API_BASE_URL}/transport/drivers`, { method: "POST", headers, body: JSON.stringify(form) })
        if (response.ok) { setForm({ full_name: "", phone: "", license_number: "" }); void load() }
        else setError("Enregistrement impossible.")
    }

    const remove = async (id: number) => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/transport/drivers/${id}`, { method: "DELETE", headers })
        if (response.ok) void load()
    }

    const columns = useMemo<FilterColumn<Driver>[]>(() => [
        { key: "name", label: "Nom", accessor: driver => driver.full_name },
        { key: "phone", label: "Téléphone", accessor: driver => driver.phone },
        { key: "license", label: "Permis", accessor: driver => driver.license_number },
        { key: "status", label: "Statut", accessor: driver => driver.employment_status },
    ], [])
    const filter = useTableFilter(drivers, columns, { storageKey: "transport-drivers" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">Chauffeurs</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">Gérez les chauffeurs, leurs permis et leur disponibilité.</p>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>Ajouter un chauffeur</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-4">
                    <input value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} placeholder="Nom complet" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="Téléphone" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input value={form.license_number} onChange={e => setForm({ ...form, license_number: e.target.value })} placeholder="N° de permis" className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <Button onClick={create} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> Ajouter</Button>
                    {error && <p className="text-sm text-red-600 md:col-span-4">{error}</p>}
                </CardContent>
            </Card>

            <div className="max-w-2xl"><TableFilter {...filter.controls} /></div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>Liste des chauffeurs ({filter.filtered.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]">
                                <th className="px-3 py-2">Nom</th><th className="px-3 py-2">Téléphone</th><th className="px-3 py-2">Permis</th><th className="px-3 py-2">Statut</th><th className="px-3 py-2 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filter.filtered.length === 0 ? (
                                <tr><td colSpan={5} className="px-3 py-6 text-center text-[#6B7280]">Aucun chauffeur.</td></tr>
                            ) : filter.filtered.map(driver => (
                                <tr key={driver.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{driver.full_name}</td>
                                    <td className="px-3 py-2">{driver.phone || "-"}</td>
                                    <td className="px-3 py-2">{driver.license_number || "-"}</td>
                                    <td className="px-3 py-2">{driver.employment_status}</td>
                                    <td className="px-3 py-2 text-right"><Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => remove(driver.id)}><Trash2 className="h-4 w-4" /></Button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
