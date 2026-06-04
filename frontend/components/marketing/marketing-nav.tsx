import Link from "next/link"
import { ArrowRight, LogIn } from "lucide-react"

import { Button } from "@/components/ui/button"
import { TeducAILogo } from "@/components/marketing/teducai-logo"

type MarketingNavProps = {
  locale: string
}

export function MarketingNav({ locale }: MarketingNavProps) {
  const links = [
    { href: `/${locale}`, label: "Accueil" },
    { href: `/${locale}#fonctionnalites`, label: "Fonctionnalités" },
    { href: `/${locale}/pricing`, label: "Tarification" },
    { href: `/${locale}/contact`, label: "Contact" },
  ]

  return (
    <header className="sticky top-0 z-40 border-b border-[#DDE5E8] bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href={`/${locale}`} aria-label="TeducAI Accueil">
          <TeducAILogo />
        </Link>
        <nav className="hidden items-center gap-7 text-sm font-medium text-[#334155] lg:flex">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className="hover:text-[#0F766E]">
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <Button asChild className="hidden bg-black text-white hover:bg-black/90 sm:inline-flex">
            <Link href={`/${locale}/contact`}>
              S&apos;enregistrer
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild variant="outline" className="border-[#CBD5E1] text-[#0F172A]">
            <Link href={`/${locale}/login`}>
              <LogIn className="h-4 w-4" />
              Se connecter
            </Link>
          </Button>
        </div>
      </div>
    </header>
  )
}
