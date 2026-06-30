"use client"

import { useState, useEffect } from "react"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Teacher } from "./teacher-list-table" // Importing interface

interface EditTeacherModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    teacher: Teacher | null
    onSuccess?: () => void
}

export function EditTeacherModal({ open, onOpenChange, teacher, onSuccess }: EditTeacherModalProps) {
    const tf = useTranslations("teacherForm")
    const { token } = useAuth()
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const [formData, setFormData] = useState({
        full_name: "",
        email: "",
        phone_number: "",
        address: "",
        specialization: "",
        join_date: "",
        bio: ""
    })

    useEffect(() => {
        if (teacher) {
            setFormData({
                full_name: teacher.full_name,
                email: teacher.email,
                phone_number: teacher.phone_number || "",
                address: teacher.address || "",
                specialization: teacher.teacher_profile?.specialization || "",
                join_date: teacher.teacher_profile?.join_date ? teacher.teacher_profile.join_date.split('T')[0] : "",
                bio: teacher.teacher_profile?.bio || ""
            })
        }
    }, [teacher])

    const handleChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!teacher) return

        setIsLoading(true)
        setError(null)

        try {
            const payload = {
                full_name: formData.full_name,
                email: formData.email,
                phone_number: formData.phone_number,
                address: formData.address,
                profile: {
                    specialization: formData.specialization,
                    join_date: formData.join_date || null,
                    bio: formData.bio
                }
            }

            const res = await fetch(`${API_BASE_URL}/teachers/${teacher.id}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            })

            if (!res.ok) {
                const err = await res.json()
                throw new Error(err.detail || tf("updateError"))
            }

            onOpenChange(false)
            onSuccess?.()
        } catch (err) {
            setError(err instanceof Error ? err.message : tf("genericError"))
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>{tf("editTitle")}</DialogTitle>
                    <DialogDescription>{tf("editDesc")}</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm">
                            {error}
                        </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="edit_full_name">{tf("fullName")}</Label>
                            <Input
                                id="edit_full_name"
                                value={formData.full_name}
                                onChange={(e) => handleChange("full_name", e.target.value)}
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="edit_email">{tf("email")}</Label>
                            <Input
                                id="edit_email"
                                type="email"
                                value={formData.email}
                                onChange={(e) => handleChange("email", e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="edit_phone">{tf("phone")}</Label>
                            <Input
                                id="edit_phone"
                                value={formData.phone_number}
                                onChange={(e) => handleChange("phone_number", e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="edit_specialization">{tf("specialization")}</Label>
                            <Input
                                id="edit_specialization"
                                value={formData.specialization}
                                onChange={(e) => handleChange("specialization", e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="edit_address">{tf("address")}</Label>
                        <Input
                            id="edit_address"
                            value={formData.address}
                            onChange={(e) => handleChange("address", e.target.value)}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="edit_join_date">{tf("joinDate")}</Label>
                            <Input
                                id="edit_join_date"
                                type="date"
                                value={formData.join_date}
                                onChange={(e) => handleChange("join_date", e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="edit_bio">{tf("bio")}</Label>
                        <Textarea
                            id="edit_bio"
                            value={formData.bio}
                            onChange={(e) => handleChange("bio", e.target.value)}
                        />
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                            {tf("cancel")}
                        </Button>
                        <Button type="submit" disabled={isLoading}>
                            {isLoading ? tf("saving") : tf("saveChanges")}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
