"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
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
import { Pencil, Trash2, Plus } from "lucide-react"
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

export default function ClassesPage() {
    const { token } = useAuth()
    const [classes, setClasses] = useState<ClassItem[]>([])
    const [teachers, setTeachers] = useState<TeacherOption[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [isDialogOpen, setIsDialogOpen] = useState(false)
    const [currentClass, setCurrentClass] = useState<ClassItem | null>(null)
    const [formData, setFormData] = useState<{ name: string, level: string, main_teacher_id: string | null }>({ name: "", level: "", main_teacher_id: null })

    useEffect(() => {
        if (token) {
            fetchClasses()
            fetchTeachers()
        }
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
                const data = await res.json()
                setClasses(data)
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
        if (!confirm("Are you sure you want to delete this class?")) return

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

    const resetForm = () => {
        setCurrentClass(null)
        setFormData({ name: "", level: "", main_teacher_id: null })
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Classes Management</h1>
                <Dialog open={isDialogOpen} onOpenChange={(open) => {
                    setIsDialogOpen(open)
                    if (!open) resetForm()
                }}>
                    <DialogTrigger asChild>
                        <Button onClick={resetForm}>
                            <Plus className="mr-2 h-4 w-4" /> Add Class
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>{currentClass ? "Edit Class" : "Add Class"}</DialogTitle>
                            <DialogDescription>
                                {currentClass ? "Update class details." : "Create a new class for your school."}
                            </DialogDescription>
                        </DialogHeader>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Class Name</Label>
                                <Input
                                    id="name"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    required
                                    placeholder="e.g. 6eme A"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="level">Level</Label>
                                <Input
                                    id="level"
                                    value={formData.level}
                                    onChange={(e) => setFormData({ ...formData, level: e.target.value })}
                                    placeholder="e.g. 6eme"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="teacher">Main Teacher</Label>
                                <Select
                                    value={formData.main_teacher_id || ""}
                                    onValueChange={(val) => setFormData({ ...formData, main_teacher_id: val === "none" ? null : val })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select a teacher" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="none">No Teacher</SelectItem>
                                        {teachers.map(t => (
                                            <SelectItem key={t.id} value={t.id.toString()}>{t.full_name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <DialogFooter>
                                <Button type="submit">Save</Button>
                            </DialogFooter>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="border rounded-md">
                <table className="w-full text-sm text-left">
                    <thead className="bg-gray-50 border-b">
                        <tr>
                            <th className="px-6 py-3 font-medium text-gray-500">Name</th>
                            <th className="px-6 py-3 font-medium text-gray-500">Level</th>
                            <th className="px-6 py-3 font-medium text-gray-500">Main Teacher</th>
                            <th className="px-6 py-3 font-medium text-gray-500 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y">
                        {isLoading ? (
                            <tr><td colSpan={3} className="px-6 py-4 text-center">Loading...</td></tr>
                        ) : classes.length === 0 ? (
                            <tr><td colSpan={3} className="px-6 py-4 text-center text-gray-500">No classes found.</td></tr>
                        ) : (
                            classes.map((cls) => (
                                <tr key={cls.id}>
                                    <td className="px-6 py-4 font-medium">{cls.name}</td>
                                    <td className="px-6 py-4">{cls.level}</td>
                                    <td className="px-6 py-4 text-gray-500">
                                        {cls.main_teacher_id
                                            ? teachers.find(t => t.id === cls.main_teacher_id)?.full_name
                                            : "-"}
                                    </td>
                                    <td className="px-6 py-4 text-right space-x-2">
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
        </div>
    )
}
