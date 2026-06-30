"use client"

import { useEffect, useState } from "react"
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"

interface AddStudentModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess?: () => void
}

export function AddStudentModal({ open, onOpenChange, onSuccess }: AddStudentModalProps) {
    const { token } = useAuth()
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Form state
    const [formData, setFormData] = useState({
        // Student info
        fullName: "",
        email: "",
        password: "",
        registrationNumber: "",
        dateOfBirth: "",
        gender: "",
        studentAddress: "",
        // Parent info
        parentName: "",
        parentPhone: "",
        parentEmail: "",
        parentAddress: "",
        // Class (optional)
        currentClassId: "",
    })

    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
    const [levels, setLevels] = useState<{ id: number; code: string; name: string }[]>([])
    const [classes, setClasses] = useState<{ id: number; name: string; level: string }[]>([])
    const [selectedLevel, setSelectedLevel] = useState("")

    // Load the levels referential + classes when the modal opens (#4 cascade).
    useEffect(() => {
        if (!open || !token) return
        const headers = { Authorization: `Bearer ${token}` }
        fetch(`${API_BASE_URL}/levels?active_only=true`, { headers }).then(r => r.ok ? r.json() : []).then(setLevels).catch(() => undefined)
        fetch(`${API_BASE_URL}/education/classes`, { headers }).then(r => r.ok ? r.json() : []).then(setClasses).catch(() => undefined)
    }, [open, token])

    const classesForLevel = selectedLevel ? classes.filter(c => c.level === selectedLevel) : []

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
        if (!formData.fullName.trim()) errors.fullName = "Full name is required"
        if (!formData.email.trim()) errors.email = "Email is required"
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            errors.email = "Invalid email format"
        }
        if (!formData.password) errors.password = "Password is required"
        else if (formData.password.length < 8) {
            errors.password = "Password must be at least 8 characters"
        }
        if (!formData.registrationNumber.trim()) errors.registrationNumber = "Registration number is required"
        if (!formData.dateOfBirth) errors.dateOfBirth = "Date of birth is required"
        if (!formData.gender) errors.gender = "Gender is required"
        if (!formData.studentAddress.trim()) errors.studentAddress = "Student address is required"
        if (!formData.parentName.trim()) errors.parentName = "Parent name is required"
        if (!formData.parentPhone.trim()) errors.parentPhone = "Parent phone is required"
        if (!formData.parentAddress.trim()) errors.parentAddress = "Parent address is required"

        // Optional parent email validation
        if (formData.parentEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.parentEmail)) {
            errors.parentEmail = "Invalid email format"
        }

        setValidationErrors(errors)
        return Object.keys(errors).length === 0
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!validateForm()) {
            return
        }

        setIsLoading(true)
        setError(null)

        try {
            // Get JWT token from auth context
            if (!token) {
                throw new Error("Not authenticated. Please log in first.")
            }

            const response = await fetch(`${API_BASE_URL}/students`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({
                    email: formData.email,
                    password: formData.password,
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
                const errorData = await response.json()
                throw new Error(errorData.detail || "Failed to create student")
            }

            // Success
            await response.json()

            // Reset form
            setFormData({
                fullName: "",
                email: "",
                password: "",
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

            // Close modal and trigger refresh
            onOpenChange(false)
            onSuccess?.()

        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Add New Student</DialogTitle>
                    <DialogDescription>
                        Enter the student&apos;s information to register them in the system.
                    </DialogDescription>
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
                                <Label htmlFor="fullName">Full Name *</Label>
                                <Input
                                    id="fullName"
                                    value={formData.fullName}
                                    onChange={(e) => handleInputChange("fullName", e.target.value)}
                                    placeholder="John Doe"
                                />
                                {validationErrors.fullName && (
                                    <p className="text-xs text-red-600">{validationErrors.fullName}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="email">Email *</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => handleInputChange("email", e.target.value)}
                                    placeholder="student@example.com"
                                />
                                {validationErrors.email && (
                                    <p className="text-xs text-red-600">{validationErrors.email}</p>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="password">Password *</Label>
                                <Input
                                    id="password"
                                    type="password"
                                    value={formData.password}
                                    onChange={(e) => handleInputChange("password", e.target.value)}
                                    placeholder="Min. 8 characters"
                                />
                                {validationErrors.password && (
                                    <p className="text-xs text-red-600">{validationErrors.password}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="registrationNumber">Registration Number *</Label>
                                <Input
                                    id="registrationNumber"
                                    value={formData.registrationNumber}
                                    onChange={(e) => handleInputChange("registrationNumber", e.target.value)}
                                    placeholder="STU2024001"
                                />
                                {validationErrors.registrationNumber && (
                                    <p className="text-xs text-red-600">{validationErrors.registrationNumber}</p>
                                )}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="dateOfBirth">Date of Birth *</Label>
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

                            <div className="space-y-2">
                                <Label htmlFor="gender">Gender *</Label>
                                <Select value={formData.gender} onValueChange={(value) => handleInputChange("gender", value)}>
                                    <SelectTrigger id="gender">
                                        <SelectValue placeholder="Select gender" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Male">Male</SelectItem>
                                        <SelectItem value="Female">Female</SelectItem>
                                        <SelectItem value="Other">Other</SelectItem>
                                    </SelectContent>
                                </Select>
                                {validationErrors.gender && (
                                    <p className="text-xs text-red-600">{validationErrors.gender}</p>
                                )}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="studentAddress">Student Address *</Label>
                            <Textarea
                                id="studentAddress"
                                value={formData.studentAddress}
                                onChange={(e) => handleInputChange("studentAddress", e.target.value)}
                                placeholder="Enter full address"
                                rows={2}
                            />
                            {validationErrors.studentAddress && (
                                <p className="text-xs text-red-600">{validationErrors.studentAddress}</p>
                            )}
                        </div>
                    </div>

                    {/* Parent/Guardian Information */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-semibold text-[#111827]">Parent/Guardian Information</h3>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="parentName">Parent Name *</Label>
                                <Input
                                    id="parentName"
                                    value={formData.parentName}
                                    onChange={(e) => handleInputChange("parentName", e.target.value)}
                                    placeholder="Jane Doe"
                                />
                                {validationErrors.parentName && (
                                    <p className="text-xs text-red-600">{validationErrors.parentName}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="parentPhone">Parent Phone *</Label>
                                <Input
                                    id="parentPhone"
                                    type="tel"
                                    value={formData.parentPhone}
                                    onChange={(e) => handleInputChange("parentPhone", e.target.value)}
                                    placeholder="+1234567890"
                                />
                                {validationErrors.parentPhone && (
                                    <p className="text-xs text-red-600">{validationErrors.parentPhone}</p>
                                )}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="parentEmail">Parent Email (Optional)</Label>
                            <Input
                                id="parentEmail"
                                type="email"
                                value={formData.parentEmail}
                                onChange={(e) => handleInputChange("parentEmail", e.target.value)}
                                placeholder="parent@example.com"
                            />
                            {validationErrors.parentEmail && (
                                <p className="text-xs text-red-600">{validationErrors.parentEmail}</p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="parentAddress">Parent Address *</Label>
                            <Textarea
                                id="parentAddress"
                                value={formData.parentAddress}
                                onChange={(e) => handleInputChange("parentAddress", e.target.value)}
                                placeholder="Enter full address"
                                rows={2}
                            />
                            {validationErrors.parentAddress && (
                                <p className="text-xs text-red-600">{validationErrors.parentAddress}</p>
                            )}
                        </div>
                    </div>

                    {/* Informations sur la Classe (#4): level -> dynamically filtered classes */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-semibold text-[#111827]">Informations sur la Classe</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="level">Niveau scolaire</Label>
                                <Select value={selectedLevel} onValueChange={value => { setSelectedLevel(value); handleInputChange("currentClassId", "") }}>
                                    <SelectTrigger id="level"><SelectValue placeholder="Sélectionner un niveau" /></SelectTrigger>
                                    <SelectContent>
                                        {levels.map(level => <SelectItem key={level.id} value={level.code}>{level.code} — {level.name}</SelectItem>)}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="currentClassId">Classe</Label>
                                <Select value={formData.currentClassId} onValueChange={value => handleInputChange("currentClassId", value)} disabled={!selectedLevel}>
                                    <SelectTrigger id="currentClassId"><SelectValue placeholder={selectedLevel ? "Sélectionner une classe" : "Choisissez d'abord un niveau"} /></SelectTrigger>
                                    <SelectContent>
                                        {classesForLevel.length === 0 ? (
                                            <SelectItem value="none" disabled>Aucune classe pour ce niveau</SelectItem>
                                        ) : classesForLevel.map(cls => <SelectItem key={cls.id} value={String(cls.id)}>{cls.name}</SelectItem>)}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => onOpenChange(false)}
                            disabled={isLoading}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            className="bg-black text-white hover:bg-black/90"
                            disabled={isLoading}
                        >
                            {isLoading ? "Creating..." : "Create Student"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
