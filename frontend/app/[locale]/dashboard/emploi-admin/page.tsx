"use client"

import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import { Bell, BriefcaseBusiness, Building2, GraduationCap, Send, Users } from "lucide-react"

import { Button } from "@/components/ui/button"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"

type Overview = {
  stats: {
    students: number
    recruiters: number
    active_jobs: number
    pending_recruiters: number
    applications: number
  }
  students: Array<{ id: number; name?: string; sharecode: string; professional_title?: string; sectors?: string[]; total_experience_years?: number }>
  recruiters: Array<{ id: number; company_name: string; payment_status: string; subscription_plan: string; days_remaining?: number | null; ai_credits_balance?: number }>
  jobs: Array<{ id: number; title: string; company: string; sector: string; status: string; applications_count?: number }>
  notifications: Array<{ id: number; audience: string; title: string; message: string; created_at: string }>
}

const emptyOverview: Overview = {
  stats: { students: 0, recruiters: 0, active_jobs: 0, pending_recruiters: 0, applications: 0 },
  students: [],
  recruiters: [],
  jobs: [],
  notifications: [],
}

export default function EmploymentAdminPage() {
  const { token, user } = useAuth()
  const params = useParams()
  const locale = normalizeLocale(params.locale as string)
  const [overview, setOverview] = useState<Overview>(emptyOverview)
  const [status, setStatus] = useState("")
  const [notification, setNotification] = useState({ audience: "all", title: "", message: "" })
  const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : null, [token])

  const load = () => {
    if (!headers) return
    fetch(`${API_BASE_URL}/employment/admin/overview`, { headers })
      .then(res => res.ok ? res.json() : Promise.reject(res))
      .then(data => setOverview({ ...emptyOverview, ...data }))
      .catch(() => setStatus("Vue Super Admin Emploi indisponible."))
  }

  useEffect(load, [headers])

  const sendNotification = async (event: FormEvent) => {
    event.preventDefault()
    if (!headers) return
    const response = await fetch(`${API_BASE_URL}/employment/admin/notifications`, {
      method: "POST",
      headers,
      body: JSON.stringify(notification),
    })
    const data = await response.json().catch(() => null)
    setStatus(response.ok ? "Notification Emploi publiee." : data?.detail || "Notification impossible.")
    if (response.ok) {
      setNotification({ audience: "all", title: "", message: "" })
      load()
    }
  }

  if (user && user.role !== "super_admin") {
    return <div className="rounded-lg border bg-white p-6 text-[#111827] dark:border-[#3b4248] dark:bg-[#252b30] dark:text-white">Acces reserve au Super Admin.</div>
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5 text-[#111827] dark:text-white">
      <header>
        <p className="text-sm font-semibold text-[#0F766E] dark:text-[#5eead4]">Super Admin</p>
        <h1 className="flex items-center gap-2 text-2xl font-bold"><BriefcaseBusiness className="h-6 w-6" /> Pilotage du module Emploi</h1>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <Stat icon={<GraduationCap />} label="Etudiants CV" value={overview.stats.students} />
        <Stat icon={<Building2 />} label="Recruteurs" value={overview.stats.recruiters} />
        <Stat icon={<BriefcaseBusiness />} label="Offres actives" value={overview.stats.active_jobs} />
        <Stat icon={<Users />} label={locale === "en" ? "Pending Payments" : "Paiements en attente"} value={overview.stats.pending_recruiters} />
        <Stat icon={<Bell />} label="Candidatures" value={overview.stats.applications} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="Recruteurs">
          <div className="grid gap-2">
            {overview.recruiters.map(item => (
              <div key={item.id} className="rounded-lg border p-3 text-sm dark:border-[#56616a]">
                <strong>{item.company_name}</strong>
                <p className="text-[#64748B] dark:text-[#c7d0da]">{item.subscription_plan} - {item.payment_status} - {item.days_remaining ?? "-"} jours - {item.ai_credits_balance || 0} credits</p>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Offres et activite">
          <div className="grid gap-2">
            {overview.jobs.map(item => (
              <div key={item.id} className="rounded-lg border p-3 text-sm dark:border-[#56616a]">
                <strong>{item.title}</strong>
                <p className="text-[#64748B] dark:text-[#c7d0da]">{item.company} - {item.sector} - {item.status} - {item.applications_count || 0} candidature(s)</p>
              </div>
            ))}
          </div>
        </Panel>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1fr_0.9fr]">
        <Panel title="Etudiants et CV">
          <div className="grid gap-2">
            {overview.students.map(item => (
              <div key={item.id} className="rounded-lg border p-3 text-sm dark:border-[#56616a]">
                <strong>{item.name || "Profil etudiant"}</strong>
                <p className="text-[#64748B] dark:text-[#c7d0da]">{item.sharecode} - {item.professional_title || "Sans titre"} - {(item.sectors || []).join(", ")}</p>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Centre de notifications">
          <form onSubmit={sendNotification} className="grid gap-3">
            <select value={notification.audience} onChange={event => setNotification({ ...notification, audience: event.target.value })} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]">
              <option value="all">Tous</option>
              <option value="students">Etudiants</option>
              <option value="recruiters">Recruteurs</option>
            </select>
            <input value={notification.title} onChange={event => setNotification({ ...notification, title: event.target.value })} placeholder="Titre" className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />
            <textarea value={notification.message} onChange={event => setNotification({ ...notification, message: event.target.value })} placeholder="Message" className="min-h-28 rounded-lg border px-3 py-2 dark:border-[#56616a] dark:bg-[#1f2427]" />
            <Button className="w-fit bg-black text-white"><Send className="h-4 w-4" /> Publier</Button>
          </form>
          <div className="mt-4 grid gap-2">
            {overview.notifications.map(item => <div key={item.id} className="rounded-lg border p-3 text-sm dark:border-[#56616a]"><strong>{item.title}</strong><p>{item.message}</p></div>)}
          </div>
        </Panel>
      </section>

      {status && <p className="text-sm text-[#475569] dark:text-[#c7d0da]">{status}</p>}
    </div>
  )
}

function Stat({ icon, label, value }: { icon: ReactNode; label: string; value: number }) {
  return <div className="rounded-lg border bg-white p-4 dark:border-[#3b4248] dark:bg-[#252b30]"><div className="h-5 w-5 text-[#0F766E]">{icon}</div><p className="mt-3 text-sm text-[#64748B] dark:text-[#c7d0da]">{label}</p><p className="text-2xl font-bold">{value}</p></div>
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return <section className="rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]"><h2 className="mb-4 text-lg font-semibold">{title}</h2>{children}</section>
}
