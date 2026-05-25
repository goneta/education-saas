"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Plus, Trash2 } from "lucide-react"

interface TimetableEntry {
    id: number
    day_of_week: string
    start_time: string
    end_time: string
    class_id: number
    subject_id: number
    teacher_id: number | null
}

interface ClassItem {
    id: number
    name: string
}

interface Subject {
    id: number
    name: string
}

interface Teacher {
    id: number
    full_name: string
}

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]

export default function TimetablePage() {
    const { token } = useAuth()
    const [entries, setEntries] = useState<TimetableEntry[]>([])
    const [classes, setClasses] = useState<ClassItem[]>([])
    const [subjects, setSubjects] = useState<Subject[]>([])
    const [teachers, setTeachers] = useState<Teacher[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [filterClassId, setFilterClassId] = useState("")
    const [showModal, setShowModal] = useState(false)
    const [formData, setFormData] = useState({
        class_id: "",
        subject_id: "",
        teacher_id: "",
        day_of_week: "monday",
        start_time: "08:00",
        end_time: "09:00"
    })
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const fetchEntries = async () => {
        if (!token) return
        setIsLoading(true)
        try {
            const params = filterClassId ? `?class_id=${filterClassId}` : ""
            const res = await fetch(`${API_BASE_URL}/education/timetables${params}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) setEntries(await res.json())
        } catch (e) {
            console.error(e)
        } finally {
            setIsLoading(false)
        }
    }

    const fetchMeta = async () => {
        if (!token) return
        try {
            const [classRes, subjectRes, teacherRes] = await Promise.all([
                fetch(`${API_BASE_URL}/education/classes`, { headers: { Authorization: `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/education/subjects`, { headers: { Authorization: `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/teachers/`, { headers: { Authorization: `Bearer ${token}` } })
            ])
            if (classRes.ok) setClasses(await classRes.json())
            if (subjectRes.ok) setSubjects(await subjectRes.json())
            if (teacherRes.ok) setTeachers(await teacherRes.json())
        } catch (e) {
            console.error(e)
        }
    }

    useEffect(() => {
        fetchMeta()
    // Timetable metadata loading is intentionally bound to the auth token.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token])

    useEffect(() => {
        fetchEntries()
    /* Entries intentionally refresh only when auth or the class filter changes. */
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token, filterClassId])

    const openCreate = () => {
        setFormData({
            class_id: classes[0]?.id.toString() || "",
            subject_id: subjects[0]?.id.toString() || "",
            teacher_id: "",
            day_of_week: "monday",
            start_time: "08:00",
            end_time: "09:00"
        })
        setError(null)
        setShowModal(true)
    }

    const handleSave = async () => {
        if (!formData.class_id || !formData.subject_id) {
            setError("Class and subject are required")
            return
        }
        setSaving(true)
        setError(null)
        try {
            const payload = {
                class_id: parseInt(formData.class_id),
                subject_id: parseInt(formData.subject_id),
                teacher_id: formData.teacher_id ? parseInt(formData.teacher_id) : null,
                day_of_week: formData.day_of_week,
                start_time: formData.start_time,
                end_time: formData.end_time
            }
            const res = await fetch(`${API_BASE_URL}/education/timetables`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify(payload)
            })
            if (res.ok) {
                setShowModal(false)
                fetchEntries()
            } else {
                const data = await res.json()
                setError(data.detail || "Failed to save timetable entry")
            }
        } catch {
            setError("An error occurred")
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async (entry: TimetableEntry) => {
        if (!confirm("Delete this timetable entry?")) return
        try {
            const res = await fetch(`${API_BASE_URL}/education/timetables/${entry.id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok || res.status === 204) fetchEntries()
        } catch (e) {
            console.error(e)
        }
    }

    const getClassName = (id: number) => classes.find(c => c.id === id)?.name || "—"
    const getSubjectName = (id: number) => subjects.find(s => s.id === id)?.name || "—"
    const getTeacherName = (id: number | null) => id ? (teachers.find(t => t.id === id)?.full_name || "—") : "—"

    const entriesByDay = DAYS.map(day => ({
        day,
        entries: entries.filter(e => e.day_of_week === day)
    })).filter(d => d.entries.length > 0)

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">Timetable</h1>
                    <p className="text-sm text-[#6B7280] mt-1">Manage class schedules and timetable entries</p>
                </div>
                <Button onClick={openCreate} className="bg-black text-white hover:bg-black/90 rounded-lg">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Entry
                </Button>
            </div>

            <div className="flex items-center gap-4">
                <Label className="text-sm text-[#6B7280]">Filter by class:</Label>
                <select
                    value={filterClassId}
                    onChange={(e) => setFilterClassId(e.target.value)}
                    className="border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                    <option value="">All Classes</option>
                    {classes.map(c => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                </select>
            </div>

            {isLoading ? (
                <div className="text-center py-12 text-[#6B7280]">Loading timetable...</div>
            ) : entries.length === 0 ? (
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                    <CardContent className="text-center py-12 text-[#6B7280]">
                        No timetable entries yet. Add your first entry!
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-4">
                    {entriesByDay.map(({ day, entries: dayEntries }) => (
                        <Card key={day} className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-[#111827] capitalize text-base">{day}</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead>
                                            <tr className="border-b border-[#E5E7EB]">
                                                <th className="text-left py-2 px-4 text-sm font-medium text-[#6B7280]">Time</th>
                                                <th className="text-left py-2 px-4 text-sm font-medium text-[#6B7280]">Class</th>
                                                <th className="text-left py-2 px-4 text-sm font-medium text-[#6B7280]">Subject</th>
                                                <th className="text-left py-2 px-4 text-sm font-medium text-[#6B7280]">Teacher</th>
                                                <th className="text-left py-2 px-4 text-sm font-medium text-[#6B7280]">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {dayEntries.sort((a, b) => a.start_time.localeCompare(b.start_time)).map((entry) => (
                                                <tr key={entry.id} className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] transition-colors">
                                                    <td className="py-2 px-4 text-sm text-[#111827]">{entry.start_time} – {entry.end_time}</td>
                                                    <td className="py-2 px-4 text-sm text-[#6B7280]">{getClassName(entry.class_id)}</td>
                                                    <td className="py-2 px-4 text-sm text-[#6B7280]">{getSubjectName(entry.subject_id)}</td>
                                                    <td className="py-2 px-4 text-sm text-[#6B7280]">{getTeacherName(entry.teacher_id)}</td>
                                                    <td className="py-2 px-4">
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="h-8 text-red-600 hover:text-red-600 hover:bg-red-50"
                                                            onClick={() => handleDelete(entry)}
                                                        >
                                                            <Trash2 className="h-4 w-4" />
                                                        </Button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            <Dialog open={showModal} onOpenChange={setShowModal}>
                <DialogContent className="sm:max-w-[450px]">
                    <DialogHeader>
                        <DialogTitle>Add Timetable Entry</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded text-sm">{error}</div>
                        )}
                        <div className="space-y-2">
                            <Label>Class *</Label>
                            <select
                                value={formData.class_id}
                                onChange={(e) => setFormData({ ...formData, class_id: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="">Select class</option>
                                {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                            </select>
                        </div>
                        <div className="space-y-2">
                            <Label>Subject *</Label>
                            <select
                                value={formData.subject_id}
                                onChange={(e) => setFormData({ ...formData, subject_id: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="">Select subject</option>
                                {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                            </select>
                        </div>
                        <div className="space-y-2">
                            <Label>Teacher</Label>
                            <select
                                value={formData.teacher_id}
                                onChange={(e) => setFormData({ ...formData, teacher_id: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="">No teacher assigned</option>
                                {teachers.map(t => <option key={t.id} value={t.id}>{t.full_name}</option>)}
                            </select>
                        </div>
                        <div className="space-y-2">
                            <Label>Day of Week *</Label>
                            <select
                                value={formData.day_of_week}
                                onChange={(e) => setFormData({ ...formData, day_of_week: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                {DAYS.map(d => <option key={d} value={d} className="capitalize">{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
                            </select>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Start Time *</Label>
                                <input
                                    type="time"
                                    value={formData.start_time}
                                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                                    className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>End Time *</Label>
                                <input
                                    type="time"
                                    value={formData.end_time}
                                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                                    className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                                />
                            </div>
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
