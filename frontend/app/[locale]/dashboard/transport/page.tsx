"use client"

import { useCallback, useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { Bus, Users, Route as RouteIcon, Gauge, Wallet, Wrench, MapPin, ShieldAlert, Fuel, Satellite } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent } from "@/components/ui/card"

interface TransportDashboard {
    vehicles: number
    drivers: number
    routes: number
    bus_stops: number
    students_transported: number
    fleet_capacity: number
    occupancy_rate: number
    monthly_transport_revenue: number
    active_routes: number
    vehicles_in_maintenance: number
    fuel_cost_total: number
    open_incidents: number
    boardings_today: number
}

const EMPTY: TransportDashboard = {
    vehicles: 0, drivers: 0, routes: 0, bus_stops: 0, students_transported: 0, fleet_capacity: 0,
    occupancy_rate: 0, monthly_transport_revenue: 0, active_routes: 0, vehicles_in_maintenance: 0,
    fuel_cost_total: 0, open_incidents: 0, boardings_today: 0,
}

interface IntegrationStatus {
    provider: string
    connected: boolean
    configured: boolean
    capabilities: { key: string; label_fr: string }[]
    message: string
}

export default function TransportDashboardPage() {
    const t = useTranslations("transport")
    const { token } = useAuth()
    const [data, setData] = useState<TransportDashboard>(EMPTY)
    const [integration, setIntegration] = useState<IntegrationStatus | null>(null)

    const load = useCallback(async () => {
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/transport/dashboard`, { headers: { Authorization: `Bearer ${token}` } })
        if (response.ok) setData(await response.json())
        // Future TTransportAI integration status (architecture placeholder —
        // honest "not connected" until the real client ships).
        fetch(`${API_BASE_URL}/transport/integration/status`, { headers: { Authorization: `Bearer ${token}` } })
            .then(r => r.ok ? r.json() : null)
            .then(payload => setIntegration(payload))
            .catch(() => undefined)
    }, [token])

    useEffect(() => { void load() }, [load])

    const metrics = [
        { label: t("dashboard.vehicles"), value: data.vehicles, icon: Bus },
        { label: t("dashboard.drivers"), value: data.drivers, icon: Users },
        { label: t("dashboard.activeRoutes"), value: `${data.active_routes}/${data.routes}`, icon: RouteIcon },
        { label: t("dashboard.busStops"), value: data.bus_stops, icon: MapPin },
        { label: t("dashboard.studentsTransported"), value: data.students_transported, icon: Users },
        { label: t("dashboard.occupancyRate"), value: `${data.occupancy_rate}%`, icon: Gauge },
        { label: t("dashboard.monthlyRevenue"), value: `${data.monthly_transport_revenue.toLocaleString()} FCFA`, icon: Wallet },
        { label: t("dashboard.fleetCapacity"), value: data.fleet_capacity, icon: Bus },
        { label: t("dashboard.inMaintenance"), value: data.vehicles_in_maintenance, icon: Wrench },
        { label: t("dashboard.boardingsToday"), value: data.boardings_today, icon: Users },
        { label: t("dashboard.openIncidents"), value: data.open_incidents, icon: ShieldAlert },
        { label: t("dashboard.fuelCost"), value: `${data.fuel_cost_total.toLocaleString()} FCFA`, icon: Fuel },
    ]

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("dashboard.title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("dashboard.subtitle")}</p>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {metrics.map(metric => (
                    <Card key={metric.label} className="rounded-[20px] border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                        <CardContent className="flex items-center gap-4 pt-6">
                            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#eef1f4] dark:bg-[#343b41]">
                                <metric.icon className="h-5 w-5 text-[#111827] dark:text-white" />
                            </div>
                            <div>
                                <p className="text-xs font-medium text-[#6B7280] dark:text-[#c7d0da]">{metric.label}</p>
                                <p className="mt-1 text-xl font-semibold text-[#111827] dark:text-white">{metric.value}</p>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {integration && (
                <Card className="rounded-[20px] border border-dashed border-[#94A3B8] bg-white shadow-sm dark:border-[#4b5563] dark:bg-[#202528]">
                    <CardContent className="pt-6">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                            <div className="flex items-center gap-3">
                                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#eef1f4] dark:bg-[#343b41]">
                                    <Satellite className="h-5 w-5 text-[#111827] dark:text-white" />
                                </div>
                                <div>
                                    <p className="font-semibold text-[#111827] dark:text-white">Intégration {integration.provider}</p>
                                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{integration.message}</p>
                                </div>
                            </div>
                            <span className={`rounded-full px-3 py-1 text-xs font-medium ${integration.connected ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800 dark:bg-[#3a3125] dark:text-amber-100"}`}>
                                {integration.connected ? "Connectée" : "À venir"}
                            </span>
                        </div>
                        <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-[#6B7280] dark:text-[#c7d0da]">
                            Cette section deviendra le point d&apos;entrée TTransportAI pour :
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2">
                            {integration.capabilities.map(capability => (
                                <span key={capability.key} className="rounded-full border border-[#E5E7EB] px-3 py-1 text-xs text-[#374151] dark:border-[#3b4248] dark:text-[#c7d0da]">
                                    {capability.label_fr}
                                </span>
                            ))}
                        </div>
                        <p className="mt-3 text-xs text-[#94A3B8]">
                            La gestion locale (véhicules, chauffeurs, lignes, arrêts, embarquements, incidents, carburant) reste pleinement fonctionnelle en attendant l&apos;API TTransportAI.
                        </p>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
