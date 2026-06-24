"use client"

import { useEffect } from "react"
import { useParams, usePathname, useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"
import { canAccessDashboardPath, dashboardPathForUser } from "@/lib/auth-routing"

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, isLoading, user } = useAuth()
    const router = useRouter()
    const pathname = usePathname()
    const params = useParams()
    const locale = normalizeLocale(params.locale as string)
    const t = useTranslations("app")

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.push(`/${locale}/login`)
            return
        }
        if (!isLoading && isAuthenticated && !canAccessDashboardPath(user, pathname, locale)) {
            router.replace(dashboardPathForUser(user, locale))
        }
    }, [isAuthenticated, isLoading, locale, pathname, router, user])

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-[#6B7280]">{t("loading")}</div>
            </div>
        )
    }

    if (!isAuthenticated || !canAccessDashboardPath(user, pathname, locale)) {
        return null
    }

    return <>{children}</>
}
