"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter, useParams } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"
import { requestConfirmation } from "@/lib/confirmation"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Pencil, Trash2, Plus, Eye, Printer, Users, X } from "lucide-react"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

interface ClassItem {
    id: number
    name: string
    level: string
    main_teacher_id?: number
}

interface TeacherOption {
    id: number
    full_name: string
}

interface RosterRow {
    student_user_id: number
    full_name: string
    registration_number: string
    parent_name: string
    parent_phone: string
    expected: number
    paid: number
    remaining: number
    has_finance_record: boolean
    reason?: string
}

interface Roster {
    class: { id: number; name: string; level: string }
    students: RosterRow[]
    anomalies: RosterRow[]
}

export default function ClassesPage() {
    const { token } = useAuth()
    const [classes, setClasses] = useState<ClassItem[]>([])
    const [teachers, setTeachers] = useState<TeacherOption[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [isDialogOpen, setIsDialogOpen] = useState(false)
    const [currentClass, setCurrentClass] = useState<ClassItem | null>(null)
    const [formData, setFormData] = useState<{ name: string, level: string, main_teacher_id: string | null }>({ name: "", level: "", main_teacher_id: null })
    const [roster, setRoster] = useState<Roster | null>(null)
    const router = useRouter()
    const params = useParams()
    const locale = (params?.locale as string) || "fr"
    const [studentCounts, setStudentCounts] = useState<Record<number, number>>({})
    const [studentsModal, setStudentsModal] = useState<{ cls: ClassItem; students: { id: number; user_id: number; full_name: string; age: number | null; gender?: string | null }[] } | null>(null)

    const openStudents = async (cls: ClassItem) => {
        const res = await fetch(`${API_BASE_URL}/education/classes/${cls.id}/students`, { headers: { Authorization: `Bearer ${token}` } })
        if (res.ok) setStudentsModal({ cls, students: (await res.json()).students })
    }

    useEffect(() => {
        if (token) {
            fetchClasses()
            fetchTeachers()
        }
    // Initial metadata load is intentionally bound to the auth token.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token])

    const fetchTeachers = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/teachers`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) {
                setTeachers(await res.json())
            }
        } catch (error) {
            console.error(error)
        }
    }

    const fetchClasses = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/education/classes`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) {
                const data: ClassItem[] = await res.json()
                setClasses(data)
                // Nb Élèves per class (#1/#6).
                const counts = await Promise.all(data.map(async cls => {
                    const r = await fetch(`${API_BASE_URL}/education/classes/${cls.id}/students`, { headers: { Authorization: `Bearer ${token}` } })
                    return [cls.id, r.ok ? (await r.json()).count : 0] as const
                }))
                setStudentCounts(Object.fromEntries(counts))
            }
        } catch (error) {
            console.error("Failed to fetch classes", error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const url = currentClass
                ? `${API_BASE_URL}/education/classes/${currentClass.id}`
                : `${API_BASE_URL}/education/classes`

            const method = currentClass ? "PUT" : "POST"


            // Convert main_teacher_id to number if present
            const payload = {
                ...formData,
                main_teacher_id: formData.main_teacher_id ? parseInt(formData.main_teacher_id) : null
            }

            const res = await fetch(url, {
                method,
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            })

            if (res.ok) {
                fetchClasses()
                setIsDialogOpen(false)
                resetForm()
            }
        } catch (error) {
            console.error("Failed to save class", error)
        }
    }

    const handleDelete = async (id: number) => {
        if (!await requestConfirmation({ title: "Supprimer cette classe", description: "Cette action est irréversible si la classe n'est pas protégée par des données liées.", confirmLabel: "Supprimer définitivement", destructive: true })) return

        try {
            const res = await fetch(`${API_BASE_URL}/education/classes/${id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) {
                fetchClasses()
            }
        } catch (error) {
            console.error("Failed to delete class", error)
        }
    }

    const openEdit = (cls: ClassItem) => {
        setCurrentClass(cls)
        setFormData({
            name: cls.name,
            level: cls.level || "",
            main_teacher_id: cls.main_teacher_id ? cls.main_teacher_id.toString() : null
        })
        setIsDialogOpen(true)
    }

    const openRoster = async (cls: ClassItem) => {
        const res = await fetch(`${API_BASE_URL}/education/classes/${cls.id}/roster`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) setRoster(await res.json())
    }

    const resetForm = () => {
        setCurrentClass(null)
        setFormData({ name: "", level: "", main_teacher_id: null })
    }

    const filterColumns = useMemo<FilterColumn<ClassItem>[]>(() => [
        { key: "name", label: "Nom", accessor: cls => cls.name },
        { key: "level", label: "Niveau", accessor: cls => cls.level },
        { key: "teacher", label: "Professeur principal", accessor: cls => teachers.find(t => t.id === cls.main_teacher_id)?.full_name },
    ], [teachers])
    const filter = useTableFilter(classes, filterColumns, { storageKey: "classes" })

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Gestion des classes</h1>
                <Dialog open={isDialogOpen} onOpenChange={(open) => {
                    setIsDialogOpen(open)
                    if (!open) resetForm()
                }}>
                    <DialogTrigger asChild>
                        <Button onClick={resetForm}>
                            <Plus className="mr-2 h-4 w-4" /> Ajouter une classe
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>{currentClass ? "Modifier la classe" : "Ajouter une classe"}</DialogTitle>
                            <DialogDescription>
                                {currentClass ? "Modifiez les informations de cette classe." : "Créez une nouvelle classe pour votre établissement."}
                            </DialogDescription>
                        </DialogHeader>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Nom de la classe</Label>
                                <Input
                                    id="name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    required
                                    placeholder="e.g. 6eme A"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="level">Niveau</Label>
                                <Input
                                    id="level"
                                    value={formData.level}
                                    onChange={(e) => setFormData({ ...formData, level: e.target.value })}
                                    placeholder="e.g. 6eme"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="teacher">Professeur principal</Label>
                                <Select
                                    value={formData.main_teacher_id || ""}
                                    onValueChange={(val) => setFormData({ ...formData, main_teacher_id: val === "none" ? null : val })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Sélectionner un professeur" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="none">Aucun professeur</SelectItem>
                                        {teachers.map(t => (
                                            <SelectItem key={t.id} value={t.id.toString()}>{t.full_name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <DialogFooter>
                                <Button type="submit">Enregistrer</Button>
                            </DialogFooter>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="max-w-2xl">
                <TableFilter {...filter.controls} />
            </div>

            <div data-teducai-collapsible="false" className="overflow-x-auto rounded-[22px] border border-[#E5E7EB] bg-white dark:border-[#3b4248] dark:bg-[#202528]">
                <table className="w-full text-sm text-left">
                    <thead className="border-b bg-[#F8FAFC] dark:border-[#3b4248] dark:bg-[#252b30]">
                        <tr>
                            <th className="px-6 py-3 font-medium text-gray-500 dark:text-[#eef3f8]">Nom</th>
                            <th className="px-6 py-3 font-medium text-gray-500 dark:text-[#eef3f8]">Niveau</th>
                            <th className="px-6 py-3 font-medium text-gray-500 dark:text-[#eef3f8]">Professeur principal</th>
                            <th className="px-6 py-3 font-medium text-gray-500 dark:text-[#eef3f8]">Nb Élèves</th>
                            <th className="px-6 py-3 font-medium text-gray-500 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y">
                        {isLoading ? (
                            <tr><td colSpan={5} className="px-6 py-4 text-center">Chargement...</td></tr>
                        ) : filter.filtered.length === 0 ? (
                            <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500">Aucune classe trouvée.</td></tr>
                        ) : (
                            filter.filtered.map((cls) => (
                                <tr key={cls.id} className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] dark:border-[#343b41] dark:hover:bg-[#2a3035]">
                                    <td className="px-6 py-4 font-medium">{cls.name}</td>
                                    <td className="px-6 py-4">{cls.level}</td>
                                    <td className="px-6 py-4 text-gray-500">
                                        {cls.main_teacher_id
                                            ? teachers.find(t => t.id === cls.main_teacher_id)?.full_name
                                            : "-"}
                                    </td>
                                    <td className="px-6 py-4">{studentCounts[cls.id] ?? "—"}</td>
                                    <td className="px-6 py-4 text-right space-x-2">
                                        <Button variant="ghost" size="sm" onClick={() => openStudents(cls)} title="Voir les élèves">
                                            <Users className="h-4 w-4" />
                                        </Button>
                                        <Button variant="ghost" size="sm" onClick={() => openRoster(cls)} title="Détails / finances">
                                            <Eye className="h-4 w-4" />
                                        </Button>
                                        <Button variant="ghost" size="sm" onClick={() => openEdit(cls)}>
                                            <Pencil className="h-4 w-4" />
                                        </Button>
                                        <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => handleDelete(cls.id)}>
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {roster && (
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-semibold text-[#111827]">{roster.class.name} roster</h2>
                            <p className="text-sm text-[#6B7280]">{roster.students.length} students, {roster.anomalies.length} finance anomalies</p>
                        </div>
                        <Button variant="outline" onClick={() => window.print()} className="gap-2">
                            <Printer className="h-4 w-4" /> Print
                        </Button>
                    </div>
                    {roster.anomalies.length > 0 && (
                        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                            <h3 className="text-sm font-semibold text-red-800">Anomalies</h3>
                            <div className="mt-2 space-y-1">
                                {roster.anomalies.map((row) => (
                                    <p key={row.student_user_id} className="text-sm text-red-700">{row.full_name} - {row.reason}</p>
                                ))}
                            </div>
                        </div>
                    )}
                    <div className="border rounded-md overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 border-b">
                                <tr>
                                    <th className="px-4 py-3 text-left font-medium text-gray-500">Student</th>
                                    <th className="px-4 py-3 text-left font-medium text-gray-500">Matricule</th>
                                    <th className="px-4 py-3 text-left font-medium text-gray-500">Parent</th>
                                    <th className="px-4 py-3 text-right font-medium text-gray-500">Expected</th>
                                    <th className="px-4 py-3 text-right font-medium text-gray-500">Paid</th>
                                    <th className="px-4 py-3 text-right font-medium text-gray-500">Remaining</th>
                                </tr>
                            </thead>
                            <tbody>
                                {roster.students.map((row) => (
                                    <tr key={row.student_user_id} className="border-b last:border-0">
                                        <td className="px-4 py-3 font-medium">{row.full_name}</td>
                                        <td className="px-4 py-3">{row.registration_number}</td>
                                        <td className="px-4 py-3">{row.parent_name} / {row.parent_phone}</td>
                                        <td className="px-4 py-3 text-right">{row.expected.toLocaleString()} FCFA</td>
                                        <td className="px-4 py-3 text-right text-green-700">{row.paid.toLocaleString()} FCFA</td>
                                        <td className="px-4 py-3 text-right text-red-700">{row.remaining.toLocaleString()} FCFA</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {studentsModal && (
                <div className="fixed inset-0 z-[1300] flex items-center justify-center bg-black/40 p-4" onClick={() => setStudentsModal(null)}>
                    <div className="w-full max-w-lg rounded-[20px] bg-white p-5 shadow-xl dark:bg-[#202528]" onClick={e => e.stopPropagation()}>
                        <div className="mb-3 flex items-center justify-between">
                            <div>
                                <h3 className="font-semibold text-[#111827] dark:text-white">{studentsModal.cls.name}</h3>
                                <p className="text-sm text-[#6B7280]">{studentsModal.students.length} élève(s) inscrit(s)</p>
                            </div>
                            <button onClick={() => setStudentsModal(null)} aria-label="Fermer"><X className="h-4 w-4" /></button>
                        </div>
                        {studentsModal.students.length === 0 ? (
                            <p className="py-6 text-center text-sm text-[#6B7280]">Aucun élève inscrit dans cette classe.</p>
                        ) : (
                            <div className="max-h-[55vh] overflow-y-auto rounded-xl border border-[#E5E7EB] dark:border-[#3b4248]">
                                <table className="w-full text-left text-sm">
                                    <thead className="sticky top-0 bg-[#F8FAFC] dark:bg-[#252b30]">
                                        <tr className="text-[#6B7280]"><th className="px-3 py-2">Nom complet</th><th className="px-3 py-2">Âge</th><th className="px-3 py-2">Sexe</th></tr>
                                    </thead>
                                    <tbody>
                                        {studentsModal.students.map(s => (
                                            <tr key={s.id} onClick={() => router.push(`/${locale}/dashboard/students/${s.user_id}`)} className="cursor-pointer border-t border-[#F0F1F3] hover:bg-[#F6F7F9] dark:border-[#2a3035] dark:hover:bg-[#2a3035]">
                                                <td className="px-3 py-2 font-medium text-[#111827] dark:text-[#f4f7fb]">{s.full_name}</td>
                                                <td className="px-3 py-2">{s.age ?? "—"}</td>
                                                <td className="px-3 py-2">{s.gender || "—"}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
