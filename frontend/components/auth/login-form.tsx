"use client"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { normalizeLocale } from "@/lib/i18n"
import { dashboardPathForUser } from "@/lib/auth-routing"

export function LoginForm() {
    const router = useRouter()
    const { login } = useAuth()
    const params = useParams()
    const locale = normalizeLocale(params.locale as string)
    const t = useTranslations("auth")
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [otpCode, setOtpCode] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [sessionMessage, setSessionMessage] = useState<string | null>(null)

    useEffect(() => {
        const message = sessionStorage.getItem("teducai_session_expired")
        if (message) {
            setSessionMessage(message)
            sessionStorage.removeItem("teducai_session_expired")
        }
    }, [])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)
        setIsLoading(true)

        try {
            const user = await login(email, password, otpCode)
            router.push(dashboardPathForUser(user, locale))
        } catch (err) {
            setError(err instanceof Error ? err.message : t("failed"))
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Card className="w-full max-w-md rounded-[32px] border border-[#E2E8F0] bg-white/95 shadow-[0_28px_90px_rgba(15,23,42,0.14)] backdrop-blur">
            <CardHeader>
                <CardTitle className="text-3xl font-semibold tracking-normal text-[#111827]">{t("login")}</CardTitle>
                <CardDescription className="text-[15px] leading-6 text-[#64748B]">
                    {t("description")}
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-5">
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                            {error}
                        </div>
                    )}
                    {sessionMessage && !error && (
                        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                            {sessionMessage}
                        </div>
                    )}

                    <div className="space-y-2">
                        <Label htmlFor="email">{t("email")}</Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="admin@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            disabled={isLoading}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="password">{t("password")}</Label>
                        <Input
                            id="password"
                            type="password"
                            placeholder={t("passwordPlaceholder")}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            disabled={isLoading}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="otp">Code MFA / 2FA</Label>
                        <Input
                            id="otp"
                            type="text"
                            inputMode="numeric"
                            placeholder="123456"
                            value={otpCode}
                            onChange={(e) => setOtpCode(e.target.value)}
                            disabled={isLoading}
                        />
                    </div>

                    <Button
                        type="submit"
                        className="w-full justify-center bg-black text-white hover:bg-black/90"
                        disabled={isLoading}
                    >
                        {isLoading ? t("submitting") : t("submit")}
                    </Button>
                </form>
            </CardContent>
        </Card>
    )
}
