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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus, CreditCard } from "lucide-react"

interface Fee {
    id: number
    student_id: number
    amount: number
    due_date: string
    description: string
    status: string
}

export default function FeesPage() {
    const [fees, setFees] = useState<Fee[]>([])
    const [open, setOpen] = useState(false)

    // Form State
    const [studentId, setStudentId] = useState("")
    const [amount, setAmount] = useState("")
    const [description, setDescription] = useState("")
    const [dueDate, setDueDate] = useState("")

    const fetchFees = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/finance/fees`, {
                headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
            })
            if (res.ok) setFees(await res.json())
        } catch (e) {
            console.error(e)
        }
    }

    useEffect(() => {
        fetchFees()
    }, [])

    const handleCreateFee = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/finance/fees`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify({
                    student_id: parseInt(studentId),
                    amount: parseFloat(amount),
                    description,
                    due_date: new Date(dueDate).toISOString()
                })
            })

            if (res.ok) {
                setOpen(false)
                fetchFees()
                // Reset form
                setStudentId("")
                setAmount("")
                setDescription("")
                setDueDate("")
            } else {
                alert("Failed to create fee")
            }
        } catch (error) {
            console.error(error)
            alert("Error creating fee")
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Fee Collection</h2>
                    <p className="text-muted-foreground">Manage student fees and payments.</p>
                </div>

                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" /> Assign Fee
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>Assign Fee to Student</DialogTitle>
                            <DialogDescription>
                                Create a new fee payment request for a student.
                            </DialogDescription>
                        </DialogHeader>
                        <form onSubmit={handleCreateFee}>
                            <div className="grid gap-4 py-4">
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="studentId" className="text-right">
                                        Student ID
                                    </Label>
                                    <Input
                                        id="studentId"
                                        value={studentId}
                                        onChange={(e) => setStudentId(e.target.value)}
                                        className="col-span-3"
                                        placeholder="Enter Student ID"
                                        required
                                        type="number"
                                    />
                                </div>
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
                                        placeholder="e.g. Term 1 Tuition"
                                        required
                                    />
                                </div>
                                <div className="grid grid-cols-4 items-center gap-4">
                                    <Label htmlFor="dueDate" className="text-right">
                                        Due Date
                                    </Label>
                                    <Input
                                        id="dueDate"
                                        value={dueDate}
                                        onChange={(e) => setDueDate(e.target.value)}
                                        className="col-span-3"
                                        type="date"
                                        required
                                    />
                                </div>
                            </div>
                            <DialogFooter>
                                <Button type="submit">Save changes</Button>
                            </DialogFooter>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="border rounded-md">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Desc</TableHead>
                            <TableHead>Student ID</TableHead>
                            <TableHead>Amount</TableHead>
                            <TableHead>Due Date</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {fees.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={6} className="text-center py-4">No fees found</TableCell>
                            </TableRow>
                        ) : fees.map((fee) => (
                            <TableRow key={fee.id}>
                                <TableCell className="font-medium">{fee.description}</TableCell>
                                <TableCell>{fee.student_id}</TableCell>
                                <TableCell>${fee.amount.toLocaleString()}</TableCell>
                                <TableCell>{new Date(fee.due_date).toLocaleDateString()}</TableCell>
                                <TableCell>
                                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${fee.status === 'paid' ? 'bg-green-100 text-green-800' :
                                            fee.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                                'bg-red-100 text-red-800'
                                        }`}>
                                        {fee.status.toUpperCase()}
                                    </span>
                                </TableCell>
                                <TableCell className="text-right">
                                    <Button variant="ghost" size="sm">
                                        <CreditCard className="h-4 w-4 mr-2" />
                                        Pay
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </div>
    )
}
