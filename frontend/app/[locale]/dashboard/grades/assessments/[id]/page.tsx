"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ArrowLeft, Save } from "lucide-react"
import { useRouter, useParams } from "next/navigation"

interface Assessment {
    id: number
    title: string
    date: string
    max_score: number
    weight: number
    class_id: number
    subject_id: number
    term_id: number
}

interface Grade {
    id: number
    student_id: number
    score: number
    comment: string | null
    assessment_id: number
}

interface Student {
    id: number
    full_name: string
    email: string
    student_profile: {
        registration_number: string
        current_class_id: number | null
    }
}

export default function AssessmentGradesPage() {
    const { token } = useAuth()
    const router = useRouter()
    const params = useParams()
    const locale = params.locale as string
    const assessmentId = params.id as string

    const [assessment, setAssessment] = useState<Assessment | null>(null)
    const [students, setStudents] = useState<Student[]>([])
    const [grades, setGrades] = useState<Grade[]>([])
    const [gradeInputs, setGradeInputs] = useState<Record<number, { score: string; comment: string }>>({})
    const [isLoading, setIsLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [saveMessage, setSaveMessage] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!token || !assessmentId) return
        loadData()
    }, [token, assessmentId])

    const loadData = async () => {
        setIsLoading(true)
        try {
            const [assessmentRes, gradesRes] = await Promise.all([
                fetch(`${API_BASE_URL}/grades/assessments/${assessmentId}`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                fetch(`${API_BASE_URL}/grades/assessments/${assessmentId}/grades`, {
                    headers: { Authorization: `Bearer ${token}` }
                })
            ])

            if (!assessmentRes.ok) throw new Error("Assessment not found")
            const assessmentData: Assessment = await assessmentRes.json()
            setAssessment(assessmentData)

            const existingGrades: Grade[] = gradesRes.ok ? await gradesRes.json() : []
            setGrades(existingGrades)

            // Fetch students in the class
            const studentsRes = await fetch(
                `${API_BASE_URL}/students/?class_id=${assessmentData.class_id}`,
                { headers: { Authorization: `Bearer ${token}` } }
            )
            const studentsData: Student[] = studentsRes.ok ? await studentsRes.json() : []
            setStudents(studentsData)

            // Initialize grade inputs from existing grades
            const inputs: Record<number, { score: string; comment: string }> = {}
            studentsData.forEach(student => {
                const existing = existingGrades.find(g => g.student_id === student.id)
                inputs[student.id] = {
                    score: existing ? existing.score.toString() : "",
                    comment: existing?.comment || ""
                }
            })
            setGradeInputs(inputs)
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load data")
        } finally {
            setIsLoading(false)
        }
    }

    const handleSaveGrades = async () => {
        setSaving(true)
        setError(null)
        setSaveMessage(null)
        try {
            const gradesToSubmit = students
                .filter(s => gradeInputs[s.id]?.score !== "")
                .map(s => ({
                    student_id: s.id,
                    score: parseFloat(gradeInputs[s.id].score),
                    comment: gradeInputs[s.id].comment || null
                }))

            if (gradesToSubmit.length === 0) {
                setError("No grades entered")
                return
            }

            const res = await fetch(`${API_BASE_URL}/grades/entry/bulk`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({
                    assessment_id: parseInt(assessmentId),
                    grades: gradesToSubmit
                })
            })

            if (res.ok) {
                setSaveMessage(`Successfully saved ${gradesToSubmit.length} grades`)
                loadData()
            } else {
                const data = await res.json()
                setError(data.detail || "Failed to save grades")
            }
        } catch (e) {
            setError("An error occurred")
        } finally {
            setSaving(false)
        }
    }

    if (isLoading) {
        return <div className="text-center py-12 text-[#6B7280]">Loading assessment...</div>
    }

    if (error && !assessment) {
        return (
            <div className="space-y-4">
                <Button variant="ghost" onClick={() => router.back()} className="gap-2">
                    <ArrowLeft className="h-4 w-4" /> Back
                </Button>
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">{error}</div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Button variant="ghost" onClick={() => router.push(`/${locale}/dashboard/grades/assessments`)} className="gap-2">
                    <ArrowLeft className="h-4 w-4" /> Back
                </Button>
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">{assessment?.title}</h1>
                    <p className="text-sm text-[#6B7280] mt-1">
                        {assessment && new Date(assessment.date).toLocaleDateString()}
                        {" — "}Max Score: {assessment?.max_score}
                        {" — "}Weight: {assessment?.weight}
                    </p>
                </div>
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">{error}</div>
            )}
            {saveMessage && (
                <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg">{saveMessage}</div>
            )}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-[#111827]">Grade Entry ({students.length} students)</CardTitle>
                    <Button
                        onClick={handleSaveGrades}
                        disabled={saving}
                        className="bg-black text-white hover:bg-black/90"
                    >
                        <Save className="h-4 w-4 mr-2" />
                        {saving ? "Saving..." : "Save Grades"}
                    </Button>
                </CardHeader>
                <CardContent>
                    {students.length === 0 ? (
                        <div className="text-center py-12 text-[#6B7280]">No students found in this class.</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-[#E5E7EB]">
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Student</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Reg. No.</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Score (/{assessment?.max_score})</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Comment</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {students.map((student) => (
                                        <tr key={student.id} className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] transition-colors">
                                            <td className="py-3 px-4 text-sm font-medium text-[#111827]">{student.full_name}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{student.student_profile?.registration_number || "—"}</td>
                                            <td className="py-3 px-4 w-32">
                                                <Input
                                                    type="number"
                                                    min="0"
                                                    max={assessment?.max_score}
                                                    step="0.5"
                                                    placeholder="—"
                                                    value={gradeInputs[student.id]?.score || ""}
                                                    onChange={(e) => setGradeInputs(prev => ({
                                                        ...prev,
                                                        [student.id]: { ...prev[student.id], score: e.target.value }
                                                    }))}
                                                    className="h-8 text-sm"
                                                />
                                            </td>
                                            <td className="py-3 px-4">
                                                <Input
                                                    placeholder="Optional comment"
                                                    value={gradeInputs[student.id]?.comment || ""}
                                                    onChange={(e) => setGradeInputs(prev => ({
                                                        ...prev,
                                                        [student.id]: { ...prev[student.id], comment: e.target.value }
                                                    }))}
                                                    className="h-8 text-sm"
                                                />
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
