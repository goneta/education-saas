"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Eye, Plus, Route, Search } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AddStudentModal } from "@/components/students/add-student-modal"
import { EditStudentModal } from "@/components/students/edit-student-modal"
import { DeleteStudentDialog } from "@/components/students/delete-student-dialog"
import { ProfileAvatar } from "@/components/users/profile-avatar"

interface StudentProfile {
    registration_number: string
    date_of_birth: string
    gender: string
    student_address: string
    parent_name: string
    parent_phone: string
    parent_email: string | null
    parent_address: string
    current_class_id: number | null
}

interface Student {
    id: number
    email: string
    full_name: string
    role: string
    school_id: number
    is_active: boolean
    profile_photo_url?: string | null
    student_profile: StudentProfile
}

function normalizeStudents(payload: unknown): Student[] {
    if (Array.isArray(payload)) return payload as Student[]
    if (payload && typeof payload === "object") {
        const value = payload as { items?: unknown; students?: unknown; data?: unknown }
        const rows = value.students ?? value.items ?? value.data
        if (Array.isArray(rows)) return rows as Student[]
    }
    return []
}

export default function StudentsPage() {
    const { token } = useAuth()
    const params = useParams()
    const router = useRouter()
    const locale = params.locale as string
    const [searchQuery, setSearchQuery] = useState("")
    const [showAddModal, setShowAddModal] = useState(false)
    const [showEditModal, setShowEditModal] = useState(false)
    const [showDeleteDialog, setShowDeleteDialog] = useState(false)
    const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
    const [students, setStudents] = useState<Student[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchStudents = useCallback(async () => {
        if (!token) {
            setError("Vous devez être connecté pour consulter les élèves.")
            setIsLoading(false)
            return
        }
        setIsLoading(true)
        setError(null)
        try {
            const response = await fetch(`${API_BASE_URL}/students`, {
                headers: { Authorization: `Bearer ${token}` },
                cache: "no-store",
            })
            const payload = await response.json().catch(() => null)
            if (!response.ok) {
                if (response.status === 401) throw new Error("Votre session a expiré. Veuillez vous reconnecter.")
                throw new Error(payload?.detail || `Impossible de charger les élèves (${response.status}).`)
            }
            const rows = normalizeStudents(payload)
            if (!Array.isArray(payload) && rows.length === 0) throw new Error("La réponse de la liste des élèves est invalide.")
            setStudents(rows)
        } catch (reason) {
            setStudents([])
            setError(reason instanceof Error ? reason.message : "Impossible de charger les élèves.")
        } finally {
            setIsLoading(false)
        }
    }, [token])

    useEffect(() => {
        void fetchStudents()
    }, [fetchStudents])

    const filteredStudents = useMemo(() => {
        const query = searchQuery.trim().toLowerCase()
        if (!query) return students
        return students.filter(student =>
            student.full_name.toLowerCase().includes(query) ||
            student.email.toLowerCase().includes(query) ||
            (student.student_profile?.registration_number || "").toLowerCase().includes(query)
        )
    }, [searchQuery, students])

    const openStudent = (studentId: number) => router.push(`/${locale}/dashboard/students/${studentId}`)

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">Élèves</h1>
                    <p className="mt-1 text-sm text-[#6B7280]">Gérez les inscriptions, dossiers et profils des élèves.</p>
                </div>
                <div className="flex flex-wrap gap-2">
                <Button variant="outline" onClick={() => router.push(`/${locale}/dashboard/student-lifecycle`)} className="gap-2">
                    <Route className="h-4 w-4" /> Parcours et transferts
                </Button>
                <Button onClick={() => setShowAddModal(true)} className="rounded-lg bg-black text-white hover:bg-black/90">
                    <Plus className="mr-2 h-4 w-4" /> Ajouter un élève
                </Button>
                </div>
            </div>

            <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6B7280]" />
                <input
                    type="search"
                    placeholder="Rechercher un élève..."
                    value={searchQuery}
                    onChange={event => setSearchQuery(event.target.value)}
                    className="w-full rounded-lg border border-[#E5E7EB] bg-white py-2 pl-10 pr-4 text-[#111827] placeholder:text-[#6B7280] focus:border-transparent focus:outline-none focus:ring-2 focus:ring-primary dark:border-[#3b4248] dark:bg-[#202528] dark:text-[#f4f7fb]"
                />
            </div>

            {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-800 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <Card data-teducai-collapsible="false" className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="text-[#111827]">Liste des élèves ({filteredStudents.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <p className="py-12 text-center text-[#6B7280]">Chargement des élèves...</p>
                    ) : filteredStudents.length === 0 ? (
                        <p className="py-12 text-center text-[#6B7280]">
                            {searchQuery ? `Aucun élève ne correspond à « ${searchQuery} ».` : "Aucun élève trouvé. Ajoutez votre premier élève."}
                        </p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-[#E5E7EB]">
                                        {["Nom", "Email", "Matricule", "Genre", "Statut", "Actions"].map(label => (
                                            <th key={label} className="px-4 py-3 text-left text-sm font-medium text-[#6B7280]">{label}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredStudents.map(student => (
                                        <tr key={student.id} onClick={() => openStudent(student.id)} className="cursor-pointer border-b border-[#E5E7EB] transition-colors last:border-0 hover:bg-[#F6F7F9]">
                                            <td className="px-4 py-3 text-sm font-medium text-[#111827] dark:text-[#f4f7fb]">
                                                <div className="flex items-center gap-3">
                                                    <ProfileAvatar userId={student.id} name={student.full_name} photoUrl={student.profile_photo_url} onChanged={fetchStudents} />
                                                    <span>{student.full_name}</span>
                                                </div>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-[#6B7280]">{student.email}</td>
                                            <td className="px-4 py-3 text-sm text-[#6B7280]">{student.student_profile?.registration_number || "-"}</td>
                                            <td className="px-4 py-3 text-sm text-[#6B7280]">{student.student_profile?.gender || "-"}</td>
                                            <td className="px-4 py-3">
                                                <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${student.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}>
                                                    {student.is_active ? "Actif" : "Inactif"}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3" onClick={event => event.stopPropagation()}>
                                                <div className="flex gap-2">
                                                    <Button variant="ghost" size="sm" onClick={() => openStudent(student.id)} title="Afficher les détails"><Eye className="h-4 w-4" /></Button>
                                                    <Button variant="ghost" size="sm" onClick={() => { setSelectedStudent(student); setShowEditModal(true) }}>Modifier</Button>
                                                    <Button variant="ghost" size="sm" className="text-red-600" onClick={() => { setSelectedStudent(student); setShowDeleteDialog(true) }}>Supprimer</Button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>

            <AddStudentModal open={showAddModal} onOpenChange={setShowAddModal} onSuccess={fetchStudents} />
            <EditStudentModal open={showEditModal} onOpenChange={setShowEditModal} student={selectedStudent} onSuccess={fetchStudents} />
            <DeleteStudentDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog} student={selectedStudent} onSuccess={fetchStudents} />
        </div>
    )
}
