"use client"

import { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { useTranslations } from "next-intl"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { normalizeLocale } from "@/lib/i18n"

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

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)
        setIsLoading(true)

        try {
            await login(email, password, otpCode)
            // Redirect to dashboard on success
            router.push(`/${locale}/dashboard`)
        } catch (err) {
            setError(err instanceof Error ? err.message : t("failed"))
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Card className="w-full max-w-md rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
            <CardHeader>
                <CardTitle className="text-2xl text-[#111827]">{t("login")}</CardTitle>
                <CardDescription className="text-[#6B7280]">
                    {t("description")}
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                            {error}
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
                        <Label htmlFor="otp">MFA / 2FA code</Label>
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
                        className="w-full bg-black text-white hover:bg-black/90 rounded-lg"
                        disabled={isLoading}
                    >
                        {isLoading ? t("submitting") : t("submit")}
                    </Button>
                </form>
            </CardContent>
        </Card>
    )
}
