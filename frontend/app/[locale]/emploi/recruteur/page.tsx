"use client"

import { FormEvent, use, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Building2 } from "lucide-react"

import { MarketingNav } from "@/components/marketing/marketing-nav"
import { MarketingFooter } from "@/components/marketing/marketing-footer"
import { Button } from "@/components/ui/button"
import { API_BASE_URL } from "@/lib/config"
import { normalizeLocale } from "@/lib/i18n"

export default function RecruiterRegisterPage({ params }: { params: Promise<{ locale: string }> }) {
  const locale = normalizeLocale(use(params).locale)
  const router = useRouter()
  const [form, setForm] = useState({ email: "", password: "", company_name: "", contact_name: "", sector: "", phone: "", website: "", plan: "sharecode_only" })
  const [status, setStatus] = useState("")
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  const validateForm = () => {
    const errors: Record<string, string> = {}
    if (!form.company_name.trim()) errors.company_name = "Entreprise requise."
    if (!form.contact_name.trim()) errors.contact_name = "Contact requis."
    if (!form.email.trim()) errors.email = "Email requis."
    if (form.password.length < 12) errors.password = "Le mot de passe doit contenir au moins 12 caracteres."
    else if (!/[A-Z]/.test(form.password) || !/[a-z]/.test(form.password) || !/\d/.test(form.password) || !/[^A-Za-z0-9]/.test(form.password)) {
      errors.password = "Le mot de passe doit contenir une majuscule, une minuscule, un chiffre et un caractere special."
    }
    if (form.phone && form.phone.replace(/\D/g, "").length < 6) errors.phone = "Numero de telephone invalide."
    return errors
  }

  const readBackendError = async (response: Response) => {
    const contentType = response.headers.get("content-type") || ""
    if (contentType.includes("application/json")) return response.json().catch(() => null)
    const text = await response.text().catch(() => "")
    return { detail: text || (response.status >= 500 ? "Erreur serveur." : "Requete refusee.") }
  }

  const mapBackendErrors = (payload: unknown, statusCode: number) => {
    const errors: Record<string, string> = {}
    const detail = (payload as { detail?: unknown } | null)?.detail
    if (Array.isArray(detail)) {
      detail.forEach(item => {
        const field = Array.isArray(item?.loc) ? String(item.loc[item.loc.length - 1]) : ""
        if (field) errors[field] = item?.msg || "Champ invalide."
      })
    } else if (typeof detail === "string") {
      const message = detail.replace("deja", "déjà")
      const lower = message.toLowerCase()
      if (lower.includes("email")) errors.email = message
      else if (lower.includes("telephone") || lower.includes("phone")) errors.phone = message
      else if (lower.includes("mot de passe") || lower.includes("password")) errors.password = message
      else errors.form = message
    }
    if (!Object.keys(errors).length && statusCode >= 500) {
      errors.form = "Le service d'inscription recruteur est momentanement indisponible. Veuillez reessayer."
    }
    return errors
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setStatus("Création en cours...")
    setFieldErrors({})
    const clientErrors = validateForm()
    if (Object.keys(clientErrors).length) {
      setFieldErrors(clientErrors)
      setStatus("")
      return
    }
    const response = await fetch(`${API_BASE_URL}/employment/recruiters/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, payment_provider: "manual" }),
    })
    const data = await readBackendError(response)
    if (response.ok) {
      setStatus("Compte recruteur créé. Redirection vers la connexion...")
      router.push(`/${locale}/login?intent=recruiter`)
      return
    }
    const errors = mapBackendErrors(data, response.status)
    setFieldErrors(Object.keys(errors).length ? errors : { form: response.status >= 500 ? "Le service d'inscription recruteur est momentanement indisponible. Veuillez reessayer." : "Inscription impossible. Vérifiez les champs du formulaire." })
    setStatus("")
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] dark:bg-[#1f2427] dark:text-white">
      <MarketingNav locale={locale} />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <Link href={`/${locale}/emploi`} className="text-sm font-medium text-[#0F766E]">Retour Emploi</Link>
        <h1 className="mt-4 flex items-center gap-3 text-3xl font-bold"><Building2 className="h-7 w-7" /> Inscription recruteur</h1>
        <form onSubmit={submit} className="mt-6 grid gap-4 rounded-lg border border-[#DDE5E8] bg-white p-5 dark:border-[#3b4248] dark:bg-[#252b30]">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Entreprise" value={form.company_name} error={fieldErrors.company_name} required onChange={value => setForm({ ...form, company_name: value })} />
            <Field label="Contact" value={form.contact_name} error={fieldErrors.contact_name} required onChange={value => setForm({ ...form, contact_name: value })} />
            <Field label="Email" type="email" value={form.email} error={fieldErrors.email} required onChange={value => setForm({ ...form, email: value })} />
            <Field label="Mot de passe" type="password" value={form.password} error={fieldErrors.password} required onChange={value => setForm({ ...form, password: value })} />
            <Field label="Secteur" value={form.sector} error={fieldErrors.sector} onChange={value => setForm({ ...form, sector: value })} />
            <Field label="Telephone" value={form.phone} error={fieldErrors.phone} onChange={value => setForm({ ...form, phone: value })} />
          </div>
          <Field label="Site web" value={form.website} error={fieldErrors.website} onChange={value => setForm({ ...form, website: value })} />
          <label className="grid gap-1 text-sm font-medium text-[#0F172A] dark:text-white">Offre
            <select value={form.plan} onChange={event => setForm({ ...form, plan: event.target.value })} className="min-h-11 rounded-lg border border-[#CBD5E1] bg-white px-3 text-[#0F172A] dark:border-[#56616a] dark:bg-[#1f2427] dark:text-white">
              <option value="sharecode_only">Acces sharecode uniquement</option>
              <option value="job_posts">Publication d&apos;offres</option>
              <option value="cvtheque_limited">CVtheque limitee</option>
              <option value="cvtheque_advanced">CVtheque avancee</option>
            </select>
            {fieldErrors.plan && <span className="text-xs font-medium text-red-700 dark:text-red-300">{fieldErrors.plan}</span>}
          </label>
          <Button className="bg-black text-white">Creer mon compte recruteur</Button>
          {fieldErrors.form && <p className="text-sm font-medium text-red-700 dark:text-red-300">{fieldErrors.form}</p>}
          {status && <p className="text-sm text-[#475569] dark:text-[#c7d0da]">{status}</p>}
        </form>
      </main>
      <MarketingFooter locale={locale} />
    </div>
  )
}

function Field({ label, value, onChange, type = "text", error, required = false }: { label: string; value: string; onChange: (value: string) => void; type?: string; error?: string; required?: boolean }) {
  return (
    <label className="grid gap-1 text-sm font-medium text-[#0F172A] dark:text-white">
      {label}
      <input type={type} value={value} required={required} onChange={event => onChange(event.target.value)} aria-invalid={Boolean(error)} className="min-h-11 rounded-lg border border-[#CBD5E1] bg-white px-3 text-[16px] text-[#0F172A] outline-none focus:border-black aria-[invalid=true]:border-red-500 dark:border-[#56616a] dark:bg-[#1f2427] dark:text-white" />
      {error && <span className="text-xs font-medium text-red-700 dark:text-red-300">{error}</span>}
    </label>
  )
}
