"use client"

import Link from "next/link"
import { LayoutDashboard, LogOut } from "lucide-react"
import { useRouter } from "next/navigation"

import { Button } from "@/components/ui/button"
import { TeducAILogo } from "@/components/marketing/teducai-logo"
import { useAuth } from "@/contexts/auth-context"
import { dashboardPathForUser } from "@/lib/auth-routing"

type MarketingNavProps = {
  locale: string
}

export function MarketingNav({ locale }: MarketingNavProps) {
  const router = useRouter()
  const { isAuthenticated, isLoading, logout, user } = useAuth()
  const links = [
    { href: `/${locale}`, label: "Accueil" },
    { href: `/${locale}/emploi`, label: "Emploi" },
    { href: `/${locale}#fonctionnalites`, label: "Fonctionnalités" },
    { href: `/${locale}/pricing`, label: "Tarification" },
    { href: `/${locale}/contact`, label: "Contact" },
  ]

  const handleLogout = () => {
    logout()
    router.push(`/${locale}/login`)
  }

  return (
    <header className="sticky top-0 z-40 border-b border-[#DDE5E8] bg-white/95 backdrop-blur dark:border-[#3b4248] dark:bg-[#111827]/95">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href={`/${locale}`} aria-label="TeducAI Accueil">
          <TeducAILogo />
        </Link>
        <nav className="hidden items-center gap-7 text-sm font-medium text-[#334155] dark:text-white lg:flex">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className="hover:text-[#0F766E] dark:hover:text-white">
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {isAuthenticated && !isLoading ? (
            <>
              <Button asChild className="hidden bg-black text-white hover:bg-black/90 dark:bg-white dark:text-black dark:hover:bg-white/90 sm:inline-flex">
                <Link href={dashboardPathForUser(user, locale)}>
                  <LayoutDashboard className="h-4 w-4" />
                  Dashboard
                </Link>
              </Button>
              <Button type="button" variant="outline" className="border-[#CBD5E1] bg-white text-[#0F172A] dark:border-[#56616a] dark:bg-[#252b30] dark:text-white" onClick={handleLogout}>
                <LogOut className="h-4 w-4" />
                Déconnexion
              </Button>
            </>
          ) : (
            <>
              <Button asChild className="hidden bg-black text-white hover:bg-black/90 dark:bg-white dark:text-black dark:hover:bg-white/90 sm:inline-flex">
                <Link href={`/${locale}/contact`}>
                  S&apos;enregistrer
                </Link>
              </Button>
              <Button asChild variant="outline" className="border-[#CBD5E1] bg-white text-[#0F172A] dark:border-[#56616a] dark:bg-[#252b30] dark:text-white">
                <Link href={`/${locale}/login`}>
                  Se connecter
                </Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
