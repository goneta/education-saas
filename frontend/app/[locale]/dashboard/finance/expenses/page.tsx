"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"

interface Expense {
    id: number
    amount: number
    description: string
    category: string
    date: string
}

export default function ExpensesPage() {
    const [expenses, setExpenses] = useState<Expense[]>([])
    const [open, setOpen] = useState(false)

    // Form State
    const [amount, setAmount] = useState("")
    const [description, setDescription] = useState("")
    const [category, setCategory] = useState("other")
    const [date, setDate] = useState("")

    useEffect(() => {
        fetchExpenses()
    }, [])

    const fetchExpenses = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/finance/expenses`, {
                headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
            })
            if (res.ok) {
                const data = await res.json()
                setExpenses(Array.isArray(data) ? data : [])
            }
        } catch (e) {
            console.error(e)
        }
    }

    const handleCreateExpense = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const res = await fetch(`${API_BASE_URL}/finance/expenses`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify({
                    amount: parseFloat(amount),
                    description,
                    category,
                    date: new Date(date).toISOString()
                })
            })

            if (res.ok) {
                setOpen(false)
                fetchExpenses()
                // Reset
                setAmount("")
                setDescription("")
                setCategory("other")
                setDate("")
            } else {
                alert("Failed to create expense")
            }
        } catch (error) {
            console.error(error)
            alert("Error creating expense")
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Expense Tracking</h2>
                    <p className="text-muted-foreground">Track school operational expenses.</p>
                </div>

                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" /> Add Expense
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>Add New Expense</DialogTitle>
                            <DialogDescription>
                                Record a new expense for the school.
                            </DialogDescription>
                        </DialogHeader>
                        <form onSubmit={handleCreateExpense}>
                            <div className="grid gap-4 py-4">
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="amount" className="text-right">
                                        Amount
                                    </Label>
                                    <Input
                                        id="amount"
                                        value={amount}
                                        onChange={(e) => setAmount(e.target.value)}
                                        className="col-span-3"
                                        placeholder="0.00"
                                        required
                                        type="number"
                                        step="0.01"
                                    />
                                </div>
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="description" className="text-right">
                                        Description
                                    </Label>
                                    <Input
                                        id="description"
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        className="col-span-3"
                                        placeholder="e.g. Textbooks"
                                        required
                                    />
                                </div>
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="category" className="text-right">
                                        Category
                                    </Label>
                                    <Select value={category} onValueChange={setCategory}>
                                        <SelectTrigger className="col-span-3">
                                            <SelectValue placeholder="Select category" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="salary">Salary</SelectItem>
                                            <SelectItem value="utilities">Utilities</SelectItem>
                                            <SelectItem value="maintenance">Maintenance</SelectItem>
                                            <SelectItem value="supplies">Supplies</SelectItem>
                                            <SelectItem value="other">Other</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="date" className="text-right">
                                        Date
                                    </Label>
                                    <Input
                                        id="date"
                                        value={date}
                                        onChange={(e) => setDate(e.target.value)}
                                        className="col-span-3"
                                        type="date"
                                        required
                                    />
                                </div>
                            </div>
                            <DialogFooter>
                                <Button type="submit">Save Expense</Button>
                            </DialogFooter>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="border rounded-md">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Date</TableHead>
                            <TableHead>Category</TableHead>
                            <TableHead>Description</TableHead>
                            <TableHead className="text-right">Amount</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {expenses.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-4">No expenses recorded</TableCell>
                            </TableRow>
                        ) : expenses.map((exp) => (
                            <TableRow key={exp.id}>
                                <TableCell>{new Date(exp.date).toLocaleDateString()}</TableCell>
                                <TableCell className="capitalize">{exp.category}</TableCell>
                                <TableCell>{exp.description}</TableCell>
                                <TableCell className="text-right">${exp.amount.toLocaleString()}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </div>
    )
}
