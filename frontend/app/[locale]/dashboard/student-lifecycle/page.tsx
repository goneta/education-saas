"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import { Archive, ArrowRightLeft, FileUp, LockKeyhole, RefreshCw } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type Transfer = {
    id: number
    global_student_number: string
    student_name: string
    from_school_id: number
    to_school_id: number
    status: string
}

export default function StudentLifecycleAdministrationPage() {
    const { token } = useAuth()
    const [transfers, setTransfers] = useState<Transfer[]>([])
    const [message, setMessage] = useState("")
    const [error, setError] = useState("")
    const [importFile, setImportFile] = useState<File | null>(null)
    const [importPreview, setImportPreview] = useState<{ batch_id: number; rows: unknown[]; errors: unknown[]; duplicate_count: number } | null>(null)
    const [yearId, setYearId] = useState("")
    const [confirmation, setConfirmation] = useState("")
    const [transferForm, setTransferForm] = useState({ student_global_profile_id: "", from_enrollment_id: "", to_school_model_assignment_id: "", to_academic_year_id: "" })
    const [enrollmentForm, setEnrollmentForm] = useState({ student_global_profile_id: "", school_model_assignment_id: "", academic_year_id: "", enrollment_type: "part_time", schedule_type: "evening", start_time: "", end_time: "", days_of_week: "monday,tuesday" })

    const authHeaders = useCallback(() => ({ Authorization: `Bearer ${token}` }), [token])
    const loadTransfers = useCallback(async () => {
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/student-lifecycle/transfers`, { headers: authHeaders(), cache: "no-store" })
        if (response.ok) setTransfers(await response.json())
    }, [authHeaders, token])

    useEffect(() => { void loadTransfers() }, [loadTransfers])

    const decide = async (id: number, decision: "approved" | "rejected" | "completed") => {
        setError("")
        const response = await fetch(`${API_BASE_URL}/student-lifecycle/transfers/${id}/decision`, {
            method: "POST",
            headers: { ...authHeaders(), "Content-Type": "application/json" },
            body: JSON.stringify({ decision }),
        })
        const payload = await response.json()
        if (!response.ok) setError(typeof payload.detail === "string" ? payload.detail : "Action refusée.")
        else {
            setMessage(`Transfert ${decision}.`)
            void loadTransfers()
        }
    }

    const previewImport = async (event: FormEvent) => {
        event.preventDefault()
        if (!importFile) return
        const form = new FormData()
        form.append("file", importFile)
        const response = await fetch(`${API_BASE_URL}/student-lifecycle/imports/preview`, {
            method: "POST",
            headers: authHeaders(),
            body: form,
        })
        const payload = await response.json()
        if (!response.ok) setError(payload.detail || "Prévisualisation impossible.")
        else setImportPreview(payload)
    }

    const commitImport = async () => {
        if (!importPreview) return
        const response = await fetch(`${API_BASE_URL}/student-lifecycle/imports/commit`, {
            method: "POST",
            headers: { ...authHeaders(), "Content-Type": "application/json" },
            body: JSON.stringify({ batch_id: importPreview.batch_id, confirm: true }),
        })
        const payload = await response.json()
        if (!response.ok) setError(payload.detail || "Import impossible.")
        else {
            setMessage(`${payload.created_profiles} profil(s) créé(s), ${payload.linked_existing} profil(s) existant(s) réutilisé(s).`)
            setImportPreview(null)
        }
    }

    const closeYear = async (event: FormEvent) => {
        event.preventDefault()
        const response = await fetch(`${API_BASE_URL}/student-lifecycle/academic-years/${yearId}/close`, {
            method: "POST",
            headers: { ...authHeaders(), "Content-Type": "application/json" },
            body: JSON.stringify({ confirmation }),
        })
        const payload = await response.json()
        if (!response.ok) setError(payload.detail || "Clôture impossible.")
        else {
            setMessage("Année académique clôturée. Ses données sont désormais en lecture seule.")
            setConfirmation("")
        }
    }

    const requestTransfer = async (event: FormEvent) => {
        event.preventDefault()
        const response = await fetch(`${API_BASE_URL}/student-lifecycle/transfers`, {
            method: "POST",
            headers: { ...authHeaders(), "Content-Type": "application/json" },
            body: JSON.stringify(Object.fromEntries(Object.entries(transferForm).map(([key, value]) => [key, Number(value)]))),
        })
        const payload = await response.json()
        if (!response.ok) setError(payload.detail || "Demande de transfert impossible.")
        else {
            setMessage("Demande de transfert créée sans dupliquer le profil élève.")
            void loadTransfers()
        }
    }

    const createConcurrentEnrollment = async (event: FormEvent) => {
        event.preventDefault()
        const response = await fetch(`${API_BASE_URL}/student-lifecycle/enrollments`, {
            method: "POST",
            headers: { ...authHeaders(), "Content-Type": "application/json" },
            body: JSON.stringify({
                student_global_profile_id: Number(enrollmentForm.student_global_profile_id),
                school_model_assignment_id: Number(enrollmentForm.school_model_assignment_id),
                academic_year_id: Number(enrollmentForm.academic_year_id),
                enrollment_type: enrollmentForm.enrollment_type,
                schedule_type: enrollmentForm.schedule_type,
                allows_concurrent_enrollment: true,
                primary_enrollment: false,
                start_time: enrollmentForm.start_time || null,
                end_time: enrollmentForm.end_time || null,
                days_of_week: enrollmentForm.days_of_week.split(",").map(value => value.trim()).filter(Boolean),
            }),
        })
        const payload = await response.json()
        if (!response.ok) {
            const detail = typeof payload.detail === "string" ? payload.detail : payload.detail?.message
            setError(detail || "Inscription impossible ou conflit d'horaires détecté.")
        } else setMessage("Inscription simultanée créée dans son contexte isolé.")
    }

    const transferColumns = useMemo<FilterColumn<Transfer>[]>(() => [
        { key: "student", label: "Élève", accessor: transfer => transfer.student_name },
        { key: "number", label: "Numéro élève", accessor: transfer => transfer.global_student_number },
        { key: "status", label: "Statut", accessor: transfer => transfer.status },
    ], [])
    const transferFilter = useTableFilter(transfers, transferColumns, { storageKey: "transfers" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-950 dark:text-white">Parcours scolaire et transferts</h1>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-300">Gérez les profils globaux, transferts, imports et clôtures sans dupliquer les élèves.</p>
            </div>
            {message && <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-4 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-100">{message}</div>}
            {error && <div className="rounded-xl border border-red-300 bg-red-50 p-4 text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-100">{error}</div>}

            <div className="grid gap-6 xl:grid-cols-2">
                <Card className="border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
                    <CardHeader><CardTitle className="text-base text-slate-950 dark:text-white">Demander un transfert</CardTitle></CardHeader>
                    <CardContent>
                        <form onSubmit={requestTransfer} className="grid gap-3 sm:grid-cols-2">
                            <Field placeholder="ID profil global" value={transferForm.student_global_profile_id} onChange={value => setTransferForm({ ...transferForm, student_global_profile_id: value })} />
                            <Field placeholder="ID inscription source" value={transferForm.from_enrollment_id} onChange={value => setTransferForm({ ...transferForm, from_enrollment_id: value })} />
                            <Field placeholder="ID modèle destination" value={transferForm.to_school_model_assignment_id} onChange={value => setTransferForm({ ...transferForm, to_school_model_assignment_id: value })} />
                            <Field placeholder="ID année destination" value={transferForm.to_academic_year_id} onChange={value => setTransferForm({ ...transferForm, to_academic_year_id: value })} />
                            <Button type="submit" className="sm:col-span-2">Créer la demande</Button>
                        </form>
                    </CardContent>
                </Card>
                <Card className="border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
                    <CardHeader><CardTitle className="text-base text-slate-950 dark:text-white">Inscription simultanée</CardTitle></CardHeader>
                    <CardContent>
                        <form onSubmit={createConcurrentEnrollment} className="grid gap-3 sm:grid-cols-2">
                            <Field placeholder="ID profil global" value={enrollmentForm.student_global_profile_id} onChange={value => setEnrollmentForm({ ...enrollmentForm, student_global_profile_id: value })} />
                            <Field placeholder="ID modèle scolaire" value={enrollmentForm.school_model_assignment_id} onChange={value => setEnrollmentForm({ ...enrollmentForm, school_model_assignment_id: value })} />
                            <Field placeholder="ID année académique" value={enrollmentForm.academic_year_id} onChange={value => setEnrollmentForm({ ...enrollmentForm, academic_year_id: value })} />
                            <select value={enrollmentForm.enrollment_type} onChange={event => setEnrollmentForm({ ...enrollmentForm, enrollment_type: event.target.value })} className="rounded-lg border border-slate-300 bg-white p-3 dark:border-slate-700 dark:bg-slate-950">
                                <option value="part_time">Temps partiel</option><option value="module">Module</option><option value="certification">Certification</option><option value="evening_course">Cours du soir</option><option value="weekend_course">Weekend</option><option value="internship">Stage</option>
                            </select>
                            <input type="time" value={enrollmentForm.start_time} onChange={event => setEnrollmentForm({ ...enrollmentForm, start_time: event.target.value })} className="rounded-lg border border-slate-300 bg-white p-3 dark:border-slate-700 dark:bg-slate-950" />
                            <input type="time" value={enrollmentForm.end_time} onChange={event => setEnrollmentForm({ ...enrollmentForm, end_time: event.target.value })} className="rounded-lg border border-slate-300 bg-white p-3 dark:border-slate-700 dark:bg-slate-950" />
                            <input value={enrollmentForm.days_of_week} onChange={event => setEnrollmentForm({ ...enrollmentForm, days_of_week: event.target.value })} placeholder="monday,tuesday" className="rounded-lg border border-slate-300 bg-white p-3 sm:col-span-2 dark:border-slate-700 dark:bg-slate-950" />
                            <Button type="submit" className="sm:col-span-2">Vérifier et inscrire</Button>
                        </form>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
                <CardHeader className="flex-row items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base text-slate-950 dark:text-white"><ArrowRightLeft className="h-4 w-4" /> Demandes de transfert</CardTitle>
                    <Button variant="ghost" size="sm" onClick={() => void loadTransfers()} title="Actualiser"><RefreshCw className="h-4 w-4" /></Button>
                </CardHeader>
                <CardContent className="overflow-x-auto">
                    <div className="mb-4 max-w-2xl">
                        <TableFilter {...transferFilter.controls} />
                    </div>
                    <table className="w-full min-w-[760px] text-sm">
                        <thead><tr className="border-b border-slate-200 text-left text-slate-500 dark:border-slate-700 dark:text-slate-300">
                            <th className="p-3">Élève</th><th className="p-3">Source</th><th className="p-3">Destination</th><th className="p-3">Statut</th><th className="p-3">Actions</th>
                        </tr></thead>
                        <tbody>{transferFilter.filtered.map(transfer => (
                            <tr key={transfer.id} className="border-b border-slate-200 dark:border-slate-700">
                                <td className="p-3"><strong>{transfer.student_name}</strong><br /><span className="text-xs text-slate-500">{transfer.global_student_number}</span></td>
                                <td className="p-3">Établissement #{transfer.from_school_id}</td>
                                <td className="p-3">Établissement #{transfer.to_school_id}</td>
                                <td className="p-3">{transfer.status}</td>
                                <td className="flex gap-2 p-3">
                                    {transfer.status === "pending" && <Button size="sm" onClick={() => void decide(transfer.id, "approved")}>Approuver</Button>}
                                    {transfer.status === "approved" && <Button size="sm" onClick={() => void decide(transfer.id, "completed")}>Finaliser</Button>}
                                    {transfer.status === "pending" && <Button size="sm" variant="outline" onClick={() => void decide(transfer.id, "rejected")}>Refuser</Button>}
                                </td>
                            </tr>
                        ))}</tbody>
                    </table>
                    {transferFilter.filtered.length === 0 && <p className="py-8 text-center text-slate-500 dark:text-slate-300">Aucune demande de transfert.</p>}
                </CardContent>
            </Card>

            <div className="grid gap-6 lg:grid-cols-2">
                <Card className="border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
                    <CardHeader><CardTitle className="flex items-center gap-2 text-base text-slate-950 dark:text-white"><FileUp className="h-4 w-4" /> Import élèves</CardTitle></CardHeader>
                    <CardContent>
                        <form onSubmit={previewImport} className="space-y-3">
                            <p className="text-sm text-slate-500 dark:text-slate-300">Formats : CSV, Excel, JSON, XML ou Markdown. Le système prévisualise et détecte les doublons avant toute écriture.</p>
                            <input type="file" accept=".csv,.xlsx,.json,.xml,.md,.markdown" onChange={event => setImportFile(event.target.files?.[0] || null)} className="block w-full rounded-lg border border-slate-300 p-3 text-sm dark:border-slate-700 dark:bg-slate-950" />
                            <Button type="submit">Prévisualiser</Button>
                        </form>
                        {importPreview && (
                            <div className="mt-4 rounded-lg border border-slate-200 p-4 dark:border-slate-700">
                                <p>{importPreview.rows.length} ligne(s) valide(s), {importPreview.duplicate_count} doublon(s), {importPreview.errors.length} erreur(s).</p>
                                <Button className="mt-3" onClick={() => void commitImport()}>Confirmer l&apos;import transactionnel</Button>
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card className="border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
                    <CardHeader><CardTitle className="flex items-center gap-2 text-base text-slate-950 dark:text-white"><LockKeyhole className="h-4 w-4" /> Clôturer une année</CardTitle></CardHeader>
                    <CardContent>
                        <form onSubmit={closeYear} className="space-y-3">
                            <p className="text-sm text-slate-500 dark:text-slate-300">La clôture rend les données historiques non modifiables, sauf autorisation temporaire du Super Administrateur.</p>
                            <input value={yearId} onChange={event => setYearId(event.target.value)} type="number" required placeholder="ID de l'année académique" className="w-full rounded-lg border border-slate-300 bg-white p-3 dark:border-slate-700 dark:bg-slate-950" />
                            <input value={confirmation} onChange={event => setConfirmation(event.target.value)} required placeholder="Saisissez CLOTURER" className="w-full rounded-lg border border-slate-300 bg-white p-3 dark:border-slate-700 dark:bg-slate-950" />
                            <Button type="submit" className="gap-2"><Archive className="h-4 w-4" /> Clôturer l&apos;année</Button>
                        </form>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

function Field({ placeholder, value, onChange }: { placeholder: string; value: string; onChange: (value: string) => void }) {
    return <input type="number" required placeholder={placeholder} value={value} onChange={event => onChange(event.target.value)} className="rounded-lg border border-slate-300 bg-white p-3 dark:border-slate-700 dark:bg-slate-950" />
}
