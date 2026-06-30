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
import { Teacher } from "./teacher-list-table"

interface DeleteTeacherDialogProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    teacher: Teacher | null
    onSuccess?: () => void
}

export function DeleteTeacherDialog({ open, onOpenChange, teacher, onSuccess }: DeleteTeacherDialogProps) {
    const tf = useTranslations("teacherForm")
    const { token } = useAuth()
    const [isDeleting, setIsDeleting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleDelete = async () => {
        if (!teacher || !token) return

        setIsDeleting(true)
        setError(null)

        try {
            const response = await fetch(`${API_BASE_URL}/teachers/${teacher.id}`, {
                method: "DELETE",
                headers: {
                    Authorization: `Bearer ${token}`
                }
            })

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error(tf("sessionExpired"))
                }
                throw new Error(tf("deleteError"))
            }

            // Success
            onOpenChange(false)
            onSuccess?.()
        } catch (err) {
            setError(err instanceof Error ? err.message : tf("genericError"))
        } finally {
            setIsDeleting(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle>{tf("deleteTitle")}</DialogTitle>
                    <DialogDescription>{tf("deleteConfirm", { name: teacher?.full_name || "" })}</DialogDescription>
                </DialogHeader>

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
                    >
                        {tf("cancel")}
                    </Button>
                    <Button
                        type="button"
                        className="bg-red-600 text-white hover:bg-red-700"
                        onClick={handleDelete}
                        disabled={isDeleting}
                    >
                        {isDeleting ? tf("deleting") : tf("deleteBtn")}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
