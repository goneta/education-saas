"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"

interface ClassItem {
    id: number
    name: string
}

interface AttendanceStats {
    total: number
    present: number
    absent: number
    late: number
    excused: number
}

export default function AttendanceReportsPage() {
    const { token } = useAuth()
    const [classes, setClasses] = useState<ClassItem[]>([])
    const [selectedClassId, setSelectedClassId] = useState("")
    const [startDate, setStartDate] = useState("")
    const [endDate, setEndDate] = useState("")
    const [stats, setStats] = useState<AttendanceStats | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!token) return
        const fetchClasses = async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/education/classes`, {
                    headers: { Authorization: `Bearer ${token}` }
                })
                if (res.ok) setClasses(await res.json())
            } catch (error) {
                console.error(error)
            }
        }
        fetchClasses()
    }, [token])

    const handleGenerateReport = async () => {
        if (!selectedClassId) {
            setError("Please select a class")
            return
        }
        setIsLoading(true)
        setError(null)
        setStats(null)
        try {
            const parts = [`class_id=${selectedClassId}`]
            if (startDate) parts.push(`start_date=${startDate}T00:00:00`)
            if (endDate) parts.push(`end_date=${endDate}T23:59:59`)
            const res = await fetch(`${API_BASE_URL}/attendance/stats?${parts.join("&")}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) {
                setStats(await res.json())
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

    const selectedClass = classes.find(c => c.id.toString() === selectedClassId)

    const getPercentage = (value: number, total: number) =>
        total > 0 ? Math.round((value / total) * 100) : 0

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">Attendance Reports</h1>
                <p className="text-sm text-[#6B7280] mt-1">View attendance statistics by class and date range</p>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-[#111827] text-base">Report Filters</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                        <div className="space-y-2">
                            <Label>Class *</Label>
                            <select
                                value={selectedClassId}
                                onChange={(e) => setSelectedClassId(e.target.value)}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="">Select class</option>
                                {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                            </select>
                        </div>
                        <div className="space-y-2">
                            <Label>Start Date</Label>
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>End Date</Label>
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                        <div className="flex items-end">
                            <Button
                                onClick={handleGenerateReport}
                                disabled={isLoading || !selectedClassId}
                                className="bg-black text-white hover:bg-black/90 w-full"
                            >
                                {isLoading ? "Loading..." : "Generate Report"}
                            </Button>
                        </div>
                    </div>
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded text-sm">{error}</div>
                    )}
                </CardContent>
            </Card>

            {stats && (
                <>
                    <div className="flex items-center gap-2">
                        <h2 className="text-lg font-semibold text-[#111827]">
                            Results for {selectedClass?.name}
                        </h2>
                        {(startDate || endDate) && (
                            <span className="text-sm text-[#6B7280]">
                                ({startDate && new Date(startDate).toLocaleDateString()}{startDate && endDate && " – "}{endDate && new Date(endDate).toLocaleDateString()})
                            </span>
                        )}
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                            <CardContent className="pt-6">
                                <p className="text-sm text-[#6B7280]">Total Records</p>
                                <p className="text-3xl font-bold text-[#111827]">{stats.total}</p>
                            </CardContent>
                        </Card>
                        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                            <CardContent className="pt-6">
                                <p className="text-sm text-[#6B7280]">Present</p>
                                <p className="text-3xl font-bold text-green-600">{stats.present}</p>
                                <p className="text-xs text-[#6B7280]">{getPercentage(stats.present, stats.total)}%</p>
                            </CardContent>
                        </Card>
                        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                            <CardContent className="pt-6">
                                <p className="text-sm text-[#6B7280]">Absent</p>
                                <p className="text-3xl font-bold text-red-600">{stats.absent}</p>
                                <p className="text-xs text-[#6B7280]">{getPercentage(stats.absent, stats.total)}%</p>
                            </CardContent>
                        </Card>
                        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                            <CardContent className="pt-6">
                                <p className="text-sm text-[#6B7280]">Late / Excused</p>
                                <p className="text-3xl font-bold text-yellow-600">{stats.late + stats.excused}</p>
                                <p className="text-xs text-[#6B7280]">
                                    {stats.late} late, {stats.excused} excused
                                </p>
                            </CardContent>
                        </Card>
                    </div>

                    <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                        <CardHeader>
                            <CardTitle className="text-[#111827] text-base">Attendance Breakdown</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {stats.total === 0 ? (
                                <div className="text-center py-8 text-[#6B7280]">No attendance records found for the selected filters.</div>
                            ) : (
                                <div className="space-y-3">
                                    {[
                                        { label: "Present", value: stats.present, color: "bg-green-500" },
                                        { label: "Absent", value: stats.absent, color: "bg-red-500" },
                                        { label: "Late", value: stats.late, color: "bg-yellow-500" },
                                        { label: "Excused", value: stats.excused, color: "bg-blue-500" }
                                    ].map((item) => (
                                        <div key={item.label} className="flex items-center gap-4">
                                            <span className="w-16 text-sm text-[#6B7280]">{item.label}</span>
                                            <div className="flex-1 bg-[#F3F4F6] rounded-full h-3 overflow-hidden">
                                                <div
                                                    className={`${item.color} h-full rounded-full transition-all`}
                                                    style={{ width: `${getPercentage(item.value, stats.total)}%` }}
                                                />
                                            </div>
                                            <span className="w-20 text-sm text-[#111827] text-right">
                                                {item.value} ({getPercentage(item.value, stats.total)}%)
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    )
}
