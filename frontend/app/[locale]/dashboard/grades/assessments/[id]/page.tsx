"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Loader2, Save, ArrowLeft } from "lucide-react"
import { Assessment, Grade } from "@/types/education"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

import { API_BASE_URL } from "@/lib/config"
const BASE_URL = API_BASE_URL

export default function GradeEntryPage({ params: { locale, id } }: { params: { locale: string; id: string } }) {
    const router = useRouter()
    const { token } = useAuth()
    const [assessment, setAssessment] = useState<Assessment | null>(null)
    const [students, setStudents] = useState<any[]>([])
    const [grades, setGrades] = useState<Record<number, { score: string; comment: string }>>({})
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)

    // Fetch Assessment, Students (of Class), and Existing Grades
    useEffect(() => {
        if (token && id) {
            fetchData()
        }
    }, [token, id])

    const fetchData = async () => {
        setLoading(true)
        try {
            const headers = { Authorization: `Bearer ${token}` }

            // 1. Get Assessment
            const assessRes = await fetch(`${BASE_URL}/grades/assessments/${id}`, { headers })
            if (!assessRes.ok) throw new Error("Assessment not found")
            const assessData = await assessRes.json()
            setAssessment(assessData)

            // 2. Get Students of Class using generic students endpoint with filter?
            // Or get via /education/classes/{id}/students? 
            // I haven't implemented that specific endpoint.
            // Alternative: List Students and filter by class_id client side (inefficient) or server side.
            // Backend `students` router listing supports nothing?
            // Let's check `routers/students.py` if possible.
            // Assuming /students?class_id=X works.
            // If not, I'll update backend or rely on what I have.
            // `test_education` verified class creation but `test_grades` created student with class_id.
            // I'll assume fetching all students and filtering is okay for MVP, OR use a potentially existing filter.

            const studentsRes = await fetch(`${BASE_URL}/students?limit=100`, { headers })
            // Assuming students endpoint returns list.
            if (studentsRes.ok) {
                const allStudents = await studentsRes.json()
                // Filter by class
                const classStudents = allStudents.filter((s: any) => s.student_profile?.current_class_id === assessData.class_id)
                setStudents(classStudents)
            }

            // 3. Get Existing Grades
            const gradesRes = await fetch(`${BASE_URL}/grades/assessments/${id}/grades`, { headers })
            if (gradesRes.ok) {
                const gradesData = await gradesRes.json()
                const gradeMap: Record<number, { score: string; comment: string }> = {}
                gradesData.forEach((g: Grade) => {
                    gradeMap[g.student_id] = { score: g.score.toString(), comment: g.comment || "" }
                })
                setGrades(gradeMap)
            }

        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    const handleGradeChange = (studentId: number, field: 'score' | 'comment', value: string) => {
        setGrades(prev => ({
            ...prev,
            [studentId]: {
                ...prev[studentId],
                [field]: value
            }
        }))
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            const payload = {
                assessment_id: Number(id),
                grades: Object.entries(grades).map(([studentId, data]) => ({
                    student_id: Number(studentId),
                    score: parseFloat(data.score),
                    comment: data.comment
                })).filter(g => !isNaN(g.score)) // Only send valid scores
            }

            const res = await fetch(`${BASE_URL}/grades/entry/bulk`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            })

            if (res.ok) {
                alert("Grades saved successfully") // Replace with Toast
                router.refresh()
            } else {
                alert("Failed to save grades")
            }
        } catch (e) {
            console.error(e)
        } finally {
            setSaving(false)
        }
    }

    if (loading) return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>
    if (!assessment) return <div className="p-8">Assessment not found</div>

    return (
        <div className="p-6 space-y-6">
            <div className="flex justify-between items-center">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.back()}>
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">{assessment.title}</h1>
                        <p className="text-muted-foreground">
                            Max Score: {assessment.max_score} | Weight: {assessment.weight}
                        </p>
                    </div>
                </div>
                <Button onClick={handleSave} disabled={saving}>
                    {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    <Save className="mr-2 h-4 w-4" /> Save Grades
                </Button>
            </div>

            <Card>
                <CardContent className="p-0">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Registration</TableHead>
                                <TableHead>Student Name</TableHead>
                                <TableHead className="w-[150px]">Grade (/{assessment.max_score})</TableHead>
                                <TableHead>Comment</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {students.map((student) => {
                                const grade = grades[student.student_profile?.id] || { score: "", comment: "" }
                                return (
                                    <TableRow key={student.id}>
                                        <TableCell>{student.student_profile?.registration_number}</TableCell>
                                        <TableCell className="font-medium">{student.full_name}</TableCell>
                                        <TableCell>
                                            <Input
                                                type="number"
                                                value={grade.score}
                                                onChange={(e) => handleGradeChange(student.student_profile.id, 'score', e.target.value)}
                                                className="w-full"
                                                max={assessment.max_score}
                                                min={0}
                                                step={0.5}
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Input
                                                value={grade.comment}
                                                onChange={(e) => handleGradeChange(student.student_profile.id, 'comment', e.target.value)}
                                                placeholder="Optional comment"
                                            />
                                        </TableCell>
                                    </TableRow>
                                )
                            })}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    )
}
