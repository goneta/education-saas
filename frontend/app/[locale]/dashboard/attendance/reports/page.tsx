"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"

export default function AttendanceReportsPage() {
    const { token } = useAuth()
    const [selectedClass, setSelectedClass] = useState<string>("")
    const [classes, setClasses] = useState<any[]>([])
    const [students, setStudents] = useState<any[]>([])
    const [attendanceData, setAttendanceData] = useState<any[]>([])
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (token) fetchClasses()
    }, [token])

    useEffect(() => {
        if (token && selectedClass) {
            fetchData()
        }
    }, [token, selectedClass])

    const fetchClasses = async () => {
        const res = await fetch(`${API_BASE_URL}/education/classes`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) setClasses(await res.json())
    }

    const fetchData = async () => {
        setLoading(true)
        try {
            // Fetch Students
            const studentsRes = await fetch(`${API_BASE_URL}/students?class_id=${selectedClass}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            const studentsList = await studentsRes.json()
            setStudents(studentsList)

            // Fetch All Attendance for Class
            // Note: This matches the class filter in GET /attendance
            const attRes = await fetch(`${API_BASE_URL}/attendance/?class_id=${selectedClass}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            const attList = await attRes.json()
            setAttendanceData(attList)

        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    // Compute stats per student
    const getStudentStats = (studentId: number) => {
        const records = attendanceData.filter(a => a.student_id === studentId)
        const total = records.length
        const present = records.filter(a => a.status === "present").length
        const absent = records.filter(a => a.status === "absent").length
        const late = records.filter(a => a.status === "late").length
        const excused = records.filter(a => a.status === "excused").length

        const rate = total > 0 ? ((present + late) / total) * 100 : 0

        return { total, present, absent, late, excused, rate }
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Attendance Reports</h1>
                <Select value={selectedClass} onValueChange={setSelectedClass}>
                    <SelectTrigger className="w-[200px]">
                        <SelectValue placeholder="Select Class" />
                    </SelectTrigger>
                    <SelectContent>
                        {classes.map(c => (
                            <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            {selectedClass ? (
                <Card>
                    <CardHeader>
                        <CardTitle>Class Overview</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div>Loading...</div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Student</TableHead>
                                        <TableHead className="text-center">Total Classes</TableHead>
                                        <TableHead className="text-center text-green-600">Present</TableHead>
                                        <TableHead className="text-center text-red-600">Absent</TableHead>
                                        <TableHead className="text-center text-yellow-600">Late</TableHead>
                                        <TableHead className="text-center text-blue-600">Excused</TableHead>
                                        <TableHead className="text-right">Presence Rate</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {students.map(student => {
                                        const stats = getStudentStats(student.student_profile.id)
                                        return (
                                            <TableRow key={student.id}>
                                                <TableCell className="font-medium">{student.full_name}</TableCell>
                                                <TableCell className="text-center">{stats.total}</TableCell>
                                                <TableCell className="text-center bg-green-50">{stats.present}</TableCell>
                                                <TableCell className="text-center bg-red-50">{stats.absent}</TableCell>
                                                <TableCell className="text-center bg-yellow-50">{stats.late}</TableCell>
                                                <TableCell className="text-center bg-blue-50">{stats.excused}</TableCell>
                                                <TableCell className="text-right font-bold">
                                                    {stats.rate.toFixed(1)}%
                                                </TableCell>
                                            </TableRow>
                                        )
                                    })}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            ) : (
                <div className="text-center py-12 text-gray-500 border rounded-lg bg-gray-50">
                    Select a class to view reports.
                </div>
            )}
        </div>
    )
}
