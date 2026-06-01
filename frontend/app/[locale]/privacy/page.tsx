import { MarketingFooter } from "@/components/marketing/marketing-footer"
import { MarketingNav } from "@/components/marketing/marketing-nav"
import { normalizeLocale } from "@/lib/i18n"

export default async function PrivacyPage({
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
          Confidentialité
        </p>
        <h1 className="mt-4 text-4xl font-bold tracking-normal">
          Politique de confidentialité TeducAI
        </h1>
        <div className="mt-8 space-y-5 rounded-lg border border-[#DDE5E8] bg-white p-7 text-sm leading-7 text-[#475569] shadow-sm">
          <p>
            TeducAI protège les données des établissements, élèves, étudiants,
            parents, enseignants et personnels selon les principes de
            confidentialité, de sécurité, de minimisation et de traçabilité.
          </p>
          <p>
            Les données sont utilisées pour fournir les services de gestion
            administrative, académique, financière, documentaire et de
            communication demandés par l’établissement.
          </p>
          <p>
            Les administrateurs autorisés peuvent configurer les accès, les
            durées de conservation, les exports et les demandes liées aux droits
            des personnes conformément aux réglementations applicables.
          </p>
        </div>
      </main>
      <MarketingFooter locale={locale} />
    </div>
  )
}
