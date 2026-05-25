"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Search } from "lucide-react"

interface Student {
    id: number
    full_name: string
    email: string
    student_profile: {
        registration_number: string
        current_class_id: number | null
    }
}

interface Term {
    id: number
    name: string
}

interface ReportSubject {
    subject_id: number
    subject_name: string
    coefficient: number
    average: number
    assessments: Array<{ assessment: string; score: number; max: number; weight: number }>
}

interface ReportCard {
    student_id: number
    term_id: number
    subjects: ReportSubject[]
    overall_average: number
}

export default function GradeReportsPage() {
    const { token } = useAuth()
    const [students, setStudents] = useState<Student[]>([])
    const [terms, setTerms] = useState<Term[]>([])
    const [selectedStudentId, setSelectedStudentId] = useState("")
    const [selectedTermId, setSelectedTermId] = useState("")
    const [searchQuery, setSearchQuery] = useState("")
    const [report, setReport] = useState<ReportCard | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!token) return
        const fetchMeta = async () => {
            try {
                const [studentsRes, termsRes] = await Promise.all([
                    fetch(`${API_BASE_URL}/students/`, { headers: { Authorization: `Bearer ${token}` } }),
                    fetch(`${API_BASE_URL}/education/terms`, { headers: { Authorization: `Bearer ${token}` } })
                ])
                if (studentsRes.ok) setStudents(await studentsRes.json())
                if (termsRes.ok) setTerms(await termsRes.json())
            } catch (error) {
                console.error(error)
            }
        }
        fetchMeta()
    }, [token])

    const handleGenerateReport = async () => {
        if (!selectedStudentId || !selectedTermId) {
            setError("Please select a student and a term")
            return
        }
        setIsLoading(true)
        setError(null)
        setReport(null)
        try {
            const res = await fetch(
                `${API_BASE_URL}/grades/reports/student/${selectedStudentId}/term/${selectedTermId}`,
                { headers: { Authorization: `Bearer ${token}` } }
            )
            if (res.ok) {
                setReport(await res.json())
            } else {
                const data = await res.json()
                setError(data.detail || "Failed to generate report")
            }
        } catch {
            setError("An error occurred")
        } finally {
            setIsLoading(false)
        }
    }

    const filteredStudents = students.filter(s =>
        s.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.student_profile?.registration_number?.toLowerCase().includes(searchQuery.toLowerCase())
    )

    const selectedStudent = students.find(s => s.id.toString() === selectedStudentId)
    const selectedTerm = terms.find(t => t.id.toString() === selectedTermId)

    const getGradeBadge = (avg: number) => {
        if (avg >= 16) return "bg-green-100 text-green-800"
        if (avg >= 12) return "bg-blue-100 text-blue-800"
        if (avg >= 10) return "bg-yellow-100 text-yellow-800"
        return "bg-red-100 text-red-800"
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">Grade Reports</h1>
                <p className="text-sm text-[#6B7280] mt-1">Generate student report cards by term</p>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-[#111827] text-base">Generate Report Card</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className="space-y-2">
                            <Label>Student *</Label>
                            <div className="space-y-2">
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6B7280]" />
                                    <input
                                        type="search"
                                        placeholder="Search students..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="w-full pl-10 pr-4 py-2 border border-[#E5E7EB] rounded-lg bg-white text-[#111827] placeholder:text-[#6B7280] focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                                    />
                                </div>
                                <select
                                    value={selectedStudentId}
                                    onChange={(e) => setSelectedStudentId(e.target.value)}
                                    className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                                    size={4}
                                >
                                    <option value="">-- Select student --</option>
                                    {filteredStudents.map(s => (
                                        <option key={s.id} value={s.id}>{s.full_name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Term *</Label>
                            <select
                                value={selectedTermId}
                                onChange={(e) => setSelectedTermId(e.target.value)}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="">-- Select term --</option>
                                {terms.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                            </select>
                        </div>
                        <div className="flex items-end">
                            <Button
                                onClick={handleGenerateReport}
                                disabled={isLoading || !selectedStudentId || !selectedTermId}
                                className="bg-black text-white hover:bg-black/90 w-full"
                            >
                                {isLoading ? "Generating..." : "Generate Report"}
                            </Button>
                        </div>
                    </div>
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded text-sm">{error}</div>
                    )}
                </CardContent>
            </Card>

            {report && selectedStudent && selectedTerm && (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader>
                        <div className="flex items-start justify-between">
                            <div>
                                <CardTitle className="text-[#111827]">Report Card</CardTitle>
                                <p className="text-sm text-[#6B7280] mt-1">
                                    {selectedStudent.full_name} — {selectedStudent.student_profile?.registration_number}
                                </p>
                                <p className="text-sm text-[#6B7280]">Term: {selectedTerm.name}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm text-[#6B7280]">Overall Average</p>
                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-lg font-bold ${getGradeBadge(report.overall_average)}`}>
                                    {report.overall_average}/20
                                </span>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        {report.subjects.length === 0 ? (
                            <div className="text-center py-8 text-[#6B7280]">No grades recorded for this term.</div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-[#E5E7EB]">
                                            <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Subject</th>
                                            <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Coeff.</th>
                                            <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Average /20</th>
                                            <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Assessments</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {report.subjects.map((subject) => (
                                            <tr key={subject.subject_id} className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] transition-colors">
                                                <td className="py-3 px-4 text-sm font-medium text-[#111827]">{subject.subject_name}</td>
                                                <td className="py-3 px-4 text-sm text-[#6B7280]">{subject.coefficient}</td>
                                                <td className="py-3 px-4">
                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getGradeBadge(subject.average)}`}>
                                                        {subject.average}/20
                                                    </span>
                                                </td>
                                                <td className="py-3 px-4 text-sm text-[#6B7280]">
                                                    {subject.assessments.map((a, i) => (
                                                        <span key={i} className="mr-2">
                                                            {a.assessment}: {a.score}/{a.max}
                                                        </span>
                                                    ))}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    )
}
