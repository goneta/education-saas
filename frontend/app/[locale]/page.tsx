import Link from "next/link"
import {
  ArrowRight,
  Banknote,
  BrainCircuit,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  GraduationCap,
  LineChart,
  MessageCircle,
  School,
  ShieldCheck,
  Users,
} from "lucide-react"

import { MarketingFooter } from "@/components/marketing/marketing-footer"
import { MarketingNav } from "@/components/marketing/marketing-nav"
import { Button } from "@/components/ui/button"
import { normalizeLocale } from "@/lib/i18n"

const institutions = [
  "Écoles primaires",
  "Collèges et lycées",
  "Formation professionnelle",
  "Établissements techniques",
  "Universités et grandes écoles",
  "Instituts de recherche",
  "Formation continue",
  "Organismes de certification",
]

const features = [
  {
    icon: Users,
    title: "Gestion élèves / étudiants",
    text: "Inscription en ligne, dossiers numériques, classes, filières, niveaux et suivi administratif centralisé.",
    benefit: "Chaque service travaille sur une fiche fiable, à jour et exploitable.",
  },
  {
    icon: CalendarDays,
    title: "Gestion académique",
    text: "Emplois du temps, présences, notes, bulletins, examens, moyennes automatiques et suivi pédagogique.",
    benefit: "Les équipes réduisent la ressaisie et gardent une vision claire des performances.",
  },
  {
    icon: MessageCircle,
    title: "Portail Parents",
    text: "Notes, absences, paiements, documents et communication école-famille dans un espace sécurisé.",
    benefit: "Les familles sont mieux informées et les demandes sont tracées.",
  },
  {
    icon: Banknote,
    title: "Gestion financière",
    text: "Facturation, paiements, reçus, caisse, comptabilité, rapports financiers et suivi des impayés.",
    benefit: "La direction pilote les encaissements, les soldes et les écarts sans confusion.",
  },
  {
    icon: BrainCircuit,
    title: "IA TeducAI",
    text: "Assistant IA, rapports, analyses prédictives, aide administrative et recommandations opérationnelles.",
    benefit: "Les équipes gagnent du temps sur les tâches répétitives et les décisions de gestion.",
  },
]

const dashboardRows = [
  ["Inscriptions", "1 284", "+18%"],
  ["Présences", "96,4%", "Stable"],
  ["Recettes FCFA", "42,8M", "+12%"],
]

const trustHighlights = [
  {
    icon: School,
    title: "Multi-établissements",
    text: "Séparation stricte des données, secteurs, pays, devises et langues par établissement.",
  },
  {
    icon: ClipboardCheck,
    title: "Documents et conformité",
    text: "Reçus, attestations, bulletins, audits et exports adaptés aux usages locaux.",
  },
  {
    icon: GraduationCap,
    title: "Tous niveaux d’enseignement",
    text: "Primaire, secondaire, technique, professionnel, universitaire et formation continue.",
  },
]

export default async function Home({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale: rawLocale } = await params
  const locale = normalizeLocale(rawLocale)

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A]">
      <MarketingNav locale={locale} />

      <main>
        <section className="relative overflow-hidden border-b border-[#DDE5E8] bg-[#F8FAFC]">
          <div className="absolute inset-0 bg-[linear-gradient(#DDE5E8_1px,transparent_1px),linear-gradient(90deg,#DDE5E8_1px,transparent_1px)] bg-[size:56px_56px] opacity-45" />
          <div className="relative mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl items-center gap-12 px-4 py-14 sm:px-6 lg:grid-cols-[1fr_0.92fr] lg:px-8">
            <div className="max-w-3xl">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#99F6E4] bg-white px-4 py-2 text-sm font-semibold text-[#0F766E] shadow-sm">
                <ShieldCheck className="h-4 w-4" />
                SaaS multi-établissements, sécurisé et international
              </div>
              <h1 className="max-w-4xl text-4xl font-bold leading-tight tracking-normal text-[#0F172A] sm:text-5xl lg:text-6xl">
                TeducAI – La Plateforme Intelligente de Gestion des
                Établissements d’Enseignement et de Formation
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-[#475569]">
                Automatisez la gestion administrative, académique et financière
                de votre établissement grâce à l’Intelligence Artificielle.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button asChild size="lg" className="bg-[#0F766E] hover:bg-[#115E59]">
                  <Link href={`/${locale}/contact`}>
                    Essayer Gratuitement
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild size="lg" variant="outline" className="border-[#94A3B8] bg-white">
                  <Link href={`/${locale}/contact`}>Demander une Démonstration</Link>
                </Button>
              </div>
            </div>

            <div className="relative">
              <div className="rounded-[2rem] border border-[#CBD5E1] bg-white p-4 shadow-2xl shadow-slate-300/50">
                <div className="rounded-[1.5rem] border border-[#E2E8F0] bg-[#0F172A] p-5 text-white">
                  <div className="flex items-center justify-between border-b border-white/10 pb-4">
                    <div>
                      <p className="text-sm text-[#99F6E4]">Console TeducAI</p>
                      <p className="text-lg font-semibold">Direction générale</p>
                    </div>
                    <BrainCircuit className="h-8 w-8 text-[#5EEAD4]" />
                  </div>
                  <div className="grid gap-4 py-5 sm:grid-cols-3">
                    {dashboardRows.map(([label, value, trend]) => (
                      <div key={label} className="rounded-xl border border-white/10 bg-white/[0.08] p-4">
                        <p className="text-xs text-[#CBD5E1]">{label}</p>
                        <p className="mt-2 text-2xl font-bold">{value}</p>
                        <p className="mt-1 text-xs text-[#99F6E4]">{trend}</p>
                      </div>
                    ))}
                  </div>
                  <div className="grid gap-4 lg:grid-cols-[1fr_0.8fr]">
                    <div className="rounded-xl bg-white p-4 text-[#0F172A]">
                      <div className="mb-4 flex items-center justify-between">
                        <p className="font-semibold">Flux académique</p>
                        <LineChart className="h-5 w-5 text-[#0F766E]" />
                      </div>
                      <div className="space-y-3">
                        {["Notes validées", "Absences signalées", "Bulletins prêts"].map((item, index) => (
                          <div key={item} className="flex items-center gap-3">
                            <div className="h-2.5 w-2.5 rounded-full bg-[#14B8A6]" />
                            <div className="h-2 flex-1 rounded-full bg-[#E2E8F0]">
                              <div
                                className="h-2 rounded-full bg-[#0F766E]"
                                style={{ width: `${82 - index * 14}%` }}
                              />
                            </div>
                            <span className="w-24 text-xs text-[#475569]">{item}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="rounded-xl border border-white/10 bg-[#134E4A] p-4">
                      <p className="text-sm font-semibold text-[#CCFBF1]">Assistant IA</p>
                      <p className="mt-3 text-sm leading-6 text-[#ECFEFF]">
                        24 alertes traitées, 8 recommandations finance et 5
                        rapports prêts pour la direction.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-white py-8">
          <div className="mx-auto flex max-w-7xl flex-wrap gap-3 px-4 sm:px-6 lg:px-8">
            {institutions.map((item) => (
              <span
                key={item}
                className="rounded-full border border-[#CBD5E1] bg-[#F8FAFC] px-4 py-2 text-sm font-medium text-[#334155]"
              >
                {item}
              </span>
            ))}
          </div>
        </section>

        <section id="fonctionnalites" className="bg-[#F1F5F9] py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl">
              <p className="text-sm font-bold uppercase tracking-wide text-[#0F766E]">
                Fonctionnalités
              </p>
              <h2 className="mt-3 text-3xl font-bold tracking-normal text-[#0F172A] sm:text-4xl">
                Une plateforme complète pour gérer l’administration, la
                pédagogie, la finance et la relation avec les familles.
              </h2>
            </div>
            <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {features.map((feature) => {
                const Icon = feature.icon
                return (
                  <article key={feature.title} className="rounded-lg border border-[#DDE5E8] bg-white p-6 shadow-sm">
                    <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#CCFBF1] text-[#0F766E]">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h3 className="mt-5 text-xl font-semibold text-[#0F172A]">{feature.title}</h3>
                    <p className="mt-3 text-sm leading-6 text-[#475569]">{feature.text}</p>
                    <p className="mt-4 flex gap-2 text-sm font-medium text-[#0F766E]">
                      <CheckCircle2 className="mt-0.5 h-4 w-4" />
                      {feature.benefit}
                    </p>
                  </article>
                )
              })}
            </div>
          </div>
        </section>

        <section className="bg-white py-20">
          <div className="mx-auto grid max-w-7xl gap-10 px-4 sm:px-6 lg:grid-cols-3 lg:px-8">
            {trustHighlights.map((highlight) => {
              const FeatureIcon = highlight.icon
              return (
                <div key={highlight.title} className="border-l-4 border-[#0F766E] pl-5">
                  <FeatureIcon className="h-7 w-7 text-[#0F766E]" />
                  <h3 className="mt-4 text-xl font-semibold">{highlight.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-[#475569]">{highlight.text}</p>
                </div>
              )
            })}
          </div>
        </section>
      </main>

      <MarketingFooter locale={locale} />
    </div>
  )
}
