"use client"

import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { LogOut, User } from "lucide-react"
import { useRouter } from "next/navigation"

export function UserMenu() {
    const { user, logout, isAuthenticated } = useAuth()
    const router = useRouter()

    if (!isAuthenticated || !user) {
        return null
    }

    const handleLogout = () => {
        logout()
        router.push("/en/login")
    }

    return (
        <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm text-[#111827]">
                <User className="h-4 w-4" />
                <span className="font-medium">{user.full_name}</span>
            </div>
            <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="h-8 text-[#6B7280] hover:text-[#111827] hover:bg-[#F0F1F3]"
            >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
            </Button>
        </div>
    )
}
