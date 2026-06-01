import { MarketingFooter } from "@/components/marketing/marketing-footer"
import { MarketingNav } from "@/components/marketing/marketing-nav"
import { normalizeLocale } from "@/lib/i18n"

export default async function TermsPage({
  params,
}: {
  params: Promise<{ locale: string }>
}) {
  const { locale: rawLocale } = await params
  const locale = normalizeLocale(rawLocale)

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A]">
      <MarketingNav locale={locale} />
      <main className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
        <p className="text-sm font-bold uppercase tracking-wide text-[#0F766E]">
          Conditions
        </p>
        <h1 className="mt-4 text-4xl font-bold tracking-normal">
          Conditions d’utilisation TeducAI
        </h1>
        <div className="mt-8 space-y-5 rounded-lg border border-[#DDE5E8] bg-white p-7 text-sm leading-7 text-[#475569] shadow-sm">
          <p>
            TeducAI est fourni aux établissements d’enseignement et de formation
            pour gérer leurs activités administratives, pédagogiques,
            financières et documentaires dans un cadre sécurisé.
          </p>
          <p>
            Chaque établissement reste responsable de la qualité des données
            saisies, de l’attribution des rôles utilisateurs et du respect des
            obligations locales applicables à son pays et à son secteur.
          </p>
          <p>
            L’accès à la plateforme peut être limité, suspendu ou adapté selon
            le plan souscrit, les règles de sécurité, les contraintes légales et
            les conditions contractuelles convenues avec Thunderfam Group.
          </p>
        </div>
      </main>
      <MarketingFooter locale={locale} />
    </div>
  )
}
