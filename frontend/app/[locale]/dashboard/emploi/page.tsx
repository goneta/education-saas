"use client"

import { FormEvent, useEffect, useState } from "react"
import { BriefcaseBusiness, Copy, RefreshCw, Save } from "lucide-react"

import { Button } from "@/components/ui/button"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"

type CV = {
  sharecode: string
  professional_title?: string
  summary?: string
  sectors?: string[]
  skills?: string[]
  languages?: string[]
  looking_for_job: boolean
  privacy_settings?: Record<string, boolean>
  work_history?: { id: number; company: string; position: string; experience_type: string }[]
}

export default function EmploymentDashboardPage() {
  const { token } = useAuth()
  const [cv, setCv] = useState<CV | null>(null)
  const [status, setStatus] = useState("")
  const [work, setWork] = useState({ company: "", position: "", experience_type: "stage", sector: "" })

  const load = () => {
    if (!token) return
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    fetch(`${API_BASE_URL}/employment/me/cv`, { headers }).then(res => res.json()).then(setCv).catch(() => setStatus("CV indisponible."))
  }

  useEffect(load, [token])

  const save = async (event: FormEvent) => {
    event.preventDefault()
    if (!cv) return
    if (!token) return
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    const response = await fetch(`${API_BASE_URL}/employment/me/cv`, {
      method: "PUT",
      headers,
      body: JSON.stringify({
        professional_title: cv.professional_title,
        summary: cv.summary,
        sectors: cv.sectors || [],
        skills: cv.skills || [],
        languages: cv.languages || [],
        looking_for_job: cv.looking_for_job,
        privacy_settings: cv.privacy_settings || {},
      }),
    })
    setStatus(response.ok ? "CV enregistre." : "Enregistrement impossible.")
    if (response.ok) setCv(await response.json())
  }

  const addWork = async () => {
    if (!token) return
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    const response = await fetch(`${API_BASE_URL}/employment/me/cv/work-history`, { method: "POST", headers, body: JSON.stringify({ ...work, missions: [], skills_used: [] }) })
    setStatus(response.ok ? "Experience ajoutee." : "Experience refusee.")
    if (response.ok) {
      setWork({ company: "", position: "", experience_type: "stage", sector: "" })
      load()
    }
  }

  const regenerate = async () => {
    if (!token) return
    const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    const response = await fetch(`${API_BASE_URL}/employment/me/cv/regenerate-sharecode`, { method: "POST", headers })
    const data = await response.json().catch(() => null)
    if (response.ok && cv) setCv({ ...cv, sharecode: data.sharecode })
  }

  if (!cv) return <div className="p-6">Chargement Emploi...</div>

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-[#0F766E]">TeducAI Emploi</p>
          <h1 className="flex items-center gap-2 text-2xl font-bold"><BriefcaseBusiness className="h-6 w-6" /> Page CV et partage recruteur</h1>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigator.clipboard.writeText(cv.sharecode)}><Copy className="h-4 w-4" /> Copier sharecode</Button>
          <Button variant="outline" onClick={regenerate}><RefreshCw className="h-4 w-4" /> Regenerer</Button>
        </div>
      </header>

      <section className="rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
        <p className="text-sm text-[#64748B]">Sharecode</p>
        <p className="mt-1 text-2xl font-bold tracking-normal">{cv.sharecode}</p>
      </section>

      <form onSubmit={save} className="grid gap-4 rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
        <label className="grid gap-1 text-sm font-medium">Titre professionnel
          <input value={cv.professional_title || ""} onChange={event => setCv({ ...cv, professional_title: event.target.value })} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />
        </label>
        <label className="grid gap-1 text-sm font-medium">Resume personnel
          <textarea value={cv.summary || ""} onChange={event => setCv({ ...cv, summary: event.target.value })} className="min-h-28 rounded-lg border px-3 py-2 dark:border-[#56616a] dark:bg-[#1f2427]" />
        </label>
        <div className="grid gap-4 md:grid-cols-3">
          <Tags label="Secteurs" values={cv.sectors || []} onChange={values => setCv({ ...cv, sectors: values })} />
          <Tags label="Competences" values={cv.skills || []} onChange={values => setCv({ ...cv, skills: values })} />
          <Tags label="Langues" values={cv.languages || []} onChange={values => setCv({ ...cv, languages: values })} />
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={cv.looking_for_job} onChange={event => setCv({ ...cv, looking_for_job: event.target.checked })} /> Recherche un emploi</label>
          <Privacy cv={cv} name="visible_in_sector_search" label="Visible dans la recherche secteur" setCv={setCv} />
          <Privacy cv={cv} name="show_direct_contact" label="Afficher contact direct" setCv={setCv} />
          <Privacy cv={cv} name="show_averages" label="Afficher moyennes" setCv={setCv} />
          <Privacy cv={cv} name="show_teacher_comments" label="Afficher appreciations" setCv={setCv} />
          <Privacy cv={cv} name="show_behavior" label="Afficher comportement" setCv={setCv} />
        </div>
        <Button className="w-fit bg-black text-white"><Save className="h-4 w-4" /> Enregistrer</Button>
      </form>

      <section className="rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
        <h2 className="text-lg font-semibold">Work history</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          <input placeholder="Entreprise" value={work.company} onChange={event => setWork({ ...work, company: event.target.value })} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />
          <input placeholder="Poste" value={work.position} onChange={event => setWork({ ...work, position: event.target.value })} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />
          <input placeholder="Secteur" value={work.sector} onChange={event => setWork({ ...work, sector: event.target.value })} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" />
          <Button type="button" onClick={addWork}>Ajouter</Button>
        </div>
        <div className="mt-4 grid gap-2">{(cv.work_history || []).map(item => <div key={item.id} className="rounded-lg border p-3 text-sm dark:border-[#56616a]">{item.position} - {item.company} ({item.experience_type})</div>)}</div>
      </section>

      {status && <p className="text-sm text-[#475569]">{status}</p>}
    </div>
  )
}

function Tags({ label, values, onChange }: { label: string; values: string[]; onChange: (values: string[]) => void }) {
  return <label className="grid gap-1 text-sm font-medium">{label}<input value={values.join(", ")} onChange={event => onChange(event.target.value.split(",").map(item => item.trim()).filter(Boolean))} className="min-h-11 rounded-lg border px-3 dark:border-[#56616a] dark:bg-[#1f2427]" /></label>
}

function Privacy({ cv, name, label, setCv }: { cv: CV; name: string; label: string; setCv: (cv: CV) => void }) {
  const settings = cv.privacy_settings || {}
  return <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={Boolean(settings[name])} onChange={event => setCv({ ...cv, privacy_settings: { ...settings, [name]: event.target.checked } })} /> {label}</label>
}
