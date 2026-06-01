"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { normalizeLocale } from "@/lib/i18n"
// We will replace these with Lucide icons later
import { Home, Users, Settings, BookOpen, GraduationCap, Calendar, ClipboardCheck, ChevronDown, CreditCard, BarChart3, MessageSquare } from "lucide-react"

interface SidebarProps {
    isResizablePanel?: boolean;
}

export function Sidebar({ isResizablePanel = false }: SidebarProps) {
    const pathname = usePathname()
    const params = useParams()
    const locale = normalizeLocale(params.locale as string)
    const t = useTranslations("navigation")

    // State to track open sections. Initially empty means all closed? 
    // Or maybe we want them open by default? 
    // User asked "section should open... reveals items", implying start closed.
    // Let's start with all CLOSED except maybe 'Overview' which has no title.
    const [openSections, setOpenSections] = useState<string[]>([])

    const toggleSection = (title: string) => {
        setOpenSections(prev =>
            prev.includes(title)
                ? prev.filter(t => t !== title)
                : [...prev, title]
        )
    }

    const sidebarSections = [
        {
            title: "",
            items: [
                { href: `/${locale}/dashboard`, label: t("overview"), icon: Home },
            ]
        },
        {
            title: t("management"),
            items: [
                { href: `/${locale}/dashboard/students`, label: t("students"), icon: Users },
                { href: `/${locale}/dashboard/teachers`, label: t("teachers"), icon: GraduationCap },
            ]
        },
        {
            title: t("academics"),
            items: [
                { href: `/${locale}/dashboard/education/classes`, label: t("classes"), icon: BookOpen },
                { href: `/${locale}/dashboard/education/subjects`, label: t("subjects"), icon: BookOpen },
                { href: `/${locale}/dashboard/education/timetable`, label: t("timetable"), icon: Calendar },
                { href: `/${locale}/dashboard/education/pedagogy`, label: t("pedagogy"), icon: GraduationCap },
                { href: `/${locale}/dashboard/grades/assessments`, label: t("grades"), icon: ClipboardCheck },
                { href: `/${locale}/dashboard/library`, label: t("library"), icon: BookOpen },
                { href: `/${locale}/dashboard/portal`, label: t("portal"), icon: Users },
            ]
        },
        {
            title: t("operations"),
            items: [
                { href: `/${locale}/dashboard/operations`, label: t("operations"), icon: Settings },
                { href: `/${locale}/dashboard/enterprise`, label: t("enterprise"), icon: BarChart3 },
            ]
        },
        {
            title: t("finance"),
            items: [
                { href: `/${locale}/dashboard/finance`, label: t("finance"), icon: CreditCard },
                { href: `/${locale}/dashboard/finance/fees`, label: t("fees"), icon: CreditCard },
                { href: `/${locale}/dashboard/finance/reports`, label: t("reports"), icon: BarChart3 },
                { href: `/${locale}/dashboard/finance/cash-journal`, label: t("cashJournal"), icon: ClipboardCheck },
                { href: `/${locale}/dashboard/finance/forecasts`, label: t("forecasts"), icon: BarChart3 },
                { href: `/${locale}/dashboard/finance/settings`, label: t("feeSettings"), icon: Settings },
                { href: `/${locale}/dashboard/finance/sms`, label: t("sms"), icon: MessageSquare },
            ]
        },
        {
            title: t("system"),
            items: [
                { href: `/${locale}/dashboard/settings`, label: t("settings"), icon: Settings },
            ]
        }
    ]

    return (
        <div className={cn(
            "hidden md:block w-64 h-full flex flex-col",
            !isResizablePanel && "fixed top-0 left-0 bottom-0 z-30",
            isResizablePanel && "w-full border-r-0"
        )}>
            <div className="flex h-14 items-center border-b border-[#E5E7EB] px-4 lg:h-[60px] lg:px-6">
                <Link href={`/${locale}`} className="flex items-center gap-2 font-semibold text-[#111827]">
                    <BookOpen className="h-6 w-6 text-primary" />
                    <span className="">EduSaas</span>
                </Link>
            </div>
            <div className="flex-1">
                <nav className="grid items-start px-2 text-sm font-medium lg:px-4 space-y-2 mt-4">
                    {sidebarSections.map((section, idx) => {
                        const isOpen = !section.title || openSections.includes(section.title)

                        return (
                            <div key={idx} className="mb-2">
                                {section.title ? (
                                    <button
                                        onClick={() => toggleSection(section.title)}
                                        className="flex w-full items-center justify-between px-4 py-2 hover:bg-gray-50 rounded-md transition-colors group"
                                    >
                                        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400 group-hover:text-gray-600">
                                            {section.title}
                                        </h4>
                                        <ChevronDown className={cn(
                                            "h-4 w-4 text-gray-400 transition-transform duration-200",
                                            isOpen ? "transform rotate-180" : ""
                                        )} />
                                    </button>
                                ) : (
                                    // For items without a section title (Overview), strictly wrap? 
                                    // Actually the design usually just lists them.
                                    // But we need to maintain the loop structure.
                                    null
                                )}

                                <div className={cn(
                                    "grid transition-all duration-300 ease-in-out",
                                    isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                                )}>
                                    <div className="overflow-hidden">
                                        <div className="space-y-1 mt-1">
                                            {section.items.map((item) => {
                                                const Icon = item.icon
                                                const isActive = pathname === item.href || (item.href !== `/${locale}/dashboard` && pathname?.startsWith(item.href))
                                                return (
                                                    <Link
                                                        key={item.href}
                                                        href={item.href}
                                                        className={cn(
                                                            "flex items-center gap-3 rounded-lg px-3 py-2 transition-all",
                                                            isActive
                                                                ? "bg-[#F0F1F3] text-[#111827] font-medium"
                                                                : "text-[#6B7280] hover:text-[#111827]"
                                                        )}
                                                    >
                                                        <Icon className="h-4 w-4" />
                                                        {item.label}
                                                    </Link>
                                                )
                                            })}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </nav>
            </div>
        </div>
    )
}
