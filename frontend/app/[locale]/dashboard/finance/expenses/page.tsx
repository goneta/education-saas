"use client"

import { useState, useEffect, useMemo } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"
import { requestConfirmation } from "@/lib/confirmation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Plus, Pencil, Trash2 } from "lucide-react"

interface Expense {
    id: number
    title: string
    amount: number
    category: string
    date: string | null
    description: string | null
    school_id: number
    created_at: string
}

const CATEGORIES = ["salaries", "utilities", "maintenance", "supplies", "equipment", "other"]

const categoryLabel = (c: string) => c.charAt(0).toUpperCase() + c.slice(1)

export default function ExpensesPage() {
    const { token } = useAuth()
    const [expenses, setExpenses] = useState<Expense[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [filterCategory, setFilterCategory] = useState("")
    const [showModal, setShowModal] = useState(false)
    const [editingExpense, setEditingExpense] = useState<Expense | null>(null)
    const [formData, setFormData] = useState({
        title: "",
        amount: "",
        category: "other",
        date: "",
        description: ""
    })
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const fetchExpenses = async () => {
        if (!token) return
        setIsLoading(true)
        try {
            const params = filterCategory ? `?category=${filterCategory}` : ""
            const res = await fetch(`${API_BASE_URL}/finance/expenses${params}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) setExpenses(await res.json())
        } catch (e) {
            console.error(e)
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchExpenses()
    // Expenses are intentionally refreshed when auth or category filter changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token, filterCategory])

    const openCreate = () => {
        setEditingExpense(null)
        setFormData({ title: "", amount: "", category: "other", date: "", description: "" })
        setError(null)
        setShowModal(true)
    }

    const openEdit = (expense: Expense) => {
        setEditingExpense(expense)
        setFormData({
            title: expense.title,
            amount: expense.amount.toString(),
            category: expense.category,
            date: expense.date ? expense.date.substring(0, 10) : "",
            description: expense.description || ""
        })
        setError(null)
        setShowModal(true)
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
                category: formData.category,
                date: formData.date || null,
                description: formData.description || null
            }
            const url = editingExpense
                ? `${API_BASE_URL}/finance/expenses/${editingExpense.id}`
                : `${API_BASE_URL}/finance/expenses`
            const method = editingExpense ? "PUT" : "POST"
            const res = await fetch(url, {
                method,
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify(payload)
            })
            if (res.ok) {
                setShowModal(false)
                fetchExpenses()
            } else {
                const data = await res.json()
                setError(data.detail || "Failed to save expense")
            }
        } catch {
            setError("An error occurred")
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async (expense: Expense) => {
        if (!await requestConfirmation({ title: "Supprimer cette dépense", description: `La dépense « ${expense.title} » sera supprimée définitivement et l'action sera auditée.`, confirmLabel: "Supprimer définitivement", destructive: true })) return
        try {
            const res = await fetch(`${API_BASE_URL}/finance/expenses/${expense.id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok || res.status === 204) fetchExpenses()
        } catch (e) {
            console.error(e)
        }
    }

    const filterColumns = useMemo<FilterColumn<Expense>[]>(() => [
        { key: "title", label: "Title", accessor: expense => expense.title },
        { key: "category", label: "Category", accessor: expense => categoryLabel(expense.category) },
    ], [])
    const filter = useTableFilter(expenses, filterColumns, { storageKey: "expenses" })
    const filtered = filter.filtered

    const totalAmount = filtered.reduce((sum, e) => sum + e.amount, 0)

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">Expenses</h1>
                    <p className="text-sm text-[#6B7280] mt-1">Track and manage school expenditures</p>
                </div>
                <Button onClick={openCreate} className="bg-black text-white hover:bg-black/90 rounded-lg">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Expense
                </Button>
            </div>

            <div className="flex flex-wrap gap-4">
                <div className="flex-1 min-w-[200px] max-w-xl">
                    <TableFilter {...filter.controls} />
                </div>
                <select
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                    className="border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                    <option value="">All Categories</option>
                    {CATEGORIES.map(c => <option key={c} value={c}>{categoryLabel(c)}</option>)}
                </select>
            </div>

            {filtered.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                        <CardContent className="pt-6">
                            <p className="text-sm text-[#6B7280]">Total ({filtered.length} entries)</p>
                            <p className="text-2xl font-bold text-[#111827]">{totalAmount.toLocaleString()} FCFA</p>
                        </CardContent>
                    </Card>
                </div>
            )}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-[#111827]">Expense List ({filtered.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="text-center py-12 text-[#6B7280]">Loading expenses...</div>
                    ) : filtered.length === 0 ? (
                        <div className="text-center py-12 text-[#6B7280]">
                            {filter.controls.query ? `No expenses found matching "${filter.controls.query}"` : "No expenses yet. Add your first expense!"}
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-[#E5E7EB]">
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Title</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Category</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Amount</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Date</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtered.map((expense) => (
                                        <tr key={expense.id} className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] transition-colors">
                                            <td className="py-3 px-4 text-sm font-medium text-[#111827]">{expense.title}</td>
                                            <td className="py-3 px-4 text-sm">
                                                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                                                    {categoryLabel(expense.category)}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-sm text-[#111827] font-medium">{expense.amount.toLocaleString()} FCFA</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">
                                                {expense.date ? new Date(expense.date).toLocaleDateString() : "—"}
                                            </td>
                                            <td className="py-3 px-4">
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-[#2563EB] hover:text-[#2563EB] hover:bg-[#F0F1F3]"
                                                        onClick={() => openEdit(expense)}
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-red-600 hover:text-red-600 hover:bg-red-50"
                                                        onClick={() => handleDelete(expense)}
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

            <Dialog open={showModal} onOpenChange={setShowModal}>
                <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                        <DialogTitle>{editingExpense ? "Edit Expense" : "Add Expense"}</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded text-sm">{error}</div>
                        )}
                        <div className="space-y-2">
                            <Label htmlFor="title">Title *</Label>
                            <Input
                                id="title"
                                placeholder="e.g. Electricity bill"
                                value={formData.title}
                                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="amount">Amount (FCFA) *</Label>
                            <Input
                                id="amount"
                                type="number"
                                min="0"
                                placeholder="0"
                                value={formData.amount}
                                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Category</Label>
                            <select
                                value={formData.category}
                                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                {CATEGORIES.map(c => <option key={c} value={c}>{categoryLabel(c)}</option>)}
                            </select>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="date">Date</Label>
                            <input
                                id="date"
                                type="date"
                                value={formData.date}
                                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Input
                                id="description"
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
        </div>
    )
}
