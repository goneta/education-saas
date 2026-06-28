"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { Plus, UserPlus } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"
import { Input } from "@/components/ui/input"
import { TeacherListTable, Teacher } from "@/components/teachers/teacher-list-table"
import { AddTeacherModal } from "@/components/teachers/add-teacher-modal"
import { EditTeacherModal } from "@/components/teachers/edit-teacher-modal"
import { DeleteTeacherDialog } from "@/components/teachers/delete-teacher-dialog"

function normalizeTeachers(payload: unknown): Teacher[] {
    if (Array.isArray(payload)) return payload as Teacher[]
    if (payload && typeof payload === "object") {
        const value = payload as { items?: unknown; teachers?: unknown; data?: unknown }
        const rows = value.teachers ?? value.items ?? value.data
        if (Array.isArray(rows)) return rows as Teacher[]
    }
    return []
}

export default function TeachersPage() {
    const { token } = useAuth()
    const [teachers, setTeachers] = useState<Teacher[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [showAddModal, setShowAddModal] = useState(false)
    const [showEditModal, setShowEditModal] = useState(false)
    const [showDeleteDialog, setShowDeleteDialog] = useState(false)
    const [selectedTeacher, setSelectedTeacher] = useState<Teacher | null>(null)
    const [showAssignExisting, setShowAssignExisting] = useState(false)
    const [assignEmail, setAssignEmail] = useState("")
    const [assignBusy, setAssignBusy] = useState(false)
    const [assignMessage, setAssignMessage] = useState<string | null>(null)

    const fetchTeachers = useCallback(async () => {
        if (!token) {
            setError("Vous devez être connecté pour consulter les professeurs.")
            setIsLoading(false)
            return
        }
        setIsLoading(true)
        setError(null)
        try {
            const response = await fetch(`${API_BASE_URL}/teachers`, {
                headers: { Authorization: `Bearer ${token}` },
                cache: "no-store",
            })
            const payload = await response.json().catch(() => null)
            if (!response.ok) {
                if (response.status === 401) throw new Error("Votre session a expiré. Veuillez vous reconnecter.")
                throw new Error(payload?.detail || `Impossible de charger les professeurs (${response.status}).`)
            }
            const rows = normalizeTeachers(payload)
            if (!Array.isArray(payload) && rows.length === 0) throw new Error("La réponse de la liste des professeurs est invalide.")
            setTeachers(rows)
        } catch (reason) {
            setTeachers([])
            setError(reason instanceof Error ? reason.message : "Impossible de charger les professeurs.")
        } finally {
            setIsLoading(false)
        }
    }, [token])

    const assignExistingTeacher = useCallback(async () => {
        if (!token || !assignEmail.trim()) return
        setAssignBusy(true)
        setAssignMessage(null)
        try {
            const lookup = await fetch(`${API_BASE_URL}/teachers/lookup?email=${encodeURIComponent(assignEmail.trim())}`, {
                headers: { Authorization: `Bearer ${token}` },
            })
            const found = await lookup.json().catch(() => null)
            if (!lookup.ok) { setAssignMessage(found?.detail || "Enseignant introuvable."); return }
            if (found.already_in_school) { setAssignMessage(`${found.full_name} enseigne déjà dans cet établissement.`); return }
            const assign = await fetch(`${API_BASE_URL}/teachers/${found.id}/assignments`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({}),
            })
            const payload = await assign.json().catch(() => null)
            if (!assign.ok) { setAssignMessage(payload?.detail || "Affectation impossible."); return }
            setAssignMessage(`${found.full_name} a été affecté(e) à cet établissement.`)
            setAssignEmail("")
            void fetchTeachers()
        } finally {
            setAssignBusy(false)
        }
    }, [token, assignEmail, fetchTeachers])

    useEffect(() => {
        void fetchTeachers()
    }, [fetchTeachers])

    // Universal table filter: column selector + accent/case-insensitive search.
    const filterColumns = useMemo<FilterColumn<Teacher>[]>(() => [
        { key: "name", label: "Nom", accessor: teacher => teacher.full_name },
        { key: "email", label: "Email", accessor: teacher => teacher.email },
        { key: "phone", label: "Téléphone", accessor: teacher => teacher.phone_number },
        { key: "specialization", label: "Spécialité", accessor: teacher => teacher.teacher_profile?.specialization },
    ], [])
    const filter = useTableFilter(teachers, filterColumns, { storageKey: "teachers" })

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">Professeurs</h1>
                    <p className="mt-1 text-sm text-[#6B7280]">Gérez les enseignants, formateurs et leurs affectations.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                    <Button onClick={() => setShowAssignExisting(value => !value)} variant="outline" className="rounded-lg">
                        <UserPlus className="mr-2 h-4 w-4" /> Enseignant existant
                    </Button>
                    <Button onClick={() => setShowAddModal(true)} className="rounded-lg bg-black text-white hover:bg-black/90">
                        <Plus className="mr-2 h-4 w-4" /> Ajouter un professeur
                    </Button>
                </div>
            </div>
            {showAssignExisting && (
                <div className="rounded-lg border border-[#E5E7EB] bg-white p-4 dark:border-[#3b4248] dark:bg-[#202528]">
                    <p className="text-sm font-semibold text-[#111827] dark:text-white">Affecter un enseignant existant à cet établissement</p>
                    <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">Un enseignant déjà présent dans un autre établissement peut enseigner ici en parallèle, sans créer de doublon.</p>
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                        <Input
                            type="email"
                            placeholder="email de l'enseignant"
                            value={assignEmail}
                            onChange={event => setAssignEmail(event.target.value)}
                            className="max-w-xs rounded-lg border border-[#E5E7EB] bg-white text-[#111827] dark:border-[#3b4248] dark:bg-[#252b30] dark:text-[#f4f7fb]"
                        />
                        <Button onClick={assignExistingTeacher} disabled={assignBusy || !assignEmail.trim()} className="rounded-lg bg-black text-white hover:bg-black/90">
                            {assignBusy ? "Affectation..." : "Affecter"}
                        </Button>
                    </div>
                    {assignMessage && <p className="mt-2 text-sm text-[#0F766E] dark:text-[#5eead4]">{assignMessage}</p>}
                </div>
            )}
            <div className="max-w-2xl">
                <TableFilter {...filter.controls} />
            </div>
            <TeacherListTable
                teachers={filter.filtered}
                isLoading={isLoading}
                error={error}
                searchQuery=""
                onEdit={teacher => { setSelectedTeacher(teacher); setShowEditModal(true) }}
                onDelete={id => {
                    const teacher = teachers.find(item => item.id === id)
                    if (teacher) {
                        setSelectedTeacher(teacher)
                        setShowDeleteDialog(true)
                    }
                }}
                onPhotoChanged={fetchTeachers}
            />
            <AddTeacherModal open={showAddModal} onOpenChange={setShowAddModal} onSuccess={fetchTeachers} />
            <EditTeacherModal open={showEditModal} onOpenChange={setShowEditModal} teacher={selectedTeacher} onSuccess={fetchTeachers} />
            <DeleteTeacherDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog} teacher={selectedTeacher} onSuccess={fetchTeachers} />
        </div>
    )
}
