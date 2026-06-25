"use client"

import { FormEvent, useEffect, useMemo, useRef, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Bot, BriefcaseBusiness, Building2, CreditCard, ImageUp, Plus, Search, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"

type JobOffer = {
  id: number
  title: string
  company: string
  sector: string
  status: string
  description: string
  offer_type: string
  workplace_mode: string
  salary_fixed?: number
  salary_min?: number
  salary_max?: number
  currency?: string
  deadline?: string
  ai_match_summary?: { top_candidates?: Match[] }
}
type Application = { id: number; job_offer_id: number; student_cv_id: number; status: string; motivation_message?: string; ai_match_score?: number }
type RecruiterProfile = {
  payment_status: string
  company_name: string
  contact_name?: string
  sector?: string
  phone?: string
  website?: string
  logo_url?: string
  company_description?: string
  subscription_plan: string
  subscription_duration_months?: number
  days_remaining?: number | null
  auto_renew?: boolean
  ai_credits_balance?: number
}
type Match = { score: number; cv: { id: number; name?: string; professional_title?: string; skills?: string[]; languages?: string[]; total_experience_years?: number }; details?: Record<string, unknown> }

const PENDING_PAYMENT_MESSAGE = "Paiement: pending, must pay before using the service."

async function readUserMessage(response: Response) {
  const payload = await response.json().catch(() => null)
  if (typeof payload?.detail === "string") return payload.detail
  return "Action impossible."
}

export default function RecruiterDashboardPage() {
  const { token } = useAuth()
  const router = useRouter()
  const params = useParams()
  const locale = normalizeLocale(params.locale as string)
  const [jobs, setJobs] = useState<JobOffer[]>([])
  const [applications, setApplications] = useState<Application[]>([])
  const [profile, setProfile] = useState<RecruiterProfile | null>(null)
  const [status, setStatus] = useState("")
  const [paymentModalOpen, setPaymentModalOpen] = useState(false)
  const [sharecode, setSharecode] = useState("")
  const [sharecodeResult, setSharecodeResult] = useState<Record<string, unknown> | null>(null)
  const [matches, setMatches] = useState<Match[]>([])
  const [agentPrompt, setAgentPrompt] = useState("Trouve-moi les meilleurs diplomes en Intelligence Artificielle apres 2023.")
  const [agentResult, setAgentResult] = useState("")
  const [subscription, setSubscription] = useState({ plan: "job_posts", duration_months: 1, auto_renew: false, payment_provider: "manual" })
  const [creditPurchase, setCreditPurchase] = useState({ credits: 500, payment_provider: "manual" })
  const [logoPreview, setLogoPreview] = useState("")
  const [logoUploading, setLogoUploading] = useState(false)
  const logoInputRef = useRef<HTMLInputElement>(null)
  const [form, setForm] = useState({
    title: "",
    company: "",
    sector: "",
    description: "",
    offer_type: "emploi",
    workplace_mode: "hybrid",
    contract_type: "CDI",
    salary_fixed: "",
    salary_min: "",
    salary_max: "",
    currency: "FCFA",
    minimum_academic_level: "",
    required_years_experience: "",
    required_skills: "",
    desired_skills: "",
    required_languages: "",
    positions_count: "1",
    deadline: "",
    desired_start_date: "",
    status: "published",
  })
  const isPaymentPending = profile?.payment_status === "pending"

  const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : null, [token])

  const load = () => {
    if (!headers) return
    fetch(`${API_BASE_URL}/employment/recruiter/me`, { headers }).then(res => res.ok ? res.json() : null).then(data => {
      if (!data) return
      setProfile(data)
      setForm(previous => ({ ...previous, company: data.company_name || previous.company, sector: data.sector || previous.sector }))
      setSubscription(previous => ({ ...previous, plan: data.subscription_plan || previous.plan, duration_months: data.subscription_duration_months || 1, auto_renew: Boolean(data.auto_renew) }))
      if (data.payment_status === "confirmed") {
        fetch(`${API_BASE_URL}/employment/recruiter/applications`, { headers }).then(res => res.json()).then(appData => setApplications(Array.isArray(appData) ? appData : [])).catch(() => undefined)
      } else {
        setApplications([])
      }
    }).catch(() => undefined)
    fetch(`${API_BASE_URL}/employment/recruiter/jobs`, { headers }).then(res => res.json()).then(data => setJobs(Array.isArray(data) ? data : [])).catch(() => undefined)
  }

  useEffect(load, [headers])

  const restricted = () => {
    if (isPaymentPending) {
      setPaymentModalOpen(true)
      return true
    }
    return false
  }

  const saveProfile = async (event: FormEvent) => {
    event.preventDefault()
    if (!headers || !profile) return
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/profile`, {
      method: "PUT",
      headers,
      body: JSON.stringify(profile),
    })
    setStatus(response.ok ? "Profil entreprise enregistre." : await readUserMessage(response))
    if (response.ok) setProfile(await response.json())
  }

  const saveSubscription = async () => {
    if (!headers) return
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/subscription`, { method: "POST", headers, body: JSON.stringify(subscription) })
    setStatus(response.ok ? "Abonnement mis a jour. Paiement en attente si necessaire." : await readUserMessage(response))
    if (response.ok) setProfile(await response.json())
  }

  const buyCredits = async () => {
    router.push(`/${locale}/dashboard/checkout?purchase=ai-credits&scope=user&credits=${creditPurchase.credits}&return=emploi-recruteur`)
  }

  const uploadLogo = async (file: File) => {
    if (!headers) return
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setStatus("Format non accepte. Utilisez une image JPG, PNG ou WebP.")
      return
    }
    if (file.size > 5 * 1024 * 1024) {
      setStatus("Image trop lourde. La limite est de 5 Mo.")
      return
    }
    setLogoUploading(true)
    setLogoPreview(URL.createObjectURL(file))
    const formData = new FormData()
    formData.append("logo", file)
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/logo`, {
      method: "POST",
      headers: { Authorization: headers.Authorization },
      body: formData,
    })
    const data = await response.json().catch(() => null)
    setLogoUploading(false)
    if (!response.ok) {
      setStatus(data?.detail || "Televersement du logo impossible.")
      return
    }
    setProfile(data)
    setStatus("Logo entreprise enregistre.")
  }

  const deleteLogo = async () => {
    if (!headers || !profile) return
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/logo`, { method: "DELETE", headers: { Authorization: headers.Authorization } })
    if (!response.ok) {
      setStatus("Suppression du logo impossible.")
      return
    }
    setLogoPreview("")
    setProfile({ ...profile, logo_url: "" })
    setStatus("Logo entreprise supprime.")
  }

  const createJob = async (event: FormEvent) => {
    event.preventDefault()
    if (!headers || restricted()) return
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/jobs`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        ...form,
        salary_fixed: form.salary_fixed ? Number(form.salary_fixed) : null,
        salary_min: form.salary_min ? Number(form.salary_min) : null,
        salary_max: form.salary_max ? Number(form.salary_max) : null,
        required_years_experience: form.required_years_experience ? Number(form.required_years_experience) : null,
        positions_count: Number(form.positions_count || 1),
        required_skills: csv(form.required_skills),
        desired_skills: csv(form.desired_skills),
        required_languages: csv(form.required_languages),
        missions: [],
      }),
    })
    if (!response.ok) {
      const message = await readUserMessage(response)
      if (message === PENDING_PAYMENT_MESSAGE) setPaymentModalOpen(true)
      setStatus(message === PENDING_PAYMENT_MESSAGE ? "" : message)
      return
    }
    setStatus("Offre creee et matching IA calcule.")
    setForm(previous => ({ ...previous, title: "", description: "", required_skills: "", desired_skills: "", required_languages: "" }))
    load()
  }

  const archive = async (jobId: number) => {
    if (!headers || restricted()) return
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/jobs/${jobId}`, { method: "DELETE", headers })
    setStatus(response.ok ? "Offre archivee ou supprimee." : await readUserMessage(response))
    if (response.ok) load()
  }

  const loadMatches = async (jobId: number) => {
    if (!headers || restricted()) return
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/jobs/${jobId}/matches`, { headers })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      setStatus(data?.detail || "Matching indisponible.")
      return
    }
    setMatches(data.matches || [])
  }

  const lookupSharecode = async () => {
    if (!headers || restricted()) return
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/sharecode/lookup`, { method: "POST", headers, body: JSON.stringify({ sharecode }) })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      setStatus(data?.detail || "ShareCode introuvable.")
      return
    }
    setSharecodeResult(data)
  }

  const runAgent = async () => {
    if (!headers || restricted()) return
    const response = await fetch(`${API_BASE_URL}/employment/agent`, { method: "POST", headers, body: JSON.stringify({ prompt: agentPrompt, mode: "recruiter" }) })
    const data = await response.json().catch(() => null)
    setAgentResult(data?.message || data?.data?.recommendations?.join("\n") || "Agent IA indisponible.")
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5 text-[#111827] dark:text-white">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[#0F766E] dark:text-[#5eead4]">ATS TeducAI Emploi</p>
          <h1 className="flex items-center gap-2 text-2xl font-bold"><Building2 className="h-6 w-6" /> Espace recruteur intelligent</h1>
        </div>
        <div className="rounded-full border px-4 py-2 text-sm dark:border-[#56616a]">
          Credits IA: <strong>{profile?.ai_credits_balance || 0}</strong>
        </div>
      </header>

      {isPaymentPending && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800 dark:border-red-800 dark:bg-red-950/40 dark:text-red-100">Paiement: pending</div>}

      <section className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
        <form onSubmit={saveProfile} className="rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
          <h2 className="flex items-center gap-2 text-lg font-semibold"><ImageUp className="h-5 w-5" /> Logo et entreprise</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-[120px_1fr]">
            <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-xl border bg-[#F8FAFC] dark:border-[#56616a] dark:bg-[#1f2427]">
              {logoPreview || profile?.logo_url ? <img src={assetUrl(logoPreview || profile?.logo_url)} alt="Logo entreprise" className="h-full w-full object-cover" /> : <Building2 className="h-8 w-8 text-[#0F766E]" />}
            </div>
            <div className="grid gap-3">
              <label className="grid gap-1 text-sm font-medium text-[#111827] dark:text-white">
                Logo JPG, PNG ou WebP
                <input ref={logoInputRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={event => {
                  const file = event.target.files?.[0]
                  if (file) void uploadLogo(file)
                  event.currentTarget.value = ""
                }} />
                <Button type="button" variant="outline" onClick={() => logoInputRef.current?.click()} disabled={logoUploading}>{logoUploading ? "Televersement..." : "Choisir un logo"}</Button>
              </label>
              <div className="flex gap-2">
                <Button type="button" variant="outline" onClick={deleteLogo}>Supprimer</Button>
                <Button type="submit" className="bg-black text-white">Enregistrer</Button>
              </div>
            </div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <Field label="Entreprise" value={profile?.company_name || ""} onChange={value => setProfile(previous => previous ? { ...previous, company_name: value } : previous)} />
            <Field label="Contact" value={profile?.contact_name || ""} onChange={value => setProfile(previous => previous ? { ...previous, contact_name: value } : previous)} />
            <Field label="Secteur" value={profile?.sector || ""} onChange={value => setProfile(previous => previous ? { ...previous, sector: value } : previous)} />
            <Field label="Site web" value={profile?.website || ""} onChange={value => setProfile(previous => previous ? { ...previous, website: value } : previous)} />
          </div>
          <textarea placeholder="Description publique de l'entreprise" value={profile?.company_description || ""} onChange={event => setProfile(previous => previous ? { ...previous, company_description: event.target.value } : previous)} className="mt-3 min-h-24 w-full rounded-lg border px-3 py-2 dark:border-[#56616a] dark:bg-[#1f2427]" />
        </form>

        <section className="grid gap-4">
          <div className="rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
            <h2 className="flex items-center gap-2 text-lg font-semibold"><CreditCard className="h-5 w-5" /> Abonnement</h2>
            <p className="mt-1 text-sm text-[#64748B] dark:text-[#c7d0da]">Statut: {profile?.payment_status} - jours restants: {profile?.days_remaining ?? "-"}</p>
            <div className="mt-4 grid gap-3 md:grid-cols-4">
              <select value={subscription.duration_months} onChange={event => setSubscription({ ...subscription, duration_months: Number(event.target.value) })} className="rounded-lg border px-3 py-2 dark:border-[#56616a] dark:bg-[#1f2427]">{[1, 2, 3, 6, 12].map(month => <option key={month} value={month}>{month} mois</option>)}</select>
              <select value={subscription.plan} onChange={event => setSubscription({ ...subscription, plan: event.target.value })} className="rounded-lg border px-3 py-2 dark:border-[#56616a] dark:bg-[#1f2427]"><option value="sharecode_only">ShareCode</option><option value="job_posts">Offres</option><option value="cvtheque_limited">CVtheque</option><option value="cvtheque_advanced">CV avancee</option></select>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={subscription.auto_renew} onChange={event => setSubscription({ ...subscription, auto_renew: event.target.checked })} /> Auto-renouveler</label>
              <Button type="button" className="bg-black text-white" onClick={saveSubscription}>Mettre a jour</Button>
            </div>
          </div>
          <div className="rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
            <h2 className="flex items-center gap-2 text-lg font-semibold"><Sparkles className="h-5 w-5" /> Credits IA</h2>
            <div className="mt-4 flex flex-wrap gap-3">
              <input type="number" min={10} value={creditPurchase.credits} onChange={event => setCreditPurchase({ ...creditPurchase, credits: Number(event.target.value) })} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />
              <Button type="button" onClick={buyCredits} className="bg-black text-white">Acheter des credits</Button>
            </div>
          </div>
        </section>
      </section>

      <form onSubmit={createJob} className="grid gap-4 rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
        <h2 className="flex items-center gap-2 text-lg font-semibold"><BriefcaseBusiness className="h-5 w-5" /> Publier une offre enrichie</h2>
        <div className="grid gap-3 md:grid-cols-4">
          <Field label="Titre" value={form.title} onChange={value => setForm({ ...form, title: value })} />
          <Field label="Entreprise" value={form.company} onChange={value => setForm({ ...form, company: value })} />
          <Field label="Secteur" value={form.sector} onChange={value => setForm({ ...form, sector: value })} />
          <Field label="Type contrat" value={form.contract_type} onChange={value => setForm({ ...form, contract_type: value })} />
          <Field label="Salaire fixe" value={form.salary_fixed} onChange={value => setForm({ ...form, salary_fixed: value })} />
          <Field label="Salaire min" value={form.salary_min} onChange={value => setForm({ ...form, salary_min: value })} />
          <Field label="Salaire max" value={form.salary_max} onChange={value => setForm({ ...form, salary_max: value })} />
          <Field label="Devise" value={form.currency} onChange={value => setForm({ ...form, currency: value })} />
          <Field label="Niveau minimum" value={form.minimum_academic_level} onChange={value => setForm({ ...form, minimum_academic_level: value })} />
          <Field label="Annees experience" value={form.required_years_experience} onChange={value => setForm({ ...form, required_years_experience: value })} />
          <Field label="Nombre de postes" value={form.positions_count} onChange={value => setForm({ ...form, positions_count: value })} />
          <Field label="Date limite" type="date" value={form.deadline} onChange={value => setForm({ ...form, deadline: value })} />
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <TagsField label="Competences obligatoires" value={form.required_skills} onChange={value => setForm({ ...form, required_skills: value })} />
          <TagsField label="Competences souhaitees" value={form.desired_skills} onChange={value => setForm({ ...form, desired_skills: value })} />
          <TagsField label="Langues obligatoires" value={form.required_languages} onChange={value => setForm({ ...form, required_languages: value })} />
        </div>
        <textarea placeholder="Description, missions et conditions" value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} className="min-h-28 rounded-lg border px-3 py-2 dark:border-[#56616a] dark:bg-[#1f2427]" />
        <Button className="w-fit bg-black text-white"><Plus className="h-4 w-4" /> Ajouter l&apos;offre</Button>
      </form>

      <section className="grid gap-4 xl:grid-cols-[1fr_0.95fr]">
        <Panel title="Mes offres">
          <div className="grid gap-3">
            {jobs.map(job => (
              <div key={job.id} className="rounded-lg border p-3 dark:border-[#56616a]">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold">{job.title}</p>
                    <p className="text-sm text-[#64748B] dark:text-[#c7d0da]">{job.company} - {job.sector} - {job.status}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => loadMatches(job.id)}>Matching</Button>
                    <Button variant="outline" onClick={() => archive(job.id)}>Archiver</Button>
                  </div>
                </div>
              </div>
            ))}
            {!jobs.length && <p className="text-sm text-[#64748B] dark:text-[#c7d0da]">Aucune offre.</p>}
          </div>
        </Panel>
        <Panel title="Meilleurs candidats IA">
          <div className="grid gap-3">
            {matches.map(item => <div key={item.cv.id} className="rounded-lg border p-3 text-sm dark:border-[#56616a]"><strong>{item.score}%</strong> - {item.cv.name || "Profil"} - {(item.cv.skills || []).slice(0, 4).join(", ")}</div>)}
            {!matches.length && <p className="text-sm text-[#64748B] dark:text-[#c7d0da]">Selectionnez une offre pour calculer le matching.</p>}
          </div>
        </Panel>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <Panel title="Rechercher un etudiant par ShareCode">
          <div className="flex gap-2">
            <input value={sharecode} onChange={event => setSharecode(event.target.value.toUpperCase())} className="min-h-11 flex-1 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" placeholder="STU..." />
            <Button onClick={lookupSharecode} className="bg-black text-white"><Search className="h-4 w-4" /></Button>
          </div>
          {sharecodeResult && <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-[#F8FAFC] p-3 text-xs dark:bg-[#1f2427]">{JSON.stringify(sharecodeResult, null, 2)}</pre>}
        </Panel>
        <Panel title="Agent IA Recruteur">
          <textarea value={agentPrompt} onChange={event => setAgentPrompt(event.target.value)} className="min-h-24 w-full rounded-lg border px-3 py-2 dark:border-[#56616a] dark:bg-[#1f2427]" />
          <Button onClick={runAgent} className="mt-3 bg-black text-white"><Bot className="h-4 w-4" /> Lancer l&apos;agent</Button>
          {agentResult && <p className="mt-3 whitespace-pre-wrap text-sm text-[#475569] dark:text-[#c7d0da]">{agentResult}</p>}
        </Panel>
        <Panel title="Candidatures recues">
          <Button type="button" variant="outline" onClick={() => headers && fetch(`${API_BASE_URL}/employment/recruiter/applications`, { headers }).then(res => res.json()).then(data => setApplications(Array.isArray(data) ? data : []))}>Voir les candidatures</Button>
          <div className="mt-3 grid gap-2">{applications.map(item => <div key={item.id} className="rounded-lg border p-3 text-sm dark:border-[#56616a]">CV #{item.student_cv_id} - Offre #{item.job_offer_id} - Score {item.ai_match_score || 0}%</div>)}</div>
        </Panel>
      </section>

      {status && <p className="text-sm text-[#475569] dark:text-[#c7d0da]">{status}</p>}
      {paymentModalOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4">
          <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl dark:bg-[#252b30]">
            <h2 className="text-lg font-semibold">Paiement requis</h2>
            <p className="mt-3 text-sm text-[#475569] dark:text-[#c7d0da]">{PENDING_PAYMENT_MESSAGE}</p>
            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setPaymentModalOpen(false)}>Fermer</Button>
              <Button type="button" className="bg-black text-white" onClick={() => router.push(`/${locale}/dashboard/checkout`)}>Make payment</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function csv(value: string) {
  return value.split(",").map(item => item.trim()).filter(Boolean)
}

function assetUrl(path?: string) {
  if (!path) return ""
  if (path.startsWith("blob:") || path.startsWith("http") || path.startsWith("data:")) return path
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return <label className="grid gap-1 text-sm font-medium text-[#111827] dark:text-white">{label}<input type={type} value={value} onChange={event => onChange(event.target.value)} className="min-h-11 rounded-lg border px-3 text-[#111827] dark:border-[#56616a] dark:bg-[#1f2427] dark:text-white" /></label>
}

function TagsField(props: { label: string; value: string; onChange: (value: string) => void }) {
  return <Field {...props} />
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]"><h2 className="mb-4 text-lg font-semibold">{title}</h2>{children}</section>
}
