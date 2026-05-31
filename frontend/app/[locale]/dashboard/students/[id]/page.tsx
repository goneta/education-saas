"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowLeft, User, BookOpen, CreditCard, FileText, Printer, CheckSquare } from "lucide-react"
import { useRouter, useParams } from "next/navigation"

interface Student {
    id: number
    email: string
    full_name: string
    role: string
    school_id: number
    is_active: boolean
    created_at: string
    student_profile: {
        id: number
        registration_number: string
        date_of_birth: string
        gender: string
        student_address: string
        parent_name: string
        parent_phone: string
        parent_email: string | null
        parent_address: string
        current_class_id: number | null
    }
}

interface Fee {
    id: number
    title: string
    amount: number
    due_date: string | null
    status: string
    total_paid: number
    remaining_balance: number
}

interface ClassItem {
    id: number
    name: string
}

interface RegistrationDocument {
    id: number
    name: string
    is_received: boolean
    notes: string | null
}

interface Certificate {
    id: number
    certificate_type: string
    status: string
    blocked_reason: string | null
    content: string | null
    generated_at: string
}

const STATUS_COLORS: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    partial: "bg-blue-100 text-blue-800",
    paid: "bg-green-100 text-green-800",
    overdue: "bg-red-100 text-red-800"
}

export default function StudentDetailPage() {
    const { token } = useAuth()
    const router = useRouter()
    const params = useParams()
    const locale = params.locale as string
    const studentId = params.id as string

    const [student, setStudent] = useState<Student | null>(null)
    const [fees, setFees] = useState<Fee[]>([])
    const [classes, setClasses] = useState<ClassItem[]>([])
    const [documents, setDocuments] = useState<RegistrationDocument[]>([])
    const [certificates, setCertificates] = useState<Certificate[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [activeTab, setActiveTab] = useState<"profile" | "fees" | "documents" | "certificates">("profile")

    useEffect(() => {
        if (!token || !studentId) return
        loadData()
    /* Student details intentionally refresh when route id or auth token changes. */
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token, studentId])

    const loadData = async () => {
        setIsLoading(true)
        setError(null)
        try {
            const [studentRes, feesRes, classesRes, docsRes, certificatesRes] = await Promise.all([
                fetch(`${API_BASE_URL}/students/${studentId}`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                fetch(`${API_BASE_URL}/finance/fees?student_id=${studentId}`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                fetch(`${API_BASE_URL}/education/classes`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                fetch(`${API_BASE_URL}/students/${studentId}/documents`, {
                    headers: { Authorization: `Bearer ${token}` }
                }),
                fetch(`${API_BASE_URL}/students/${studentId}/certificates`, {
                    headers: { Authorization: `Bearer ${token}` }
                })
            ])

            if (!studentRes.ok) throw new Error("Student not found")
            setStudent(await studentRes.json())
            if (feesRes.ok) setFees(await feesRes.json())
            if (classesRes.ok) setClasses(await classesRes.json())
            if (docsRes.ok) setDocuments(await docsRes.json())
            if (certificatesRes.ok) setCertificates(await certificatesRes.json())
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load student")
        } finally {
            setIsLoading(false)
        }
    }

    const getClassName = (id: number | null) => {
        if (!id) return "—"
        return classes.find(c => c.id === id)?.name || `Class #${id}`
    }

    const updateDocument = async (document: RegistrationDocument, isReceived: boolean) => {
        const res = await fetch(`${API_BASE_URL}/students/${studentId}/documents/${document.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ name: document.name, is_received: isReceived, notes: document.notes })
        })
        if (res.ok) loadData()
    }

    const generateCertificate = async (certificateType: string) => {
        const res = await fetch(`${API_BASE_URL}/students/${studentId}/certificates`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ certificate_type: certificateType })
        })
        if (res.ok) loadData()
    }

    if (isLoading) {
        return <div className="text-center py-12 text-[#6B7280]">Loading student...</div>
    }

    if (error || !student) {
        return (
            <div className="space-y-4">
                <Button variant="ghost" onClick={() => router.back()} className="gap-2">
                    <ArrowLeft className="h-4 w-4" /> Back
                </Button>
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg">
                    {error || "Student not found"}
                </div>
            </div>
        )
    }

    const totalFees = fees.reduce((sum, f) => sum + f.amount, 0)
    const paidFees = fees.reduce((sum, f) => sum + (f.total_paid || (f.status === "paid" ? f.amount : 0)), 0)

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Button variant="ghost" onClick={() => router.push(`/${locale}/dashboard/students`)} className="gap-2">
                    <ArrowLeft className="h-4 w-4" /> Back
                </Button>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold text-[#111827]">{student.full_name}</h1>
                    <p className="text-sm text-[#6B7280] mt-1">
                        {student.student_profile?.registration_number} — {getClassName(student.student_profile?.current_class_id)}
                    </p>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${student.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}`}>
                    {student.is_active ? "Active" : "Inactive"}
                </span>
                <Button variant="outline" onClick={() => window.print()} className="gap-2">
                    <Printer className="h-4 w-4" /> Print
                </Button>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 border-b border-[#E5E7EB]">
                <button
                    className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "profile" ? "border-black text-[#111827]" : "border-transparent text-[#6B7280] hover:text-[#111827]"}`}
                    onClick={() => setActiveTab("profile")}
                >
                    <User className="h-4 w-4" /> Profile
                </button>
                <button
                    className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "fees" ? "border-black text-[#111827]" : "border-transparent text-[#6B7280] hover:text-[#111827]"}`}
                    onClick={() => setActiveTab("fees")}
                >
                    <CreditCard className="h-4 w-4" /> Fees ({fees.length})
                </button>
                <button
                    className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "documents" ? "border-black text-[#111827]" : "border-transparent text-[#6B7280] hover:text-[#111827]"}`}
                    onClick={() => setActiveTab("documents")}
                >
                    <CheckSquare className="h-4 w-4" /> Documents
                </button>
                <button
                    className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === "certificates" ? "border-black text-[#111827]" : "border-transparent text-[#6B7280] hover:text-[#111827]"}`}
                    onClick={() => setActiveTab("certificates")}
                >
                    <FileText className="h-4 w-4" /> Certificates
                </button>
            </div>

            {activeTab === "profile" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                        <CardHeader>
                            <CardTitle className="text-[#111827] text-base flex items-center gap-2">
                                <User className="h-4 w-4" /> Personal Information
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            <InfoRow label="Full Name" value={student.full_name} />
                            <InfoRow label="Email" value={student.email} />
                            <InfoRow label="Registration No." value={student.student_profile?.registration_number} />
                            <InfoRow label="Date of Birth" value={student.student_profile?.date_of_birth ? new Date(student.student_profile.date_of_birth).toLocaleDateString() : "—"} />
                            <InfoRow label="Gender" value={student.student_profile?.gender} />
                            <InfoRow label="Address" value={student.student_profile?.student_address} />
                            <InfoRow label="Current Class" value={getClassName(student.student_profile?.current_class_id)} />
                        </CardContent>
                    </Card>

                    <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                        <CardHeader>
                            <CardTitle className="text-[#111827] text-base flex items-center gap-2">
                                <BookOpen className="h-4 w-4" /> Parent / Guardian Information
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            <InfoRow label="Parent Name" value={student.student_profile?.parent_name} />
                            <InfoRow label="Phone" value={student.student_profile?.parent_phone} />
                            <InfoRow label="Email" value={student.student_profile?.parent_email || "—"} />
                            <InfoRow label="Address" value={student.student_profile?.parent_address} />
                        </CardContent>
                    </Card>
                </div>
            )}

            {activeTab === "fees" && (
                <div className="space-y-4">
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                            <CardContent className="pt-6">
                                <p className="text-sm text-[#6B7280]">Total Fees</p>
                                <p className="text-2xl font-bold text-[#111827]">{totalFees.toLocaleString()} FCFA</p>
                            </CardContent>
                        </Card>
                        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                            <CardContent className="pt-6">
                                <p className="text-sm text-[#6B7280]">Paid</p>
                                <p className="text-2xl font-bold text-green-600">{paidFees.toLocaleString()} FCFA</p>
                            </CardContent>
                        </Card>
                        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                            <CardContent className="pt-6">
                                <p className="text-sm text-[#6B7280]">Outstanding</p>
                                <p className="text-2xl font-bold text-red-600">{(totalFees - paidFees).toLocaleString()} FCFA</p>
                            </CardContent>
                        </Card>
                    </div>

                    <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                        <CardContent className="pt-4">
                            {fees.length === 0 ? (
                                <div className="text-center py-8 text-[#6B7280]">No fees recorded for this student.</div>
                            ) : (
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead>
                                            <tr className="border-b border-[#E5E7EB]">
                                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Title</th>
                                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Amount</th>
                                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Paid</th>
                                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Remaining</th>
                                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Due Date</th>
                                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {fees.map((fee) => (
                                                <tr key={fee.id} className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] transition-colors">
                                                    <td className="py-3 px-4 text-sm font-medium text-[#111827]">{fee.title}</td>
                                                    <td className="py-3 px-4 text-sm text-[#111827]">{fee.amount.toLocaleString()} FCFA</td>
                                                    <td className="py-3 px-4 text-sm text-green-700">{(fee.total_paid || 0).toLocaleString()} FCFA</td>
                                                    <td className="py-3 px-4 text-sm text-red-700">{(fee.remaining_balance ?? fee.amount).toLocaleString()} FCFA</td>
                                                    <td className="py-3 px-4 text-sm text-[#6B7280]">{fee.due_date ? new Date(fee.due_date).toLocaleDateString() : "—"}</td>
                                                    <td className="py-3 px-4">
                                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[fee.status] || "bg-gray-100 text-gray-700"}`}>
                                                            {fee.status.charAt(0).toUpperCase() + fee.status.slice(1)}
                                                        </span>
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
            )}

            {activeTab === "documents" && (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-[#111827] text-base">Registration Documents</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {documents.map((document) => (
                            <label key={document.id} className="flex items-center justify-between gap-4 rounded-lg border border-[#E5E7EB] px-4 py-3">
                                <span className="text-sm font-medium text-[#111827]">{document.name}</span>
                                <input
                                    type="checkbox"
                                    checked={document.is_received}
                                    onChange={(event) => updateDocument(document, event.target.checked)}
                                    className="h-4 w-4"
                                />
                            </label>
                        ))}
                    </CardContent>
                </Card>
            )}

            {activeTab === "certificates" && (
                <div className="space-y-4">
                    <div className="flex flex-wrap gap-2">
                        {[
                            ["schooling", "Schooling"],
                            ["enrollment", "Enrollment"],
                            ["absence_authorization", "Absence Authorization"],
                            ["payment", "Payment"],
                        ].map(([value, label]) => (
                            <Button key={value} variant="outline" onClick={() => generateCertificate(value)}>
                                {label}
                            </Button>
                        ))}
                    </div>
                    <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                        <CardContent className="pt-4">
                            {certificates.length === 0 ? (
                                <div className="text-center py-8 text-[#6B7280]">No certificates generated yet.</div>
                            ) : certificates.map((certificate) => (
                                <div key={certificate.id} className="border-b border-[#E5E7EB] last:border-0 py-4">
                                    <div className="flex items-center justify-between gap-3">
                                        <div>
                                            <p className="text-sm font-medium text-[#111827]">{certificate.certificate_type}</p>
                                            <p className="text-xs text-[#6B7280]">{new Date(certificate.generated_at).toLocaleString()}</p>
                                        </div>
                                        <span className={`text-xs font-medium rounded-full px-2.5 py-1 ${certificate.status === "blocked" ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}`}>
                                            {certificate.status}
                                        </span>
                                    </div>
                                    <p className="mt-2 text-sm text-[#6B7280]">{certificate.blocked_reason || certificate.content}</p>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    )
}

function InfoRow({ label, value }: { label: string; value: string | undefined }) {
    return (
        <div className="flex gap-2">
            <span className="text-sm text-[#6B7280] w-36 shrink-0">{label}</span>
            <span className="text-sm text-[#111827] font-medium">{value || "—"}</span>
        </div>
    )
}
