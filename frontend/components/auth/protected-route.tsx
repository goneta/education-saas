"use client"

import { useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, isLoading } = useAuth()
    const router = useRouter()
    const params = useParams()
    const locale = normalizeLocale(params.locale as string)
    const t = useTranslations("app")

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.push(`/${locale}/login`)
        }
    }, [isAuthenticated, isLoading, locale, router])

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-[#6B7280]">{t("loading")}</div>
            </div>
        )
    }

    if (!isAuthenticated) {
        return null
    }

    return <>{children}</>
}
