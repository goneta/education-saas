"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
// We will replace these with Lucide icons later
import { Home, Users, Settings, BookOpen, GraduationCap } from "lucide-react"

const sidebarItems = [
    { href: "/dashboard", label: "Overview", icon: Home },
    { href: "/dashboard/students", label: "Students", icon: Users },
    { href: "/dashboard/courses", label: "Courses", icon: BookOpen },
    { href: "/dashboard/grades", label: "Grades", icon: GraduationCap },
    { href: "/dashboard/settings", label: "Settings", icon: Settings },
]

interface SidebarProps {
    isResizablePanel?: boolean;
}

export function Sidebar({ isResizablePanel = false }: SidebarProps) {
    const pathname = usePathname()

    return (
        <div className={cn(
            "hidden border-r bg-muted/40 md:block w-64 h-full flex flex-col",
            !isResizablePanel && "fixed top-0 left-0 bottom-0 z-30",
            isResizablePanel && "w-full border-r-0"
        )}>
            <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
                <Link href="/" className="flex items-center gap-2 font-semibold">
                    <BookOpen className="h-6 w-6 text-primary" />
                    <span className="">EduSaas</span>
                </Link>
            </div>
            <div className="flex-1">
                <nav className="grid items-start px-2 text-sm font-medium lg:px-4 space-y-2 mt-4">
                    {sidebarItems.map((item) => {
                        const Icon = item.icon
                        // Simple basic checking, assumes /dashboard is prefix
                        // We can refine active state logic later
                        const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href))

                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={cn(
                                    "flex items-center gap-3 rounded-lg px-3 py-2 transition-all hover:text-primary",
                                    isActive
                                        ? "bg-muted text-primary"
                                        : "text-muted-foreground"
                                )}
                            >
                                <Icon className="h-4 w-4" />
                                {item.label}
                            </Link>
                        )
                    })}
                </nav>
            </div>
        </div>
    )
}
