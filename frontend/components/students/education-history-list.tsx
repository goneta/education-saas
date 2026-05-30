"use client"

import { useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Trash2, Plus, GraduationCap } from "lucide-react"

interface EducationHistory {
    id: number
    previous_school: string
    class_level: string
    degree_obtained?: string
    grade_average?: string
    year_completed?: number
}

interface EducationHistoryListProps {
    studentId: number
    initialHistory: EducationHistory[]
}

export function EducationHistoryList({ studentId, initialHistory }: EducationHistoryListProps) {
    const { token } = useAuth()
    const [history, setHistory] = useState<EducationHistory[]>(initialHistory)
    const [isAdding, setIsAdding] = useState(false)
    const [isDeleting, setIsDeleting] = useState<number | null>(null)
    const [showAddDialog, setShowAddDialog] = useState(false)

    // Form state
    const [newItem, setNewItem] = useState({
        previous_school: "",
        class_level: "",
        degree_obtained: "",
        grade_average: "",
        year_completed: ""
    })

    const handleAddItem = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!token) return

        setIsAdding(true)
        try {
            const response = await fetch(`${API_BASE_URL}/students/${studentId}/history`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    previous_school: newItem.previous_school,
                    class_level: newItem.class_level,
                    degree_obtained: newItem.degree_obtained || undefined,
                    grade_average: newItem.grade_average || undefined,
                    year_completed: newItem.year_completed ? parseInt(newItem.year_completed) : undefined
                })
            })

            if (response.ok) {
                const addedItem = await response.json()
                setHistory([...history, addedItem])
                setShowAddDialog(false)
                setNewItem({
                    previous_school: "",
                    class_level: "",
                    degree_obtained: "",
                    grade_average: "",
                    year_completed: ""
                })
            }
        } catch (error) {
            console.error("Failed to add history", error)
        } finally {
            setIsAdding(false)
        }
    }

    const handleDeleteItem = async (id: number) => {
        if (!token) return
        setIsDeleting(id)
        try {
            const response = await fetch(`${API_BASE_URL}/students/history/${id}`, {
                method: "DELETE",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            })

            if (response.ok) {
                setHistory(history.filter(h => h.id !== id))
            }
        } catch (error) {
            console.error("Failed to delete history", error)
        } finally {
            setIsDeleting(null)
        }
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-[#111827] flex items-center gap-2">
                    <GraduationCap className="h-5 w-5" />
                    Education History
                </h3>
                <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
                    <DialogTrigger asChild>
                        <Button size="sm" variant="outline">
                            <Plus className="h-4 w-4 mr-2" />
                            Add History
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Add Education History</DialogTitle>
                            <DialogDescription>Record previous academic achievements.</DialogDescription>
                        </DialogHeader>
                        <form onSubmit={handleAddItem} className="space-y-4">
                            <div className="grid gap-4 py-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="school">School/Institution *</Label>
                                        <Input
                                            id="school"
                                            required
                                            value={newItem.previous_school}
                                            onChange={e => setNewItem({ ...newItem, previous_school: e.target.value })}
                                            placeholder="e.g. Lycée Louis Grand"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="level">Class Level *</Label>
                                        <Input
                                            id="level"
                                            required
                                            value={newItem.class_level}
                                            onChange={e => setNewItem({ ...newItem, class_level: e.target.value })}
                                            placeholder="e.g. Terminale"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="degree">Degree/Diploma</Label>
                                        <Input
                                            id="degree"
                                            value={newItem.degree_obtained}
                                            onChange={e => setNewItem({ ...newItem, degree_obtained: e.target.value })}
                                            placeholder="e.g. Baccalauréat"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="grade">Grade/Average</Label>
                                        <Input
                                            id="grade"
                                            value={newItem.grade_average}
                                            onChange={e => setNewItem({ ...newItem, grade_average: e.target.value })}
                                            placeholder="e.g. 16/20"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="year">Year Completed</Label>
                                    <Input
                                        id="year"
                                        type="number"
                                        value={newItem.year_completed}
                                        onChange={e => setNewItem({ ...newItem, year_completed: e.target.value })}
                                        placeholder="e.g. 2023"
                                    />
                                </div>
                            </div>
                            <DialogFooter>
                                <Button type="submit" disabled={isAdding}>
                                    {isAdding ? "Adding..." : "Add Record"}
                                </Button>
                            </DialogFooter>
                        </form>
                    </DialogContent>
                </Dialog>
            </div>

            {history.length === 0 ? (
                <div className="text-sm text-gray-500 italic">No education history recorded.</div>
            ) : (
                <div className="grid gap-4">
                    {history.map((item) => (
                        <div key={item.id} className="flex items-center justify-between p-4 border rounded-lg bg-white shadow-sm">
                            <div>
                                <h4 className="font-medium text-[#111827]">{item.class_level} at {item.previous_school}</h4>
                                <div className="text-sm text-gray-500 mt-1 space-x-4">
                                    {item.degree_obtained && <span>Degree: {item.degree_obtained}</span>}
                                    {item.grade_average && <span>Grade: {item.grade_average}</span>}
                                    {item.year_completed && <span>Year: {item.year_completed}</span>}
                                </div>
                            </div>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                onClick={() => handleDeleteItem(item.id)}
                                disabled={isDeleting === item.id}
                            >
                                <Trash2 className="h-4 w-4" />
                            </Button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
