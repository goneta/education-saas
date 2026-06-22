"use client"

import { useCallback, useEffect, useState } from "react"
import { Plus, Search } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Button } from "@/components/ui/button"
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
    const [searchQuery, setSearchQuery] = useState("")
    const [error, setError] = useState<string | null>(null)
    const [showAddModal, setShowAddModal] = useState(false)
    const [showEditModal, setShowEditModal] = useState(false)
    const [showDeleteDialog, setShowDeleteDialog] = useState(false)
    const [selectedTeacher, setSelectedTeacher] = useState<Teacher | null>(null)

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

    useEffect(() => {
        void fetchTeachers()
    }, [fetchTeachers])

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">Professeurs</h1>
                    <p className="mt-1 text-sm text-[#6B7280]">Gérez les enseignants, formateurs et leurs affectations.</p>
                </div>
                <Button onClick={() => setShowAddModal(true)} className="rounded-lg bg-black text-white hover:bg-black/90">
                    <Plus className="mr-2 h-4 w-4" /> Ajouter un professeur
                </Button>
            </div>
            <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6B7280]" />
                <Input
                    type="search"
                    placeholder="Rechercher un professeur..."
                    value={searchQuery}
                    onChange={event => setSearchQuery(event.target.value)}
                    className="w-full rounded-lg border border-[#E5E7EB] bg-white py-2 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] dark:border-[#3b4248] dark:bg-[#202528] dark:text-[#f4f7fb]"
                />
            </div>
            <TeacherListTable
                teachers={teachers}
                isLoading={isLoading}
                error={error}
                searchQuery={searchQuery}
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
