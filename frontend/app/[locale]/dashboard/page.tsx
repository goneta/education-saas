"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react"
import { Activity, ArchiveRestore, Building2, Calendar, Download, FileClock, GraduationCap, Layers3, Pencil, Plus, RefreshCw, School, SlidersHorizontal, Trash2, Upload, Users } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { normalizeLocale } from "@/lib/i18n"

interface ActivityItem {
    id: number
    description: string
    time: string
    type: string
}

interface DashboardStats {
    total_students: number
    upcoming_classes_today: number
    active_classes_count: number
    recent_activities: ActivityItem[]
}

type SchoolRow = {
    id: number
    name: string
    domain_prefix: string
    school_type?: string
    country_code?: string
    address?: string
    formatted_address?: string
    is_active: boolean
    created_at: string
}

type AuditRow = {
    id: number
    action: string
    entity_type?: string
    entity_id?: string
    created_at: string
    school_id?: number
    actor_id?: number
}

const modules = [
    { label: "Élèves", href: "/dashboard/students", catalog: "Modèles de profils, documents d'inscription, règles d'import." },
    { label: "Professeurs", href: "/dashboard/teachers", catalog: "Profils enseignants, contrats types, catégories d'intervention." },
    { label: "Classes", href: "/dashboard/education/classes", catalog: "Classes standards, niveaux, cycles et groupes." },
    { label: "Matières", href: "/dashboard/education/subjects", catalog: "Matières globales, codes, coefficients et familles." },
    { label: "Emploi du temps", href: "/dashboard/education/timetable", catalog: "Modèles horaires, créneaux, règles de conflit." },
    { label: "Pédagogie", href: "/dashboard/education/pedagogy", catalog: "Programmes, modèles pédagogiques et référentiels." },
    { label: "Stages", href: "/dashboard/education/internships", catalog: "Catégories de stages, conventions et workflows." },
    { label: "Notes", href: "/dashboard/grades", catalog: "Barèmes, modèles d'évaluation et bulletins." },
    { label: "Bibliothèque", href: "/dashboard/library", catalog: "Catégories, règles de prêt et collections standards." },
    { label: "Portail Parent / Élève", href: "/dashboard/portal", catalog: "Messages, droits portail et modèles de notification." },
    { label: "Documents", href: "/dashboard/documents", catalog: "Attestations, reçus, certificats et modèles PDF." },
    { label: "Opérations", href: "/dashboard/operations", catalog: "Processus, tâches, checklists et escalades." },
    { label: "Entreprise", href: "/dashboard/enterprise", catalog: "Entités, abonnements et paramètres multi-sites." },
    { label: "Admin Emploi", href: "/dashboard/emploi-admin", catalog: "Plans recruteur, règles CV, notifications emploi." },
    { label: "Finance", href: "/dashboard/finance", catalog: "Catégories comptables, caisses et politiques de paiement." },
    { label: "Frais", href: "/dashboard/finance/fees", catalog: "Frais standards, échéanciers et remises." },
    { label: "Rapports", href: "/dashboard/finance/reports", catalog: "Rapports financiers, exports et tableaux de bord." },
    { label: "Journal de caisse", href: "/dashboard/finance/cash-journal", catalog: "Types d'écritures, contrôles et clôtures." },
    { label: "Prévisionnel", href: "/dashboard/finance/forecasts", catalog: "Hypothèses, scénarios et vues budgétaires." },
    { label: "Paramétrage des frais", href: "/dashboard/finance/settings", catalog: "Règles de facturation, devise et taxes." },
    { label: "SMS", href: "/dashboard/finance/sms", catalog: "Modèles SMS, campagnes et seuils d'envoi." },
]

const academicYears = ["2024-2025", "2025-2026", "2026-2027"]

export default function DashboardPage() {
    const { token, user } = useAuth()
    const params = useParams()
    const locale = normalizeLocale(params.locale as string)
    const [stats, setStats] = useState<DashboardStats | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchStats = async () => {
            if (!token || user?.role === "super_admin") {
                setLoading(false)
                return
            }

            try {
                const response = await fetch(`${API_BASE_URL}/dashboard/stats`, {
                    headers: { Authorization: `Bearer ${token}` },
                })

                if (response.ok) {
                    setStats(await response.json())
                }
            } catch (error) {
                console.error("Failed to fetch dashboard stats:", error)
            } finally {
                setLoading(false)
            }
        }

        fetchStats()
    }, [token, user?.role])

    if (user?.role === "super_admin") {
        return <SuperAdminControlCenter token={token} locale={locale} />
    }

    return (
        <div className="grid min-h-full w-full auto-rows-max items-start gap-4 md:gap-8">
            <div className="grid w-full gap-4 md:grid-cols-3 md:gap-8">
                <MetricCard title="Total Students" icon={<Users className="h-4 w-4" />} value={loading ? "..." : stats?.total_students ?? 0} description="Registered students" />
                <MetricCard title="Classes Today" icon={<Calendar className="h-4 w-4" />} value={loading ? "..." : stats?.upcoming_classes_today ?? 0} description="Scheduled classes" />
                <MetricCard title="Active Classes" icon={<GraduationCap className="h-4 w-4" />} value={loading ? "..." : stats?.active_classes_count ?? 0} description="Currently in session" />
            </div>
            <Card className="w-full rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="text-[#111827] dark:text-white">Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {loading ? (
                            <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">Loading activities...</p>
                        ) : stats?.recent_activities && stats.recent_activities.length > 0 ? (
                            stats.recent_activities.map((activity) => (
                                <div key={activity.id} className="flex items-center">
                                    <Activity className="mr-2 h-4 w-4 text-[#6B7280]" />
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium leading-none text-[#111827] dark:text-white">{activity.description}</p>
                                        <p className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{new Date(activity.time).toLocaleString()}</p>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">No recent activity found.</p>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}

function SuperAdminControlCenter({ token, locale }: { token: string | null; locale: string }) {
    const [schools, setSchools] = useState<SchoolRow[]>([])
    const [audits, setAudits] = useState<AuditRow[]>([])
    const [tab, setTab] = useState<"catalog" | "school">("catalog")
    const [moduleLabel, setModuleLabel] = useState(modules[0].label)
    const [selectedSchoolId, setSelectedSchoolId] = useState<number | "">("")
    const [filters, setFilters] = useState({ model: "", country: "", city: "", status: "all", year: "2025-2026" })
    const [schoolForm, setSchoolForm] = useState({ name: "", domain_prefix: "", school_type: "general", country_code: "CI", address: "", email: "" })
    const [status, setStatus] = useState("")
    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : null, [token])

    const selectedModule = modules.find(item => item.label === moduleLabel) || modules[0]
    const selectedSchool = schools.find(school => school.id === Number(selectedSchoolId))
    const filteredSchools = schools.filter(school => {
        if (filters.status === "active" && !school.is_active) return false
        if (filters.status === "inactive" && school.is_active) return false
        if (filters.country && school.country_code !== filters.country) return false
        if (filters.model && school.school_type !== filters.model) return false
        if (filters.city && !(school.formatted_address || school.address || "").toLowerCase().includes(filters.city.toLowerCase())) return false
        return true
    })

    const load = () => {
        if (!headers) return
        fetch(`${API_BASE_URL}/system/schools`, { headers })
            .then(response => response.ok ? response.json() : [])
            .then(data => setSchools(Array.isArray(data) ? data : []))
            .catch(() => setSchools([]))
        fetch(`${API_BASE_URL}/system/audit-logs?limit=80`, { headers })
            .then(response => response.ok ? response.json() : [])
            .then(data => setAudits(Array.isArray(data) ? data : []))
            .catch(() => setAudits([]))
    }

    useEffect(load, [headers])

    const createSchool = async (event: FormEvent) => {
        event.preventDefault()
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/system/schools`, {
            method: "POST",
            headers,
            body: JSON.stringify(schoolForm),
        })
        const payload = await response.json().catch(() => null)
        if (!response.ok) {
            setStatus(payload?.detail || "Création de l'établissement impossible.")
            return
        }
        setStatus("Établissement enregistré.")
        setSchoolForm({ name: "", domain_prefix: "", school_type: "general", country_code: "CI", address: "", email: "" })
        load()
    }

    const updateSchoolStatus = async (school: SchoolRow, isActive: boolean) => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/system/schools/${school.id}/status`, {
            method: "PATCH",
            headers,
            body: JSON.stringify({ is_active: isActive }),
        })
        setStatus(response.ok ? (isActive ? "Établissement réactivé." : "Établissement suspendu.") : "Mise à jour du statut impossible.")
        if (response.ok) load()
    }

    return (
        <div className="mx-auto max-w-7xl space-y-5 text-[#111827] dark:text-white">
            <header className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <p className="text-sm font-semibold text-[#0F766E] dark:text-[#5eead4]">Super Admin</p>
                    <h1 className="text-2xl font-bold">Centre d&apos;administration multi-etablissements</h1>
                    <p className="mt-1 max-w-3xl text-sm text-[#64748B] dark:text-[#dce3eb]">Pilotez le catalogue global, les écoles, les années académiques et les rubriques métier depuis une vue transverse.</p>
                </div>
                <Button type="button" variant="outline" onClick={load}><RefreshCw className="h-4 w-4" /> Actualiser</Button>
            </header>

            <section className="grid gap-4 md:grid-cols-4">
                <AdminStat icon={<School />} label="Établissements" value={schools.length} />
                <AdminStat icon={<Building2 />} label="Actifs" value={schools.filter(school => school.is_active).length} />
                <AdminStat icon={<Layers3 />} label="Rubriques" value={modules.length} />
                <AdminStat icon={<FileClock />} label="Audits récents" value={audits.length} />
            </section>

            <section className="grid gap-3 rounded-lg border bg-white p-4 dark:border-[#3b4248] dark:bg-[#202528] lg:grid-cols-5">
                <Control label="Rubrique">
                    <select value={moduleLabel} onChange={event => setModuleLabel(event.target.value)} className="admin-select">
                        {modules.map(item => <option key={item.label} value={item.label}>{item.label}</option>)}
                    </select>
                </Control>
                <Control label="Établissement">
                    <select value={selectedSchoolId} onChange={event => setSelectedSchoolId(event.target.value ? Number(event.target.value) : "")} className="admin-select">
                        <option value="">Tous les établissements</option>
                        {filteredSchools.map(school => <option key={school.id} value={school.id}>{school.name}</option>)}
                    </select>
                </Control>
                <Control label="Année académique">
                    <select value={filters.year} onChange={event => setFilters({ ...filters, year: event.target.value })} className="admin-select">
                        {academicYears.map(year => <option key={year} value={year}>{year}</option>)}
                    </select>
                </Control>
                <Control label="Pays">
                    <input value={filters.country} onChange={event => setFilters({ ...filters, country: event.target.value.toUpperCase() })} placeholder="CI" className="admin-input" />
                </Control>
                <Control label="Statut">
                    <select value={filters.status} onChange={event => setFilters({ ...filters, status: event.target.value })} className="admin-select">
                        <option value="all">Tous</option>
                        <option value="active">Actifs</option>
                        <option value="inactive">Suspendus</option>
                    </select>
                </Control>
            </section>

            <div className="flex flex-wrap gap-2">
                <TabButton active={tab === "catalog"} onClick={() => setTab("catalog")}>Catalogue Global</TabButton>
                <TabButton active={tab === "school"} onClick={() => setTab("school")}>Gestion par établissement</TabButton>
            </div>

            {tab === "catalog" ? (
                <section className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
                    <Panel title={`Catalogue Global - ${selectedModule.label}`}>
                        <p className="text-sm leading-6 text-[#64748B] dark:text-[#dce3eb]">{selectedModule.catalog}</p>
                        <div className="mt-4 grid gap-2 sm:grid-cols-2">
                            {["Créer", "Modifier", "Archiver", "Restaurer", "Importer", "Exporter"].map((action, index) => (
                                <button key={action} type="button" className="flex min-h-11 items-center gap-2 rounded-lg border px-3 text-sm font-semibold dark:border-[#56616a]">
                                    {[<Plus key="plus" />, <Pencil key="edit" />, <Trash2 key="trash" />, <ArchiveRestore key="restore" />, <Upload key="upload" />, <Download key="download" />][index]}
                                    {action}
                                </button>
                            ))}
                        </div>
                    </Panel>
                    <Panel title="Rubriques administrables">
                        <div className="grid max-h-[520px] gap-2 overflow-auto pr-1">
                            {modules.map(item => (
                                <button key={item.label} type="button" onClick={() => setModuleLabel(item.label)} className={`rounded-lg border p-3 text-left text-sm transition dark:border-[#56616a] ${item.label === moduleLabel ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "bg-white dark:bg-[#252b30]"}`}>
                                    <strong>{item.label}</strong>
                                    <span className="mt-1 block opacity-80">{item.catalog}</span>
                                </button>
                            ))}
                        </div>
                    </Panel>
                </section>
            ) : (
                <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
                    <Panel title="Gestion complète des établissements">
                        <form onSubmit={createSchool} className="grid gap-3 md:grid-cols-2">
                            <input value={schoolForm.name} onChange={event => setSchoolForm({ ...schoolForm, name: event.target.value })} required placeholder="Nom de l'établissement" className="admin-input" />
                            <input value={schoolForm.domain_prefix} onChange={event => setSchoolForm({ ...schoolForm, domain_prefix: event.target.value })} required placeholder="Domaine court" className="admin-input" />
                            <input value={schoolForm.school_type} onChange={event => setSchoolForm({ ...schoolForm, school_type: event.target.value })} placeholder="Modèle" className="admin-input" />
                            <input value={schoolForm.country_code} onChange={event => setSchoolForm({ ...schoolForm, country_code: event.target.value.toUpperCase() })} placeholder="Pays" className="admin-input" />
                            <input value={schoolForm.email} onChange={event => setSchoolForm({ ...schoolForm, email: event.target.value })} placeholder="Email" className="admin-input" />
                            <input value={schoolForm.address} onChange={event => setSchoolForm({ ...schoolForm, address: event.target.value })} placeholder="Ville / adresse" className="admin-input" />
                            <Button className="bg-black text-white md:col-span-2"><Plus className="h-4 w-4" /> Enregistrer un établissement</Button>
                        </form>
                        <div className="mt-4 grid gap-2">
                            {filteredSchools.map(school => (
                                <div key={school.id} className="rounded-lg border p-3 dark:border-[#56616a]">
                                    <div className="flex flex-wrap items-center justify-between gap-3">
                                        <div>
                                            <p className="font-semibold">{school.name}</p>
                                            <p className="text-sm text-[#64748B] dark:text-[#dce3eb]">{school.school_type || "general"} - {school.country_code || "-"} - {school.is_active ? "actif" : "suspendu"}</p>
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            <Button type="button" variant="outline" onClick={() => setSelectedSchoolId(school.id)}>Gérer</Button>
                                            <Button type="button" variant="outline" onClick={() => updateSchoolStatus(school, !school.is_active)}>{school.is_active ? "Suspendre" : "Réactiver"}</Button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Panel>
                    <Panel title={`Gestion ${selectedModule.label} par établissement`}>
                        <p className="text-sm leading-6 text-[#64748B] dark:text-[#dce3eb]">Contexte actif: {selectedSchool?.name || "Tous les établissements"} - {filters.year}. Les actions ci-dessous ouvrent la rubrique existante avec le contexte sélectionné comme repère opérationnel.</p>
                        <div className="mt-4 grid gap-2 sm:grid-cols-2">
                            {["Créer", "Modifier", "Supprimer", "Importer", "Exporter", "Archiver", "Historique"].map(action => (
                                <Link key={action} href={`/${locale}${selectedModule.href}`} className="flex min-h-11 items-center gap-2 rounded-lg border px-3 text-sm font-semibold dark:border-[#56616a]">
                                    <SlidersHorizontal className="h-4 w-4" />
                                    {action}
                                </Link>
                            ))}
                        </div>
                        <div className="mt-5 rounded-lg bg-[#F8FAFC] p-3 dark:bg-[#1f2427]">
                            <p className="font-semibold">Historique des modifications</p>
                            <div className="mt-3 grid max-h-72 gap-2 overflow-auto">
                                {audits.filter(row => !selectedSchoolId || row.school_id === selectedSchoolId).slice(0, 12).map(row => (
                                    <div key={row.id} className="rounded-lg border bg-white p-3 text-sm dark:border-[#56616a] dark:bg-[#252b30]">
                                        <strong>{row.action}</strong>
                                        <p className="text-[#64748B] dark:text-[#dce3eb]">{row.entity_type || "system"} #{row.entity_id || "-"} - {new Date(row.created_at).toLocaleString()}</p>
                                    </div>
                                ))}
                                {!audits.length && <p className="text-sm text-[#64748B] dark:text-[#dce3eb]">Aucun audit disponible.</p>}
                            </div>
                        </div>
                    </Panel>
                </section>
            )}
            {status && <p className="text-sm font-medium text-[#0F766E] dark:text-[#5eead4]">{status}</p>}
        </div>
    )
}

function MetricCard({ title, icon, value, description }: { title: string; icon: ReactNode; value: ReactNode; description: string }) {
    return (
        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-[#111827] dark:text-white">{title}</CardTitle>
                <div className="text-[#6B7280] dark:text-[#c7d0da]">{icon}</div>
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold text-[#111827] dark:text-white">{value}</div>
                <p className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{description}</p>
            </CardContent>
        </Card>
    )
}

function AdminStat({ icon, label, value }: { icon: ReactNode; label: string; value: number }) {
    return <div className="rounded-lg border bg-white p-4 dark:border-[#3b4248] dark:bg-[#202528]"><div className="h-5 w-5 text-[#0F766E]">{icon}</div><p className="mt-3 text-sm text-[#64748B] dark:text-[#dce3eb]">{label}</p><p className="text-2xl font-bold">{value}</p></div>
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
    return <section data-teducai-collapsible="false" className="min-w-0 rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#202528]"><h2 className="mb-4 text-lg font-semibold">{title}</h2>{children}</section>
}

function Control({ label, children }: { label: string; children: ReactNode }) {
    return <label className="grid gap-1 text-sm font-semibold text-[#111827] dark:text-white">{label}{children}</label>
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
    return <button type="button" onClick={onClick} className={`rounded-full border px-4 py-2 text-sm font-semibold ${active ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-[#CBD5E1] bg-white text-[#111827] dark:border-[#56616a] dark:bg-[#202528] dark:text-white"}`}>{children}</button>
}
