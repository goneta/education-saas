"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { MapPin, ShieldAlert, RefreshCw } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Position { id: number; vehicle_id: number; latitude: number; longitude: number; speed_kmh?: number | null; recorded_at?: string | null }
interface Vehicle { id: number; name: string }
interface SafetyAlert { student_id: number; student_name: string; route_id?: number | null; alert: string }

export default function TransportTrackingPage() {
    const t = useTranslations("transport")
    const { token } = useAuth()
    const [positions, setPositions] = useState<Position[]>([])
    const [vehicles, setVehicles] = useState<Vehicle[]>([])
    const [alerts, setAlerts] = useState<SafetyAlert[]>([])
    const [form, setForm] = useState({ vehicle_id: "", latitude: "", longitude: "", speed_kmh: "" })

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const [posRes, vehRes, alertRes] = await Promise.all([
            fetch(`${API_BASE_URL}/transport/positions/latest`, { headers }),
            fetch(`${API_BASE_URL}/transport/vehicles`, { headers }),
            fetch(`${API_BASE_URL}/transport/safety/alerts`, { headers }),
        ])
        if (posRes.ok) setPositions(await posRes.json())
        if (vehRes.ok) setVehicles(await vehRes.json())
        if (alertRes.ok) setAlerts((await alertRes.json()).not_boarded || [])
    }, [headers])

    useEffect(() => { void load() }, [load])

    const ingest = async () => {
        if (!headers || !form.vehicle_id) return
        const body = JSON.stringify({
            vehicle_id: Number(form.vehicle_id),
            latitude: Number(form.latitude) || 0,
            longitude: Number(form.longitude) || 0,
            speed_kmh: form.speed_kmh ? Number(form.speed_kmh) : null,
        })
        const response = await fetch(`${API_BASE_URL}/transport/positions`, { method: "POST", headers, body })
        if (response.ok) { setForm({ vehicle_id: "", latitude: "", longitude: "", speed_kmh: "" }); void load() }
    }

    const vehicleName = (id: number) => vehicles.find(v => v.id === id)?.name || `#${id}`

    const columns = useMemo<FilterColumn<Position>[]>(() => [
        { key: "vehicle", label: t("tracking.vehicle"), accessor: p => vehicleName(p.vehicle_id) },
        { key: "gps", label: t("tracking.gps"), accessor: p => `${p.latitude}, ${p.longitude}` },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- vehicleName derives from vehicles
    ], [vehicles])
    const filter = useTableFilter(positions, columns, { storageKey: "transport-positions" })

    return (
        <div className="space-y-6">
            <div className="flex items-start justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("tracking.title")}</h1>
                    <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("tracking.subtitle")}</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => void load()}><RefreshCw className="mr-2 h-4 w-4" /> {t("common.refresh")}</Button>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>{t("tracking.injectTitle")}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-5">
                    <select value={form.vehicle_id} onChange={e => setForm({ ...form, vehicle_id: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                        <option value="">{t("common.vehiclePlaceholder")}</option>
                        {vehicles.map(vehicle => <option key={vehicle.id} value={vehicle.id}>{vehicle.name}</option>)}
                    </select>
                    <input value={form.latitude} onChange={e => setForm({ ...form, latitude: e.target.value })} placeholder={t("stops.latitude")} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input value={form.longitude} onChange={e => setForm({ ...form, longitude: e.target.value })} placeholder={t("stops.longitude")} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input value={form.speed_kmh} onChange={e => setForm({ ...form, speed_kmh: e.target.value })} placeholder={t("tracking.speedPlaceholder")} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <Button onClick={ingest} className="bg-black text-white hover:bg-black/90"><MapPin className="mr-2 h-4 w-4" /> {t("tracking.send")}</Button>
                </CardContent>
            </Card>

            <div className="grid gap-6 lg:grid-cols-2">
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader><CardTitle>{t("tracking.positions")} ({filter.filtered.length})</CardTitle></CardHeader>
                    <CardContent className="overflow-x-auto">
                        <div className="mb-3"><TableFilter {...filter.controls} /></div>
                        <table className="w-full text-left text-sm">
                            <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("tracking.vehicle")}</th><th className="px-3 py-2">{t("tracking.gps")}</th><th className="px-3 py-2">{t("tracking.speed")}</th><th className="px-3 py-2">{t("tracking.timestamp")}</th></tr></thead>
                            <tbody>
                                {filter.filtered.length === 0 ? (
                                    <tr><td colSpan={4} className="px-3 py-6 text-center text-[#6B7280]">{t("tracking.noPositions")}</td></tr>
                                ) : filter.filtered.map(position => (
                                    <tr key={position.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                        <td className="px-3 py-2 font-medium">{vehicleName(position.vehicle_id)}</td>
                                        <td className="px-3 py-2">{position.latitude}, {position.longitude}</td>
                                        <td className="px-3 py-2">{position.speed_kmh != null ? `${position.speed_kmh} km/h` : "-"}</td>
                                        <td className="px-3 py-2">{position.recorded_at ? new Date(position.recorded_at).toLocaleTimeString() : "-"}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </CardContent>
                </Card>

                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader><CardTitle className="flex items-center gap-2"><ShieldAlert className="h-4 w-4 text-amber-600" /> {t("tracking.safetyAlerts")} ({alerts.length})</CardTitle></CardHeader>
                    <CardContent className="space-y-2">
                        {alerts.length === 0 ? (
                            <p className="py-6 text-center text-sm text-[#6B7280]">{t("tracking.noAlerts")}</p>
                        ) : alerts.map(alert => (
                            <div key={alert.student_id} className="flex items-center justify-between rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm dark:border-amber-900 dark:bg-amber-950/30">
                                <span className="font-medium">{alert.student_name}</span>
                                <span className="text-xs text-amber-700 dark:text-amber-300">{t("tracking.notBoarded")}</span>
                            </div>
                        ))}
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
