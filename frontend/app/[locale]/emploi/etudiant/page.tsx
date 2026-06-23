"use client"

import { FormEvent, use, useState } from "react"
import Link from "next/link"
import { UserPlus } from "lucide-react"

import { MarketingNav } from "@/components/marketing/marketing-nav"
import { MarketingFooter } from "@/components/marketing/marketing-footer"
import { Button } from "@/components/ui/button"
import { API_BASE_URL } from "@/lib/config"
import { normalizeLocale } from "@/lib/i18n"

export default function ExternalStudentPage({ params }: { params: Promise<{ locale: string }> }) {
  const locale = normalizeLocale(use(params).locale)
  const [form, setForm] = useState({ email: "", password: "", first_name: "", last_name: "", phone: "", sector: "", professional_title: "" })
  const [status, setStatus] = useState("")

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setStatus("Creation en cours...")
    const response = await fetch(`${API_BASE_URL}/employment/external-students/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, payment_provider: "manual" }),
    })
    const data = await response.json().catch(() => null)
    setStatus(response.ok ? `Compte cree. Sharecode: ${data.sharecode}` : data?.detail || "Inscription impossible.")
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] dark:bg-[#1f2427] dark:text-white">
      <MarketingNav locale={locale} />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <Link href={`/${locale}/emploi`} className="text-sm font-medium text-[#0F766E]">Retour Emploi</Link>
        <h1 className="mt-4 flex items-center gap-3 text-3xl font-bold"><UserPlus className="h-7 w-7" /> Compte etudiant externe</h1>
        <form onSubmit={submit} className="mt-6 grid gap-4 rounded-lg border border-[#DDE5E8] bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Prenom" value={form.first_name} onChange={value => setForm({ ...form, first_name: value })} />
            <Field label="Nom" value={form.last_name} onChange={value => setForm({ ...form, last_name: value })} />
            <Field label="Email" type="email" value={form.email} onChange={value => setForm({ ...form, email: value })} />
            <Field label="Mot de passe" type="password" value={form.password} onChange={value => setForm({ ...form, password: value })} />
            <Field label="Telephone" value={form.phone} onChange={value => setForm({ ...form, phone: value })} />
            <Field label="Secteur recherche" value={form.sector} onChange={value => setForm({ ...form, sector: value })} />
          </div>
          <Field label="Titre professionnel" value={form.professional_title} onChange={value => setForm({ ...form, professional_title: value })} />
          <Button className="bg-black text-white">Creer mon CV Emploi</Button>
          {status && <p className="text-sm text-[#475569] dark:text-[#c7d0da]">{status}</p>}
        </form>
      </main>
      <MarketingFooter locale={locale} />
    </div>
  )
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return <label className="grid gap-1 text-sm font-medium">{label}<input type={type} value={value} onChange={event => onChange(event.target.value)} className="min-h-11 rounded-lg border border-[#CBD5E1] bg-white px-3 text-[16px] outline-none focus:border-black dark:border-[#56616a] dark:bg-[#1f2427]" /></label>
}
