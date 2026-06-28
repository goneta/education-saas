"use client"

import { Building2 } from "lucide-react"
import { useTranslations } from "next-intl"

import { useWorkingContext } from "@/contexts/working-context"

/**
 * Guards module pages that need an active working context. While the active
 * context is loading nothing is blocked; once resolved, if no institution /
 * model / academic year is active it renders a consistent prompt instead of the
 * module content. The message disappears automatically once a context is set
 * (the selector reloads the app after `setContext`).
 */
export function RequireContext({ children }: { children: React.ReactNode }) {
    const { active, ready } = useWorkingContext()
    const t = useTranslations("layout")

    if (!ready || active) return <>{children}</>

    return (
        <div className="flex min-h-[60vh] items-center justify-center p-6">
            <div className="max-w-md rounded-[20px] border border-[#e5e7eb] bg-white p-8 text-center shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#eef1f4] dark:bg-[#343b41]">
                    <Building2 className="h-6 w-6 text-[#111827] dark:text-white" />
                </div>
                <h2 className="mb-2 text-base font-semibold text-[#111827] dark:text-white">{t("contextRequiredTitle")}</h2>
                <p className="text-sm text-[#667085] dark:text-[#b6c0cb]">{t("contextRequiredMessage")}</p>
            </div>
        </div>
    )
}
