"use client"

import { useCallback, useEffect, useState } from "react"
import { Bus, Users, Route as RouteIcon, Gauge, Wallet, Wrench } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent } from "@/components/ui/card"

interface TransportDashboard {
    vehicles: number
    drivers: number
    routes: number
    students_transported: number
    fleet_capacity: number
    occupancy_rate: number
    monthly_transport_revenue: number
    active_routes: number
    vehicles_in_maintenance: number
}

const EMPTY: TransportDashboard = {
    vehicles: 0, drivers: 0, routes: 0, students_transported: 0, fleet_capacity: 0,
    occupancy_rate: 0, monthly_transport_revenue: 0, active_routes: 0, vehicles_in_maintenance: 0,
}

export default function TransportDashboardPage() {
    const { token } = useAuth()
    const [data, setData] = useState<TransportDashboard>(EMPTY)

    const load = useCallback(async () => {
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/transport/dashboard`, { headers: { Authorization: `Bearer ${token}` } })
        if (response.ok) setData(await response.json())
    }, [token])

    useEffect(() => { void load() }, [load])

    const metrics = [
        { label: "Véhicules", value: data.vehicles, icon: Bus },
        { label: "Chauffeurs", value: data.drivers, icon: Users },
        { label: "Trajets actifs", value: `${data.active_routes}/${data.routes}`, icon: RouteIcon },
        { label: "Élèves transportés", value: data.students_transported, icon: Users },
        { label: "Taux d'occupation", value: `${data.occupancy_rate}%`, icon: Gauge },
        { label: "Recettes transport / mois", value: `${data.monthly_transport_revenue.toLocaleString()} FCFA`, icon: Wallet },
        { label: "Capacité de la flotte", value: data.fleet_capacity, icon: Bus },
        { label: "En maintenance", value: data.vehicles_in_maintenance, icon: Wrench },
    ]

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">Smart Transport</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">
                    Vue d&apos;ensemble de la flotte, des chauffeurs, des trajets et des affectations élèves — source unique de données, intégrée à la facturation et aux dossiers élèves.
                </p>
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
        </div>
    )
}
