"use client"

import { useState, useEffect } from "react"
import { useTranslations } from "next-intl"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { parseApiErrorResponse } from "@/lib/api-errors"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"

// API (snake_case) -> form state field mapping for backend validation errors.
const API_FIELD_TO_FORM: Record<string, string> = {
    full_name: "fullName",
    email: "email",
    registration_number: "registrationNumber",
    date_of_birth: "dateOfBirth",
    gender: "gender",
    student_address: "studentAddress",
    parent_name: "parentName",
    parent_phone: "parentPhone",
    parent_email: "parentEmail",
    parent_address: "parentAddress",
    current_class_id: "currentClassId",
}
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"

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
    student_profile: StudentProfile
}

interface EditStudentModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    student: Student | null
    onSuccess?: () => void
}

export function EditStudentModal({ open, onOpenChange, student, onSuccess }: EditStudentModalProps) {
    const sf = useTranslations("studentForm")
    const { token } = useAuth()
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Form state
    const [formData, setFormData] = useState({
        fullName: "",
        email: "",
        registrationNumber: "",
        dateOfBirth: "",
        gender: "",
        studentAddress: "",
        parentName: "",
        parentPhone: "",
        parentEmail: "",
        parentAddress: "",
        currentClassId: "",
    })

    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

    // Pre-fill form when student changes
    useEffect(() => {
        if (student) {
            setFormData({
                fullName: student.full_name,
                email: student.email,
                registrationNumber: student.student_profile.registration_number,
                dateOfBirth: student.student_profile.date_of_birth,
                gender: student.student_profile.gender,
                studentAddress: student.student_profile.student_address,
                parentName: student.student_profile.parent_name,
                parentPhone: student.student_profile.parent_phone,
                parentEmail: student.student_profile.parent_email || "",
                parentAddress: student.student_profile.parent_address,
                currentClassId: student.student_profile.current_class_id?.toString() || "",
            })
        }
    }, [student])

    const handleInputChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        // Clear validation error for this field
        if (validationErrors[field]) {
            setValidationErrors(prev => {
                const newErrors = { ...prev }
                delete newErrors[field]
                return newErrors
            })
        }
    }

    const validateForm = (): boolean => {
        const errors: Record<string, string> = {}

        // Required fields
        if (!formData.fullName.trim()) errors.fullName = sf("vFullName")
        if (!formData.email.trim()) errors.email = sf("vEmailReq")
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            errors.email = sf("vEmailInvalid")
        }
        if (!formData.registrationNumber.trim()) errors.registrationNumber = sf("vRegistration")
        if (!formData.dateOfBirth) errors.dateOfBirth = sf("vDob")
        if (!formData.gender) errors.gender = sf("vGender")
        if (!formData.studentAddress.trim()) errors.studentAddress = sf("vStudentAddress")
        if (!formData.parentName.trim()) errors.parentName = sf("vParentName")
        if (!formData.parentPhone.trim()) errors.parentPhone = sf("vParentPhone")
        if (!formData.parentAddress.trim()) errors.parentAddress = sf("vParentAddress")

        // Optional parent email validation
        if (formData.parentEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.parentEmail)) {
            errors.parentEmail = sf("vEmailInvalid")
        }

        setValidationErrors(errors)
        return Object.keys(errors).length === 0
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!validateForm() || !student) {
            return
        }

        setIsLoading(true)
        setError(null)

        try {
            if (!token) {
                throw new Error(sf("notAuth"))
            }

            const response = await fetch(`${API_BASE_URL}/students/${student.id}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({
                    email: formData.email,
                    full_name: formData.fullName,
                    profile: {
                        registration_number: formData.registrationNumber,
                        date_of_birth: formData.dateOfBirth,
                        gender: formData.gender,
                        student_address: formData.studentAddress,
                        parent_name: formData.parentName,
                        parent_phone: formData.parentPhone,
                        parent_email: formData.parentEmail || undefined,
                        parent_address: formData.parentAddress,
                        current_class_id: formData.currentClassId ? parseInt(formData.currentClassId) : undefined,
                    },
                }),
            })

            if (!response.ok) {
                // Never show "[object Object]": parse FastAPI string/array/object
                // details into a readable message + per-field errors, keeping the
                // values the user already typed.
                const parsed = await parseApiErrorResponse(response, sf("updateError"))
                const mapped: Record<string, string> = {}
                for (const [apiField, message] of Object.entries(parsed.fieldErrors)) {
                    const formField = API_FIELD_TO_FORM[apiField]
                    if (formField) mapped[formField] = message
                }
                if (Object.keys(mapped).length) setValidationErrors(prev => ({ ...prev, ...mapped }))
                throw new Error(parsed.message)
            }

            // Success
            onOpenChange(false)
            onSuccess?.()

        } catch (err) {
            setError(err instanceof Error ? err.message : sf("genericError"))
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>{sf("editTitle")}</DialogTitle>
                    <DialogDescription>{sf("editDesc")}</DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Error message */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                            {error}
                        </div>
                    )}

                    {/* Student Information */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-semibold text-[#111827]">Student Information</h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="fullName">{sf("fullName")}</Label>
                                <Input
                                    id="fullName"
                                    value={formData.fullName}
                                    onChange={(e) => handleInputChange("fullName", e.target.value)}
                                    placeholder={sf("fullNamePh")}
                                />
                                {validationErrors.fullName && (
                                    <p className="text-xs text-red-600">{validationErrors.fullName}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="email">{sf("email")}</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => handleInputChange("email", e.target.value)}
                                    placeholder={sf("emailPh")}
                                />
                                {validationErrors.email && (
                                    <p className="text-xs text-red-600">{validationErrors.email}</p>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="registrationNumber">{sf("registration")}</Label>
                                <Input
                                    id="registrationNumber"
                                    value={formData.registrationNumber}
                                    onChange={(e) => handleInputChange("registrationNumber", e.target.value)}
                                    placeholder={sf("registrationPh")}
                                />
                                {validationErrors.registrationNumber && (
                                    <p className="text-xs text-red-600">{validationErrors.registrationNumber}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="dateOfBirth">{sf("dob")}</Label>
                                <Input
                                    id="dateOfBirth"
                                    type="date"
                                    value={formData.dateOfBirth}
                                    onChange={(e) => handleInputChange("dateOfBirth", e.target.value)}
                                />
                                {validationErrors.dateOfBirth && (
                                    <p className="text-xs text-red-600">{validationErrors.dateOfBirth}</p>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="gender">{sf("gender")}</Label>
                                <Select value={formData.gender} onValueChange={(value) => handleInputChange("gender", value)}>
                                    <SelectTrigger id="gender">
                                        <SelectValue placeholder={sf("genderPh")} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Male">{sf("male")}</SelectItem>
                                        <SelectItem value="Female">{sf("female")}</SelectItem>
                                        <SelectItem value="Other">{sf("other")}</SelectItem>
                                    </SelectContent>
                                </Select>
                                {validationErrors.gender && (
                                    <p className="text-xs text-red-600">{validationErrors.gender}</p>
                                )}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="studentAddress">{sf("studentAddress")}</Label>
                            <Textarea
                                id="studentAddress"
                                value={formData.studentAddress}
                                onChange={(e) => handleInputChange("studentAddress", e.target.value)}
                                placeholder={sf("addressPh")}
                                rows={2}
                            />
                            {validationErrors.studentAddress && (
                                <p className="text-xs text-red-600">{validationErrors.studentAddress}</p>
                            )}
                        </div>
                    </div>

                    {/* Parent/Guardian Information */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-semibold text-[#111827]">{sf("parentInfo")}</h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="parentName">{sf("parentName")}</Label>
                                <Input
                                    id="parentName"
                                    value={formData.parentName}
                                    onChange={(e) => handleInputChange("parentName", e.target.value)}
                                    placeholder={sf("parentNamePh")}
                                />
                                {validationErrors.parentName && (
                                    <p className="text-xs text-red-600">{validationErrors.parentName}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="parentPhone">{sf("parentPhone")}</Label>
                                <Input
                                    id="parentPhone"
                                    type="tel"
                                    value={formData.parentPhone}
                                    onChange={(e) => handleInputChange("parentPhone", e.target.value)}
                                    placeholder={sf("parentPhonePh")}
                                />
                                {validationErrors.parentPhone && (
                                    <p className="text-xs text-red-600">{validationErrors.parentPhone}</p>
                                )}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="parentEmail">{sf("parentEmail")}</Label>
                            <Input
                                id="parentEmail"
                                type="email"
                                value={formData.parentEmail}
                                onChange={(e) => handleInputChange("parentEmail", e.target.value)}
                                placeholder={sf("parentEmailPh")}
                            />
                            {validationErrors.parentEmail && (
                                <p className="text-xs text-red-600">{validationErrors.parentEmail}</p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="parentAddress">{sf("parentAddress")}</Label>
                            <Textarea
                                id="parentAddress"
                                value={formData.parentAddress}
                                onChange={(e) => handleInputChange("parentAddress", e.target.value)}
                                placeholder={sf("addressPh")}
                                rows={2}
                            />
                            {validationErrors.parentAddress && (
                                <p className="text-xs text-red-600">{validationErrors.parentAddress}</p>
                            )}
                        </div>
                    </div>

                    <DialogFooter>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => onOpenChange(false)}
                            disabled={isLoading}
                        >
                            {sf("cancel")}
                        </Button>
                        <Button
                            type="submit"
                            className="bg-black text-white hover:bg-black/90"
                            disabled={isLoading}
                        >
                            {isLoading ? sf("saving") : sf("saveChanges")}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
