"use client"

import { Search } from "lucide-react"
import { cn } from "@/lib/utils"
import { UserMenu } from "@/components/layout/user-menu"

interface HeaderProps {
    isResizablePanel?: boolean;
}

export function Header({ isResizablePanel = false }: HeaderProps) {
    return (
        <header className={cn(
            "flex h-14 items-center gap-4 border-b border-[#E5E7EB] bg-white px-4 lg:h-[60px] lg:px-6",
            !isResizablePanel && "fixed top-0 right-0 left-0 md:left-64 z-20",
            isResizablePanel && "w-full"
        )}>
            <div className="w-full flex-1">
                <form>
                    <div className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <input
                            type="search"
                            placeholder="Search..."
                            className="w-full appearance-none bg-background pl-8 shadow-none md:w-2/3 lg:w-1/3 rounded-md border border-input px-3 py-1 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        />
                    </div>
                </form>
            </div>
            <UserMenu />
        </header>
    )
}
