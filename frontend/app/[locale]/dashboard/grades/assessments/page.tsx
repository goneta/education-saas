"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Plus, Loader2 } from "lucide-react"
import { Assessment } from "@/types/education"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CreateAssessmentModal } from "@/components/dashboard/grades/create-assessment-modal"

import { API_BASE_URL } from "@/lib/config"
const BASE_URL = API_BASE_URL

export default function AssessmentsPage({ params: { locale } }: { params: { locale: string } }) {
    const router = useRouter()
    const { token } = useAuth()
    const [assessments, setAssessments] = useState<Assessment[]>([])
    const [loading, setLoading] = useState(true)
    const [isModalOpen, setIsModalOpen] = useState(false)

    useEffect(() => {
        if (token) {
            fetchAssessments()
        }
    }, [token])

    const fetchAssessments = async () => {
        try {
            const res = await fetch(`${BASE_URL}/grades/assessments`, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            })
            if (res.ok) {
                const data = await res.json()
                setAssessments(data)
            } else {
                console.error("Failed to fetch assessments")
            }
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="p-6 space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Assessments</h1>
                    <p className="text-muted-foreground">Manage exams and assignments.</p>
                </div>
                <Button onClick={() => setIsModalOpen(true)}>
                    <Plus className="mr-2 h-4 w-4" /> New Assessment
                </Button>
            </div>

            <CreateAssessmentModal
                open={isModalOpen}
                onOpenChange={setIsModalOpen}
                onSuccess={fetchAssessments}
            />

            <Card>
                <CardHeader>
                    <CardTitle>Recent Assessments</CardTitle>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="flex justify-center p-4">
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        </div>
                    ) : assessments.length === 0 ? (
                        <div className="text-center p-8 text-muted-foreground">
                            No assessments found. Create one to get started.
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Title</TableHead>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Date</TableHead>
                                    <TableHead>Class</TableHead>
                                    <TableHead>Subject</TableHead>
                                    <TableHead className="text-right">Max Score</TableHead>
                                    <TableHead></TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {assessments.map((assessment) => (
                                    <TableRow key={assessment.id}>
                                        <TableCell className="font-medium">{assessment.title}</TableCell>
                                        <TableCell className="capitalize">{assessment.type}</TableCell>
                                        <TableCell>{new Date(assessment.date).toLocaleDateString()}</TableCell>
                                        <TableCell>{assessment.class_id}</TableCell>
                                        <TableCell>{assessment.subject_id}</TableCell>
                                        <TableCell className="text-right">{assessment.max_score}</TableCell>
                                        <TableCell className="text-right">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => router.push(`/${locale}/dashboard/grades/assessments/${assessment.id}`)}
                                            >
                                                Enter Grades
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
