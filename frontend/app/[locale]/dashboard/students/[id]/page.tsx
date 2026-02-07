"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { ArrowLeft, User, Phone, Mail, MapPin, Calendar, CreditCard, Edit, Trash2 } from "lucide-react"
import { EducationHistoryList } from "@/components/students/education-history-list"
import { DeleteStudentDialog } from "@/components/students/delete-student-dialog"
import { EditStudentModal } from "@/components/students/edit-student-modal"

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
    education_history: any[]
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
    const studentId = params.id
    const locale = params.locale as string

    const [student, setStudent] = useState<Student | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [showEdit, setShowEdit] = useState(false)
    const [showDelete, setShowDelete] = useState(false)

    const fetchStudent = async () => {
        if (!token) return

        try {
            setIsLoading(true)
            const response = await fetch(`${API_BASE_URL}/students/${studentId}`, {
                headers: { "Authorization": `Bearer ${token}` }
            })

            if (!response.ok) throw new Error("Student not found")
            const data = await response.json()
            setStudent(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error fetching student")
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchStudent()
    }, [token, studentId])

    if (isLoading) return <div className="p-8 text-center text-gray-500">Loading profile...</div>
    if (error || !student) return <div className="p-8 text-center text-red-500">Error: {error}</div>

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.back()}>
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                    <div>
                        <h1 className="text-2xl font-bold text-[#111827]">{student.full_name}</h1>
                        <p className="text-sm text-gray-500">{student.email}</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setShowEdit(true)}>
                        <Edit className="h-4 w-4 mr-2" />
                        Edit Profile
                    </Button>
                    <Button variant="destructive" onClick={() => setShowDelete(true)}>
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                    </Button>
                </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid gap-6 md:grid-cols-2">

                {/* Personal Info Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <User className="h-5 w-5" />
                            Personal Information
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <p className="text-gray-500">Registration Number</p>
                                <p className="font-medium">{student.student_profile.registration_number}</p>
                            </div>
                            <div>
                                <p className="text-gray-500">Date of Birth</p>
                                <p className="font-medium">{new Date(student.student_profile.date_of_birth).toLocaleDateString()}</p>
                            </div>
                            <div>
                                <p className="text-gray-500">Gender</p>
                                <p className="font-medium">{student.student_profile.gender}</p>
                            </div>
                            <div>
                                <p className="text-gray-500">Status</p>
                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${student.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                    {student.is_active ? "Active" : "Inactive"}
                                </span>
                            </div>
                        </div>
                        <div className="pt-4 border-t">
                            <p className="text-sm text-gray-500 mb-1">Address</p>
                            <p className="text-sm font-medium flex items-start gap-2">
                                <MapPin className="h-4 w-4 mt-0.5 text-gray-400" />
                                {student.student_profile.student_address}
                            </p>
                        </div>
                    </CardContent>
                </Card>

                {/* Parent Info Card */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <User className="h-5 w-5" />
                            Parent / Guardian
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-3">
                            <div>
                                <p className="text-sm text-gray-500">Name</p>
                                <p className="text-base font-medium">{student.student_profile.parent_name}</p>
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                                <Phone className="h-4 w-4 text-gray-400" />
                                <span>{student.student_profile.parent_phone}</span>
                            </div>
                            {student.student_profile.parent_email && (
                                <div className="flex items-center gap-2 text-sm">
                                    <Mail className="h-4 w-4 text-gray-400" />
                                    <span>{student.student_profile.parent_email}</span>
                                </div>
                            )}
                            <div className="flex items-start gap-2 text-sm">
                                <MapPin className="h-4 w-4 mt-0.5 text-gray-400" />
                                <span>{student.student_profile.parent_address}</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Education History - Spans full width */}
                <Card className="md:col-span-2">
                    <CardHeader>
                        <CardTitle>Academic Background</CardTitle>
                        <CardDescription>Records of previous education and achievements</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <EducationHistoryList
                            studentId={student.id}
                            initialHistory={student.student_profile.education_history || []}
                        />
                    </CardContent>
                </Card>
            </div>

            {/* Modals */}
            <EditStudentModal
                open={showEdit}
                onOpenChange={setShowEdit}
                student={student}
                onSuccess={fetchStudent}
            />
            <DeleteStudentDialog
                open={showDelete}
                onOpenChange={setShowDelete}
                student={student}
                onSuccess={() => router.push(`/${locale}/dashboard/students`)}
            />
        </div>
    )
}
