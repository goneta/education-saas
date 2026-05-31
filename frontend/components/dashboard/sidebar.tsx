"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useParams } from "next/navigation"
import { cn } from "@/lib/utils"
// We will replace these with Lucide icons later
import { Home, Users, Settings, BookOpen, GraduationCap, Calendar, ClipboardCheck, ChevronDown, CreditCard, BarChart3, MessageSquare } from "lucide-react"

interface SidebarProps {
    isResizablePanel?: boolean;
}

export function Sidebar({ isResizablePanel = false }: SidebarProps) {
    const pathname = usePathname()
    const params = useParams()
    const locale = params.locale as string

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
                { href: `/${locale}/dashboard`, label: "Overview", icon: Home },
            ]
        },
        {
            title: "Management",
            items: [
                { href: `/${locale}/dashboard/students`, label: "Students", icon: Users },
                { href: `/${locale}/dashboard/teachers`, label: "Teachers", icon: GraduationCap },
            ]
        },
        {
            title: "Academics",
            items: [
                { href: `/${locale}/dashboard/education/classes`, label: "Classes", icon: BookOpen },
                { href: `/${locale}/dashboard/education/subjects`, label: "Subjects", icon: BookOpen },
                { href: `/${locale}/dashboard/education/timetable`, label: "Timetable", icon: Calendar },
                { href: `/${locale}/dashboard/education/pedagogy`, label: "Pedagogy", icon: GraduationCap },
                { href: `/${locale}/dashboard/grades/assessments`, label: "Grades", icon: ClipboardCheck },
                { href: `/${locale}/dashboard/library`, label: "Library", icon: BookOpen },
                { href: `/${locale}/dashboard/portal`, label: "Parent / Student Portal", icon: Users },
            ]
        },
        {
            title: "Operations",
            items: [
                { href: `/${locale}/dashboard/operations`, label: "Operations", icon: Settings },
            ]
        },
        {
            title: "Finance",
            items: [
                { href: `/${locale}/dashboard/finance`, label: "Finance", icon: CreditCard },
                { href: `/${locale}/dashboard/finance/fees`, label: "Fees", icon: CreditCard },
                { href: `/${locale}/dashboard/finance/reports`, label: "Reports", icon: BarChart3 },
                { href: `/${locale}/dashboard/finance/cash-journal`, label: "Cash Journal", icon: ClipboardCheck },
                { href: `/${locale}/dashboard/finance/forecasts`, label: "Forecasts", icon: BarChart3 },
                { href: `/${locale}/dashboard/finance/settings`, label: "Fee Settings", icon: Settings },
                { href: `/${locale}/dashboard/finance/sms`, label: "SMS", icon: MessageSquare },
            ]
        },
        {
            title: "System",
            items: [
                { href: `/${locale}/dashboard/settings`, label: "Settings", icon: Settings },
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
