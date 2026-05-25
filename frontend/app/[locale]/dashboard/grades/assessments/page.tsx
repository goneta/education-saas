"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Plus, Pencil, Trash2, Search, ClipboardList } from "lucide-react"
import { useRouter, useParams } from "next/navigation"

interface Assessment {
    id: number
    title: string
    date: string
    max_score: number
    weight: number
    class_id: number
    subject_id: number
    term_id: number
}

interface ClassItem {
    id: number
    name: string
}

interface Subject {
    id: number
    name: string
}

interface Term {
    id: number
    name: string
}

export default function AssessmentsPage() {
    const { token } = useAuth()
    const router = useRouter()
    const params = useParams()
    const locale = params.locale as string

    const [assessments, setAssessments] = useState<Assessment[]>([])
    const [classes, setClasses] = useState<ClassItem[]>([])
    const [subjects, setSubjects] = useState<Subject[]>([])
    const [terms, setTerms] = useState<Term[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [filterClassId, setFilterClassId] = useState("")
    const [showModal, setShowModal] = useState(false)
    const [editingAssessment, setEditingAssessment] = useState<Assessment | null>(null)
    const [formData, setFormData] = useState({
        title: "",
        date: "",
        max_score: "20",
        weight: "1",
        class_id: "",
        subject_id: "",
        term_id: ""
    })
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const fetchAssessments = async () => {
        if (!token) return
        setIsLoading(true)
        try {
            const parts: string[] = []
            if (filterClassId) parts.push(`class_id=${filterClassId}`)
            const qs = parts.length ? `?${parts.join("&")}` : ""
            const res = await fetch(`${API_BASE_URL}/grades/assessments${qs}`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) setAssessments(await res.json())
        } catch (e) {
            console.error(e)
        } finally {
            setIsLoading(false)
        }
    }

    const fetchMeta = async () => {
        if (!token) return
        try {
            const [classRes, subjectRes, termRes] = await Promise.all([
                fetch(`${API_BASE_URL}/education/classes`, { headers: { Authorization: `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/education/subjects`, { headers: { Authorization: `Bearer ${token}` } }),
                fetch(`${API_BASE_URL}/education/terms`, { headers: { Authorization: `Bearer ${token}` } })
            ])
            if (classRes.ok) setClasses(await classRes.json())
            if (subjectRes.ok) setSubjects(await subjectRes.json())
            if (termRes.ok) setTerms(await termRes.json())
        } catch (e) {
            console.error(e)
        }
    }

    useEffect(() => {
        fetchMeta()
    }, [token])

    useEffect(() => {
        fetchAssessments()
    }, [token, filterClassId])

    const openCreate = () => {
        setEditingAssessment(null)
        setFormData({
            title: "",
            date: new Date().toISOString().substring(0, 10),
            max_score: "20",
            weight: "1",
            class_id: classes[0]?.id.toString() || "",
            subject_id: subjects[0]?.id.toString() || "",
            term_id: terms[0]?.id.toString() || ""
        })
        setError(null)
        setShowModal(true)
    }

    const openEdit = (assessment: Assessment) => {
        setEditingAssessment(assessment)
        setFormData({
            title: assessment.title,
            date: assessment.date.substring(0, 10),
            max_score: assessment.max_score.toString(),
            weight: assessment.weight.toString(),
            class_id: assessment.class_id.toString(),
            subject_id: assessment.subject_id.toString(),
            term_id: assessment.term_id.toString()
        })
        setError(null)
        setShowModal(true)
    }

    const handleSave = async () => {
        if (!formData.title.trim() || !formData.class_id || !formData.subject_id || !formData.term_id) {
            setError("Title, class, subject, and term are required")
            return
        }
        setSaving(true)
        setError(null)
        try {
            const payload = {
                title: formData.title,
                date: formData.date,
                max_score: parseFloat(formData.max_score) || 20,
                weight: parseInt(formData.weight) || 1,
                class_id: parseInt(formData.class_id),
                subject_id: parseInt(formData.subject_id),
                term_id: parseInt(formData.term_id)
            }
            const url = editingAssessment
                ? `${API_BASE_URL}/grades/assessments/${editingAssessment.id}`
                : `${API_BASE_URL}/grades/assessments`
            const method = editingAssessment ? "PUT" : "POST"
            const res = await fetch(url, {
                method,
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify(payload)
            })
            if (res.ok) {
                setShowModal(false)
                fetchAssessments()
            } else {
                const data = await res.json()
                setError(data.detail || "Failed to save assessment")
            }
        } catch (e) {
            setError("An error occurred")
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async (assessment: Assessment) => {
        if (!confirm(`Delete assessment "${assessment.title}"? This cannot be undone.`)) return
        try {
            const res = await fetch(`${API_BASE_URL}/grades/assessments/${assessment.id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok || res.status === 204) fetchAssessments()
        } catch (e) {
            console.error(e)
        }
    }

    const getClassName = (id: number) => classes.find(c => c.id === id)?.name || "—"
    const getSubjectName = (id: number) => subjects.find(s => s.id === id)?.name || "—"
    const getTermName = (id: number) => terms.find(t => t.id === id)?.name || "—"

    const filtered = assessments.filter(a =>
        a.title.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">Assessments</h1>
                    <p className="text-sm text-[#6B7280] mt-1">Manage exams, tests and grade entries</p>
                </div>
                <Button onClick={openCreate} className="bg-black text-white hover:bg-black/90 rounded-lg">
                    <Plus className="h-4 w-4 mr-2" />
                    New Assessment
                </Button>
            </div>

            <div className="flex flex-wrap gap-4">
                <div className="relative flex-1 min-w-[200px] max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6B7280]" />
                    <input
                        type="search"
                        placeholder="Search assessments..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-[#E5E7EB] rounded-lg bg-white text-[#111827] placeholder:text-[#6B7280] focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                </div>
                <select
                    value={filterClassId}
                    onChange={(e) => setFilterClassId(e.target.value)}
                    className="border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                    <option value="">All Classes</option>
                    {classes.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-[#111827]">Assessment List ({filtered.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="text-center py-12 text-[#6B7280]">Loading assessments...</div>
                    ) : filtered.length === 0 ? (
                        <div className="text-center py-12 text-[#6B7280]">
                            {searchQuery ? `No assessments found matching "${searchQuery}"` : "No assessments yet. Create your first assessment!"}
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-[#E5E7EB]">
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Title</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Class</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Subject</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Term</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Date</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Max Score</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtered.map((assessment) => (
                                        <tr key={assessment.id} className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] transition-colors">
                                            <td className="py-3 px-4 text-sm font-medium text-[#111827]">{assessment.title}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{getClassName(assessment.class_id)}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{getSubjectName(assessment.subject_id)}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{getTermName(assessment.term_id)}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{new Date(assessment.date).toLocaleDateString()}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{assessment.max_score}</td>
                                            <td className="py-3 px-4">
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                                                        onClick={() => router.push(`/${locale}/dashboard/grades/assessments/${assessment.id}`)}
                                                        title="Enter grades"
                                                    >
                                                        <ClipboardList className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-[#2563EB] hover:text-[#2563EB] hover:bg-[#F0F1F3]"
                                                        onClick={() => openEdit(assessment)}
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-red-600 hover:text-red-600 hover:bg-red-50"
                                                        onClick={() => handleDelete(assessment)}
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
                <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                        <DialogTitle>{editingAssessment ? "Edit Assessment" : "New Assessment"}</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded text-sm">{error}</div>
                        )}
                        <div className="space-y-2">
                            <Label>Title *</Label>
                            <Input
                                placeholder="e.g. Mid-term exam, Quiz 1"
                                value={formData.title}
                                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
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
                        </div>
                        <div className="space-y-2">
                            <Label>Term *</Label>
                            <select
                                value={formData.term_id}
                                onChange={(e) => setFormData({ ...formData, term_id: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            >
                                <option value="">Select term</option>
                                {terms.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                            </select>
                        </div>
                        <div className="space-y-2">
                            <Label>Date *</Label>
                            <input
                                type="date"
                                value={formData.date}
                                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                                className="w-full border border-[#E5E7EB] rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Max Score</Label>
                                <Input
                                    type="number"
                                    min="1"
                                    placeholder="20"
                                    value={formData.max_score}
                                    onChange={(e) => setFormData({ ...formData, max_score: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Weight</Label>
                                <Input
                                    type="number"
                                    min="1"
                                    placeholder="1"
                                    value={formData.weight}
                                    onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
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
