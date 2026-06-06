"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Users, GraduationCap, Activity, Calendar } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"

interface ActivityItem {
    id: number
    description: string
    time: string
    type: string
}

interface DashboardStats {
    total_students: number
    upcoming_classes_today: number
    active_classes_count: number
    recent_activities: ActivityItem[]
}

export default function DashboardPage() {
    const { token } = useAuth()
    const [stats, setStats] = useState<DashboardStats | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchStats = async () => {
            if (!token) return

            try {
                const response = await fetch(`${API_BASE_URL}/dashboard/stats`, {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                })

                if (response.ok) {
                    const data = await response.json()
                    setStats(data)
                }
            } catch (error) {
                console.error("Failed to fetch dashboard stats:", error)
            } finally {
                setLoading(false)
            }
        }

        fetchStats()
    }, [token])

    return (
        <div className="grid min-h-full w-full auto-rows-max items-start gap-4 md:gap-8">
            <div className="grid w-full gap-4 md:grid-cols-3 md:gap-8">
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-[#111827]">
                            Total Students
                        </CardTitle>
                        <Users className="h-4 w-4 text-[#6B7280]" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-[#111827]">
                            {loading ? "..." : stats?.total_students ?? 0}
                        </div>
                        <p className="text-xs text-[#6B7280]">
                            Registered students
                        </p>
                    </CardContent>
                </Card>
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-[#111827]">
                            Classes Today
                        </CardTitle>
                        <Calendar className="h-4 w-4 text-[#6B7280]" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-[#111827]">
                            {loading ? "..." : stats?.upcoming_classes_today ?? 0}
                        </div>
                        <p className="text-xs text-[#6B7280]">
                            Scheduled classes
                        </p>
                    </CardContent>
                </Card>
                {/* Placeholder for future cards to keep layout balanced */}
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-[#111827]">Active Classes</CardTitle>
                        <GraduationCap className="h-4 w-4 text-[#6B7280]" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-[#111827]">{loading ? "..." : stats?.active_classes_count ?? 0}</div>
                        <p className="text-xs text-[#6B7280]">
                            Currently in session
                        </p>
                    </CardContent>
                </Card>
            </div>
            <div className="grid w-full gap-4 md:gap-8">
                <Card className="w-full rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-[#111827]">Recent Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {loading ? (
                                <p className="text-sm text-[#6B7280]">Loading activities...</p>
                            ) : stats?.recent_activities && stats.recent_activities.length > 0 ? (
                                stats.recent_activities.map((activity) => (
                                    <div key={activity.id} className="flex items-center">
                                        <Activity className="mr-2 h-4 w-4 text-[#6B7280]" />
                                        <div className="space-y-1">
                                            <p className="text-sm font-medium leading-none text-[#111827]">
                                                {activity.description}
                                            </p>
                                            <p className="text-xs text-[#6B7280]">
                                                {new Date(activity.time).toLocaleString()}
                                            </p>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <p className="text-sm text-[#6B7280]">
                                    No recent activity found.
                                </p>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
