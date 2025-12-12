"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Edit, Trash2 } from "lucide-react"
import { EditStudentModal } from "@/components/students/edit-student-modal"
import { DeleteStudentDialog } from "@/components/students/delete-student-dialog"
import { Separator } from "@/components/ui/separator"

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
    student_profile: StudentProfile
}

export default function StudentDetailPage() {
    const { token } = useAuth()
    const params = useParams()
    const router = useRouter()
    const id = params.id as string
    const locale = params.locale as string

    const [student, setStudent] = useState<Student | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [showEditModal, setShowEditModal] = useState(false)
    const [showDeleteDialog, setShowDeleteDialog] = useState(false)

    // Fetch student details
    const fetchStudent = async () => {
        if (!token) return

        try {
            setIsLoading(true)
            setError(null)
            const response = await fetch(`${API_BASE_URL}/students/${id}`, {
                headers: {
                    "Authorization": `Bearer ${token}`,
                },
            })

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error("Student not found")
                }
                throw new Error("Failed to fetch student details")
            }

            const data = await response.json()
            setStudent(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred")
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        if (token && id) {
            fetchStudent()
        }
    }, [token, id])

    const handleBack = () => {
        router.push(`/${locale}/dashboard/students`)
    }

    const handleStudentUpdated = () => {
        fetchStudent()
    }

    const handleStudentDeleted = () => {
        router.push(`/${locale}/dashboard/students`)
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <p className="text-[#6B7280]">Loading student details...</p>
            </div>
        )
    }

    if (error || !student) {
        return (
            <div className="space-y-4">
                <Button variant="ghost" onClick={handleBack} className="text-[#6B7280]">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Students
                </Button>
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
                    {error || "Student not found"}
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header / Navigation */}
            <div className="flex items-center justify-between">
                <div className="space-y-1">
                    <Button
                        variant="ghost"
                        onClick={handleBack}
                        className="pl-0 text-[#6B7280] hover:text-[#111827] hover:bg-transparent"
                    >
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back to Students
                    </Button>
                    <h1 className="text-2xl font-bold text-[#111827]">Student Profile</h1>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        onClick={() => setShowEditModal(true)}
                        className="border-[#E5E7EB] text-[#111827] hover:bg-[#F9FAFB]"
                    >
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                    </Button>
                    <Button
                        variant="outline"
                        onClick={() => setShowDeleteDialog(true)}
                        className="border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 hover:border-red-300"
                    >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Personal Information */}
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-lg font-semibold text-[#111827]">Personal Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <h4 className="text-sm font-medium text-[#6B7280]">Full Name</h4>
                                <p className="text-sm text-[#111827] mt-1">{student.full_name}</p>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-[#6B7280]">Gender</h4>
                                <p className="text-sm text-[#111827] mt-1">{student.student_profile.gender}</p>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-[#6B7280]">Date of Birth</h4>
                                <p className="text-sm text-[#111827] mt-1">
                                    {new Date(student.student_profile.date_of_birth).toLocaleDateString()}
                                </p>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-[#6B7280]">Status</h4>
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${student.is_active
                                    ? "bg-green-100 text-green-800"
                                    : "bg-gray-100 text-gray-800"
                                    }`}>
                                    {student.is_active ? "Active" : "Inactive"}
                                </span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Academic Information */}
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-lg font-semibold text-[#111827]">Academic Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 gap-4">
                            <div>
                                <h4 className="text-sm font-medium text-[#6B7280]">Registration Number</h4>
                                <p className="text-sm text-[#111827] mt-1">{student.student_profile.registration_number}</p>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-[#6B7280]">Current Class</h4>
                                <p className="text-sm text-[#111827] mt-1">
                                    {student.student_profile.current_class_id || "Not assigned"}
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Contact Information */}
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-lg font-semibold text-[#111827]">Contact Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <h4 className="text-sm font-medium text-[#6B7280]">Email Address</h4>
                            <p className="text-sm text-[#111827] mt-1">{student.email}</p>
                        </div>
                        <Separator />
                        <div>
                            <h4 className="text-sm font-medium text-[#6B7280]">Student Address</h4>
                            <p className="text-sm text-[#111827] mt-1 whitespace-pre-wrap">{student.student_profile.student_address}</p>
                        </div>
                    </CardContent>
                </Card>

                {/* Parent/Guardian Information */}
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-lg font-semibold text-[#111827]">Parent/Guardian</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <h4 className="text-sm font-medium text-[#6B7280]">Parent Name</h4>
                                <p className="text-sm text-[#111827] mt-1">{student.student_profile.parent_name}</p>
                            </div>
                            <div>
                                <h4 className="text-sm font-medium text-[#6B7280]">Phone Number</h4>
                                <p className="text-sm text-[#111827] mt-1">{student.student_profile.parent_phone}</p>
                            </div>
                        </div>
                        <div>
                            <h4 className="text-sm font-medium text-[#6B7280]">Parent Email</h4>
                            <p className="text-sm text-[#111827] mt-1">{student.student_profile.parent_email || "N/A"}</p>
                        </div>
                        <Separator />
                        <div>
                            <h4 className="text-sm font-medium text-[#6B7280]">Parent Address</h4>
                            <p className="text-sm text-[#111827] mt-1 whitespace-pre-wrap">{student.student_profile.parent_address}</p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Modals */}
            <EditStudentModal
                open={showEditModal}
                onOpenChange={setShowEditModal}
                student={student}
                onSuccess={handleStudentUpdated}
            />

            <DeleteStudentDialog
                open={showDeleteDialog}
                onOpenChange={setShowDeleteDialog}
                student={student}
                onSuccess={handleStudentDeleted}
            />
        </div>
    )
}
