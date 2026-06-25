import Link from "next/link"
import { CheckCircle2, Star } from "lucide-react"

import { MarketingFooter } from "@/components/marketing/marketing-footer"
import { MarketingNav } from "@/components/marketing/marketing-nav"
import { Button } from "@/components/ui/button"
import { normalizeLocale } from "@/lib/i18n"

const plans = [
  {
    name: "Free",
    slug: "free",
    price: "0 FCFA",
    description: "Pour découvrir TeducAI avec une petite équipe pilote.",
    features: [
      "1 établissement",
      "Jusqu'à 50 élèves / étudiants",
      "Dossiers numériques de base",
      "Tableau de bord essentiel",
      "Support communautaire",
    ],
  },
  {
    name: "Pro",
    slug: "pro",
    billingOptions: ["99 000 FCFA / Mois", "900 000 FCFA / An"],
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
    slug: "max",
    billingOptions: ["199 000 FCFA / Mois", "1 700 000 FCFA / An"],
    description: "Pour les groupes scolaires, universités et réseaux avancés.",
    features: [
      "Tous les outils inclus dans le Plan PRO",
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
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] dark:bg-[#1f2427] dark:text-[#f4f7fb]">
      <MarketingNav locale={locale} />
      <main>
        <section className="border-b border-[#DDE5E8] bg-white py-20 dark:border-[#3b4248] dark:bg-[#202528]">
          <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
            <p className="text-sm font-bold uppercase tracking-normal text-[#0F766E]">
              Tarification
            </p>
            <h1 className="mt-4 text-4xl font-bold tracking-normal sm:text-5xl">
              Choisissez le plan TeducAI adapté à votre établissement.
            </h1>
            <p className="mt-5 text-lg leading-8 text-[#475569] dark:text-[#c7d0da]">
              Les offres Pro et Max sont configurées selon le pays, la taille,
              les modules activés, les volumes de notification et le niveau
              d&apos;accompagnement souhaité.
            </p>
          </div>
        </section>

        <section className="py-16">
          <div className="mx-auto grid max-w-7xl gap-6 px-4 sm:px-6 lg:grid-cols-3 lg:px-8">
            {plans.map((plan) => (
              <article
                key={plan.name}
                className={`relative rounded-[22px] border bg-white p-7 shadow-sm dark:bg-[#252b30] ${
                  plan.highlighted
                    ? "border-[#0F766E] ring-2 ring-[#99F6E4] dark:ring-[#0F766E]"
                    : "border-[#DDE5E8] dark:border-[#56616a]"
                }`}
              >
                {plan.highlighted ? (
                  <div className="absolute right-5 top-5 flex items-center gap-1 rounded-full bg-[#CCFBF1] px-3 py-1 text-xs font-bold text-[#0F766E]">
                    <Star className="h-3.5 w-3.5" />
                    Recommandé
                  </div>
                ) : null}
                <h2 className="text-2xl font-bold">{plan.name}</h2>
                <p className="mt-3 text-sm leading-6 text-[#475569] dark:text-[#c7d0da]">{plan.description}</p>
                {plan.billingOptions ? (
                  <fieldset className="mt-6 space-y-3">
                    <legend className="sr-only">Choix de facturation {plan.name}</legend>
                    {plan.billingOptions.map((option, index) => (
                      <label key={option} className="flex items-center gap-3 rounded-[16px] border border-[#DDE5E8] px-4 py-3 text-sm font-semibold text-[#0F172A] dark:border-[#56616a] dark:text-white">
                        <input
                          type="radio"
                          name={`billing-${plan.slug}`}
                          value={option}
                          defaultChecked={index === 0}
                          className="h-4 w-4 accent-black"
                        />
                        {option}
                      </label>
                    ))}
                  </fieldset>
                ) : (
                  <p className="mt-6 text-3xl font-bold text-[#0F766E]">{plan.price}</p>
                )}
                <div className="mt-7 space-y-3">
                  {plan.features.map((feature) => (
                    <p key={feature} className="flex gap-2 text-sm text-[#334155] dark:text-[#dce3eb]">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 text-[#0F766E]" />
                      {feature}
                    </p>
                  ))}
                </div>
                <Button asChild className="mt-8 w-full bg-black hover:bg-black/90">
                  <Link href={`/${locale}/contact?plan=${plan.slug}`}>Souscrire</Link>
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
