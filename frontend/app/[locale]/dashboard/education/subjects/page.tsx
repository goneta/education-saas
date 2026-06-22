"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { requestConfirmation } from "@/lib/confirmation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Plus, Pencil, Trash2, Search } from "lucide-react"

interface Subject {
    id: number
    name: string
    description: string | null
    coefficient: number
    school_id: number
}

export default function SubjectsPage() {
    const { token } = useAuth()
    const [subjects, setSubjects] = useState<Subject[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState("")
    const [showModal, setShowModal] = useState(false)
    const [editingSubject, setEditingSubject] = useState<Subject | null>(null)
    const [formData, setFormData] = useState({ name: "", description: "", coefficient: "1" })
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const fetchSubjects = async () => {
        if (!token) return
        setIsLoading(true)
        try {
            const res = await fetch(`${API_BASE_URL}/education/subjects`, {
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok) setSubjects(await res.json())
        } catch (e) {
            console.error(e)
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchSubjects()
    // Subject list loading is intentionally bound to the auth token.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token])

    const openCreate = () => {
        setEditingSubject(null)
        setFormData({ name: "", description: "", coefficient: "1" })
        setError(null)
        setShowModal(true)
    }

    const openEdit = (subject: Subject) => {
        setEditingSubject(subject)
        setFormData({
            name: subject.name,
            description: subject.description || "",
            coefficient: subject.coefficient.toString()
        })
        setError(null)
        setShowModal(true)
    }

    const handleSave = async () => {
        if (!formData.name.trim()) {
            setError("Le nom de la matière est obligatoire.")
            return
        }
        setSaving(true)
        setError(null)
        try {
            const payload = {
                name: formData.name,
                description: formData.description || null,
                coefficient: parseInt(formData.coefficient) || 1
            }
            const url = editingSubject
                ? `${API_BASE_URL}/education/subjects/${editingSubject.id}`
                : `${API_BASE_URL}/education/subjects`
            const method = editingSubject ? "PUT" : "POST"
            const res = await fetch(url, {
                method,
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify(payload)
            })
            if (res.ok) {
                setShowModal(false)
                fetchSubjects()
            } else {
                const data = await res.json()
                setError(data.detail || "Impossible d'enregistrer la matière.")
            }
        } catch {
            setError("Une erreur est survenue.")
        } finally {
            setSaving(false)
        }
    }

    const handleDelete = async (subject: Subject) => {
        if (!await requestConfirmation({ title: "Supprimer cette matière", description: `La matière « ${subject.name} » sera supprimée définitivement si aucune donnée ne la protège.`, confirmLabel: "Supprimer définitivement", destructive: true })) return
        try {
            const res = await fetch(`${API_BASE_URL}/education/subjects/${subject.id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            })
            if (res.ok || res.status === 204) fetchSubjects()
        } catch (e) {
            console.error(e)
        }
    }

    const filtered = subjects.filter(s =>
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (s.description || "").toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-[#111827]">Matières</h1>
                    <p className="text-sm text-[#6B7280] mt-1">Gérez les matières et programmes de l&apos;établissement.</p>
                </div>
                <Button onClick={openCreate} className="bg-black text-white hover:bg-black/90 rounded-lg">
                    <Plus className="h-4 w-4 mr-2" />
                    Ajouter une matière
                </Button>
            </div>

            <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#6B7280]" />
                <input
                    type="search"
                    placeholder="Rechercher une matière..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-[#E5E7EB] rounded-lg bg-white text-[#111827] placeholder:text-[#6B7280] focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
            </div>

            <Card data-teducai-collapsible="false" className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="text-[#111827]">Liste des matières ({filtered.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="text-center py-12 text-[#6B7280]">Chargement des matières...</div>
                    ) : filtered.length === 0 ? (
                        <div className="text-center py-12 text-[#6B7280]">
                            {searchQuery ? `Aucune matière ne correspond à « ${searchQuery} ».` : "Aucune matière enregistrée. Ajoutez votre première matière."}
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-[#E5E7EB]">
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Nom</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Description</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Coefficient</th>
                                        <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filtered.map((subject) => (
                                        <tr key={subject.id} className="border-b border-[#E5E7EB] last:border-0 hover:bg-[#F6F7F9] transition-colors">
                                            <td className="py-3 px-4 text-sm font-medium text-[#111827]">{subject.name}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{subject.description || "—"}</td>
                                            <td className="py-3 px-4 text-sm text-[#6B7280]">{subject.coefficient}</td>
                                            <td className="py-3 px-4">
                                                <div className="flex gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-[#111827] hover:bg-[#F0F1F3] dark:text-white dark:hover:bg-[#343b41]"
                                                        onClick={() => openEdit(subject)}
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className="h-8 text-red-600 hover:text-red-600 hover:bg-red-50"
                                                        onClick={() => handleDelete(subject)}
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
                        <DialogTitle>{editingSubject ? "Modifier la matière" : "Ajouter une matière"}</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        {error && (
                            <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded text-sm">{error}</div>
                        )}
                        <div className="space-y-2">
                            <Label htmlFor="name">Nom de la matière *</Label>
                            <Input
                                id="name"
                                placeholder="Ex. Mathématiques, Français"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Input
                                id="description"
                                placeholder="Description facultative"
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="coefficient">Coefficient</Label>
                            <Input
                                id="coefficient"
                                type="number"
                                min="1"
                                placeholder="1"
                                value={formData.coefficient}
                                onChange={(e) => setFormData({ ...formData, coefficient: e.target.value })}
                            />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowModal(false)}>Annuler</Button>
                        <Button onClick={handleSave} disabled={saving} className="bg-black text-white hover:bg-black/90">
                            {saving ? "Enregistrement..." : "Enregistrer"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}
