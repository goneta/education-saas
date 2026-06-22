"use client"

import { useEffect, useState } from "react"
import { BookOpen, Building2, Download, LockKeyhole, Route, WalletCards } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type Enrollment = {
    id: number
    school_name: string
    model_name: string
    academic_year_name: string
    class_name?: string | null
    program_name?: string | null
    enrollment_status: string
    enrollment_type: string
    schedule_type: string
    primary_enrollment: boolean
    read_only: boolean
    lock_status: string
    academic_summary: { grades: number; attendance_records: number; internships: number }
    financial?: { invoice_count: number; amount_due: number; amount_paid: number; remaining_balance: number } | null
}

type Journey = {
    global_student_number: string
    full_name: string
    enrollments: Enrollment[]
    transfers: Array<{ id: number; from_school_id: number; to_school_id: number; status: string; created_at: string }>
}

export function StudentJourney({ studentUserId }: { studentUserId: string }) {
    const { token } = useAuth()
    const [journey, setJourney] = useState<Journey | null>(null)
    const [error, setError] = useState("")

    useEffect(() => {
        if (!token) return
        fetch(`${API_BASE_URL}/student-lifecycle/students/${studentUserId}`, {
            headers: { Authorization: `Bearer ${token}` },
            cache: "no-store",
        })
            .then(async response => {
                const payload = await response.json()
                if (!response.ok) throw new Error(payload.detail || "Impossible de charger le parcours scolaire.")
                return payload
            })
            .then(setJourney)
            .catch(reason => setError(reason instanceof Error ? reason.message : "Erreur de chargement."))
    }, [studentUserId, token])

    const download = async (format: string) => {
        const response = await fetch(`${API_BASE_URL}/student-lifecycle/students/${studentUserId}/export?format=${format}`, {
            headers: { Authorization: `Bearer ${token}` },
        })
        if (!response.ok) {
            setError("Impossible d'exporter ce parcours avec vos permissions actuelles.")
            return
        }
        const blob = await response.blob()
        const href = URL.createObjectURL(blob)
        const anchor = document.createElement("a")
        anchor.href = href
        anchor.download = `parcours-eleve.${format === "markdown" ? "md" : format}`
        anchor.click()
        URL.revokeObjectURL(href)
    }

    if (error) return <div className="rounded-xl border border-red-300 bg-red-50 p-4 text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-100">{error}</div>
    if (!journey) return <div className="py-8 text-center text-slate-500 dark:text-slate-300">Chargement du parcours scolaire...</div>

    return (
        <div className="space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <p className="text-sm text-slate-500 dark:text-slate-300">Numéro élève global</p>
                    <p className="font-semibold text-slate-950 dark:text-white">{journey.global_student_number}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                    {["pdf", "csv", "xlsx", "markdown", "xml"].map(format => (
                        <Button key={format} variant="outline" size="sm" onClick={() => download(format)} className="gap-2">
                            <Download className="h-4 w-4" /> {format.toUpperCase()}
                        </Button>
                    ))}
                </div>
            </div>

            <div className="space-y-4">
                {journey.enrollments.map((enrollment, index) => (
                    <Card key={enrollment.id} className="border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
                        <CardHeader className="pb-3">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                                <div>
                                    <CardTitle className="flex items-center gap-2 text-base text-slate-950 dark:text-white">
                                        <Building2 className="h-4 w-4" />
                                        {enrollment.academic_year_name} · {enrollment.school_name}
                                    </CardTitle>
                                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">
                                        {enrollment.model_name} · {enrollment.class_name || "Classe non affectée"}
                                        {enrollment.program_name ? ` · ${enrollment.program_name}` : ""}
                                    </p>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {index === 0 || enrollment.primary_enrollment ? <Badge text="Inscription principale" /> : <Badge text="Inscription secondaire" />}
                                    <Badge text={enrollment.enrollment_type.replaceAll("_", " ")} />
                                    {enrollment.read_only && <Badge text="Lecture seule · année clôturée" locked />}
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                                <Metric icon={BookOpen} label="Notes" value={enrollment.academic_summary.grades} />
                                <Metric icon={Route} label="Présences" value={enrollment.academic_summary.attendance_records} />
                                <Metric icon={LockKeyhole} label="Stages" value={enrollment.academic_summary.internships} />
                                {enrollment.financial ? (
                                    <Metric icon={WalletCards} label="Solde local" value={`${enrollment.financial.remaining_balance.toLocaleString()} FCFA`} />
                                ) : (
                                    <Metric icon={WalletCards} label="Finance" value="Masquée pour cet établissement" />
                                )}
                            </div>
                        </CardContent>
                    </Card>
                ))}
                {journey.enrollments.length === 0 && (
                    <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-500 dark:border-slate-700 dark:text-slate-300">
                        Aucune inscription historisée.
                    </div>
                )}
            </div>

            <Card className="border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
                <CardHeader><CardTitle className="text-base text-slate-950 dark:text-white">Historique des transferts</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                    {journey.transfers.map(transfer => (
                        <div key={transfer.id} className="flex flex-wrap justify-between gap-2 border-b border-slate-200 py-2 text-sm last:border-0 dark:border-slate-700">
                            <span>Établissement #{transfer.from_school_id} vers #{transfer.to_school_id}</span>
                            <span className="font-medium">{transfer.status}</span>
                        </div>
                    ))}
                    {journey.transfers.length === 0 && <p className="text-sm text-slate-500 dark:text-slate-300">Aucun transfert enregistré.</p>}
                </CardContent>
            </Card>
        </div>
    )
}

function Badge({ text, locked = false }: { text: string; locked?: boolean }) {
    return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${locked ? "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-100" : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-100"}`}>{text}</span>
}

function Metric({ icon: Icon, label, value }: { icon: typeof BookOpen; label: string; value: string | number }) {
    return (
        <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-300"><Icon className="h-4 w-4" /> {label}</div>
            <p className="mt-2 text-sm font-semibold text-slate-950 dark:text-white">{value}</p>
        </div>
    )
}
