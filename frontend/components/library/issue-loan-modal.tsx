"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useAuth } from "@/contexts/auth-context"
import { useParams } from "next/navigation"
import { API_BASE_URL } from "@/lib/config"
import { parseApiErrorResponse } from "@/lib/api-errors"
import { MissingDependency, missingRequired } from "@/components/ui/missing-dependency"

export interface LibraryBook {
    id: number
    title: string
    available_quantity: number
}

interface StudentOption {
    id: number
    full_name: string
    student_profile?: {
        registration_number?: string | null
    }
}

interface IssueLoanModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
    books: LibraryBook[]
}

export function IssueLoanModal({ open, onOpenChange, onSuccess, books }: IssueLoanModalProps) {
    const { token } = useAuth()
    const params = useParams()
    const locale = (params?.locale as string) || "fr"
    const [isLoading, setIsLoading] = useState(false)
    const [students, setStudents] = useState<StudentOption[]>([])
    const [studentsLoaded, setStudentsLoaded] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const [formData, setFormData] = useState({
        book_id: "",
        user_id: "",
        due_date: "",
        notes: ""
    })

    // Fetch students on mount
    useEffect(() => {
        if (open) {
            const fetchStudents = async () => {
                try {
                    const res = await fetch(`${API_BASE_URL}/students/`, {
                        headers: { "Authorization": `Bearer ${token}` }
                    })
                    if (res.ok) {
                        const data: StudentOption[] = await res.json()
                        setStudents(data)
                    }
                } catch {
                    console.error("Failed to fetch students")
                } finally {
                    setStudentsLoaded(true)
                }
            }
            fetchStudents()
        }
    }, [open, token])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)
        setIsLoading(true)

        try {
            const payload = {
                book_id: parseInt(formData.book_id),
                user_id: parseInt(formData.user_id),
                due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
                notes: formData.notes
            }

            const response = await fetch(`${API_BASE_URL}/library/loans`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            })

            if (!response.ok) {
                // Readable message, never "[object Object]".
                const parsed = await parseApiErrorResponse(response, "Impossible d'enregistrer le prêt.")
                throw new Error(parsed.message)
            }

            onSuccess()
            onOpenChange(false)
            setFormData({
                book_id: "",
                user_id: "",
                due_date: "",
                notes: ""
            })
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Failed to issue book")
        } finally {
            setIsLoading(false)
        }
    }

    // Filter only available books
    const availableBooks = books.filter(b => b.available_quantity > 0)

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Issue Book Loan</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm">
                            {error}
                        </div>
                    )}
                    {availableBooks.length === 0 && (
                        <MissingDependency
                            message="Aucun livre disponible à l'emprunt. Ajoutez d'abord un livre (ou attendez un retour) avant d'enregistrer un prêt."
                            actions={[]}
                        />
                    )}
                    {studentsLoaded && students.length === 0 && (
                        <MissingDependency
                            message="Impossible de continuer. Vous devez d'abord créer au moins un élève avant d'enregistrer un prêt."
                            actions={[{ label: "Créer un élève", href: `/${locale}/dashboard/students` }]}
                        />
                    )}

                    <div className="grid gap-2">
                        <Label htmlFor="book">Select Book</Label>
                        <Select
                            value={formData.book_id}
                            onValueChange={(val) => setFormData({ ...formData, book_id: val })}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select a book" />
                            </SelectTrigger>
                            <SelectContent>
                                {availableBooks.map((book) => (
                                    <SelectItem key={book.id} value={book.id.toString()}>
                                        {book.title} ({book.available_quantity} avl.)
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="student">Select Student</Label>
                        <Select
                            value={formData.user_id}
                            onValueChange={(val) => setFormData({ ...formData, user_id: val })}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select a student" />
                            </SelectTrigger>
                            <SelectContent>
                                {students.map((student) => (
                                    <SelectItem key={student.id} value={student.id.toString()}>
                                        {student.full_name} ({student.student_profile?.registration_number})
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="due_date">Due Date</Label>
                        <Input
                            id="due_date"
                            type="date"
                            value={formData.due_date}
                            onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                            required
                        />
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="notes">Notes (Optional)</Label>
                        <Input
                            id="notes"
                            value={formData.notes}
                            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        />
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={isLoading || availableBooks.length === 0 || missingRequired([{ loaded: studentsLoaded, count: students.length }])} className="bg-black text-white hover:bg-black/90">
                            {isLoading ? "Processing..." : "Issue Book"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
