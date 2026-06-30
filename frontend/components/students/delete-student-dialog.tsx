"use client"

import { useState } from "react"
import { useTranslations } from "next-intl"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

interface Student {
    id: number
    full_name: string
    email: string
}

interface DeleteStudentDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    student: Student | null
    onSuccess: () => void
}

export function DeleteStudentDialog({ open, onOpenChange, student, onSuccess }: DeleteStudentDialogProps) {
    const sf = useTranslations("studentForm")
    const { token } = useAuth()
    const [isDeleting, setIsDeleting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleDelete = async () => {
        if (!student || !token) return

        setIsDeleting(true)
        setError(null)

        try {
            const response = await fetch(`${API_BASE_URL}/students/${student.id}`, {
                method: "DELETE",
                headers: {
                    "Authorization": `Bearer ${token}`,
                },
            })

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error(sf("sessionExpired"))
                }
                if (response.status === 404) {
                    throw new Error(sf("notFound"))
                }
                throw new Error(sf("deleteError"))
            }

            // Success
            onOpenChange(false)
            onSuccess()
        } catch (err) {
            setError(err instanceof Error ? err.message : sf("genericError"))
        } finally {
            setIsDeleting(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle>{sf("deleteTitle")}</DialogTitle>
                    <DialogDescription>
                        {sf("deleteConfirm")}
                    </DialogDescription>
                </DialogHeader>

                {student && (
                    <div className="bg-[#F6F7F9] border border-[#E5E7EB] rounded-lg p-4 space-y-1">
                        <p className="text-sm font-medium text-[#111827]">{student.full_name}</p>
                        <p className="text-sm text-[#6B7280]">{student.email}</p>
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                        {error}
                    </div>
                )}

                <DialogFooter>
                    <Button
                        type="button"
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        disabled={isDeleting}
                    >{sf("cancel")}</Button>
                    <Button
                        type="button"
                        className="bg-red-600 text-white hover:bg-red-700"
                        onClick={handleDelete}
                        disabled={isDeleting}
                    >
                        {isDeleting ? sf("deleting") : sf("deleteBtn")}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
