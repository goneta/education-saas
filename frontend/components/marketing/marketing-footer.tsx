import Link from "next/link"
import { Building2, Mail, MapPin, Phone } from "lucide-react"

import { TeducAILogo } from "@/components/marketing/teducai-logo"

type MarketingFooterProps = {
  locale: string
}

export function MarketingFooter({ locale }: MarketingFooterProps) {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="border-t border-[#DDE5E8] bg-[#0F172A] text-white">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.2fr_0.8fr_1fr_1fr] lg:px-8">
        <div className="space-y-4">
          <TeducAILogo
            showTagline
            className="[&_p]:text-white"
            markClassName="bg-[#14B8A6]"
          />
          <p className="max-w-sm text-sm leading-6 text-[#CBD5E1]">
            Plateforme SaaS intelligente pour piloter les établissements
            scolaires, techniques, professionnels et universitaires.
          </p>
          <p className="text-sm text-[#94A3B8]">Powered by Thunderfam Group.</p>
        </div>

        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-[#99F6E4]">
            Liens rapides
          </h2>
          <div className="mt-4 grid gap-3 text-sm text-[#CBD5E1]">
            <Link href={`/${locale}`}>Accueil</Link>
            <Link href={`/${locale}#fonctionnalites`}>Fonctionnalités</Link>
            <Link href={`/${locale}/pricing`}>Tarification</Link>
            <Link href={`/${locale}/contact`}>Contact</Link>
            <Link href={`/${locale}/privacy`}>Politique de confidentialité</Link>
            <Link href={`/${locale}/terms`}>Conditions d’utilisation</Link>
          </div>
        </div>

        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-[#99F6E4]">
            Côte d’Ivoire
          </h2>
          <div className="mt-4 space-y-3 text-sm leading-6 text-[#CBD5E1]">
            <p className="flex gap-2">
              <Building2 className="mt-1 h-4 w-4 text-[#5EEAD4]" />
              <span>
                THUNDERFAM GROUP LIMITED COTE D’IVOIRE, TGL-CI
                <br />
                RCCM CI-ABJ-03-2024-B22-00006
              </span>
            </p>
            <p className="flex gap-2">
              <MapPin className="mt-1 h-4 w-4 text-[#5EEAD4]" />
              <span>
                Abidjan Cocody, Boulevard de l’Université, 166 Logements,
                près RTI, Bloc F3, Appartement.
              </span>
            </p>
            <p className="flex gap-2">
              <Phone className="mt-1 h-4 w-4 text-[#5EEAD4]" />
              <span>+225 05 00 78 23 04 / +225 07 08 53 47 84</span>
            </p>
          </div>
        </div>

        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-[#99F6E4]">
            Royaume-Uni
          </h2>
          <div className="mt-4 space-y-3 text-sm leading-6 text-[#CBD5E1]">
            <p className="flex gap-2">
              <Building2 className="mt-1 h-4 w-4 text-[#5EEAD4]" />
              <span>
                THUNDERFAM GROUP LTD UK
                <br />
                Company Number 11341841
              </span>
            </p>
            <p className="flex gap-2">
              <MapPin className="mt-1 h-4 w-4 text-[#5EEAD4]" />
              <span>
                152 Tower Road, Tividale, Oldbury, West Midlands, United
                Kingdom, B69 1PE.
              </span>
            </p>
            <p className="flex gap-2">
              <Phone className="mt-1 h-4 w-4 text-[#5EEAD4]" />
              <span>+44 736 270 3933</span>
            </p>
            <p className="flex gap-2">
              <Mail className="mt-1 h-4 w-4 text-[#5EEAD4]" />
              <span>contact@thunderfamgroup.com</span>
            </p>
          </div>
        </div>
      </div>
      <div className="border-t border-white/10 px-4 py-5 text-center text-sm text-[#94A3B8]">
        © {currentYear} TeducAI. Tous droits réservés.
      </div>
    </footer>
  )
}
