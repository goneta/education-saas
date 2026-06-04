import { BarChart3, CheckCircle2, GraduationCap, ShieldCheck } from "lucide-react"

import { LoginForm } from "@/components/auth/login-form"
import { MarketingNav } from "@/components/marketing/marketing-nav"
import { normalizeLocale } from "@/lib/i18n"

export default async function LoginPage({
    params,
}: {
    params: Promise<{ locale: string }>
}) {
    const { locale: rawLocale } = await params
    const locale = normalizeLocale(rawLocale)

    return (
        <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A]">
            <MarketingNav locale={locale} />
            <main className="relative overflow-hidden">
                <div className="absolute inset-0 bg-[linear-gradient(#DDE5E8_1px,transparent_1px),linear-gradient(90deg,#DDE5E8_1px,transparent_1px)] bg-[size:56px_56px] opacity-45" />
                <section className="relative mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl items-center gap-10 px-4 py-10 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8">
                    <div className="max-w-2xl">
                        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#DDE5E8] bg-white px-4 py-2 text-sm font-semibold text-[#0F172A] shadow-sm">
                            <ShieldCheck className="h-4 w-4" />
                            Accès sécurisé TeducAI
                        </div>
                        <h1 className="text-4xl font-semibold leading-tight tracking-normal text-[#0F172A] sm:text-5xl">
                            Accédez à votre tableau de bord pour gérer vos établissements d&apos;enseignement et de formation.
                        </h1>
                        <p className="mt-6 text-lg leading-8 text-[#475569]">
                            Retrouvez vos élèves, finances, documents, rapports, notifications et workflows dans un espace unifié, sécurisé et adapté à chaque rôle.
                        </p>
                        <div className="mt-8 grid gap-3 sm:grid-cols-2">
                            {[
                                ["Pilotage complet", "Suivi académique, financier et administratif."],
                                ["Données protégées", "Accès limités par rôles et permissions."],
                                ["Multi-établissements", "Gestion séparée par école, pays et devise."],
                                ["Assistant IA", "Aide adaptée au profil de l'utilisateur."],
                            ].map(([title, text]) => (
                                <div key={title} className="rounded-[24px] border border-[#E2E8F0] bg-white/90 p-4 shadow-sm">
                                    <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-[#0F172A]">
                                        <CheckCircle2 className="h-4 w-4 text-[#0F766E]" />
                                        {title}
                                    </div>
                                    <p className="text-sm leading-6 text-[#64748B]">{text}</p>
                                </div>
                            ))}
                        </div>
                        <div className="mt-8 flex items-center gap-5 rounded-[28px] border border-[#E2E8F0] bg-white p-5 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
                            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-black text-white">
                                <GraduationCap className="h-7 w-7" />
                            </div>
                            <div>
                                <p className="text-sm font-semibold text-[#0F172A]">Plateforme éducative internationale</p>
                                <p className="text-sm text-[#64748B]">Afrique, Europe, Royaume-Uni, FCFA, GBP, EUR et USD.</p>
                            </div>
                            <BarChart3 className="ml-auto hidden h-8 w-8 text-[#0F766E] sm:block" />
                        </div>
                    </div>
                    <div className="flex justify-center lg:justify-end">
                        <LoginForm />
                    </div>
                </section>
            </main>
        </div>
    )
}
