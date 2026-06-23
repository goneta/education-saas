"use client"

import { FormEvent, useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Building2, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"

type JobOffer = { id: number; title: string; company: string; sector: string; status: string; description: string; offer_type: string; workplace_mode: string }
type Application = { id: number; job_offer_id: number; student_cv_id: number; status: string; motivation_message?: string }
type RecruiterProfile = { payment_status: string; company_name: string; subscription_plan: string }

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
  const [form, setForm] = useState({ title: "", company: "", sector: "", description: "", offer_type: "emploi", workplace_mode: "on_site", status: "published" })
  const isPaymentPending = profile?.payment_status === "pending"

  const load = () => {
    if (!token) return
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    fetch(`${API_BASE_URL}/employment/recruiter/me`, { headers }).then(res => res.ok ? res.json() : null).then(data => data && setProfile(data)).catch(() => undefined)
    fetch(`${API_BASE_URL}/employment/recruiter/jobs`, { headers }).then(res => res.json()).then(data => setJobs(Array.isArray(data) ? data : [])).catch(() => undefined)
    fetch(`${API_BASE_URL}/employment/recruiter/applications`, { headers }).then(res => res.json()).then(data => setApplications(Array.isArray(data) ? data : [])).catch(() => undefined)
  }

  useEffect(load, [token])

  const createJob = async (event: FormEvent) => {
    event.preventDefault()
    if (!token) return
    if (isPaymentPending) {
      setPaymentModalOpen(true)
      return
    }
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/jobs`, {
      method: "POST",
      headers,
      body: JSON.stringify({ ...form, missions: [], required_skills: [] }),
    })
    if (!response.ok) {
      const message = await readUserMessage(response)
      if (message === PENDING_PAYMENT_MESSAGE) setPaymentModalOpen(true)
      setStatus(message === PENDING_PAYMENT_MESSAGE ? "" : message)
      return
    }
    setStatus("Offre creee.")
    if (response.ok) {
      setForm({ title: "", company: "", sector: "", description: "", offer_type: "emploi", workplace_mode: "on_site", status: "published" })
      load()
    }
  }

  const archive = async (jobId: number) => {
    if (!token) return
    if (isPaymentPending) {
      setPaymentModalOpen(true)
      return
    }
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    const response = await fetch(`${API_BASE_URL}/employment/recruiter/jobs/${jobId}`, { method: "DELETE", headers })
    if (!response.ok) {
      const message = await readUserMessage(response)
      if (message === PENDING_PAYMENT_MESSAGE) setPaymentModalOpen(true)
      setStatus(message === PENDING_PAYMENT_MESSAGE ? "" : message)
      return
    }
    setStatus("Offre archivee ou supprimee.")
    if (response.ok) load()
  }

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <header>
        <p className="text-sm font-semibold text-[#0F766E]">TeducAI Emploi</p>
        <h1 className="flex items-center gap-2 text-2xl font-bold"><Building2 className="h-6 w-6" /> Dashboard recruteur</h1>
      </header>

      {isPaymentPending && (
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800 dark:border-red-800 dark:bg-red-950/40 dark:text-red-200">
          Paiement: pending
        </div>
      )}

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
      {paymentModalOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4">
          <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl dark:bg-[#252b30]">
            <h2 className="text-lg font-semibold">Paiement requis</h2>
            <p className="mt-3 text-sm text-[#475569] dark:text-[#c7d0da]">{PENDING_PAYMENT_MESSAGE}</p>
            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setPaymentModalOpen(false)}>Fermer</Button>
              <Button type="button" className="bg-black text-white" onClick={() => router.push(`/${locale}/dashboard/checkout`)}>
                Make payment
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <label className="grid gap-1 text-sm font-medium">{label}<input value={value} onChange={event => onChange(event.target.value)} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" /></label>
}
