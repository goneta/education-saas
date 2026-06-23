"use client"

import { FormEvent, useEffect, useState } from "react"
import { Building2, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"

type JobOffer = { id: number; title: string; company: string; sector: string; status: string; description: string; offer_type: string; workplace_mode: string }
type Application = { id: number; job_offer_id: number; student_cv_id: number; status: string; motivation_message?: string }

export default function RecruiterDashboardPage() {
  const { token } = useAuth()
  const [jobs, setJobs] = useState<JobOffer[]>([])
  const [applications, setApplications] = useState<Application[]>([])
  const [status, setStatus] = useState("")
  const [form, setForm] = useState({ title: "", company: "", sector: "", description: "", offer_type: "emploi", workplace_mode: "on_site", status: "published" })

  const load = () => {
    if (!token) return
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    fetch(`${API_BASE_URL}/employment/recruiter/jobs`, { headers }).then(res => res.json()).then(data => setJobs(Array.isArray(data) ? data : [])).catch(() => undefined)
    fetch(`${API_BASE_URL}/employment/recruiter/applications`, { headers }).then(res => res.json()).then(data => setApplications(Array.isArray(data) ? data : [])).catch(() => undefined)
  }

  useEffect(load, [token])

  const createJob = async (event: FormEvent) => {
    event.preventDefault()
    if (!token) return
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/jobs`, {
      method: "POST",
      headers,
      body: JSON.stringify({ ...form, missions: [], required_skills: [] }),
    })
    setStatus(response.ok ? "Offre creee." : "Creation refusee. Verifiez votre abonnement recruteur.")
    if (response.ok) {
      setForm({ title: "", company: "", sector: "", description: "", offer_type: "emploi", workplace_mode: "on_site", status: "published" })
      load()
    }
  }

  const archive = async (jobId: number) => {
    if (!token) return
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/jobs/${jobId}`, { method: "DELETE", headers })
    setStatus(response.ok ? "Offre archivee ou supprimee." : "Action impossible.")
    if (response.ok) load()
  }

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <header>
        <p className="text-sm font-semibold text-[#0F766E]">TeducAI Emploi</p>
        <h1 className="flex items-center gap-2 text-2xl font-bold"><Building2 className="h-6 w-6" /> Dashboard recruteur</h1>
      </header>

      <form onSubmit={createJob} className="grid gap-4 rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
        <h2 className="text-lg font-semibold">Publier une offre</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <Field label="Titre" value={form.title} onChange={value => setForm({ ...form, title: value })} />
          <Field label="Entreprise" value={form.company} onChange={value => setForm({ ...form, company: value })} />
          <Field label="Secteur" value={form.sector} onChange={value => setForm({ ...form, sector: value })} />
        </div>
        <textarea placeholder="Description" value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} className="min-h-28 rounded-lg border px-3 py-2 dark:border-[#56616a] dark:bg-[#1f2427]" />
        <Button className="w-fit bg-black text-white"><Plus className="h-4 w-4" /> Ajouter l&apos;offre</Button>
      </form>

      <section className="rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
        <h2 className="text-lg font-semibold">Mes offres</h2>
        <div className="mt-4 grid gap-3">
          {jobs.map(job => (
            <div key={job.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3 dark:border-[#56616a]">
              <div>
                <p className="font-semibold">{job.title}</p>
                <p className="text-sm text-[#64748B]">{job.company} - {job.sector} - {job.status}</p>
              </div>
              <Button variant="outline" onClick={() => archive(job.id)}>Cloturer / archiver</Button>
            </div>
          ))}
          {!jobs.length && <p className="text-sm text-[#64748B]">Aucune offre.</p>}
        </div>
      </section>

      <section className="rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
        <h2 className="text-lg font-semibold">Candidatures recues</h2>
        <div className="mt-4 grid gap-3">
          {applications.map(item => <div key={item.id} className="rounded-lg border p-3 text-sm dark:border-[#56616a]">CV #{item.student_cv_id} - Offre #{item.job_offer_id} - {item.status}</div>)}
          {!applications.length && <p className="text-sm text-[#64748B]">Aucune candidature.</p>}
        </div>
      </section>
      {status && <p className="text-sm text-[#475569]">{status}</p>}
    </div>
  )
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="grid gap-1 text-sm font-medium">{label}<input value={value} onChange={event => onChange(event.target.value)} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" /></label>
}
