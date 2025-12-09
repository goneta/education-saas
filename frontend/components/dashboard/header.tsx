"use client"

import Link from "next/link"
import { Menu, Search, CircleUser } from "lucide-react"
import { cn } from "@/lib/utils"

interface HeaderProps {
    isResizablePanel?: boolean;
}

export function Header({ isResizablePanel = false }: HeaderProps) {
    return (
        <header className={cn(
            "flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6 bg-background",
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
            <button className="rounded-full border border-input w-8 h-8 flex items-center justify-center">
                <CircleUser className="h-5 w-5" />
                <span className="sr-only">Toggle user menu</span>
            </button>
        </header>
    )
}
