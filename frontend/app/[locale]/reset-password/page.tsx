"use client"

// SEC-05 — page ciblée par le lien envoyé par e-mail (?token=…). Le jeton est à
// usage unique et expire ; une réinitialisation réussie révoque toutes les
// sessions ouvertes avant elle (token_version côté serveur).

import { useState } from "react"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { API_BASE_URL } from "@/lib/config"
import { parseApiErrorResponse } from "@/lib/api-errors"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const RULES = "12 caractères minimum, avec au moins une majuscule, une minuscule, un chiffre et un caractère spécial."

export default function ResetPasswordPage() {
    const params = useParams()
    const router = useRouter()
    const searchParams = useSearchParams()
    const locale = (params?.locale as string) || "fr"
    const token = searchParams.get("token") || ""

    const [password, setPassword] = useState("")
    const [confirm, setConfirm] = useState("")
    const [error, setError] = useState("")
    const [done, setDone] = useState(false)
    const [loading, setLoading] = useState(false)

    const submit = async (event: React.FormEvent) => {
        event.preventDefault()
        setError("")
        if (password !== confirm) {
            setError("Les deux mots de passe ne correspondent pas.")
            return
        }
        setLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/auth/password/reset`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token, new_password: password }),
            })
            if (!response.ok) {
                setError((await parseApiErrorResponse(response, "Réinitialisation impossible.")).message)
                return
            }
            setDone(true)
            window.setTimeout(() => router.push(`/${locale}/login`), 2500)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="mx-auto flex min-h-screen max-w-md items-center px-4">
            <Card className="w-full">
                <CardHeader><CardTitle>Nouveau mot de passe</CardTitle></CardHeader>
                <CardContent>
                    {!token ? (
                        <div className="space-y-3">
                            <p className="text-sm text-red-800">Lien incomplet : le jeton de réinitialisation est absent.</p>
                            <a href={`/${locale}/forgot-password`} className="text-sm underline">Demander un nouveau lien</a>
                        </div>
                    ) : done ? (
                        <div className="space-y-3">
                            <p className="text-sm text-[#374151]">
                                Mot de passe réinitialisé. Toutes vos sessions ouvertes ont été déconnectées par
                                sécurité. Redirection vers la connexion…
                            </p>
                            <a href={`/${locale}/login`} className="text-sm underline">Se connecter maintenant</a>
                        </div>
                    ) : (
                        <form onSubmit={submit} className="space-y-4">
                            <p className="text-sm text-[#6B7280]">{RULES}</p>
                            {error && (
                                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>
                            )}
                            <div className="space-y-2">
                                <Label htmlFor="password">Nouveau mot de passe</Label>
                                <Input id="password" type="password" required value={password}
                                    onChange={event => setPassword(event.target.value)} />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="confirm">Confirmer</Label>
                                <Input id="confirm" type="password" required value={confirm}
                                    onChange={event => setConfirm(event.target.value)} />
                            </div>
                            <Button type="submit" disabled={loading || !password || !confirm}
                                className="w-full justify-center bg-black text-white hover:bg-black/90">
                                {loading ? "Enregistrement…" : "Réinitialiser"}
                            </Button>
                        </form>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
