"use client"

import { FormEvent, use, useEffect, useState } from "react"
import Link from "next/link"
import { BriefcaseBusiness, Search, ShieldCheck, UserRoundSearch } from "lucide-react"

import { MarketingNav } from "@/components/marketing/marketing-nav"
import { MarketingFooter } from "@/components/marketing/marketing-footer"
import { Button } from "@/components/ui/button"
import { API_BASE_URL } from "@/lib/config"
import { normalizeLocale } from "@/lib/i18n"
import { useAuth } from "@/contexts/auth-context"

type Props = { params: Promise<{ locale: string }> }

type PublicCV = {
  id: number
  name?: string
  professional_title?: string
  summary?: string
  sectors?: string[]
  skills?: string[]
  availability?: string
  work_history?: { id: number; company: string; position: string; experience_type: string }[]
  academic_timeline?: { school?: string; academic_year?: string; average?: number; school_model?: string }[]
}

type JobOffer = {
  id: number
  title: string
  company: string
  sector: string
  offer_type: string
  location?: string
  workplace_mode: string
  description: string
}

export default function EmploiPage({ params }: Props) {
  const { locale: rawLocale } = use(params)
  const locale = normalizeLocale(rawLocale)
  const { token } = useAuth()
  const [sharecode, setSharecode] = useState("")
  const [sector, setSector] = useState("")
  const [sectors, setSectors] = useState<string[]>([])
  const [profiles, setProfiles] = useState<PublicCV[]>([])
  const [jobs, setJobs] = useState<JobOffer[]>([])
  const [selectedCv, setSelectedCv] = useState<PublicCV | null>(null)
  const [status, setStatus] = useState("")

  useEffect(() => {
    fetch(`${API_BASE_URL}/employment/sectors`).then(res => res.json()).then(data => setSectors(data.sectors || [])).catch(() => setSectors([]))
    fetch(`${API_BASE_URL}/employment/jobs`).then(res => res.json()).then(data => setJobs(Array.isArray(data) ? data : [])).catch(() => setJobs([]))
  }, [])

  useEffect(() => {
    const url = new URL(`${API_BASE_URL}/employment/public-profiles`, window.location.origin)
    if (sector) url.searchParams.set("sector", sector)
    fetch(url.toString(), {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    }).then(res => res.json()).then(data => setProfiles(Array.isArray(data) ? data : [])).catch(() => setProfiles([]))
  }, [sector, token])

  const lookup = async (event: FormEvent) => {
    event.preventDefault()
    setStatus("Recherche en cours...")
    setSelectedCv(null)
    const response = await fetch(`${API_BASE_URL}/employment/sharecode/lookup`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ sharecode }),
    })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      setStatus(data?.detail || "Sharecode invalide.")
      return
    }
    setSelectedCv(data)
    setStatus("Page CV trouvee.")
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] dark:bg-[#1f2427] dark:text-[#f4f7fb]">
      <MarketingNav locale={locale} />
      <main>
        <section className="border-b border-[#DDE5E8] bg-white py-10 dark:border-[#3b4248] dark:bg-[#202528]">
          <div className="mx-auto grid max-w-7xl gap-8 px-4 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:px-8">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-[#99F6E4] px-4 py-2 text-sm font-semibold text-[#0F766E]">
                <BriefcaseBusiness className="h-4 w-4" />
                TeducAI Emploi
              </div>
              <h1 className="mt-6 text-4xl font-bold tracking-normal sm:text-5xl">CV, sharecode et recrutement etudiant</h1>
              <p className="mt-4 max-w-2xl text-lg leading-8 text-[#475569] dark:text-[#c7d0da]">
                Les recruteurs consultent les Pages CV autorisees, recherchent par secteur et publient des offres. Les etudiants gardent le controle des informations partagees.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Button asChild className="bg-black text-white"><Link href={`/${locale}/emploi/recruteur`}>Inscription recruteur</Link></Button>
                <Button asChild variant="outline"><Link href={`/${locale}/emploi/etudiant`}>Etudiant externe</Link></Button>
              </div>
            </div>

            <form onSubmit={lookup} className="rounded-lg border border-[#DDE5E8] bg-[#F8FAFC] p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
              <label className="text-sm font-semibold">Acces par sharecode</label>
              <div className="mt-3 flex gap-2">
                <input value={sharecode} onChange={event => setSharecode(event.target.value.toUpperCase())} placeholder="STU2024001-KC" className="min-h-11 flex-1 rounded-lg border border-[#CBD5E1] bg-white px-3 text-[16px] outline-none focus:border-black dark:border-[#56616a] dark:bg-[#1f2427]" />
                <Button type="submit" className="bg-black text-white"><Search className="h-4 w-4" /> Rechercher</Button>
              </div>
              {status && <p className="mt-3 text-sm text-[#475569] dark:text-[#c7d0da]">{status}</p>}
              <p className="mt-5 flex gap-2 text-sm text-[#475569] dark:text-[#c7d0da]"><ShieldCheck className="h-4 w-4 text-[#0F766E]" /> Les donnees financieres, internes et privees restent masquees par defaut.</p>
            </form>
          </div>
        </section>

        {selectedCv && <CvPanel cv={selectedCv} />}

        <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-2xl font-bold">Recherche par secteur</h2>
            <select value={sector} onChange={event => setSector(event.target.value)} className="min-h-11 rounded-lg border border-[#CBD5E1] bg-white px-3 dark:border-[#56616a] dark:bg-[#252b30]">
              <option value="">Tous les secteurs</option>
              {sectors.map(item => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {profiles.map(profile => (
              <button key={profile.id} onClick={() => setSelectedCv(profile)} className="rounded-lg border border-[#DDE5E8] bg-white p-5 text-left shadow-sm transition hover:border-black dark:border-[#3b4248] dark:bg-[#252b30]">
                <UserRoundSearch className="h-6 w-6 text-[#0F766E]" />
                <h3 className="mt-3 font-semibold">{profile.name || "Profil etudiant"}</h3>
                <p className="text-sm text-[#475569] dark:text-[#c7d0da]">{profile.professional_title || "Disponible"}</p>
                <p className="mt-3 line-clamp-3 text-sm leading-6">{profile.summary}</p>
                <div className="mt-3 flex flex-wrap gap-2">{(profile.skills || []).slice(0, 4).map(skill => <span key={skill} className="rounded-full bg-[#ECFDF5] px-2 py-1 text-xs text-[#047857]">{skill}</span>)}</div>
              </button>
            ))}
            {!profiles.length && <p className="text-sm text-[#64748B]">Aucun profil public pour ce filtre.</p>}
          </div>
        </section>

        <section className="bg-white py-10 dark:bg-[#202528]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <h2 className="text-2xl font-bold">Offres publiees</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              {jobs.map(job => (
                <article key={job.id} className="rounded-lg border border-[#DDE5E8] p-5 dark:border-[#3b4248]">
                  <p className="text-sm font-semibold text-[#0F766E]">{job.sector} - {job.offer_type}</p>
                  <h3 className="mt-2 text-xl font-semibold">{job.title}</h3>
                  <p className="text-sm text-[#475569] dark:text-[#c7d0da]">{job.company} - {job.location || job.workplace_mode}</p>
                  <p className="mt-3 line-clamp-3 text-sm leading-6">{job.description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>
      <MarketingFooter locale={locale} />
    </div>
  )
}

function CvPanel({ cv }: { cv: PublicCV }) {
  return (
    <section className="border-b border-[#DDE5E8] bg-[#ECFDF5] py-8 dark:border-[#3b4248] dark:bg-[#14312f]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <h2 className="text-2xl font-bold">{cv.name || "Page CV"}</h2>
        <p className="mt-1 text-[#475569] dark:text-[#c7d0da]">{cv.professional_title}</p>
        <p className="mt-4 max-w-3xl leading-7">{cv.summary}</p>
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          <div><h3 className="font-semibold">Competences</h3><p className="mt-2 text-sm">{(cv.skills || []).join(", ") || "Non renseigne"}</p></div>
          <div><h3 className="font-semibold">Parcours academique</h3><p className="mt-2 text-sm">{(cv.academic_timeline || []).map(row => `${row.school || "Etablissement"} ${row.academic_year || ""}`).join(" | ") || "Masque ou non renseigne"}</p></div>
          <div><h3 className="font-semibold">Experiences</h3><p className="mt-2 text-sm">{(cv.work_history || []).map(row => `${row.position} - ${row.company}`).join(" | ") || "Non renseigne"}</p></div>
        </div>
      </div>
    </section>
  )
}
