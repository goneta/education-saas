"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { Plus, Trash2, Sparkles, Bell } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Route {
    id: number
    name: string
    monthly_fee: number
    driver_id?: number | null
    vehicle_id?: number | null
    capacity?: number | null
    is_active: boolean
}
interface NamedRef { id: number; name: string }
interface DriverRef { id: number; full_name: string }

export default function TransportRoutesPage() {
    const t = useTranslations("transport")
    const { token } = useAuth()
    const [routes, setRoutes] = useState<Route[]>([])
    const [drivers, setDrivers] = useState<DriverRef[]>([])
    const [vehicles, setVehicles] = useState<NamedRef[]>([])
    const [form, setForm] = useState({ name: "", monthly_fee: "", driver_id: "", vehicle_id: "" })
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const [routesRes, driversRes, vehiclesRes] = await Promise.all([
            fetch(`${API_BASE_URL}/transport/routes`, { headers }),
            fetch(`${API_BASE_URL}/transport/drivers`, { headers }),
            fetch(`${API_BASE_URL}/transport/vehicles`, { headers }),
        ])
        if (routesRes.ok) setRoutes(await routesRes.json())
        if (driversRes.ok) setDrivers(await driversRes.json())
        if (vehiclesRes.ok) setVehicles(await vehiclesRes.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const create = async () => {
        if (!headers || !form.name.trim()) return
        setError(null)
        const body = JSON.stringify({
            name: form.name,
            monthly_fee: Number(form.monthly_fee) || 0,
            driver_id: form.driver_id ? Number(form.driver_id) : null,
            vehicle_id: form.vehicle_id ? Number(form.vehicle_id) : null,
        })
        const response = await fetch(`${API_BASE_URL}/transport/routes`, { method: "POST", headers, body })
        if (response.ok) { setForm({ name: "", monthly_fee: "", driver_id: "", vehicle_id: "" }); void load() }
        else setError(t("common.saveFailed"))
    }

    const remove = async (id: number) => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/transport/routes/${id}`, { method: "DELETE", headers })
        if (response.ok) void load()
    }

    const [advice, setAdvice] = useState<{ name: string; text: string } | null>(null)
    const [busyId, setBusyId] = useState<number | null>(null)

    const optimize = async (route: Route) => {
        if (!headers) return
        setBusyId(route.id)
        setAdvice(null)
        try {
            const response = await fetch(`${API_BASE_URL}/transport/routes/${route.id}/optimize`, { method: "POST", headers })
            if (response.ok) {
                const data = await response.json()
                setAdvice({ name: route.name, text: data.advice || data.details || t("routes.noRecommendation") })
            }
        } finally {
            setBusyId(null)
        }
    }

    const notify = async (route: Route) => {
        if (!headers) return
        const message = window.prompt(t("routes.notifyPrompt", { name: route.name }), t("routes.notifyDefault"))
        if (!message) return
        const url = `${API_BASE_URL}/transport/routes/${route.id}/notify?subject=${encodeURIComponent("Transport")}&message=${encodeURIComponent(message)}`
        const response = await fetch(url, { method: "POST", headers })
        if (response.ok) {
            const data = await response.json()
            window.alert(t("routes.notifySent", { count: data.notified }))
        }
    }

    const driverName = (id?: number | null) => drivers.find(d => d.id === id)?.full_name || "-"
    const vehicleName = (id?: number | null) => vehicles.find(v => v.id === id)?.name || "-"

    const columns = useMemo<FilterColumn<Route>[]>(() => [
        { key: "name", label: t("routes.route"), accessor: route => route.name },
        { key: "driver", label: t("routes.driver"), accessor: route => driverName(route.driver_id) },
        { key: "vehicle", label: t("routes.vehicle"), accessor: route => vehicleName(route.vehicle_id) },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- driverName/vehicleName derive from drivers/vehicles
    ], [drivers, vehicles])
    const filter = useTableFilter(routes, columns, { storageKey: "transport-routes" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("routes.title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("routes.subtitle")}</p>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>{t("routes.addTitle")}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-5">
                    <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder={t("routes.routeName")} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <input type="number" value={form.monthly_fee} onChange={e => setForm({ ...form, monthly_fee: e.target.value })} placeholder={t("routes.monthlyFee")} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent" />
                    <select value={form.driver_id} onChange={e => setForm({ ...form, driver_id: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                        <option value="">{t("common.driverPlaceholder")}</option>
                        {drivers.map(driver => <option key={driver.id} value={driver.id}>{driver.full_name}</option>)}
                    </select>
                    <select value={form.vehicle_id} onChange={e => setForm({ ...form, vehicle_id: e.target.value })} className="rounded-md border px-3 py-2 text-sm dark:border-[#4a535b] dark:bg-transparent">
                        <option value="">{t("common.vehiclePlaceholder")}</option>
                        {vehicles.map(vehicle => <option key={vehicle.id} value={vehicle.id}>{vehicle.name}</option>)}
                    </select>
                    <Button onClick={create} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> {t("common.add")}</Button>
                    {error && <p className="text-sm text-red-600 md:col-span-5">{error}</p>}
                </CardContent>
            </Card>

            {advice && (
                <Card className="rounded-xl border border-[#CCFBF1] bg-[#F0FDFA] shadow-sm dark:border-[#134E4A] dark:bg-[#0f1f1d]">
                    <CardHeader><CardTitle className="flex items-center gap-2 text-base"><Sparkles className="h-4 w-4 text-[#0F766E]" /> {t("routes.aiOptimization")} — {advice.name}</CardTitle></CardHeader>
                    <CardContent><p className="whitespace-pre-wrap text-sm text-[#134E4A] dark:text-[#5eead4]">{advice.text}</p></CardContent>
                </Card>
            )}

            <div className="max-w-2xl"><TableFilter {...filter.controls} /></div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>{t("routes.list")} ({filter.filtered.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]">
                                <th className="px-3 py-2">{t("routes.route")}</th><th className="px-3 py-2">{t("routes.driver")}</th><th className="px-3 py-2">{t("routes.vehicle")}</th><th className="px-3 py-2">{t("routes.monthlyFeeCol")}</th><th className="px-3 py-2 text-right">{t("common.actions")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filter.filtered.length === 0 ? (
                                <tr><td colSpan={5} className="px-3 py-6 text-center text-[#6B7280]">{t("routes.empty")}</td></tr>
                            ) : filter.filtered.map(route => (
                                <tr key={route.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{route.name}</td>
                                    <td className="px-3 py-2">{driverName(route.driver_id)}</td>
                                    <td className="px-3 py-2">{vehicleName(route.vehicle_id)}</td>
                                    <td className="px-3 py-2">{(route.monthly_fee || 0).toLocaleString()} FCFA</td>
                                    <td className="px-3 py-2 text-right">
                                        <div className="flex justify-end gap-1">
                                            <Button variant="ghost" size="sm" disabled={busyId === route.id} onClick={() => optimize(route)} title={t("routes.optimizeTitle")}><Sparkles className="h-4 w-4 text-[#0F766E]" /></Button>
                                            <Button variant="ghost" size="sm" onClick={() => notify(route)} title={t("routes.notifyTitle")}><Bell className="h-4 w-4" /></Button>
                                            <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => remove(route.id)}><Trash2 className="h-4 w-4" /></Button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
