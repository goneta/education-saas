"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Button } from "@/components/ui/button"
import { Plus, Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { TeacherListTable, Teacher } from "@/components/teachers/teacher-list-table"
import { AddTeacherModal } from "@/components/teachers/add-teacher-modal"
import { EditTeacherModal } from "@/components/teachers/edit-teacher-modal"
import { DeleteTeacherDialog } from "@/components/teachers/delete-teacher-dialog"

export default function TeachersPage() {
    const { token } = useAuth()
    const [teachers, setTeachers] = useState<Teacher[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")

    // Modals state
    const [showAddModal, setShowAddModal] = useState(false)
    const [showEditModal, setShowEditModal] = useState(false)
    const [showDeleteDialog, setShowDeleteDialog] = useState(false)
    const [selectedTeacher, setSelectedTeacher] = useState<Teacher | null>(null)

    useEffect(() => {
        if (token) {
            fetchTeachers()
        }
    // Teacher list loading is intentionally bound to the auth token.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token])

    const fetchTeachers = async () => {
        setIsLoading(true)
        try {
            const res = await fetch(`${API_BASE_URL}/teachers`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) {
                const data = await res.json()
                setTeachers(data)
            }
        } catch (error) {
            console.error("Failed to fetch teachers", error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleEdit = (teacher: Teacher) => {
        setSelectedTeacher(teacher)
        setShowEditModal(true)
    }

    const handleDelete = (id: number) => {
        const teacher = teachers.find(t => t.id === id)
        if (teacher) {
            setSelectedTeacher(teacher)
            setShowDeleteDialog(true)
        }
    }

    const handleSuccess = () => {
        fetchTeachers()
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">Teachers</h1>
                    <p className="text-sm text-[#6B7280] mt-1">
                        Manage teaching staff and assignments
                    </p>
                </div>
                <Button
                    onClick={() => setShowAddModal(true)}
                    className="bg-black text-white hover:bg-black/90 rounded-lg"
                >
                    <Plus className="mr-2 h-4 w-4" /> Add Teacher
                </Button>
            </div>

            {/* Search Bar */}
            <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6B7280]" />
                <Input
                    type="search"
                    placeholder="Search teachers..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-[#E5E7EB] rounded-lg bg-white text-[#111827] placeholder:text-[#6B7280] focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
            </div>

            <TeacherListTable
                teachers={teachers}
                isLoading={isLoading}
                searchQuery={searchQuery}
                onEdit={handleEdit}
                onDelete={(id) => handleDelete(id)}
            />

            <AddTeacherModal
                open={showAddModal}
                onOpenChange={setShowAddModal}
                onSuccess={handleSuccess}
            />

            <EditTeacherModal
                open={showEditModal}
                onOpenChange={setShowEditModal}
                teacher={selectedTeacher}
                onSuccess={handleSuccess}
            />

            <DeleteTeacherDialog
                open={showDeleteDialog}
                onOpenChange={setShowDeleteDialog}
                teacher={selectedTeacher}
                onSuccess={handleSuccess}
            />
        </div>
    )
}
