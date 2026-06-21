"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Pencil, Trash2 } from "lucide-react"

export interface Teacher {
    id: number
    full_name: string
    email: string
    phone_number?: string
    address?: string
    teacher_profile?: {
        specialization?: string
        join_date?: string
        bio?: string
    }
}

interface TeacherListTableProps {
    teachers: Teacher[]
    isLoading: boolean
    error?: string | null
    searchQuery: string
    onEdit: (teacher: Teacher) => void
    onDelete: (id: number) => void
}

export function TeacherListTable({
    teachers,
    isLoading,
    error,
    searchQuery,
    onEdit,
    onDelete
}: TeacherListTableProps) {
    const filteredTeachers = teachers.filter(teacher =>
        teacher.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        teacher.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (teacher.teacher_profile?.specialization || "").toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
            <CardHeader>
                <CardTitle className="text-[#111827]">Teacher List</CardTitle>
            </CardHeader>
            <CardContent>
                {error ? (
                    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                        {error}
                    </div>
                ) : isLoading ? (
                    <div className="text-center py-12">
                        <p className="text-[#6B7280]">Loading teachers...</p>
                    </div>
                ) : filteredTeachers.length === 0 ? (
                    <div className="text-center py-12">
                        <p className="text-[#6B7280]">
                            {searchQuery ? `No teachers found matching "${searchQuery}"` : "No teachers found. Add your first teacher!"}
                        </p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-[#E5E7EB]">
                                    <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Name</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Specialization</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Email</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Phone</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredTeachers.map((teacher) => (
                                    <tr
                                        key={teacher.id}
                                        className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] transition-colors"
                                    >
                                        <td className="py-3 px-4 text-sm text-[#111827] font-medium">
                                            <div className="flex items-center gap-3">
                                                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs">
                                                    {teacher.full_name.charAt(0)}
                                                </div>
                                                {teacher.full_name}
                                            </div>
                                        </td>
                                        <td className="py-3 px-4 text-sm text-[#6B7280]">
                                            {teacher.teacher_profile?.specialization || "General"}
                                        </td>
                                        <td className="py-3 px-4 text-sm text-[#6B7280]">{teacher.email}</td>
                                        <td className="py-3 px-4 text-sm text-[#6B7280]">{teacher.phone_number || "-"}</td>
                                        <td className="py-3 px-4">
                                            <div className="flex gap-2">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="h-8 text-[#2563EB] hover:text-[#2563EB] hover:bg-[#F0F1F3]"
                                                    onClick={() => onEdit(teacher)}
                                                >
                                                    <Pencil className="h-3.5 w-3.5 mr-1" /> Edit
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="h-8 text-red-600 hover:text-red-600 hover:bg-red-50"
                                                    onClick={() => onDelete(teacher.id)}
                                                >
                                                    <Trash2 className="h-3.5 w-3.5 mr-1" /> Delete
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
    )
}
