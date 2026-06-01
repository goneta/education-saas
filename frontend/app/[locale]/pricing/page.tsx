import Link from "next/link"
import { CheckCircle2, Star } from "lucide-react"

import { MarketingFooter } from "@/components/marketing/marketing-footer"
import { MarketingNav } from "@/components/marketing/marketing-nav"
import { Button } from "@/components/ui/button"
import { normalizeLocale } from "@/lib/i18n"

const plans = [
  {
    name: "Free",
    price: "0 FCFA",
    description: "Pour découvrir TeducAI avec une petite équipe pilote.",
    features: [
      "1 établissement",
      "Jusqu’à 50 élèves / étudiants",
      "Dossiers numériques de base",
      "Tableau de bord essentiel",
      "Support communautaire",
    ],
  },
  {
    name: "Pro",
    price: "À définir",
    description: "Pour les écoles, centres et établissements en croissance.",
    highlighted: true,
    features: [
      "Multi-classes, filières et niveaux",
      "Paiements, reçus et rapports financiers",
      "Portails parent, élève et professeur",
      "Notifications SMS / email / WhatsApp",
      "Assistance prioritaire",
    ],
  },
  {
    name: "Max",
    price: "À définir",
    description: "Pour les groupes scolaires, universités et réseaux multi-sites.",
    features: [
      "Multi-établissements et multi-pays",
      "Comptabilité, RH, transport et cantine",
      "Exports officiels et conformité avancée",
      "IA TeducAI et analytique direction",
      "Accompagnement dédié",
    ],
  },
]

export default async function PricingPage({
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
        <section className="border-b border-[#DDE5E8] bg-white py-20">
          <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
            <p className="text-sm font-bold uppercase tracking-wide text-[#0F766E]">
              Tarification
            </p>
            <h1 className="mt-4 text-4xl font-bold tracking-normal sm:text-5xl">
              Choisissez le plan TeducAI adapté à votre établissement.
            </h1>
            <p className="mt-5 text-lg leading-8 text-[#475569]">
              Les offres Pro et Max sont configurées selon le pays, la taille,
              les modules activés, les volumes SMS et le niveau
              d’accompagnement souhaité.
            </p>
          </div>
        </section>

        <section className="py-16">
          <div className="mx-auto grid max-w-7xl gap-6 px-4 sm:px-6 lg:grid-cols-3 lg:px-8">
            {plans.map((plan) => (
              <article
                key={plan.name}
                className={`relative rounded-lg border bg-white p-7 shadow-sm ${
                  plan.highlighted
                    ? "border-[#0F766E] ring-2 ring-[#99F6E4]"
                    : "border-[#DDE5E8]"
                }`}
              >
                {plan.highlighted ? (
                  <div className="absolute right-5 top-5 flex items-center gap-1 rounded-full bg-[#CCFBF1] px-3 py-1 text-xs font-bold text-[#0F766E]">
                    <Star className="h-3.5 w-3.5" />
                    Recommandé
                  </div>
                ) : null}
                <h2 className="text-2xl font-bold">{plan.name}</h2>
                <p className="mt-3 text-sm leading-6 text-[#475569]">{plan.description}</p>
                <p className="mt-6 text-3xl font-bold text-[#0F766E]">{plan.price}</p>
                <div className="mt-7 space-y-3">
                  {plan.features.map((feature) => (
                    <p key={feature} className="flex gap-2 text-sm text-[#334155]">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 text-[#0F766E]" />
                      {feature}
                    </p>
                  ))}
                </div>
                <Button asChild className="mt-8 w-full bg-[#0F766E] hover:bg-[#115E59]">
                  <Link href={`/${locale}/contact`}>Souscrire</Link>
                </Button>
              </article>
            ))}
          </div>
        </section>
      </main>
      <MarketingFooter locale={locale} />
    </div>
  )
}
