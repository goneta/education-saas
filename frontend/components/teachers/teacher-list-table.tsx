"use client"

import { useTranslations } from "next-intl"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Pencil, Trash2 } from "lucide-react"
import { ProfileAvatar } from "@/components/users/profile-avatar"

export interface Teacher {
    id: number
    full_name: string
    email: string
    phone_number?: string
    address?: string
    profile_photo_url?: string | null
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
    onPhotoChanged?: () => void | Promise<void>
}

export function TeacherListTable({
    teachers,
    isLoading,
    error,
    searchQuery,
    onEdit,
    onDelete,
    onPhotoChanged,
}: TeacherListTableProps) {
    const t = useTranslations("lists")
    const filteredTeachers = teachers.filter(teacher =>
        teacher.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        teacher.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (teacher.teacher_profile?.specialization || "").toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <Card data-teducai-collapsible="false" className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
            <CardHeader>
                <CardTitle className="text-[#111827]">{t("teachers.list")} ({filteredTeachers.length})</CardTitle>
            </CardHeader>
            <CardContent>
                {error ? (
                    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                        {error}
                    </div>
                ) : isLoading ? (
                    <div className="text-center py-12">
                        <p className="text-[#6B7280]">{t("teachers.loading")}</p>
                    </div>
                ) : filteredTeachers.length === 0 ? (
                    <div className="text-center py-12">
                        <p className="text-[#6B7280]">
                            {searchQuery ? t("teachers.emptySearch", { query: searchQuery }) : t("teachers.empty")}
                        </p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-[#E5E7EB]">
                                    <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">{t("common.name")}</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">{t("teachers.specialization")}</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">{t("common.email")}</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">{t("teachers.phone")}</th>
                                    <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">{t("common.actions")}</th>
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
                                                <ProfileAvatar userId={teacher.id} name={teacher.full_name} photoUrl={teacher.profile_photo_url} onChanged={onPhotoChanged} />
                                                {teacher.full_name}
                                            </div>
                                        </td>
                                        <td className="py-3 px-4 text-sm text-[#6B7280]">
                                            {teacher.teacher_profile?.specialization || t("teachers.general")}
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
                                                    <Pencil className="h-3.5 w-3.5 mr-1" /> {t("common.edit")}
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="h-8 text-red-600 hover:text-red-600 hover:bg-red-50"
                                                    onClick={() => onDelete(teacher.id)}
                                                >
                                                    <Trash2 className="h-3.5 w-3.5 mr-1" /> {t("common.delete")}
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
