"use client"

import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react"
import { Bot, BriefcaseBusiness, Camera, Copy, RefreshCw, Save, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"

type WorkHistory = {
  id: number
  company: string
  position: string
  experience_type: string
  start_date?: string
  end_date?: string
  sector?: string
  technologies_used?: string[]
  skills_acquired?: string[]
}

type RecommendedJob = {
  score: number
  job: {
    id: number
    title: string
    company: string
    sector: string
    deadline?: string
    salary_fixed?: number
    salary_min?: number
    salary_max?: number
    currency?: string
  }
}

type CV = {
  sharecode: string
  professional_title?: string
  summary?: string
  sectors?: string[]
  skills?: string[]
  languages?: string[]
  photo_url?: string
  desired_location?: string
  portfolio_url?: string
  looking_for_job: boolean
  privacy_settings?: Record<string, boolean>
  detailed_skills?: Array<{ category: string; name: string; level: string; years: number; certificate?: string }>
  academic_credentials?: Array<{ school: string; degree: string; field: string; start_year?: string; end_year?: string }>
  certificates?: Array<{ name: string; issuer: string; year?: string; url?: string }>
  total_experience_years?: number
  work_history?: WorkHistory[]
}

const skillTemplate = { category: "Technique", name: "", level: "intermediaire", years: 1, certificate: "" }

export default function EmploymentDashboardPage() {
  const { token } = useAuth()
  const [cv, setCv] = useState<CV | null>(null)
  const [status, setStatus] = useState("")
  const [recommendations, setRecommendations] = useState<RecommendedJob[]>([])
  const [agentPrompt, setAgentPrompt] = useState("Analyse mon profil et propose trois offres compatibles.")
  const [agentResult, setAgentResult] = useState("")
  const [credits, setCredits] = useState(250)
  const [work, setWork] = useState({
    company: "",
    position: "",
    experience_type: "stage",
    sector: "",
    start_date: "",
    end_date: "",
    description: "",
    technologies_used: "",
    skills_acquired: "",
  })

  const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : null, [token])

  const load = () => {
    if (!headers) return
    fetch(`${API_BASE_URL}/employment/me/cv`, { headers }).then(res => res.json()).then(setCv).catch(() => setStatus("CV indisponible."))
    fetch(`${API_BASE_URL}/employment/me/recommended-jobs`, { headers }).then(res => res.json()).then(data => setRecommendations(Array.isArray(data?.jobs) ? data.jobs : [])).catch(() => setRecommendations([]))
  }

  useEffect(load, [headers])

  const save = async (event: FormEvent) => {
    event.preventDefault()
    if (!cv || !headers) return
    const response = await fetch(`${API_BASE_URL}/employment/me/cv`, {
      method: "PUT",
      headers,
      body: JSON.stringify({
        professional_title: cv.professional_title,
        summary: cv.summary,
        sectors: cv.sectors || [],
        skills: cv.skills || [],
        languages: cv.languages || [],
        photo_url: cv.photo_url,
        portfolio_url: cv.portfolio_url,
        desired_location: cv.desired_location,
        detailed_skills: cv.detailed_skills || [],
        academic_credentials: cv.academic_credentials || [],
        certificates: cv.certificates || [],
        looking_for_job: cv.looking_for_job,
        privacy_settings: cv.privacy_settings || {},
      }),
    })
    setStatus(response.ok ? "CV enregistre et recommandations recalculees." : "Enregistrement impossible.")
    if (response.ok) {
      setCv(await response.json())
      load()
    }
  }

  const addWork = async () => {
    if (!headers) return
    const response = await fetch(`${API_BASE_URL}/employment/me/cv/work-history`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        ...work,
        missions: [work.description].filter(Boolean),
        skills_used: csv(work.skills_acquired),
        technologies_used: csv(work.technologies_used),
        skills_acquired: csv(work.skills_acquired),
      }),
    })
    setStatus(response.ok ? "Experience ajoutee et total recalcule." : "Experience refusee.")
    if (response.ok) {
      setWork({ company: "", position: "", experience_type: "stage", sector: "", start_date: "", end_date: "", description: "", technologies_used: "", skills_acquired: "" })
      load()
    }
  }

  const regenerate = async () => {
    if (!headers || !cv) return
    const response = await fetch(`${API_BASE_URL}/employment/me/cv/regenerate-sharecode`, { method: "POST", headers })
    const data = await response.json().catch(() => null)
    if (response.ok) setCv({ ...cv, sharecode: data.sharecode })
  }

  const buyCredits = async () => {
    if (!headers) return
    const response = await fetch(`${API_BASE_URL}/employment/me/ai-credits`, { method: "POST", headers, body: JSON.stringify({ credits, payment_provider: "manual" }) })
    const data = await response.json().catch(() => null)
    setStatus(response.ok ? `Demande de ${data?.credits_requested || credits} credits IA enregistree.` : data?.detail || "Achat de credits impossible.")
  }

  const runAgent = async () => {
    if (!headers) return
    const response = await fetch(`${API_BASE_URL}/employment/agent`, { method: "POST", headers, body: JSON.stringify({ prompt: agentPrompt, mode: "student" }) })
    const data = await response.json().catch(() => null)
    setAgentResult(data?.message || data?.data?.recommendations?.join("\n") || "Agent IA indisponible.")
  }

  const applyToJob = async (jobId: number) => {
    if (!headers) return
    const response = await fetch(`${API_BASE_URL}/employment/jobs/${jobId}/apply`, { method: "POST", headers, body: JSON.stringify({ motivation_message: "Candidature envoyee depuis les recommandations TeducAI." }) })
    setStatus(response.ok ? "Candidature envoyee." : "Candidature impossible.")
  }

  if (!cv) return <div className="p-6 text-[#111827] dark:text-white">Chargement Emploi...</div>

  return (
    <div className="mx-auto max-w-7xl space-y-5 text-[#111827] dark:text-white">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[#0F766E] dark:text-[#5eead4]">TeducAI Emploi</p>
          <h1 className="flex items-center gap-2 text-2xl font-bold"><BriefcaseBusiness className="h-6 w-6" /> CV intelligent et matching emploi</h1>
          <p className="mt-1 text-sm text-[#64748B] dark:text-[#c7d0da]">Experience totale: {cv.total_experience_years || 0} an(s)</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => navigator.clipboard.writeText(cv.sharecode)}><Copy className="h-4 w-4" /> Copier sharecode</Button>
          <Button variant="outline" onClick={regenerate}><RefreshCw className="h-4 w-4" /> Regenerer</Button>
        </div>
      </header>

      <section className="grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
        <Panel title="Photo et sharecode">
          <div className="grid gap-4 sm:grid-cols-[120px_1fr]">
            <div className="flex h-28 w-28 items-center justify-center overflow-hidden rounded-xl border bg-[#F8FAFC] dark:border-[#56616a] dark:bg-[#1f2427]">
              {cv.photo_url ? <img src={cv.photo_url} alt="Photo CV" className="h-full w-full object-cover" /> : <Camera className="h-8 w-8 text-[#0F766E]" />}
            </div>
            <div className="grid gap-3">
              <Field label="Photo URL ou image compressee" value={cv.photo_url || ""} onChange={value => setCv({ ...cv, photo_url: value })} />
              <div className="flex flex-wrap gap-2">
                <Button type="button" variant="outline" onClick={() => setCv({ ...cv, photo_url: "" })}>Supprimer</Button>
                <div className="rounded-full border px-4 py-2 text-sm font-semibold dark:border-[#56616a]">{cv.sharecode}</div>
              </div>
            </div>
          </div>
        </Panel>
        <Panel title="Credits et agent IA etudiant">
          <div className="grid gap-3 md:grid-cols-[180px_1fr_auto]">
            <input type="number" min={10} value={credits} onChange={event => setCredits(Number(event.target.value))} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />
            <input value={agentPrompt} onChange={event => setAgentPrompt(event.target.value)} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={buyCredits}><Sparkles className="h-4 w-4" /> Credits</Button>
              <Button type="button" className="bg-black text-white" onClick={runAgent}><Bot className="h-4 w-4" /> Agent</Button>
            </div>
          </div>
          {agentResult && <p className="mt-3 whitespace-pre-wrap text-sm text-[#475569] dark:text-[#c7d0da]">{agentResult}</p>}
        </Panel>
      </section>

      <form onSubmit={save} className="grid gap-4 rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
        <h2 className="text-lg font-semibold">Profil CV</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <Field label="Titre professionnel" value={cv.professional_title || ""} onChange={value => setCv({ ...cv, professional_title: value })} />
          <Field label="Localisation souhaitee" value={cv.desired_location || ""} onChange={value => setCv({ ...cv, desired_location: value })} />
          <Field label="Portfolio" value={cv.portfolio_url || ""} onChange={value => setCv({ ...cv, portfolio_url: value })} />
        </div>
        <textarea value={cv.summary || ""} onChange={event => setCv({ ...cv, summary: event.target.value })} placeholder="Resume personnel" className="min-h-28 rounded-lg border px-3 py-2 dark:border-[#56616a] dark:bg-[#1f2427]" />
        <div className="grid gap-4 md:grid-cols-3">
          <Tags label="Secteurs" values={cv.sectors || []} onChange={values => setCv({ ...cv, sectors: values })} />
          <Tags label="Competences generales" values={cv.skills || []} onChange={values => setCv({ ...cv, skills: values })} />
          <Tags label="Langues CECR" values={cv.languages || []} onChange={values => setCv({ ...cv, languages: values })} />
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={cv.looking_for_job} onChange={event => setCv({ ...cv, looking_for_job: event.target.checked })} /> Recherche un emploi</label>
          <Privacy cv={cv} name="visible_in_sector_search" label="Visible recherche secteur" setCv={setCv} />
          <Privacy cv={cv} name="show_direct_contact" label="Afficher contact direct" setCv={setCv} />
        </div>
        <Button className="w-fit bg-black text-white"><Save className="h-4 w-4" /> Enregistrer le CV</Button>
      </form>

      <section className="grid gap-4 xl:grid-cols-3">
        <Panel title="Competences detaillees">
          <Repeater
            items={cv.detailed_skills || []}
            add={() => setCv({ ...cv, detailed_skills: [...(cv.detailed_skills || []), skillTemplate] })}
            render={(item, index) => (
              <div className="grid gap-2 rounded-lg border p-3 dark:border-[#56616a]">
                {(["category", "name", "level", "certificate"] as const).map(key => <input key={key} value={String(item[key] || "")} placeholder={key} onChange={event => updateArray(cv, setCv, "detailed_skills", index, { ...item, [key]: event.target.value })} className="min-h-10 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />)}
                <input type="number" value={item.years || 0} onChange={event => updateArray(cv, setCv, "detailed_skills", index, { ...item, years: Number(event.target.value) })} className="min-h-10 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />
              </div>
            )}
          />
        </Panel>
        <Panel title="Parcours academique">
          <Repeater
            items={cv.academic_credentials || []}
            add={() => setCv({ ...cv, academic_credentials: [...(cv.academic_credentials || []), { school: "", degree: "", field: "" }] })}
            render={(item, index) => (
              <div className="grid gap-2 rounded-lg border p-3 dark:border-[#56616a]">
                {(["school", "degree", "field", "start_year", "end_year"] as const).map(key => <input key={key} value={String(item[key] || "")} placeholder={key} onChange={event => updateArray(cv, setCv, "academic_credentials", index, { ...item, [key]: event.target.value })} className="min-h-10 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />)}
              </div>
            )}
          />
        </Panel>
        <Panel title="Certificats">
          <Repeater
            items={cv.certificates || []}
            add={() => setCv({ ...cv, certificates: [...(cv.certificates || []), { name: "", issuer: "" }] })}
            render={(item, index) => (
              <div className="grid gap-2 rounded-lg border p-3 dark:border-[#56616a]">
                {(["name", "issuer", "year", "url"] as const).map(key => <input key={key} value={String(item[key] || "")} placeholder={key} onChange={event => updateArray(cv, setCv, "certificates", index, { ...item, [key]: event.target.value })} className="min-h-10 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />)}
              </div>
            )}
          />
        </Panel>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Panel title="Experiences professionnelles">
          <div className="grid gap-3 md:grid-cols-2">
            <Field label="Entreprise" value={work.company} onChange={value => setWork({ ...work, company: value })} />
            <Field label="Poste" value={work.position} onChange={value => setWork({ ...work, position: value })} />
            <Field label="Secteur" value={work.sector} onChange={value => setWork({ ...work, sector: value })} />
            <Field label="Type" value={work.experience_type} onChange={value => setWork({ ...work, experience_type: value })} />
            <Field label="Debut" type="date" value={work.start_date} onChange={value => setWork({ ...work, start_date: value })} />
            <Field label="Fin" type="date" value={work.end_date} onChange={value => setWork({ ...work, end_date: value })} />
          </div>
          <textarea value={work.description} onChange={event => setWork({ ...work, description: event.target.value })} placeholder="Description des missions" className="mt-3 min-h-20 w-full rounded-lg border px-3 py-2 dark:border-[#56616a] dark:bg-[#1f2427]" />
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <TagsText label="Technologies" value={work.technologies_used} onChange={value => setWork({ ...work, technologies_used: value })} />
            <TagsText label="Competences acquises" value={work.skills_acquired} onChange={value => setWork({ ...work, skills_acquired: value })} />
          </div>
          <Button type="button" onClick={addWork} className="mt-3 bg-black text-white">Ajouter experience</Button>
          <div className="mt-4 grid gap-2">{(cv.work_history || []).map(item => <div key={item.id} className="rounded-lg border p-3 text-sm dark:border-[#56616a]">{item.position} - {item.company} ({item.experience_type})</div>)}</div>
        </Panel>
        <Panel title="Offres recommandees">
          <div className="grid gap-3">
            {recommendations.map(({ score, job }) => (
              <div key={job.id} className="rounded-lg border p-4 dark:border-[#56616a]">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-semibold">{job.title}</p>
                    <p className="text-sm text-[#64748B] dark:text-[#c7d0da]">{job.company} - {job.sector}</p>
                  </div>
                  <strong className="rounded-full bg-[#ECFDF5] px-3 py-1 text-sm text-[#047857]">{score}%</strong>
                </div>
                <p className="mt-2 text-sm text-[#64748B] dark:text-[#c7d0da]">Salaire: {job.salary_fixed || job.salary_min || "-"} {job.currency || ""} - limite: {job.deadline?.slice(0, 10) || "-"}</p>
                <Button type="button" variant="outline" className="mt-3" onClick={() => applyToJob(job.id)}>Postuler</Button>
              </div>
            ))}
            {!recommendations.length && <p className="text-sm text-[#64748B] dark:text-[#c7d0da]">Aucune recommandation pour le moment.</p>}
          </div>
        </Panel>
      </section>

      {status && <p className="text-sm text-[#475569] dark:text-[#c7d0da]">{status}</p>}
    </div>
  )
}

function csv(value: string) {
  return value.split(",").map(item => item.trim()).filter(Boolean)
}

function updateArray<K extends "detailed_skills" | "academic_credentials" | "certificates">(cv: CV, setCv: (cv: CV) => void, key: K, index: number, item: NonNullable<CV[K]>[number]) {
  const next = [...((cv[key] || []) as NonNullable<CV[K]>)]
  next[index] = item as never
  setCv({ ...cv, [key]: next })
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return <label className="grid gap-1 text-sm font-medium text-[#111827] dark:text-white">{label}<input type={type} value={value} onChange={event => onChange(event.target.value)} className="min-h-11 rounded-lg border px-3 text-[#111827] dark:border-[#56616a] dark:bg-[#1f2427] dark:text-white" /></label>
}

function Tags({ label, values, onChange }: { label: string; values: string[]; onChange: (values: string[]) => void }) {
  return <label className="grid gap-1 text-sm font-medium text-[#111827] dark:text-white">{label}<input value={values.join(", ")} onChange={event => onChange(csv(event.target.value))} className="min-h-11 rounded-lg border px-3 text-[#111827] dark:border-[#56616a] dark:bg-[#1f2427] dark:text-white" /></label>
}

function TagsText({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <Field label={label} value={value} onChange={onChange} />
}

function Privacy({ cv, name, label, setCv }: { cv: CV; name: string; label: string; setCv: (cv: CV) => void }) {
  const settings = cv.privacy_settings || {}
  return <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={Boolean(settings[name])} onChange={event => setCv({ ...cv, privacy_settings: { ...settings, [name]: event.target.checked } })} /> {label}</label>
}

function Repeater<T>({ items, add, render }: { items: T[]; add: () => void; render: (item: T, index: number) => ReactNode }) {
  return <div className="grid gap-3"><Button type="button" variant="outline" onClick={add}>Ajouter</Button>{items.map(render)}</div>
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return <section className="rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]"><h2 className="mb-4 text-lg font-semibold">{title}</h2>{children}</section>
}
