"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import type { ReactNode } from "react"
import { Download, Edit3, FileText, Lock, Plus, RefreshCw, Trash2, Unlock, Upload, Wand2 } from "lucide-react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { AppleAccordion } from "@/components/ui/apple-accordion"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"

interface TimetableEntry {
    id: number
    day_of_week: string
    start_time: string
    end_time: string
    room: string | null
    class_id: number
    subject_id: number
    teacher_id: number | null
    duration_minutes?: number | null
    is_locked: boolean
    lock_scope?: string | null
    status: string
    generation_batch?: string | null
    conflict_status?: string
    conflict_details?: Array<{ type: string; severity: string; message: string; suggestions?: string[] }>
}

interface ClassItem { id: number; name: string; level?: string | null }
interface Subject { id: number; name: string }
interface Teacher { id: number; full_name: string }

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
const DAY_LABELS: Record<string, string> = {
    monday: "Lundi",
    tuesday: "Mardi",
    wednesday: "Mercredi",
    thursday: "Jeudi",
    friday: "Vendredi",
    saturday: "Samedi",
}

const emptyForm = {
    id: "",
    class_id: "",
    subject_id: "",
    teacher_id: "",
    day_of_week: "monday",
    start_time: "08:00",
    end_time: "10:00",
    room: "",
    is_locked: false,
    lock_scope: "",
}

export default function TimetablePage() {
    const { token, user } = useAuth()
    const [entries, setEntries] = useState<TimetableEntry[]>([])
    const [classes, setClasses] = useState<ClassItem[]>([])
    const [subjects, setSubjects] = useState<Subject[]>([])
    const [teachers, setTeachers] = useState<Teacher[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [filterClassId, setFilterClassId] = useState("")
    const [filterTeacherId, setFilterTeacherId] = useState("")
    const [filterRoom, setFilterRoom] = useState("")
    const [showModal, setShowModal] = useState(false)
    const [formData, setFormData] = useState(emptyForm)
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [validation, setValidation] = useState<{ has_conflicts: boolean; conflicts: TimetableEntry["conflict_details"]; suggestions: string[] } | null>(null)
    const [selectedIds, setSelectedIds] = useState<number[]>([])
    const [bulkRoom, setBulkRoom] = useState("")
    const [bulkTeacherId, setBulkTeacherId] = useState("")
    const [generation, setGeneration] = useState({
        mode: "partial",
        scope_type: "class",
        scope_id: "",
        level: "",
        subject_ids: "",
        preserve_locks: true,
        max_course_minutes: "180",
        min_start: "07:00",
        max_end: "19:00",
        rooms: "Salle 1, Salle 2, Salle 3, Laboratoire 1, Atelier 1",
    })
    const [statusText, setStatusText] = useState("")
    const [openPanels, setOpenPanels] = useState<Set<string>>(new Set())

    const isAdmin = ["super_admin", "school_admin", "admin", "direction", "director", "principal", "pedagogy_coordinator"].includes(user?.role || "")

    const authHeaders = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token])
    const togglePanel = (panel: string) => {
        setOpenPanels(previous => {
            const next = new Set(previous)
            if (next.has(panel)) next.delete(panel)
            else next.add(panel)
            return next
        })
    }

    const fetchEntries = useCallback(async () => {
        if (!token) return
        setIsLoading(true)
        const params = new URLSearchParams()
        if (filterClassId) params.set("class_id", filterClassId)
        if (filterTeacherId) params.set("teacher_id", filterTeacherId)
        if (filterRoom) params.set("room", filterRoom)
        const res = await fetch(`${API_BASE_URL}/education/timetables${params.toString() ? `?${params}` : ""}`, { headers: authHeaders })
        if (res.ok) setEntries(await res.json())
        setIsLoading(false)
    }, [authHeaders, filterClassId, filterRoom, filterTeacherId, token])

    const fetchMeta = useCallback(async () => {
        if (!token) return
        const [classRes, subjectRes, teacherRes] = await Promise.all([
            fetch(`${API_BASE_URL}/education/classes`, { headers: authHeaders }),
            fetch(`${API_BASE_URL}/education/subjects`, { headers: authHeaders }),
            fetch(`${API_BASE_URL}/teachers/`, { headers: authHeaders }),
        ])
        if (classRes.ok) setClasses(await classRes.json())
        if (subjectRes.ok) setSubjects(await subjectRes.json())
        if (teacherRes.ok) setTeachers(await teacherRes.json())
    }, [authHeaders, token])

    useEffect(() => { void fetchMeta() }, [fetchMeta])
    useEffect(() => { void fetchEntries() }, [fetchEntries])

    const getClassName = (id: number) => classes.find(item => item.id === id)?.name || "-"
    const getClassLevel = (id: number) => classes.find(item => item.id === id)?.level || ""
    const getSubjectName = (id: number) => subjects.find(item => item.id === id)?.name || "-"
    const getTeacherName = (id: number | null) => id ? teachers.find(item => item.id === id)?.full_name || "-" : "-"

    const entriesByDay = DAYS.map(day => ({
        day,
        entries: entries.filter(entry => entry.day_of_week === day).sort((a, b) => a.start_time.localeCompare(b.start_time)),
    }))

    const openCreate = () => {
        setFormData({ ...emptyForm, class_id: classes[0]?.id.toString() || "", subject_id: subjects[0]?.id.toString() || "" })
        setValidation(null)
        setError(null)
        setShowModal(true)
    }

    const openEdit = (entry: TimetableEntry) => {
        setFormData({
            id: entry.id.toString(),
            class_id: entry.class_id.toString(),
            subject_id: entry.subject_id.toString(),
            teacher_id: entry.teacher_id?.toString() || "",
            day_of_week: entry.day_of_week,
            start_time: entry.start_time.slice(0, 5),
            end_time: entry.end_time.slice(0, 5),
            room: entry.room || "",
            is_locked: entry.is_locked,
            lock_scope: entry.lock_scope || "",
        })
        setValidation({ has_conflicts: Boolean(entry.conflict_details?.length), conflicts: entry.conflict_details || [], suggestions: [] })
        setError(null)
        setShowModal(true)
    }

    const payloadFromForm = () => ({
        class_id: Number(formData.class_id),
        subject_id: Number(formData.subject_id),
        teacher_id: formData.teacher_id ? Number(formData.teacher_id) : null,
        day_of_week: formData.day_of_week,
        start_time: formData.start_time,
        end_time: formData.end_time,
        room: formData.room || null,
        is_locked: formData.is_locked,
        lock_scope: formData.lock_scope || null,
        constraints_snapshot: {
            min_start: generation.min_start,
            max_end: generation.max_end,
            max_course_minutes: Number(generation.max_course_minutes || 180),
        },
    })

    const validateForm = async () => {
        if (!token || !formData.class_id || !formData.subject_id) return
        const params = formData.id ? `?exclude_id=${formData.id}` : ""
        const res = await fetch(`${API_BASE_URL}/education/timetables/validate${params}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders },
            body: JSON.stringify(payloadFromForm()),
        })
        if (res.ok) setValidation(await res.json())
    }

    const saveEntry = async () => {
        if (!formData.class_id || !formData.subject_id) {
            setError("La classe et la matière sont obligatoires.")
            return
        }
        setSaving(true)
        setError(null)
        await validateForm()
        const method = formData.id ? "PUT" : "POST"
        const url = formData.id ? `${API_BASE_URL}/education/timetables/${formData.id}` : `${API_BASE_URL}/education/timetables`
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json", ...authHeaders },
            body: JSON.stringify(payloadFromForm()),
        })
        if (res.ok) {
            setShowModal(false)
            setStatusText("Emploi du temps mis à jour. Vérifiez les conflits avant publication.")
            await fetchEntries()
        } else {
            const data = await res.json()
            setError(data.detail || "Enregistrement impossible.")
        }
        setSaving(false)
    }

    const deleteEntry = async (entry: TimetableEntry) => {
        if (!confirm("Supprimer ce cours ?")) return
        const res = await fetch(`${API_BASE_URL}/education/timetables/${entry.id}`, { method: "DELETE", headers: authHeaders })
        if (res.ok || res.status === 204) await fetchEntries()
    }

    const runGeneration = async () => {
        const payload = {
            mode: generation.mode,
            scope_type: generation.scope_type || null,
            scope_id: generation.scope_id ? Number(generation.scope_id) : null,
            level: generation.level || null,
            subject_ids: generation.subject_ids.split(",").map(value => Number(value.trim())).filter(Boolean),
            preserve_locks: generation.preserve_locks,
            constraints: {
                min_start: generation.min_start,
                max_end: generation.max_end,
                max_course_minutes: Number(generation.max_course_minutes || 180),
                rooms: generation.rooms.split(",").map(room => room.trim()).filter(Boolean),
            },
        }
        const res = await fetch(`${API_BASE_URL}/education/timetables/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders },
            body: JSON.stringify(payload),
        })
        if (res.ok) {
            const data = await res.json()
            setStatusText(`Génération terminée: ${data.created} cours créés, ${data.deleted} supprimés, ${data.skipped?.length || 0} ignorés.`)
            await fetchEntries()
        }
    }

    const publish = async () => {
        const res = await fetch(`${API_BASE_URL}/education/timetables/publish`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders },
            body: JSON.stringify({ class_id: filterClassId ? Number(filterClassId) : null, teacher_id: filterTeacherId ? Number(filterTeacherId) : null }),
        })
        if (res.ok) {
            const data = await res.json()
            setStatusText(`${data.published} cours publiés dans les dashboards professeurs, élèves et parents.`)
            await fetchEntries()
        }
    }

    const bulkUpdate = async () => {
        if (!selectedIds.length) return
        const changes: Record<string, unknown> = {}
        if (bulkRoom) changes.room = bulkRoom
        if (bulkTeacherId) changes.teacher_id = Number(bulkTeacherId)
        if (!Object.keys(changes).length) return
        const res = await fetch(`${API_BASE_URL}/education/timetables/bulk-update`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders },
            body: JSON.stringify({ entry_ids: selectedIds, changes }),
        })
        if (res.ok) {
            setSelectedIds([])
            setBulkRoom("")
            setBulkTeacherId("")
            setStatusText("Modification multiple appliquée.")
            await fetchEntries()
        }
    }

    const exportUrl = (format: string) => {
        const params = new URLSearchParams({ export_format: format })
        if (filterClassId) params.set("class_id", filterClassId)
        if (filterTeacherId) params.set("teacher_id", filterTeacherId)
        if (filterRoom) params.set("room", filterRoom)
        return `${API_BASE_URL}/education/timetables/export?${params}`
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h1 className="apple-page-title">Emplois du temps</h1>
                    <p className="apple-page-description">Génération, édition manuelle, conflits, publication et exports.</p>
                </div>
                {isAdmin && <Button onClick={openCreate} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> Ajouter un cours</Button>}
            </div>

            {statusText && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">{statusText}</div>}

            <AppleAccordion title="Configuration" open={openPanels.has("configuration")} onToggle={() => togglePanel("configuration")}>
                <div className="grid gap-3 text-sm md:grid-cols-4">
                    <InfoTile label="Classes chargées" value={classes.length.toString()} />
                    <InfoTile label="Matières chargées" value={subjects.length.toString()} />
                    <InfoTile label="Professeurs chargés" value={teachers.length.toString()} />
                    <InfoTile label="Droits d'administration" value={isAdmin ? "Modification autorisée" : "Consultation uniquement"} />
                </div>
                <p className="mt-3 text-sm text-[#6B7280]">
                    Cliquez sur les sections ci-dessous pour configurer la génération, filtrer les cours ou consulter les journées de la semaine.
                </p>
            </AppleAccordion>

            {isAdmin && (
                <AppleAccordion title="Génération automatique et régénération" open={openPanels.has("generation")} onToggle={() => togglePanel("generation")}>
                    <div className="space-y-4">
                        <div className="grid gap-3 md:grid-cols-4">
                            <Field label="Mode">
                                <select value={generation.mode} onChange={event => setGeneration({ ...generation, mode: event.target.value })} className="apple-select">
                                    <option value="partial">Régénération partielle</option>
                                    <option value="complete">Régénération complète</option>
                                </select>
                            </Field>
                            <Field label="Périmètre">
                                <select value={generation.scope_type} onChange={event => setGeneration({ ...generation, scope_type: event.target.value })} className="apple-select">
                                    <option value="class">Classe</option>
                                    <option value="level">Niveau</option>
                                    <option value="teacher">Professeur</option>
                                    <option value="subject">Matières sélectionnées</option>
                                </select>
                            </Field>
                            <Field label="Classe / professeur">
                                <select value={generation.scope_id} onChange={event => setGeneration({ ...generation, scope_id: event.target.value })} className="apple-select">
                                    <option value="">Tous / non sélectionné</option>
                                    {generation.scope_type === "teacher" ? teachers.map(item => <option key={item.id} value={item.id}>{item.full_name}</option>) : classes.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
                                </select>
                            </Field>
                            <Field label="Niveau">
                                <input value={generation.level} onChange={event => setGeneration({ ...generation, level: event.target.value })} className="apple-input" placeholder="6e, Terminale, L1..." />
                            </Field>
                            <Field label="IDs matières">
                                <input value={generation.subject_ids} onChange={event => setGeneration({ ...generation, subject_ids: event.target.value })} className="apple-input" placeholder="1,2,3" />
                            </Field>
                            <Field label="Salles disponibles">
                                <input value={generation.rooms} onChange={event => setGeneration({ ...generation, rooms: event.target.value })} className="apple-input" />
                            </Field>
                            <Field label="Horaires autorisés">
                                <div className="grid grid-cols-2 gap-2"><input type="time" value={generation.min_start} onChange={event => setGeneration({ ...generation, min_start: event.target.value })} className="apple-input" /><input type="time" value={generation.max_end} onChange={event => setGeneration({ ...generation, max_end: event.target.value })} className="apple-input" /></div>
                            </Field>
                            <Field label="Durée max">
                                <input type="number" value={generation.max_course_minutes} onChange={event => setGeneration({ ...generation, max_course_minutes: event.target.value })} className="apple-input" />
                            </Field>
                        </div>
                        <label className="flex items-center gap-2 text-sm text-[#111827]"><input type="checkbox" checked={generation.preserve_locks} onChange={event => setGeneration({ ...generation, preserve_locks: event.target.checked })} /> Préserver les cours verrouillés</label>
                        <div className="flex flex-wrap gap-2">
                            <Button onClick={runGeneration}><Wand2 className="mr-2 h-4 w-4" /> Générer les emplois du temps</Button>
                            <Button variant="outline" onClick={publish}><Upload className="mr-2 h-4 w-4" /> Publier</Button>
                            <a className="inline-flex items-center rounded-lg border px-4 py-2 text-sm" href={exportUrl("pdf")} target="_blank"><FileText className="mr-2 h-4 w-4" /> PDF</a>
                            <a className="inline-flex items-center rounded-lg border px-4 py-2 text-sm" href={exportUrl("csv")} target="_blank"><Download className="mr-2 h-4 w-4" /> CSV</a>
                            <a className="inline-flex items-center rounded-lg border px-4 py-2 text-sm" href={exportUrl("excel")} target="_blank"><Download className="mr-2 h-4 w-4" /> Excel</a>
                        </div>
                    </div>
                </AppleAccordion>
            )}

            <AppleAccordion title="Filtres et modification multiple" open={openPanels.has("filters")} onToggle={() => togglePanel("filters")}>
                <div className="space-y-4">
                    <div className="grid gap-3 md:grid-cols-4">
                        <Field label="Classe">
                            <select value={filterClassId} onChange={event => setFilterClassId(event.target.value)} className="apple-select"><option value="">Toutes les classes</option>{classes.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
                        </Field>
                        <Field label="Professeur">
                            <select value={filterTeacherId} onChange={event => setFilterTeacherId(event.target.value)} className="apple-select"><option value="">Tous les professeurs</option>{teachers.map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select>
                        </Field>
                        <Field label="Salle">
                            <input value={filterRoom} onChange={event => setFilterRoom(event.target.value)} className="apple-input" placeholder="Salle 3" />
                        </Field>
                        <div className="flex items-end"><Button variant="outline" onClick={fetchEntries}><RefreshCw className="mr-2 h-4 w-4" /> Actualiser</Button></div>
                    </div>
                    {isAdmin && selectedIds.length > 0 && (
                        <div className="grid gap-3 rounded-2xl border bg-[#F8FAFC] p-4 md:grid-cols-4">
                            <p className="text-sm font-semibold">{selectedIds.length} cours sélectionné(s)</p>
                            <input value={bulkRoom} onChange={event => setBulkRoom(event.target.value)} className="apple-input" placeholder="Nouvelle salle" />
                            <select value={bulkTeacherId} onChange={event => setBulkTeacherId(event.target.value)} className="apple-select"><option value="">Nouveau professeur</option>{teachers.map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select>
                            <Button onClick={bulkUpdate}>Appliquer</Button>
                        </div>
                    )}
                </div>
            </AppleAccordion>

            {isLoading ? <div className="py-12 text-center text-[#6B7280]">Chargement...</div> : (
                <AppleAccordion title="Emploi du temps hebdomadaire" open={openPanels.has("weekly")} onToggle={() => togglePanel("weekly")}>
                    <div className="space-y-4">
                        {entriesByDay.map(({ day, entries: dayEntries }) => (
                            <AppleAccordion key={day} title={DAY_LABELS[day] || day} open={openPanels.has(`day:${day}`)} onToggle={() => togglePanel(`day:${day}`)} lazy>
                                {!dayEntries.length ? <p className="text-sm text-[#6B7280]">Aucun cours.</p> : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full min-w-[960px] text-sm">
                                            <thead><tr className="border-b"><th className="py-2"></th><th className="py-2 text-left">Heure</th><th className="py-2 text-left">Classe</th><th className="py-2 text-left">Matière</th><th className="py-2 text-left">Professeur</th><th className="py-2 text-left">Salle</th><th className="py-2 text-left">Statut</th><th className="py-2 text-left">Conflits</th><th className="py-2 text-right">Actions</th></tr></thead>
                                            <tbody>{dayEntries.map(entry => (
                                                <tr key={entry.id} className="border-b last:border-0">
                                                    <td className="py-2">{isAdmin && <input type="checkbox" checked={selectedIds.includes(entry.id)} onChange={event => setSelectedIds(prev => event.target.checked ? [...prev, entry.id] : prev.filter(id => id !== entry.id))} />}</td>
                                                    <td className="py-2">{entry.start_time.slice(0, 5)} - {entry.end_time.slice(0, 5)}</td>
                                                    <td className="py-2">{getClassName(entry.class_id)} <span className="text-[#6B7280]">{getClassLevel(entry.class_id)}</span></td>
                                                    <td className="py-2">{getSubjectName(entry.subject_id)}</td>
                                                    <td className="py-2">{getTeacherName(entry.teacher_id)}</td>
                                                    <td className="py-2">{entry.room || "-"}</td>
                                                    <td className="py-2">{entry.is_locked ? <span className="inline-flex items-center gap-1"><Lock className="h-3 w-3" /> verrouillé</span> : entry.status}</td>
                                                    <td className="py-2"><span className={entry.conflict_status === "conflict" ? "text-red-700" : entry.conflict_status === "warning" ? "text-amber-700" : "text-emerald-700"}>{entry.conflict_status || "clear"}</span></td>
                                                    <td className="py-2 text-right">{isAdmin && <><Button variant="ghost" size="sm" onClick={() => openEdit(entry)}><Edit3 className="h-4 w-4" /></Button><Button variant="ghost" size="sm" onClick={() => deleteEntry(entry)} className="text-red-600"><Trash2 className="h-4 w-4" /></Button></>}</td>
                                                </tr>
                                            ))}</tbody>
                                        </table>
                                    </div>
                                )}
                            </AppleAccordion>
                        ))}
                    </div>
                </AppleAccordion>
            )}

            <Dialog open={showModal} onOpenChange={setShowModal}>
                <DialogContent className="sm:max-w-[760px]">
                    <DialogHeader><DialogTitle>{formData.id ? "Modifier un cours" : "Ajouter un cours"}</DialogTitle></DialogHeader>
                    <div className="space-y-4 py-4">
                        {error && <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>}
                        <div className="grid gap-3 md:grid-cols-3">
                            <Field label="Classe"><select value={formData.class_id} onChange={event => setFormData({ ...formData, class_id: event.target.value })} className="apple-select"><option value="">Sélectionner</option>{classes.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field>
                            <Field label="Matière"><select value={formData.subject_id} onChange={event => setFormData({ ...formData, subject_id: event.target.value })} className="apple-select"><option value="">Sélectionner</option>{subjects.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field>
                            <Field label="Professeur"><select value={formData.teacher_id} onChange={event => setFormData({ ...formData, teacher_id: event.target.value })} className="apple-select"><option value="">Non affecté</option>{teachers.map(item => <option key={item.id} value={item.id}>{item.full_name}</option>)}</select></Field>
                            <Field label="Jour"><select value={formData.day_of_week} onChange={event => setFormData({ ...formData, day_of_week: event.target.value })} className="apple-select">{DAYS.map(day => <option key={day} value={day}>{DAY_LABELS[day]}</option>)}</select></Field>
                            <Field label="Début"><input type="time" value={formData.start_time} onChange={event => setFormData({ ...formData, start_time: event.target.value })} className="apple-input" /></Field>
                            <Field label="Fin"><input type="time" value={formData.end_time} onChange={event => setFormData({ ...formData, end_time: event.target.value })} className="apple-input" /></Field>
                            <Field label="Salle"><input value={formData.room} onChange={event => setFormData({ ...formData, room: event.target.value })} className="apple-input" /></Field>
                            <Field label="Verrouillage"><label className="flex h-11 items-center gap-2 rounded-lg border px-3 text-sm"><input type="checkbox" checked={formData.is_locked} onChange={event => setFormData({ ...formData, is_locked: event.target.checked })} /> {formData.is_locked ? <Lock className="h-4 w-4" /> : <Unlock className="h-4 w-4" />} Ne jamais modifier à la génération</label></Field>
                            <Field label="Portée du verrou"><input value={formData.lock_scope} onChange={event => setFormData({ ...formData, lock_scope: event.target.value })} className="apple-input" placeholder="classe, professeur, salle..." /></Field>
                        </div>
                        <Button variant="outline" onClick={validateForm}>Vérifier les conflits</Button>
                        {validation && (
                            <div className={`rounded-xl border p-4 text-sm ${validation.has_conflicts ? "border-amber-200 bg-amber-50" : "border-emerald-200 bg-emerald-50"}`}>
                                <p className="font-semibold">{validation.has_conflicts ? "Conflits détectés avant validation" : "Aucun conflit détecté"}</p>
                                {(validation.conflicts || []).map((conflict, index) => <div key={`${conflict.type}-${index}`} className="mt-2"><p>{conflict.message}</p><ul className="ml-5 list-disc text-[#6B7280]">{conflict.suggestions?.map(item => <li key={item}>{item}</li>)}</ul></div>)}
                            </div>
                        )}
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowModal(false)}>Annuler</Button>
                        <Button onClick={saveEntry} disabled={saving} className="bg-black text-white hover:bg-black/90">{saving ? "Enregistrement..." : "Enregistrer"}</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
    return <div className="space-y-2"><Label className="text-sm text-[#6B7280]">{label}</Label>{children}</div>
}

function InfoTile({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-[18px] border border-[#E5E7EB] bg-white px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-[0.08em] text-[#6B7280]">{label}</p>
            <p className="mt-1 font-semibold text-[#111827]">{value}</p>
        </div>
    )
}
