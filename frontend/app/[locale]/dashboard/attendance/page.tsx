"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter
} from "@/components/ui/dialog"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { format } from "date-fns"
import { CalendarIcon, Check, X, Clock, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Badge } from "@/components/ui/badge"

type ClassItem = { id: number; name: string }

type TimetableSlot = {
    id: number
    day_of_week: string
    start_time: string
    end_time: string
    subject_id: number
}

export default function AttendancePage() {
    const { token } = useAuth()
    const [date, setDate] = useState<Date>(new Date())
    const [selectedClass, setSelectedClass] = useState<string>("")
    const [classes, setClasses] = useState<ClassItem[]>([])
    const [slots, setSlots] = useState<TimetableSlot[]>([])
    const [selectedSlot, setSelectedSlot] = useState<TimetableSlot | null>(null)
    const [isMarkingOpen, setIsMarkingOpen] = useState(false)

    const fetchClasses = async () => {
        const res = await fetch(`${API_BASE_URL}/education/classes`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) setClasses(await res.json())
    }

    const fetchSlots = async () => {
        // Fetch timetable for the specific day
        // Note: Backend currently filters by Class.
        // We filter by day client-side for MVP based on day_of_week.
        try {
            const res = await fetch(`${API_BASE_URL}/education/timetables?class_id=${selectedClass}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) {
                const allSlots: TimetableSlot[] = await res.json()
                const dayName = format(date, "EEEE").toLowerCase()
                const daySlots = allSlots.filter((s) => s.day_of_week === dayName)
                setSlots(daySlots)
            }
        } catch (e) {
            console.error(e)
        }
    }

    useEffect(() => {
        if (token) fetchClasses()
    }, [token])

    useEffect(() => {
        if (token && selectedClass && date) {
            fetchSlots()
        } else {
            setSlots([])
        }
    }, [token, selectedClass, date])

    const handleSlotClick = (slot: TimetableSlot) => {
        setSelectedSlot(slot)
        setIsMarkingOpen(true)
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <h1 className="text-3xl font-bold tracking-tight">Attendance</h1>
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

                    <Popover>
                        <PopoverTrigger asChild>
                            <Button
                                variant={"outline"}
                                className={cn(
                                    "w-[240px] justify-start text-left font-normal",
                                    !date && "text-muted-foreground"
                                )}
                            >
                                <CalendarIcon className="mr-2 h-4 w-4" />
                                {date ? format(date, "PPP") : <span>Pick a date</span>}
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                            <Calendar
                                mode="single"
                                selected={date}
                                onSelect={(d) => d && setDate(d)}
                                initialFocus
                            />
                        </PopoverContent>
                    </Popover>
                </div>
            </div>

            {/* Slots Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {slots.length > 0 ? (
                    slots.map(slot => (
                        <div
                            key={slot.id}
                            onClick={() => handleSlotClick(slot)}
                            className="border rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer bg-white relative overflow-hidden"
                        >
                            <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
                            <h3 className="text-xl font-bold mb-2">
                                {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}
                            </h3>
                            <p className="text-gray-600 mb-4">Subject ID: {slot.subject_id}</p> {/* Ideally fetch subject name */}
                            <div className="flex items-center text-sm text-gray-500">
                                <span className="flex items-center">
                                    Click to mark attendance
                                </span>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="col-span-full text-center py-12 border rounded-lg bg-gray-50 text-gray-500">
                        {selectedClass ? "No classes scheduled for this day." : "Please select a class to view schedule."}
                    </div>
                )}
            </div>

            {selectedSlot && (
                <MarkAttendanceDialog
                    open={isMarkingOpen}
                    onOpenChange={setIsMarkingOpen}
                    slot={selectedSlot}
                    date={date}
                    classId={parseInt(selectedClass)}
                />
            )}
        </div>
    )
}

function MarkAttendanceDialog({ open, onOpenChange, slot, date, classId }: { open: boolean, onOpenChange: (open: boolean) => void, slot: any, date: Date, classId: number }) {
    const { token } = useAuth()
    const [students, setStudents] = useState<any[]>([])
    const [attendance, setAttendance] = useState<Record<number, string>>({}) // student_id -> status
    const [remarks, setRemarks] = useState<Record<number, string>>({})
    const [loading, setLoading] = useState(false)
    const [saving, setSaving] = useState(false)

    useEffect(() => {
        if (open) {
            fetchData()
        }
    }, [open, slot, date])

    const fetchData = async () => {
        setLoading(true)
        try {
            // 1. Fetch Students of the class
            const studentsRes = await fetch(`${API_BASE_URL}/students?class_id=${classId}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            const studentsData = await studentsRes.json()

            // 2. Fetch Existing Attendance
            const dateStr = date.toISOString()
            const attRes = await fetch(`${API_BASE_URL}/attendance/?timetable_id=${slot.id}&date=${dateStr}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            const attData = await attRes.json()

            // Map existing data
            const attMap: Record<number, string> = {}
            const remMap: Record<number, string> = {}

            // Default everyone to PRESENT if no record
            studentsData.forEach((s: any) => {
                attMap[s.student_profile.id] = "present"
            })

            if (Array.isArray(attData)) {
                attData.forEach((a: any) => {
                    attMap[a.student_id] = a.status
                    remMap[a.student_id] = a.remarks || ""
                })
            }

            setStudents(studentsData)
            setAttendance(attMap)
            setRemarks(remMap)

        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    const handleStatusChange = (studentId: number, status: string) => {
        setAttendance(prev => ({ ...prev, [studentId]: status }))
    }

    const handleRemarkChange = (studentId: number, val: string) => {
        setRemarks(prev => ({ ...prev, [studentId]: val }))
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            const records = students.map(s => ({
                student_id: s.student_profile.id,
                status: attendance[s.student_profile.id],
                remarks: remarks[s.student_profile.id]
            }))

            const payload = {
                timetable_id: slot.id,
                date: date.toISOString(),
                students: records
            }

            const res = await fetch(`${API_BASE_URL}/attendance/batch`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            })

            if (res.ok) {
                onOpenChange(false)
            } else {
                alert("Failed to save")
            }
        } catch (e) {
            console.error(e)
            alert("Error saving")
        } finally {
            setSaving(false)
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case "present": return "bg-green-100 text-green-800 border-green-200"
            case "absent": return "bg-red-100 text-red-800 border-red-200"
            case "late": return "bg-yellow-100 text-yellow-800 border-yellow-200"
            case "excused": return "bg-blue-100 text-blue-800 border-blue-200"
            default: return "bg-gray-100"
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Mark Attendance</DialogTitle>
                </DialogHeader>

                {loading ? (
                    <div className="py-8 text-center text-gray-500">Loading students...</div>
                ) : (
                    <div className="space-y-4">
                        <div className="grid grid-cols-12 gap-4 font-semibold text-sm text-gray-500 border-b pb-2">
                            <div className="col-span-4">Student</div>
                            <div className="col-span-5 text-center">Status</div>
                            <div className="col-span-3">Remarks</div>
                        </div>

                        {students.map(student => (
                            <div key={student.id} className="grid grid-cols-12 gap-4 items-center">
                                <div className="col-span-4 font-medium truncate">
                                    {student.full_name}
                                </div>
                                <div className="col-span-5 flex justify-center gap-1">
                                    {["present", "absent", "late", "excused"].map(status => (
                                        <button
                                            key={status}
                                            onClick={() => handleStatusChange(student.student_profile.id, status)}
                                            className={cn(
                                                "px-2 py-1 text-xs rounded border capitalize transition-all",
                                                attendance[student.student_profile.id] === status
                                                    ? getStatusColor(status) + " ring-2 ring-offset-1 ring-blue-500"
                                                    : "bg-white text-gray-600 hover:bg-gray-50"
                                            )}
                                        >
                                            {status}
                                        </button>
                                    ))}
                                </div>
                                <div className="col-span-3">
                                    <input
                                        className="w-full text-xs p-1 border rounded"
                                        placeholder="Note..."
                                        value={remarks[student.student_profile.id] || ""}
                                        onChange={(e) => handleRemarkChange(student.student_profile.id, e.target.value)}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                <DialogFooter className="mt-6">
                    <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
                    <Button onClick={handleSave} disabled={saving || loading}>
                        {saving ? "Saving..." : "Save Attendance"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
