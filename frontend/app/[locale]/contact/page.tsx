"use client"

import { FormEvent, useMemo, useState } from "react"
import { Building2, Mail, MapPin, Phone, Send } from "lucide-react"
import { useParams } from "next/navigation"

import { MarketingFooter } from "@/components/marketing/marketing-footer"
import { MarketingNav } from "@/components/marketing/marketing-nav"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { normalizeLocale } from "@/lib/i18n"

const contactFields = [
  ["fullName", "Nom complet", "text"],
  ["school", "Établissement", "text"],
  ["email", "Email", "email"],
  ["phone", "Téléphone", "tel"],
  ["country", "Pays", "text"],
  ["subject", "Sujet", "text"],
]

export default function ContactPage() {
  const params = useParams()
  const locale = normalizeLocale(params.locale as string)
  const [sent, setSent] = useState(false)

  const mailto = useMemo(() => "mailto:contact@thunderfamgroup.com", [])

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSent(true)
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] dark:bg-[#1f2427] dark:text-[#f4f7fb]">
      <MarketingNav locale={locale} />
      <main>
        <section className="border-b border-[#DDE5E8] bg-white py-16 dark:border-[#3b4248] dark:bg-[#202528]">
          <div className="mx-auto grid max-w-7xl gap-12 px-4 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8">
            <div>
              <p className="text-sm font-bold uppercase tracking-wide text-[#0F766E]">
                Contact
              </p>
              <h1 className="mt-4 text-4xl font-bold tracking-normal sm:text-5xl">
                Parlons de votre projet TeducAI.
              </h1>
              <p className="mt-5 text-lg leading-8 text-[#475569] dark:text-[#c7d0da]">
                Notre équipe accompagne les écoles, centres de formation,
                universités et groupes multi-sites en Afrique, en Europe et au
                Royaume-Uni.
              </p>

              <div className="mt-8 space-y-5 text-sm leading-6 text-[#334155] dark:text-[#dce3eb]">
                <p className="flex gap-3">
                  <Building2 className="mt-1 h-5 w-5 text-[#0F766E]" />
                  THUNDERFAM GROUP LIMITED COTE D’IVOIRE, TGL-CI, créée le
                  29/05/2024, RCCM CI-ABJ-03-2024-B22-00006.
                </p>
                <p className="flex gap-3">
                  <MapPin className="mt-1 h-5 w-5 text-[#0F766E]" />
                  Abidjan Cocody, Boulevard de l’Université, 166 Logements,
                  près RTI, Bloc F3, Appartement.
                </p>
                <p className="flex gap-3">
                  <Phone className="mt-1 h-5 w-5 text-[#0F766E]" />
                  +225 05 00 78 23 04 / +225 07 08 53 47 84 / +44 736 270 3933
                </p>
                <p className="flex gap-3">
                  <Mail className="mt-1 h-5 w-5 text-[#0F766E]" />
                  contact@thunderfamgroup.com
                </p>
              </div>
            </div>

            <form
              onSubmit={handleSubmit}
              className="rounded-lg border border-[#DDE5E8] bg-[#F8FAFC] p-6 shadow-sm dark:border-[#56616a] dark:bg-[#252b30]"
            >
              <div className="grid gap-5 sm:grid-cols-2">
                {contactFields.map(([name, label, type]) => (
                  <div key={name} className="space-y-2">
                    <Label htmlFor={name} className="dark:text-white">{label}</Label>
                    <Input id={name} name={name} type={type} required className="dark:border-[#56616a] dark:bg-[#1f2427] dark:text-white" />
                  </div>
                ))}
              </div>
              <div className="mt-5 space-y-2">
                <Label htmlFor="message" className="dark:text-white">Message</Label>
                <Textarea id="message" name="message" rows={6} required className="dark:border-[#56616a] dark:bg-[#1f2427] dark:text-white" />
              </div>
              <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
                <Button type="submit" className="bg-[#0F766E] hover:bg-[#115E59]">
                  <Send className="h-4 w-4" />
                  Envoyer
                </Button>
                <Button asChild variant="outline" className="border-[#CBD5E1] dark:border-[#56616a] dark:bg-[#252b30] dark:text-white">
                  <a href={mailto}>Envoyer par email</a>
                </Button>
                {sent ? (
                  <p className="text-sm font-medium text-[#0F766E]">
                    Votre demande est prête. Notre équipe vous contactera rapidement.
                  </p>
                ) : null}
              </div>
            </form>
          </div>
        </section>
      </main>
      <MarketingFooter locale={locale} />
    </div>
  )
}
