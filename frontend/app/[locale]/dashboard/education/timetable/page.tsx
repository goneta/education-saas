"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Plus, Trash2 } from "lucide-react"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

type ClassItem = { id: number; name: string }

type SubjectItem = { id: number; name: string }

type TeacherItem = { id: number; full_name: string }

type TimetableItem = {
    id: number
    day_of_week: string
    start_time: string
    end_time: string
    subject_id: number
    teacher_id?: number | null
    room?: string | null
}

type FormData = {
    day_of_week: string
    start_time: string
    end_time: string
    subject_id: string
    teacher_id: string
    room: string
}

export default function TimetablePage() {
    const { token } = useAuth()
    const [timetable, setTimetable] = useState<TimetableItem[]>([])
    const [classes, setClasses] = useState<ClassItem[]>([])
    const [subjects, setSubjects] = useState<SubjectItem[]>([])
    const [teachers, setTeachers] = useState<TeacherItem[]>([])
    const [selectedClass, setSelectedClass] = useState<string>("")
    const [isDialogOpen, setIsDialogOpen] = useState(false)
    const [formData, setFormData] = useState<FormData>({
        day_of_week: "monday",
        start_time: "08:00",
        end_time: "10:00",
        subject_id: "",
        teacher_id: "",
        room: ""
    })

    const fetchClasses = async () => {
        const res = await fetch(`${API_BASE_URL}/education/classes`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) setClasses(await res.json())
    }

    const fetchSubjects = async () => {
        const res = await fetch(`${API_BASE_URL}/education/subjects`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) setSubjects(await res.json())
    }

    const fetchTeachers = async () => {
        const res = await fetch(`${API_BASE_URL}/teachers`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) setTeachers(await res.json())
    }

    const fetchTimetable = async (classId: string) => {
        const res = await fetch(`${API_BASE_URL}/education/timetables?class_id=${classId}`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) setTimetable(await res.json())
    }

    useEffect(() => {
        if (token) {
            fetchClasses()
            fetchSubjects()
            fetchTeachers()
        }
    }, [token])

    useEffect(() => {
        if (token && selectedClass) {
            fetchTimetable(selectedClass)
        } else {
            setTimetable([])
        }
    }, [token, selectedClass])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!selectedClass) return

        try {
            const payload = {
                ...formData,
                start_time: formData.start_time + ":00", // Append seconds for Time format
                end_time: formData.end_time + ":00",
                class_id: parseInt(selectedClass),
                subject_id: parseInt(formData.subject_id),
                teacher_id: formData.teacher_id ? parseInt(formData.teacher_id) : null
            }

            const res = await fetch(`${API_BASE_URL}/education/timetables`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            })

            if (res.ok) {
                fetchTimetable(selectedClass)
                setIsDialogOpen(false)
            }
        } catch (error) {
            console.error(error)
        }
    }

    const handleDelete = async (id: number) => {
        if (!confirm("Delete this entry?")) return
        try {
            const res = await fetch(`${API_BASE_URL}/education/timetables/${id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok && selectedClass) {
                fetchTimetable(selectedClass)
            }
        } catch (error) {
            console.error(error)
        }
    }

    const days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Timetable</h1>
                <div className="flex gap-4">
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

                    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                        <DialogTrigger asChild>
                            <Button disabled={!selectedClass}>
                                <Plus className="mr-2 h-4 w-4" /> Add Entry
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <DialogHeader>
                                <DialogTitle>Add Timetable Entry</DialogTitle>
                            </DialogHeader>
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Day</Label>
                                    <Select
                                        value={formData.day_of_week}
                                        onValueChange={(val) => setFormData({ ...formData, day_of_week: val })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {days.map(d => (
                                                <SelectItem key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Start Time</Label>
                                        <Input type="time" value={formData.start_time} onChange={(e) => setFormData({ ...formData, start_time: e.target.value })} required />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>End Time</Label>
                                        <Input type="time" value={formData.end_time} onChange={(e) => setFormData({ ...formData, end_time: e.target.value })} required />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label>Subject</Label>
                                    <Select
                                        value={formData.subject_id}
                                        onValueChange={(val) => setFormData({ ...formData, subject_id: val })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select Subject" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {subjects.map(s => (
                                                <SelectItem key={s.id} value={s.id.toString()}>{s.name}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Teacher</Label>
                                    <Select
                                        value={formData.teacher_id}
                                        onValueChange={(val) => setFormData({ ...formData, teacher_id: val })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select Teacher (Optional)" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {teachers.map(t => (
                                                <SelectItem key={t.id} value={t.id.toString()}>{t.full_name}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Room</Label>
                                    <Input value={formData.room} onChange={(e) => setFormData({ ...formData, room: e.target.value })} placeholder="e.g. 101" />
                                </div>
                                <DialogFooter>
                                    <Button type="submit">Save</Button>
                                </DialogFooter>
                            </form>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            {selectedClass ? (
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    {days.slice(0, 5).map(day => (
                        <div key={day} className="border rounded-md p-4 bg-white">
                            <h3 className="font-semibold capitalize mb-4 text-center border-b pb-2">{day}</h3>
                            <div className="space-y-2">
                                {timetable.filter(t => t.day_of_week === day).sort((a, b) => a.start_time.localeCompare(b.start_time)).map(t => {
                                    const subjectName = subjects.find(s => s.id === t.subject_id)?.name || "Unknown"
                                    return (
                                        <div key={t.id} className="text-xs p-2 bg-blue-50 rounded border border-blue-100 relative group">
                                            <div className="font-medium">{t.start_time.slice(0, 5)} - {t.end_time.slice(0, 5)}</div>
                                            <div className="font-bold text-blue-700">{subjectName}</div>
                                            {t.teacher_id && <div className="text-xs text-gray-500 italic">{teachers.find(tr => tr.id === t.teacher_id)?.full_name}</div>}
                                            {t.room && <div className="text-gray-500">Room: {t.room}</div>}
                                            <button
                                                onClick={() => handleDelete(t.id)}
                                                className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 hover:text-red-500 transition-opacity"
                                            >
                                                <Trash2 className="h-3 w-3" />
                                            </button>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-center py-10 text-gray-500">Select a class to view timetable</div>
            )}
        </div>
    )
}
