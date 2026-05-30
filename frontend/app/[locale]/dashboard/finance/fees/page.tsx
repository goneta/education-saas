"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Plus, Pencil, Trash2, Search, CreditCard } from "lucide-react"

interface Fee {
    id: number
    title: string
    amount: number
    due_date: string | null
    status: string
    description: string | null
    student_id: number | null
    school_id: number
    created_at: string
}

interface Student {
    id: number
    full_name: string
}

const STATUS_COLORS: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    partial: "bg-blue-100 text-blue-800",
    paid: "bg-green-100 text-green-800",
    overdue: "bg-red-100 text-red-800"
}

export default function FeesPage() {
    const { token } = useAuth()
    const [fees, setFees] = useState<Fee[]>([])
    const [students, setStudents] = useState<Student[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [filterStatus, setFilterStatus] = useState("")
    const [showModal, setShowModal] = useState(false)
    const [showPaymentModal, setShowPaymentModal] = useState(false)
    const [editingFee, setEditingFee] = useState<Fee | null>(null)
    const [selectedFee, setSelectedFee] = useState<Fee | null>(null)
    const [formData, setFormData] = useState({
        title: "",
        amount: "",
        due_date: "",
        status: "pending",
        description: "",
        student_id: ""
    })
    const [paymentAmount, setPaymentAmount] = useState("")
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const fetchFees = async () => {
        if (!token) return
        setIsLoading(true)
        try {
            const params = filterStatus ? `?status=${filterStatus}` : ""
            const res = await fetch(`${API_BASE_URL}/finance/fees${params}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) setFees(await res.json())
        } catch (e) {
            console.error(e)
        } finally {
            setIsLoading(false)
        }
    }

    const fetchStudents = async () => {
        if (!token) return
        try {
            const res = await fetch(`${API_BASE_URL}/students/`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) setStudents(await res.json())
        } catch (e) {
            console.error(e)
        }
    }

    useEffect(() => {
        fetchStudents()
    // Student options are intentionally loaded when the auth token becomes available.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token])

    useEffect(() => {
        fetchFees()
    /* Fees intentionally refresh only when auth or status filter changes. */
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token, filterStatus])

    const openCreate = () => {
        setEditingFee(null)
        setFormData({ title: "", amount: "", due_date: "", status: "pending", description: "", student_id: "" })
        setError(null)
        setShowModal(true)
    }

    const openEdit = (fee: Fee) => {
        setEditingFee(fee)
        setFormData({
            title: fee.title,
            amount: fee.amount.toString(),
            due_date: fee.due_date ? fee.due_date.substring(0, 10) : "",
            status: fee.status,
            description: fee.description || "",
            student_id: fee.student_id?.toString() || ""
        })
        setError(null)
        setShowModal(true)
    }

    const openPayment = (fee: Fee) => {
        setSelectedFee(fee)
        setPaymentAmount("")
        setError(null)
        setShowPaymentModal(true)
    }

    const handleSave = async () => {
        if (!formData.title.trim() || !formData.amount) {
            setError("Title and amount are required")
            return
        }
        setSaving(true)
        setError(null)
        try {
            const payload = {
                title: formData.title,
                amount: parseFloat(formData.amount),
                due_date: formData.due_date || null,
                status: formData.status,
                description: formData.description || null,
                student_id: formData.student_id ? parseInt(formData.student_id) : null
            }
            const url = editingFee
                ? `${API_BASE_URL}/finance/fees/${editingFee.id}`
                : `${API_BASE_URL}/finance/fees`
            const method = editingFee ? "PUT" : "POST"
            const res = await fetch(url, {
                method,
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify(payload)
            })
            if (res.ok) {
                setShowModal(false)
                fetchFees()
            } else {
                const data = await res.json()
                setError(data.detail || "Failed to save fee")
            }
        } catch {
            setError("An error occurred")
        } finally {
            setSaving(false)
        }
    }

    const handleAddPayment = async () => {
        if (!selectedFee || !paymentAmount) {
            setError("Payment amount is required")
            return
        }
        setSaving(true)
        setError(null)
        try {
            const res = await fetch(`${API_BASE_URL}/finance/fees/${selectedFee.id}/payments`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({ amount: parseFloat(paymentAmount) })
            })
            if (res.ok) {
                setShowPaymentModal(false)
                fetchFees()
            } else {
                const data = await res.json()
                setError(data.detail || "Failed to add payment")
            }
        } catch {
            setError("An error occurred")
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async (fee: Fee) => {
        if (!confirm(`Delete fee "${fee.title}"? This cannot be undone.`)) return
        try {
            const res = await fetch(`${API_BASE_URL}/finance/fees/${fee.id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok || res.status === 204) fetchFees()
        } catch (e) {
            console.error(e)
        }
    }

    const getStudentName = (id: number | null) => {
        if (!id) return "—"
        return students.find(s => s.id === id)?.full_name || `Student #${id}`
    }

    const filtered = fees.filter(f =>
        f.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        getStudentName(f.student_id).toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">Fees</h1>
                    <p className="text-sm text-[#6B7280] mt-1">Manage student fees and payments</p>
                </div>
                <Button onClick={openCreate} className="bg-black text-white hover:bg-black/90 rounded-lg">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Fee
                </Button>
            </div>

            <div className="flex flex-wrap gap-4">
                <div className="relative flex-1 min-w-[200px] max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6B7280]" />
                    <input
                        type="search"
                        placeholder="Search fees..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-[#E5E7EB] rounded-lg bg-white text-[#111827] placeholder:text-[#6B7280] focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                </div>
                <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                    <option value="">All Statuses</option>
                    <option value="pending">Pending</option>
                    <option value="partial">Partial</option>
                    <option value="paid">Paid</option>
                    <option value="overdue">Overdue</option>
                </select>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-[#111827]">Fee List ({filtered.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="text-center py-12 text-[#6B7280]">Loading fees...</div>
                    ) : filtered.length === 0 ? (
                        <div className="text-center py-12 text-[#6B7280]">
                            {searchQuery ? `No fees found matching "${searchQuery}"` : "No fees yet. Add your first fee!"}
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-[#E5E7EB]">
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Title</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Student</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Amount</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Due Date</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Status</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtered.map((fee) => (
                                        <tr key={fee.id} className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] transition-colors">
                                            <td className="py-3 px-4 text-sm font-medium text-[#111827]">{fee.title}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{getStudentName(fee.student_id)}</td>
                                            <td className="py-3 px-4 text-sm text-[#111827] font-medium">{fee.amount.toLocaleString()} FCFA</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">
                                                {fee.due_date ? new Date(fee.due_date).toLocaleDateString() : "—"}
                                            </td>
                                            <td className="py-3 px-4">
                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[fee.status] || "bg-gray-100 text-gray-700"}`}>
                                                    {fee.status.charAt(0).toUpperCase() + fee.status.slice(1)}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4">
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-green-600 hover:text-green-600 hover:bg-green-50"
                                                        onClick={() => openPayment(fee)}
                                                        title="Add payment"
                                                    >
                                                        <CreditCard className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-[#2563EB] hover:text-[#2563EB] hover:bg-[#F0F1F3]"
                                                        onClick={() => openEdit(fee)}
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-red-600 hover:text-red-600 hover:bg-red-50"
                                                        onClick={() => handleDelete(fee)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
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

            {/* Add/Edit Fee Modal */}
            <Dialog open={showModal} onOpenChange={setShowModal}>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>{editingFee ? "Edit Fee" : "Add Fee"}</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded text-sm">{error}</div>
                        )}
                        <div className="space-y-2">
                            <Label>Title *</Label>
                            <Input
                                placeholder="e.g. Tuition Fee Term 1"
                                value={formData.title}
                                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Amount (FCFA) *</Label>
                            <Input
                                type="number"
                                min="0"
                                placeholder="0"
                                value={formData.amount}
                                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Student</Label>
                            <select
                                value={formData.student_id}
                                onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="">School-wide fee</option>
                                {students.map(s => <option key={s.id} value={s.id}>{s.full_name}</option>)}
                            </select>
                        </div>
                        <div className="space-y-2">
                            <Label>Due Date</Label>
                            <input
                                type="date"
                                value={formData.due_date}
                                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Status</Label>
                            <select
                                value={formData.status}
                                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="pending">Pending</option>
                                <option value="partial">Partial</option>
                                <option value="paid">Paid</option>
                                <option value="overdue">Overdue</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <Label>Description</Label>
                            <Input
                                placeholder="Optional notes"
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowModal(false)}>Cancel</Button>
                        <Button onClick={handleSave} disabled={saving} className="bg-black text-white hover:bg-black/90">
                            {saving ? "Saving..." : "Save"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Add Payment Modal */}
            <Dialog open={showPaymentModal} onOpenChange={setShowPaymentModal}>
                <DialogContent className="sm:max-w-[350px]">
                    <DialogHeader>
                        <DialogTitle>Record Payment</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded text-sm">{error}</div>
                        )}
                        {selectedFee && (
                            <p className="text-sm text-[#6B7280]">
                                Fee: <span className="font-medium text-[#111827]">{selectedFee.title}</span>
                                {" "}— Total: <span className="font-medium text-[#111827]">{selectedFee.amount.toLocaleString()} FCFA</span>
                            </p>
                        )}
                        <div className="space-y-2">
                            <Label>Payment Amount (FCFA) *</Label>
                            <Input
                                type="number"
                                min="0"
                                placeholder="0"
                                value={paymentAmount}
                                onChange={(e) => setPaymentAmount(e.target.value)}
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowPaymentModal(false)}>Cancel</Button>
                        <Button onClick={handleAddPayment} disabled={saving} className="bg-black text-white hover:bg-black/90">
                            {saving ? "Saving..." : "Record Payment"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}
