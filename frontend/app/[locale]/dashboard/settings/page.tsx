"use client"

import { useEffect, useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface School {
    id: number
    name: string
    domain_prefix: string
    school_type: string
    address: string | null
    is_active: boolean
}

export default function SettingsPage() {
    const { token, user } = useAuth()
    const [schools, setSchools] = useState<School[]>([])

    const loadSchools = async () => {
        if (!token || user?.role !== "super_admin") return
        const res = await fetch(`${API_BASE_URL}/system/schools`, { headers: { Authorization: `Bearer ${token}` } })
        if (res.ok) setSchools(await res.json())
    }

    const toggleSchool = async (school: School) => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/system/schools/${school.id}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ is_active: !school.is_active })
        })
        if (res.ok) loadSchools()
    }

    useEffect(() => { loadSchools() /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [token, user?.role])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">Settings</h1>
                <p className="text-sm text-[#6B7280] mt-1">Tenant context, school status and platform administration.</p>
            </div>

            <Card>
                <CardHeader><CardTitle>Active Context</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-3 text-sm">
                    <Info label="User" value={user?.full_name || "-"} />
                    <Info label="Role" value={user?.role || "-"} />
                    <Info label="School ID" value={user?.school_id?.toString() || "Platform"} />
                </CardContent>
            </Card>

            {user?.role === "super_admin" && (
                <Card>
                    <CardHeader><CardTitle>Schools</CardTitle></CardHeader>
                    <CardContent>
                        <table className="w-full text-sm">
                            <thead><tr className="border-b"><th className="py-2 text-left">School</th><th className="py-2 text-left">Domain</th><th className="py-2 text-left">Type</th><th className="py-2 text-left">Status</th><th className="py-2 text-right">Action</th></tr></thead>
                            <tbody>{schools.map(school => <tr key={school.id} className="border-b last:border-0"><td className="py-2 font-medium">{school.name}</td><td className="py-2">{school.domain_prefix}</td><td className="py-2">{school.school_type}</td><td className="py-2">{school.is_active ? "Active" : "Suspended"}</td><td className="py-2 text-right"><Button variant="outline" size="sm" onClick={() => toggleSchool(school)}>{school.is_active ? "Suspend" : "Reactivate"}</Button></td></tr>)}</tbody>
                        </table>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}

function Info({ label, value }: { label: string; value: string }) {
    return <div><p className="text-[#6B7280]">{label}</p><p className="font-medium text-[#111827]">{value}</p></div>
}
