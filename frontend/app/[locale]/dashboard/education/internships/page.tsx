"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import {
    BarChart3,
    BriefcaseBusiness,
    Building2,
    ClipboardCheck,
    FileText,
    NotebookTabs,
    Sparkles,
    Users,
} from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type Company = {
    id: number
    name: string
    industry?: string
    city?: string
    country?: string
    phone?: string
    email?: string
    hr_manager_name?: string
    interns_count: number
    status: string
}

type Internship = {
    id: number
    company_name: string
    company_id?: number
    academic_level?: string
    class_id?: number
    program?: string
    title?: string
    service_department?: string
    supervisor_name?: string
    start_date?: string
    end_date?: string
    status: string
    final_score?: number
    assignments_count: number
    ai_summary?: string
}

type Dashboard = {
    total_internships: number
    active_internships: number
    completed_internships: number
    partner_companies: number
    students_in_internship: number
    validation_rate: number
    insertion_rate: number
    by_company: Record<string, number>
    by_level: Record<string, number>
    by_country: Record<string, number>
}

type Student = {
    id: number
    user?: { full_name?: string }
    registration_number?: string
}

const emptyDashboard: Dashboard = {
    total_internships: 0,
    active_internships: 0,
    completed_internships: 0,
    partner_companies: 0,
    students_in_internship: 0,
    validation_rate: 0,
    insertion_rate: 0,
    by_company: {},
    by_level: {},
    by_country: {},
}

const todayDate = () => new Date().toISOString().slice(0, 10)
const toDateTime = (value: string) => value ? `${value}T00:00:00` : undefined
const shortDate = (value?: string) => value ? new Date(value).toLocaleDateString("fr-FR") : "-"

function splitIds(value: string) {
    return value.split(",").map(part => Number(part.trim())).filter(Boolean)
}

function cleanPayload<T extends Record<string, unknown>>(payload: T) {
    return Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== "" && value !== undefined && value !== null))
}

function StatCard({ title, value, icon: Icon, detail }: { title: string; value: string | number; icon: typeof BarChart3; detail: string }) {
    return (
        <Card className="rounded-[28px] border-[#E5E7EB] bg-white shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-[#6B7280]">{title}</CardTitle>
                <Icon className="h-5 w-5 text-[#111827]" />
            </CardHeader>
            <CardContent>
                <div className="text-3xl font-semibold text-[#111827]">{value}</div>
                <p className="mt-1 text-sm text-[#6B7280]">{detail}</p>
            </CardContent>
        </Card>
    )
}

export default function InternshipsPage() {
    const { token } = useAuth()
    const [companies, setCompanies] = useState<Company[]>([])
    const [internships, setInternships] = useState<Internship[]>([])
    const [students, setStudents] = useState<Student[]>([])
    const [dashboard, setDashboard] = useState<Dashboard>(emptyDashboard)
    const [status, setStatus] = useState("")
    const [selectedInternshipId, setSelectedInternshipId] = useState<number | null>(null)
    const [companyForm, setCompanyForm] = useState({
        name: "",
        rccm_number: "",
        tax_number: "",
        industry: "",
        description: "",
        address: "",
        city: "",
        region: "",
        country: "",
        latitude: "",
        longitude: "",
        hr_manager_name: "",
        hr_manager_role: "",
        phone: "",
        email: "",
        max_simultaneous_interns: "",
        website: "",
        logo_url: "",
    })
    const [internshipForm, setInternshipForm] = useState({
        company_id: "",
        company_name: "",
        student_ids: "",
        academic_level: "",
        class_id: "",
        program: "",
        training_program: "",
        title: "",
        description: "",
        objectives: "",
        service_department: "",
        supervisor_name: "",
        supervisor_role: "",
        supervisor_phone: "",
        supervisor_email: "",
        teacher_ref_id: "",
        pedagogy_coordinator_id: "",
        internship_manager_id: "",
        start_date: todayDate(),
        end_date: "",
        weeks_count: "",
        expected_schedule: "",
        status: "planned",
    })
    const [followupForm, setFollowupForm] = useState({
        internship_id: "",
        student_id: "",
        date: todayDate(),
        presence_status: "present",
        activities: "",
        tasks_description: "",
        developed_skills: "",
        tools_used: "",
        difficulties: "",
        supervisor_observation: "",
    })
    const [logbookForm, setLogbookForm] = useState({
        internship_id: "",
        student_id: "",
        date: todayDate(),
        tasks_done: "",
        acquired_skills: "",
        difficulties: "",
        proposed_solutions: "",
        hours_count: "",
    })
    const [evaluationForm, setEvaluationForm] = useState({
        internship_id: "",
        student_id: "",
        evaluation_type: "finale",
        company_score: "",
        report_score: "",
        defense_score: "",
        practical_score: "",
        final_score: "",
        comments: "",
    })
    const [documentForm, setDocumentForm] = useState({
        internship_id: "",
        student_id: "",
        document_type: "convention",
        title: "",
        secure_file_id: "",
    })

    const headers = useMemo(() => token ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } : undefined, [token])

    const loadData = useCallback(async () => {
        if (!headers) return
        const [summaryRes, companiesRes, internshipsRes, studentsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/internships/dashboard/summary`, { headers }),
            fetch(`${API_BASE_URL}/internships/companies`, { headers }),
            fetch(`${API_BASE_URL}/internships/`, { headers }),
            fetch(`${API_BASE_URL}/students/`, { headers }),
        ])
        if (summaryRes.ok) setDashboard(await summaryRes.json())
        if (companiesRes.ok) setCompanies(await companiesRes.json())
        if (internshipsRes.ok) setInternships(await internshipsRes.json())
        if (studentsRes.ok) {
            const data = await studentsRes.json()
            setStudents(Array.isArray(data) ? data : [])
        }
    }, [headers])

    useEffect(() => {
        loadData().catch(() => setStatus("Chargement impossible pour le module Stages."))
    }, [loadData])

    const submitCompany = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!headers) return
        setStatus("Enregistrement de l'entreprise partenaire...")
        const payload = {
            ...companyForm,
            latitude: companyForm.latitude ? Number(companyForm.latitude) : undefined,
            longitude: companyForm.longitude ? Number(companyForm.longitude) : undefined,
            max_simultaneous_interns: companyForm.max_simultaneous_interns ? Number(companyForm.max_simultaneous_interns) : undefined,
        }
        const res = await fetch(`${API_BASE_URL}/internships/companies`, { method: "POST", headers, body: JSON.stringify(cleanPayload(payload)) })
        setStatus(res.ok ? "Entreprise partenaire enregistree." : "Enregistrement de l'entreprise impossible.")
        if (res.ok) {
            setCompanyForm({ name: "", rccm_number: "", tax_number: "", industry: "", description: "", address: "", city: "", region: "", country: "", latitude: "", longitude: "", hr_manager_name: "", hr_manager_role: "", phone: "", email: "", max_simultaneous_interns: "", website: "", logo_url: "" })
            await loadData()
        }
    }

    const submitInternship = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!headers) return
        setStatus("Creation du stage...")
        const company = companies.find(item => item.id === Number(internshipForm.company_id))
        const studentIds = splitIds(internshipForm.student_ids)
        const payload = {
            ...internshipForm,
            company_id: internshipForm.company_id ? Number(internshipForm.company_id) : undefined,
            company_name: company?.name || internshipForm.company_name,
            student_id: studentIds[0],
            student_ids: studentIds,
            class_id: internshipForm.class_id ? Number(internshipForm.class_id) : undefined,
            teacher_ref_id: internshipForm.teacher_ref_id ? Number(internshipForm.teacher_ref_id) : undefined,
            pedagogy_coordinator_id: internshipForm.pedagogy_coordinator_id ? Number(internshipForm.pedagogy_coordinator_id) : undefined,
            internship_manager_id: internshipForm.internship_manager_id ? Number(internshipForm.internship_manager_id) : undefined,
            weeks_count: internshipForm.weeks_count ? Number(internshipForm.weeks_count) : undefined,
            start_date: toDateTime(internshipForm.start_date),
            end_date: toDateTime(internshipForm.end_date),
        }
        const res = await fetch(`${API_BASE_URL}/internships/`, { method: "POST", headers, body: JSON.stringify(cleanPayload(payload)) })
        setStatus(res.ok ? "Stage cree et publie aux comptes concernes." : "Creation du stage impossible.")
        if (res.ok) {
            setInternshipForm({ company_id: "", company_name: "", student_ids: "", academic_level: "", class_id: "", program: "", training_program: "", title: "", description: "", objectives: "", service_department: "", supervisor_name: "", supervisor_role: "", supervisor_phone: "", supervisor_email: "", teacher_ref_id: "", pedagogy_coordinator_id: "", internship_manager_id: "", start_date: todayDate(), end_date: "", weeks_count: "", expected_schedule: "", status: "planned" })
            await loadData()
        }
    }

    const postSimple = async (path: string, payload: Record<string, unknown>, okMessage: string) => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}${path}`, { method: "POST", headers, body: JSON.stringify(cleanPayload(payload)) })
        setStatus(res.ok ? okMessage : "Operation impossible.")
        if (res.ok) await loadData()
    }

    const submitFollowup = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        postSimple("/internships/followups", {
            ...followupForm,
            internship_id: Number(followupForm.internship_id),
            student_id: followupForm.student_id ? Number(followupForm.student_id) : undefined,
            date: toDateTime(followupForm.date),
        }, "Suivi quotidien enregistre.")
    }

    const submitLogbook = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        postSimple("/internships/logbook", {
            ...logbookForm,
            internship_id: Number(logbookForm.internship_id),
            student_id: Number(logbookForm.student_id),
            hours_count: logbookForm.hours_count ? Number(logbookForm.hours_count) : undefined,
            date: toDateTime(logbookForm.date),
        }, "Carnet de stage enregistre.")
    }

    const submitEvaluation = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        postSimple("/internships/evaluations", {
            ...evaluationForm,
            internship_id: Number(evaluationForm.internship_id),
            student_id: evaluationForm.student_id ? Number(evaluationForm.student_id) : undefined,
            company_score: evaluationForm.company_score ? Number(evaluationForm.company_score) : undefined,
            report_score: evaluationForm.report_score ? Number(evaluationForm.report_score) : undefined,
            defense_score: evaluationForm.defense_score ? Number(evaluationForm.defense_score) : undefined,
            practical_score: evaluationForm.practical_score ? Number(evaluationForm.practical_score) : undefined,
            final_score: evaluationForm.final_score ? Number(evaluationForm.final_score) : undefined,
        }, "Evaluation enregistree et statut mis a jour.")
    }

    const submitDocument = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        postSimple("/internships/documents", {
            ...documentForm,
            internship_id: Number(documentForm.internship_id),
            student_id: documentForm.student_id ? Number(documentForm.student_id) : undefined,
            secure_file_id: documentForm.secure_file_id ? Number(documentForm.secure_file_id) : undefined,
        }, "Document de stage enregistre.")
    }

    const generateDocuments = async (id: number) => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/internships/${id}/generate-documents`, { method: "POST", headers })
        setStatus(res.ok ? "Documents de fin de stage generes." : "Generation documentaire impossible.")
    }

    const analyze = async (id: number) => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/internships/${id}/ai-analysis`, { method: "POST", headers })
        if (res.ok) {
            const data = await res.json()
            setSelectedInternshipId(data.id)
            await loadData()
            setStatus("Analyse IA du stage generee.")
        } else {
            setStatus("Analyse IA impossible.")
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-semibold tracking-tight text-[#111827]">Gestion des stages en entreprise</h1>
                    <p className="mt-1 text-[#6B7280]">Entreprises partenaires, affectations, suivi, carnet, evaluations, documents et rapports de stage.</p>
                </div>
                {status && <div className="rounded-full border border-[#E5E7EB] bg-white px-4 py-2 text-sm text-[#111827] shadow-sm">{status}</div>}
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                <StatCard title="Stages" value={dashboard.total_internships} icon={BriefcaseBusiness} detail="Tous statuts confondus" />
                <StatCard title="Actifs" value={dashboard.active_internships} icon={ClipboardCheck} detail="Planifies ou en cours" />
                <StatCard title="Termines" value={dashboard.completed_internships} icon={FileText} detail="Completes ou evalues" />
                <StatCard title="Entreprises" value={dashboard.partner_companies} icon={Building2} detail="Partenaires actifs" />
                <StatCard title="Validation" value={`${dashboard.validation_rate}%`} icon={BarChart3} detail="Stages evalues" />
            </div>

            <Card className="rounded-[28px] border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-xl">Ajouter une entreprise partenaire</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={submitCompany} className="grid gap-3 lg:grid-cols-4">
                        <input className="apple-input" required placeholder="Nom de l'entreprise" title="Nom de l'entreprise: nom legal utilise dans les conventions, attestations et statistiques." value={companyForm.name} onChange={e => setCompanyForm({ ...companyForm, name: e.target.value })} />
                        <input className="apple-input" placeholder="Secteur d'activite" title="Secteur: domaine principal de l'entreprise, utile pour orienter les etudiants vers les stages pertinents." value={companyForm.industry} onChange={e => setCompanyForm({ ...companyForm, industry: e.target.value })} />
                        <input className="apple-input" placeholder="RCCM" title="RCCM: reference d'immatriculation optionnelle permettant d'identifier officiellement l'entreprise." value={companyForm.rccm_number} onChange={e => setCompanyForm({ ...companyForm, rccm_number: e.target.value })} />
                        <input className="apple-input" placeholder="Numero fiscal" title="Numero fiscal: identifiant fiscal optionnel pour les controles administratifs." value={companyForm.tax_number} onChange={e => setCompanyForm({ ...companyForm, tax_number: e.target.value })} />
                        <input className="apple-input lg:col-span-2" placeholder="Adresse complete" title="Adresse: localisation de l'entreprise pour les conventions, visites et exports officiels." value={companyForm.address} onChange={e => setCompanyForm({ ...companyForm, address: e.target.value })} />
                        <input className="apple-input" placeholder="Ville" title="Ville: commune ou localite de l'entreprise." value={companyForm.city} onChange={e => setCompanyForm({ ...companyForm, city: e.target.value })} />
                        <input className="apple-input" placeholder="Pays" title="Pays: utilise pour les statistiques et documents internationaux." value={companyForm.country} onChange={e => setCompanyForm({ ...companyForm, country: e.target.value })} />
                        <input className="apple-input" placeholder="Region" title="Region: province, district ou region administrative." value={companyForm.region} onChange={e => setCompanyForm({ ...companyForm, region: e.target.value })} />
                        <input className="apple-input" type="number" step="any" placeholder="Latitude" title="Latitude: coordonnee GPS optionnelle pour positionner l'entreprise sur une carte." value={companyForm.latitude} onChange={e => setCompanyForm({ ...companyForm, latitude: e.target.value })} />
                        <input className="apple-input" type="number" step="any" placeholder="Longitude" title="Longitude: coordonnee GPS optionnelle pour positionner l'entreprise sur une carte." value={companyForm.longitude} onChange={e => setCompanyForm({ ...companyForm, longitude: e.target.value })} />
                        <input className="apple-input" placeholder="Responsable RH" title="Responsable RH: contact officiel qui valide les conventions et le suivi des stagiaires." value={companyForm.hr_manager_name} onChange={e => setCompanyForm({ ...companyForm, hr_manager_name: e.target.value })} />
                        <input className="apple-input" placeholder="Fonction RH" title="Fonction RH: poste du responsable dans l'entreprise." value={companyForm.hr_manager_role} onChange={e => setCompanyForm({ ...companyForm, hr_manager_role: e.target.value })} />
                        <input className="apple-input" placeholder="Telephone" title="Telephone: numero principal de contact pour le suivi des stages." value={companyForm.phone} onChange={e => setCompanyForm({ ...companyForm, phone: e.target.value })} />
                        <input className="apple-input" type="email" placeholder="Email" title="Email: adresse utilisee pour les notifications et documents de stage." value={companyForm.email} onChange={e => setCompanyForm({ ...companyForm, email: e.target.value })} />
                        <input className="apple-input" type="number" placeholder="Capacite stagiaires" title="Capacite: nombre maximal de stagiaires pouvant etre accueillis simultanement." value={companyForm.max_simultaneous_interns} onChange={e => setCompanyForm({ ...companyForm, max_simultaneous_interns: e.target.value })} />
                        <input className="apple-input" placeholder="Site web" title="Site web: adresse publique optionnelle de l'entreprise." value={companyForm.website} onChange={e => setCompanyForm({ ...companyForm, website: e.target.value })} />
                        <textarea className="apple-input min-h-[92px] lg:col-span-3" placeholder="Description" title="Description: presente l'entreprise, ses activites et les types de missions proposees." value={companyForm.description} onChange={e => setCompanyForm({ ...companyForm, description: e.target.value })} />
                        <div className="flex items-end">
                            <Button className="rounded-full bg-black px-6 text-white hover:bg-black/90">Enregistrer</Button>
                        </div>
                    </form>
                </CardContent>
            </Card>

            <Card className="rounded-[28px] border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-xl">Entreprises partenaires</CardTitle>
                </CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full min-w-[980px] text-left">
                        <thead>
                            <tr className="border-b text-sm text-[#6B7280]">
                                <th className="py-3">Entreprise</th>
                                <th>Secteur</th>
                                <th>Ville</th>
                                <th>Pays</th>
                                <th>Telephone</th>
                                <th>Email</th>
                                <th>RH</th>
                                <th>Stagiaires</th>
                                <th>Statut</th>
                            </tr>
                        </thead>
                        <tbody>
                            {companies.map(company => (
                                <tr key={company.id} className="border-b text-sm">
                                    <td className="py-3 font-medium">{company.name}</td>
                                    <td>{company.industry || "-"}</td>
                                    <td>{company.city || "-"}</td>
                                    <td>{company.country || "-"}</td>
                                    <td>{company.phone || "-"}</td>
                                    <td>{company.email || "-"}</td>
                                    <td>{company.hr_manager_name || "-"}</td>
                                    <td>{company.interns_count}</td>
                                    <td>{company.status}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>

            <Card className="rounded-[28px] border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-xl">Créer un stage</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={submitInternship} className="grid gap-3 lg:grid-cols-4">
                        <select className="apple-select" title="Entreprise: selectionnez une entreprise partenaire existante ou saisissez un nom manuel." value={internshipForm.company_id} onChange={e => setInternshipForm({ ...internshipForm, company_id: e.target.value })}>
                            <option value="">Entreprise partenaire</option>
                            {companies.map(company => <option key={company.id} value={company.id}>{company.name}</option>)}
                        </select>
                        <input className="apple-input" placeholder="Entreprise libre" title="Entreprise libre: utilisez ce champ si l'entreprise n'est pas encore dans le referentiel." value={internshipForm.company_name} onChange={e => setInternshipForm({ ...internshipForm, company_name: e.target.value })} />
                        <input className="apple-input" required placeholder="IDs eleves, separes par virgule" title="IDs eleves: saisissez un ou plusieurs identifiants de profils eleves, separes par virgule pour les stages de groupe." value={internshipForm.student_ids} onChange={e => setInternshipForm({ ...internshipForm, student_ids: e.target.value })} />
                        <input className="apple-input" placeholder="Niveau academique" title="Niveau: classe, niveau LMD ou cycle concerne par le stage." value={internshipForm.academic_level} onChange={e => setInternshipForm({ ...internshipForm, academic_level: e.target.value })} />
                        <input className="apple-input" type="number" placeholder="Classe ID" title="Classe ID: identifiant de la classe/filiere si le stage concerne une classe precise." value={internshipForm.class_id} onChange={e => setInternshipForm({ ...internshipForm, class_id: e.target.value })} />
                        <input className="apple-input" placeholder="Filiere / Programme" title="Programme: filiere ou programme de formation du stagiaire." value={internshipForm.program} onChange={e => setInternshipForm({ ...internshipForm, program: e.target.value })} />
                        <input className="apple-input" placeholder="Formation" title="Formation: intitule precis du cursus ou de la certification." value={internshipForm.training_program} onChange={e => setInternshipForm({ ...internshipForm, training_program: e.target.value })} />
                        <input className="apple-input" required placeholder="Titre du stage" title="Titre: nom court de la mission de stage." value={internshipForm.title} onChange={e => setInternshipForm({ ...internshipForm, title: e.target.value })} />
                        <input className="apple-input" placeholder="Service d'accueil" title="Service: departement ou unite ou le stagiaire est affecte." value={internshipForm.service_department} onChange={e => setInternshipForm({ ...internshipForm, service_department: e.target.value })} />
                        <input className="apple-input" placeholder="Maitre de stage entreprise" title="Maitre de stage: superviseur entreprise responsable du suivi quotidien." value={internshipForm.supervisor_name} onChange={e => setInternshipForm({ ...internshipForm, supervisor_name: e.target.value })} />
                        <input className="apple-input" placeholder="Fonction superviseur" title="Fonction superviseur: poste du maitre de stage dans l'entreprise." value={internshipForm.supervisor_role} onChange={e => setInternshipForm({ ...internshipForm, supervisor_role: e.target.value })} />
                        <input className="apple-input" placeholder="Email superviseur" title="Email superviseur: contact pour validations, notifications et evaluations." value={internshipForm.supervisor_email} onChange={e => setInternshipForm({ ...internshipForm, supervisor_email: e.target.value })} />
                        <input className="apple-input" type="date" title="Date debut: date officielle de demarrage du stage." value={internshipForm.start_date} onChange={e => setInternshipForm({ ...internshipForm, start_date: e.target.value })} />
                        <input className="apple-input" type="date" title="Date fin: date officielle de fin du stage." value={internshipForm.end_date} onChange={e => setInternshipForm({ ...internshipForm, end_date: e.target.value })} />
                        <input className="apple-input" type="number" placeholder="Nombre de semaines" title="Semaines: duree du stage en semaines pour les statistiques et attestations." value={internshipForm.weeks_count} onChange={e => setInternshipForm({ ...internshipForm, weeks_count: e.target.value })} />
                        <select className="apple-select" title="Statut: etat actuel du stage dans le workflow." value={internshipForm.status} onChange={e => setInternshipForm({ ...internshipForm, status: e.target.value })}>
                            <option value="planned">Planifie</option>
                            <option value="in_progress">En cours</option>
                            <option value="completed">Termine</option>
                            <option value="suspended">Suspendu</option>
                            <option value="cancelled">Annule</option>
                            <option value="evaluated">Evalue</option>
                        </select>
                        <textarea className="apple-input min-h-[92px] lg:col-span-2" placeholder="Objectifs pedagogiques" title="Objectifs: competences et resultats attendus pendant le stage." value={internshipForm.objectives} onChange={e => setInternshipForm({ ...internshipForm, objectives: e.target.value })} />
                        <textarea className="apple-input min-h-[92px] lg:col-span-2" placeholder="Description de mission" title="Description: missions, activites et contexte de travail." value={internshipForm.description} onChange={e => setInternshipForm({ ...internshipForm, description: e.target.value })} />
                        <div className="lg:col-span-4">
                            <Button className="rounded-full bg-black px-6 text-white hover:bg-black/90">Enregistrer</Button>
                        </div>
                    </form>
                </CardContent>
            </Card>

            <Card className="rounded-[28px] border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader>
                    <CardTitle className="text-xl">Stages</CardTitle>
                </CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full min-w-[1100px] text-left">
                        <thead>
                            <tr className="border-b text-sm text-[#6B7280]">
                                <th className="py-3">ID</th>
                                <th>Titre</th>
                                <th>Entreprise</th>
                                <th>Niveau</th>
                                <th>Service</th>
                                <th>Superviseur</th>
                                <th>Dates</th>
                                <th>Stagiaires</th>
                                <th>Statut</th>
                                <th>Score</th>
                                <th>Operations</th>
                            </tr>
                        </thead>
                        <tbody>
                            {internships.map(item => (
                                <tr key={item.id} className="border-b text-sm">
                                    <td className="py-3">{item.id}</td>
                                    <td className="font-medium">{item.title || "-"}</td>
                                    <td>{item.company_name}</td>
                                    <td>{item.academic_level || "-"}</td>
                                    <td>{item.service_department || "-"}</td>
                                    <td>{item.supervisor_name || "-"}</td>
                                    <td>{shortDate(item.start_date)} - {shortDate(item.end_date)}</td>
                                    <td>{item.assignments_count}</td>
                                    <td>{item.status}</td>
                                    <td>{item.final_score ?? "-"}</td>
                                    <td>
                                        <div className="flex flex-wrap gap-2">
                                            <button type="button" className="rounded-full border px-3 py-1 text-xs hover:bg-[#F5F5F7]" onClick={() => setSelectedInternshipId(item.id)}>Voir</button>
                                            <button type="button" className="rounded-full border px-3 py-1 text-xs hover:bg-[#F5F5F7]" onClick={() => analyze(item.id)}><Sparkles className="mr-1 inline h-3 w-3" />IA</button>
                                            <button type="button" className="rounded-full border px-3 py-1 text-xs hover:bg-[#F5F5F7]" onClick={() => generateDocuments(item.id)}>Docs</button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {selectedInternshipId && (
                        <div className="mt-4 rounded-[24px] border border-[#E5E7EB] bg-[#F8FAFC] p-4">
                            <p className="text-sm font-semibold text-[#111827]">Analyse / resume IA</p>
                            <p className="mt-2 text-sm text-[#4B5563]">{internships.find(item => item.id === selectedInternshipId)?.ai_summary || "Cliquez sur IA pour generer une analyse du stage."}</p>
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="grid gap-4 xl:grid-cols-2">
                <Card className="rounded-[28px] border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader><CardTitle className="flex items-center gap-2 text-xl"><ClipboardCheck className="h-5 w-5" />Suivi quotidien entreprise</CardTitle></CardHeader>
                    <CardContent>
                        <form onSubmit={submitFollowup} className="grid gap-3 md:grid-cols-2">
                            <input className="apple-input" required type="number" placeholder="Stage ID" title="Stage ID: identifiant du stage suivi aujourd'hui." value={followupForm.internship_id} onChange={e => setFollowupForm({ ...followupForm, internship_id: e.target.value })} />
                            <input className="apple-input" type="number" placeholder="Eleve ID" title="Eleve ID: optionnel si le suivi concerne un stagiaire precis." value={followupForm.student_id} onChange={e => setFollowupForm({ ...followupForm, student_id: e.target.value })} />
                            <input className="apple-input" type="date" title="Date du suivi: jour observe par le superviseur." value={followupForm.date} onChange={e => setFollowupForm({ ...followupForm, date: e.target.value })} />
                            <select className="apple-select" title="Presence: indique si le stagiaire etait present, absent, en retard ou excuse." value={followupForm.presence_status} onChange={e => setFollowupForm({ ...followupForm, presence_status: e.target.value })}>
                                <option value="present">Present</option>
                                <option value="absent">Absent</option>
                                <option value="late">Retard</option>
                                <option value="excused">Excuse</option>
                            </select>
                            <textarea className="apple-input min-h-[90px] md:col-span-2" placeholder="Taches, activites, competences, outils, difficultes et observations" title="Observation: decrivez les activites realisees, competences mobilisees, outils utilises, difficultes et remarques du superviseur." value={followupForm.tasks_description} onChange={e => setFollowupForm({ ...followupForm, tasks_description: e.target.value, activities: e.target.value })} />
                            <Button className="w-fit rounded-full bg-black px-6 text-white hover:bg-black/90">Enregistrer</Button>
                        </form>
                    </CardContent>
                </Card>

                <Card className="rounded-[28px] border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader><CardTitle className="flex items-center gap-2 text-xl"><NotebookTabs className="h-5 w-5" />Carnet de stage eleve</CardTitle></CardHeader>
                    <CardContent>
                        <form onSubmit={submitLogbook} className="grid gap-3 md:grid-cols-2">
                            <input className="apple-input" required type="number" placeholder="Stage ID" title="Stage ID: stage auquel rattacher l'entree du carnet." value={logbookForm.internship_id} onChange={e => setLogbookForm({ ...logbookForm, internship_id: e.target.value })} />
                            <input className="apple-input" required type="number" placeholder="Eleve ID" title="Eleve ID: stagiaire qui declare les activites effectuees." value={logbookForm.student_id} onChange={e => setLogbookForm({ ...logbookForm, student_id: e.target.value })} />
                            <input className="apple-input" type="date" title="Date: jour de l'activite consignee dans le carnet." value={logbookForm.date} onChange={e => setLogbookForm({ ...logbookForm, date: e.target.value })} />
                            <input className="apple-input" type="number" step="0.5" placeholder="Heures" title="Heures: volume horaire effectue ce jour." value={logbookForm.hours_count} onChange={e => setLogbookForm({ ...logbookForm, hours_count: e.target.value })} />
                            <textarea className="apple-input min-h-[90px] md:col-span-2" placeholder="Taches realisees, competences, difficultes et solutions" title="Carnet: detaillez le travail realise, les competences acquises, les difficultes et les solutions proposees." value={logbookForm.tasks_done} onChange={e => setLogbookForm({ ...logbookForm, tasks_done: e.target.value })} />
                            <Button className="w-fit rounded-full bg-black px-6 text-white hover:bg-black/90">Enregistrer</Button>
                        </form>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
                <Card className="rounded-[28px] border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader><CardTitle className="flex items-center gap-2 text-xl"><Users className="h-5 w-5" />Evaluation du stage</CardTitle></CardHeader>
                    <CardContent>
                        <form onSubmit={submitEvaluation} className="grid gap-3 md:grid-cols-3">
                            <input className="apple-input" required type="number" placeholder="Stage ID" title="Stage ID: stage a evaluer." value={evaluationForm.internship_id} onChange={e => setEvaluationForm({ ...evaluationForm, internship_id: e.target.value })} />
                            <input className="apple-input" type="number" placeholder="Eleve ID" title="Eleve ID: optionnel pour une evaluation individualisee dans un stage de groupe." value={evaluationForm.student_id} onChange={e => setEvaluationForm({ ...evaluationForm, student_id: e.target.value })} />
                            <input className="apple-input" placeholder="Type evaluation" title="Type: entreprise, rapport, soutenance, pratique ou finale." value={evaluationForm.evaluation_type} onChange={e => setEvaluationForm({ ...evaluationForm, evaluation_type: e.target.value })} />
                            <input className="apple-input" type="number" step="0.01" placeholder="Note entreprise" title="Note entreprise: evaluation du superviseur entreprise." value={evaluationForm.company_score} onChange={e => setEvaluationForm({ ...evaluationForm, company_score: e.target.value })} />
                            <input className="apple-input" type="number" step="0.01" placeholder="Note rapport" title="Note rapport: evaluation du document rendu." value={evaluationForm.report_score} onChange={e => setEvaluationForm({ ...evaluationForm, report_score: e.target.value })} />
                            <input className="apple-input" type="number" step="0.01" placeholder="Note finale" title="Note finale: score global utilise pour cloturer le stage comme evalue." value={evaluationForm.final_score} onChange={e => setEvaluationForm({ ...evaluationForm, final_score: e.target.value })} />
                            <textarea className="apple-input min-h-[90px] md:col-span-3" placeholder="Commentaires et recommandations" title="Commentaires: synthese de l'evaluation, forces, points a ameliorer et recommandations." value={evaluationForm.comments} onChange={e => setEvaluationForm({ ...evaluationForm, comments: e.target.value })} />
                            <Button className="w-fit rounded-full bg-black px-6 text-white hover:bg-black/90">Enregistrer</Button>
                        </form>
                    </CardContent>
                </Card>

                <Card className="rounded-[28px] border-[#E5E7EB] bg-white shadow-sm">
                    <CardHeader><CardTitle className="flex items-center gap-2 text-xl"><FileText className="h-5 w-5" />Documents de stage</CardTitle></CardHeader>
                    <CardContent>
                        <form onSubmit={submitDocument} className="grid gap-3 md:grid-cols-2">
                            <input className="apple-input" required type="number" placeholder="Stage ID" title="Stage ID: stage auquel rattacher le document." value={documentForm.internship_id} onChange={e => setDocumentForm({ ...documentForm, internship_id: e.target.value })} />
                            <input className="apple-input" type="number" placeholder="Eleve ID" title="Eleve ID: optionnel si le document concerne un stagiaire precis." value={documentForm.student_id} onChange={e => setDocumentForm({ ...documentForm, student_id: e.target.value })} />
                            <select className="apple-select" title="Type document: convention, assurance, presence, evaluation, rapport, presentation ou annexe." value={documentForm.document_type} onChange={e => setDocumentForm({ ...documentForm, document_type: e.target.value })}>
                                <option value="convention">Convention</option>
                                <option value="insurance_attestation">Attestation assurance</option>
                                <option value="presence_sheet">Feuille de presence</option>
                                <option value="final_evaluation">Evaluation finale</option>
                                <option value="interim_report">Rapport intermediaire</option>
                                <option value="final_report">Rapport final</option>
                                <option value="presentation">Presentation</option>
                                <option value="annex">Annexe</option>
                            </select>
                            <input className="apple-input" required placeholder="Titre" title="Titre: nom du document visible dans le portail et les exports." value={documentForm.title} onChange={e => setDocumentForm({ ...documentForm, title: e.target.value })} />
                            <input className="apple-input" type="number" placeholder="Secure File ID" title="Secure File ID: identifiant du fichier securise deja televerse." value={documentForm.secure_file_id} onChange={e => setDocumentForm({ ...documentForm, secure_file_id: e.target.value })} />
                            <Button className="w-fit rounded-full bg-black px-6 text-white hover:bg-black/90">Enregistrer</Button>
                        </form>
                    </CardContent>
                </Card>
            </div>

            <Card className="rounded-[28px] border-[#E5E7EB] bg-white shadow-sm">
                <CardHeader><CardTitle className="text-xl">Eleves disponibles</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full min-w-[640px] text-left">
                        <thead>
                            <tr className="border-b text-sm text-[#6B7280]">
                                <th className="py-3">ID</th>
                                <th>Nom</th>
                                <th>Matricule</th>
                            </tr>
                        </thead>
                        <tbody>
                            {students.slice(0, 20).map(student => (
                                <tr key={student.id} className="border-b text-sm">
                                    <td className="py-3">{student.id}</td>
                                    <td>{student.user?.full_name || "-"}</td>
                                    <td>{student.registration_number || "-"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
