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

interface SubjectItem {
    id: number
    name: string
    code?: string
    description?: string
    coefficient: number
}

export default function SubjectsPage() {
    const { token } = useAuth()
    const [subjects, setSubjects] = useState<SubjectItem[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [isDialogOpen, setIsDialogOpen] = useState(false)
    const [currentSubject, setCurrentSubject] = useState<SubjectItem | null>(null)
    const [formData, setFormData] = useState({ name: "", code: "", description: "", coefficient: 1 })

    useEffect(() => {
        if (token) {
            fetchSubjects()
        }
    }, [token])

    const fetchSubjects = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/education/subjects`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) {
                const data = await res.json()
                setSubjects(data)
            }
        } catch (error) {
            console.error("Failed to fetch subjects", error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const url = currentSubject
                ? `${API_BASE_URL}/education/subjects/${currentSubject.id}`
                : `${API_BASE_URL}/education/subjects`

            const method = currentSubject ? "PUT" : "POST"

            const res = await fetch(url, {
                method,
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            })

            if (res.ok) {
                fetchSubjects()
                setIsDialogOpen(false)
                resetForm()
            }
        } catch (error) {
            console.error("Failed to save subject", error)
        }
    }

    const handleDelete = async (id: number) => {
        if (!confirm("Are you sure you want to delete this subject?")) return

        try {
            const res = await fetch(`${API_BASE_URL}/education/subjects/${id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) {
                fetchSubjects()
            }
        } catch (error) {
            console.error("Failed to delete subject", error)
        }
    }

    const openEdit = (sub: SubjectItem) => {
        setCurrentSubject(sub)
        setFormData({
            name: sub.name,
            code: sub.code || "",
            description: sub.description || "",
            coefficient: sub.coefficient
        })
        setIsDialogOpen(true)
    }

    const resetForm = () => {
        setCurrentSubject(null)
        setFormData({ name: "", code: "", description: "", coefficient: 1 })
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Subjects Management</h1>
                <Dialog open={isDialogOpen} onOpenChange={(open) => {
                    setIsDialogOpen(open)
                    if (!open) resetForm()
                }}>
                    <DialogTrigger asChild>
                        <Button onClick={resetForm}>
                            <Plus className="mr-2 h-4 w-4" /> Add Subject
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>{currentSubject ? "Edit Subject" : "Add Subject"}</DialogTitle>
                            <DialogDescription>
                                {currentSubject ? "Update subject details." : "Create a new subject."}
                            </DialogDescription>
                        </DialogHeader>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name">Subject Name</Label>
                                    <Input
                                        id="name"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        required
                                        placeholder="e.g. Mathematics"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="code">Code</Label>
                                    <Input
                                        id="code"
                                        value={formData.code}
                                        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                                        placeholder="e.g. MATH"
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="coefficient">Coefficient</Label>
                                <Input
                                    id="coefficient"
                                    type="number"
                                    min="1"
                                    value={formData.coefficient}
                                    onChange={(e) => setFormData({ ...formData, coefficient: parseInt(e.target.value) })}
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="description">Description</Label>
                                <Input
                                    id="description"
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    placeholder="Optional description"
                                />
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
                            <th className="px-6 py-3 font-medium text-gray-500">Code</th>
                            <th className="px-6 py-3 font-medium text-gray-500">Name</th>
                            <th className="px-6 py-3 font-medium text-gray-500">Coeff</th>
                            <th className="px-6 py-3 font-medium text-gray-500 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y">
                        {isLoading ? (
                            <tr><td colSpan={4} className="px-6 py-4 text-center">Loading...</td></tr>
                        ) : subjects.length === 0 ? (
                            <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-500">No subjects found.</td></tr>
                        ) : (
                            subjects.map((sub) => (
                                <tr key={sub.id}>
                                    <td className="px-6 py-4 text-gray-500">{sub.code}</td>
                                    <td className="px-6 py-4 font-medium">{sub.name}</td>
                                    <td className="px-6 py-4">{sub.coefficient}</td>
                                    <td className="px-6 py-4 text-right space-x-2">
                                        <Button variant="ghost" size="sm" onClick={() => openEdit(sub)}>
                                            <Pencil className="h-4 w-4" />
                                        </Button>
                                        <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => handleDelete(sub.id)}>
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
