"use client"

// Smart Transport → Transport Externe : la section dédiée aux établissements
// SANS flotte interne, qui dépendent de sociétés de transport externes. C'est
// le point d'entrée de la future intégration TTransportAI (architecture
// seulement — voir services/ttransport_gateway.py; rien n'est simulé).

import { useCallback, useEffect, useState } from "react"
import { Bus, CheckCircle2, Satellite } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface IntegrationStatus {
    provider: string
    connected: boolean
    configured: boolean
    capabilities: { key: string; label_fr: string }[]
    message: string
}

export default function ExternalTransportPage() {
    const { token } = useAuth()
    const [status, setStatus] = useState<IntegrationStatus | null>(null)

    const load = useCallback(async () => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/transport/integration/status`, { headers: { Authorization: `Bearer ${token}` } })
        if (res.ok) setStatus(await res.json())
    }, [token])

    useEffect(() => { void load() }, [load])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">Transport Externe</h1>
                <p className="mt-1 max-w-3xl text-sm text-[#6B7280] dark:text-[#c7d0da]">
                    Pour les établissements qui n&apos;opèrent pas leur propre flotte et s&apos;appuient sur des sociétés de
                    transport externes. Cette section deviendra le point d&apos;entrée de l&apos;application <strong>TTransportAI</strong>,
                    qui pilotera l&apos;intégralité du transport scolaire externalisé.
                </p>
            </div>

            <Card className="rounded-[20px] border border-dashed border-[#94A3B8] bg-white shadow-sm dark:border-[#4b5563] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-3">
                        <Satellite className="h-5 w-5" /> Intégration {status?.provider || "TTransportAI"}
                        <span className={`rounded-full px-3 py-1 text-xs font-medium ${status?.connected ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800 dark:bg-[#3a3125] dark:text-amber-100"}`}>
                            {status?.connected ? "Connectée" : "À venir"}
                        </span>
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{status?.message || "Chargement du statut d'intégration…"}</p>
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-[#6B7280] dark:text-[#c7d0da]">
                            Capacités qui seront pilotées via TTransportAI :
                        </p>
                        <ul className="mt-2 grid gap-2 sm:grid-cols-2">
                            {(status?.capabilities || []).map(capability => (
                                <li key={capability.key} className="flex items-center gap-2 rounded-lg border border-[#E5E7EB] px-3 py-2 text-sm dark:border-[#3b4248]">
                                    <CheckCircle2 className="h-4 w-4 text-[#94A3B8]" /> {capability.label_fr}
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="rounded-lg bg-[#F6F7F9] px-4 py-3 text-sm text-[#6B7280] dark:bg-[#2a3035] dark:text-[#c7d0da]">
                        <p className="flex items-center gap-2"><Bus className="h-4 w-4" /> En attendant l&apos;API TTransportAI :</p>
                        <ul className="ml-6 mt-1 list-disc space-y-1">
                            <li>les établissements avec flotte interne utilisent les menus Smart Transport existants (véhicules, chauffeurs, lignes, arrêts, embarquements…) ;</li>
                            <li>les abonnements et paiements de transport passent déjà par le module Finance (Payment Service centralisé) ;</li>
                            <li>aucune donnée n&apos;est simulée : le statut ci-dessus reflète honnêtement l&apos;état réel de l&apos;intégration.</li>
                        </ul>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
