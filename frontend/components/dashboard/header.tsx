"use client"

import { useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { Search } from "lucide-react"
import { cn } from "@/lib/utils"
import { LanguageSwitcher } from "@/components/layout/language-switcher"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"

interface HeaderProps {
    isResizablePanel?: boolean;
}

export function Header({ isResizablePanel = false }: HeaderProps) {
    const t = useTranslations("app")
    const { token, user } = useAuth()
    const [schoolName, setSchoolName] = useState("")

    useEffect(() => {
        if (!token || !user?.school_id) {
            setSchoolName("")
            return
        }
        setSchoolName(`Établissement #${user.school_id}`)
        let cancelled = false
        fetch(`${API_BASE_URL}/system/school-settings`, {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then(response => response.ok ? response.json() : null)
            .then(data => {
                if (!cancelled && data?.name) setSchoolName(data.name)
            })
            .catch(() => undefined)
        return () => {
            cancelled = true
        }
    }, [token, user?.school_id])

    return (
        <header className={cn(
            "sticky top-0 z-30 flex h-14 shrink-0 items-center gap-4 border-b border-[#E5E7EB] bg-white px-4 lg:h-[60px] lg:px-6",
            !isResizablePanel && "fixed top-0 right-0 left-0 md:left-64 z-20",
            isResizablePanel && "w-full"
        )}>
            <div className="flex min-w-0 flex-1 items-center gap-4">
                <form className="min-w-[180px] flex-1 md:max-w-sm">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <input
                            type="search"
                            placeholder={t("search")}
                            className="w-full appearance-none rounded-full border border-input bg-background px-3 py-1.5 pl-8 text-sm shadow-none ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        />
                    </div>
                </form>
                {schoolName && (
                    <div className="min-w-0 truncate text-[16px] font-bold text-black md:text-[18px]" title={schoolName}>
                        {schoolName}
                    </div>
                )}
            </div>
            <LanguageSwitcher />
        </header>
    )
}
