"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Search, Eye } from "lucide-react"
import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { useParams, useRouter } from "next/navigation"
import { AddStudentModal } from "@/components/students/add-student-modal"
import { EditStudentModal } from "@/components/students/edit-student-modal"
import { DeleteStudentDialog } from "@/components/students/delete-student-dialog"

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

export default function StudentsPage() {
    const { token } = useAuth()
    const params = useParams()
    const router = useRouter()
    const locale = params.locale as string

    const [searchQuery, setSearchQuery] = useState("")
    const [showAddModal, setShowAddModal] = useState(false)
    const [showEditModal, setShowEditModal] = useState(false)
    const [showDeleteDialog, setShowDeleteDialog] = useState(false)
    const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
    const [students, setStudents] = useState<Student[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Fetch students from API
    const fetchStudents = async () => {
        if (!token) {
            setError("Not authenticated")
            setIsLoading(false)
            return
        }

        try {
            setIsLoading(true)
            setError(null)

            const response = await fetch(`${API_BASE_URL}/students/`, {
                headers: {
                    "Authorization": `Bearer ${token}`,
                },
            })

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error("Session expired. Please log in again.")
                }
                throw new Error("Failed to fetch students")
            }

            const data = await response.json()
            setStudents(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred")
        } finally {
            setIsLoading(false)
        }
    }

    // Fetch students on component mount
    useEffect(() => {
        fetchStudents()
    // Student list loading is intentionally bound to the auth token.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token])

    // Filter students based on search query
    const filteredStudents = students.filter(student =>
        student.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        student.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        student.student_profile.registration_number.toLowerCase().includes(searchQuery.toLowerCase())
    )

    const handleStudentAdded = () => {
        // Refresh the student list
        fetchStudents()
    }

    const handleRowClick = (studentId: number) => {
        router.push(`/${locale}/dashboard/students/${studentId}`)
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">Students</h1>
                    <p className="text-sm text-[#6B7280] mt-1">
                        Manage student registrations and profiles
                    </p>
                </div>
                <Button
                    onClick={() => setShowAddModal(true)}
                    className="bg-black text-white hover:bg-black/90 rounded-lg"
                >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Student
                </Button>
            </div>

            {/* Search Bar */}
            <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6B7280]" />
                <input
                    type="search"
                    placeholder="Search students..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-[#E5E7EB] rounded-lg bg-white text-[#111827] placeholder:text-[#6B7280] focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
            </div>

            {/* Error Message */}
            {error && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
                    {error}
                </div>
            )}

            {/* Students Table Card */}
            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-[#111827]">Student List</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="text-center py-12">
                            <p className="text-[#6B7280]">Loading students...</p>
                        </div>
                    ) : filteredStudents.length === 0 ? (
                        <div className="text-center py-12">
                            <p className="text-[#6B7280]">
                                {searchQuery ? `No students found matching "${searchQuery}"` : "No students found. Add your first student!"}
                            </p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-[#E5E7EB]">
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Name</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Email</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Registration No.</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Gender</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Status</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredStudents.map((student) => (
                                        <tr
                                            key={student.id}
                                            className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] transition-colors cursor-pointer"
                                            onClick={() => handleRowClick(student.id)}
                                        >
                                            <td className="py-3 px-4 text-sm text-[#111827] font-medium">{student.full_name}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{student.email}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{student.student_profile.registration_number}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{student.student_profile.gender}</td>
                                            <td className="py-3 px-4">
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${student.is_active
                                                    ? "bg-green-100 text-green-800"
                                                    : "bg-gray-100 text-gray-800"
                                                    }`}>
                                                    {student.is_active ? "Active" : "Inactive"}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4" onClick={(e) => e.stopPropagation()}>
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                                                        onClick={() => handleRowClick(student.id)}
                                                    >
                                                        <Eye className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-[#2563EB] hover:text-[#2563EB] hover:bg-[#F0F1F3]"
                                                        onClick={(e) => {
                                                            e.stopPropagation()
                                                            setSelectedStudent(student)
                                                            setShowEditModal(true)
                                                        }}
                                                    >
                                                        Edit
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-red-600 hover:text-red-600 hover:bg-red-50"
                                                        onClick={(e) => {
                                                            e.stopPropagation()
                                                            setSelectedStudent(student)
                                                            setShowDeleteDialog(true)
                                                        }}
                                                    >
                                                        Delete
                                                    </Button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Add Student Modal */}
            <AddStudentModal
                open={showAddModal}
                onOpenChange={setShowAddModal}
                onSuccess={handleStudentAdded}
            />

            {/* Edit Student Modal */}
            <EditStudentModal
                open={showEditModal}
                onOpenChange={setShowEditModal}
                student={selectedStudent}
                onSuccess={handleStudentAdded}
            />

            {/* Delete Student Dialog */}
            <DeleteStudentDialog
                open={showDeleteDialog}
                onOpenChange={setShowDeleteDialog}
                student={selectedStudent}
                onSuccess={handleStudentAdded}
            />
        </div>
    )
}
