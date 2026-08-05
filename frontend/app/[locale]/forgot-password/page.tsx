"use client"

// SEC-05 — demande de réinitialisation. La réponse du serveur est volontairement
// identique que l'adresse existe ou non (aucune énumération de comptes possible).

import { useState } from "react"
import { useParams } from "next/navigation"
import { API_BASE_URL } from "@/lib/config"
import { parseApiErrorResponse } from "@/lib/api-errors"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function ForgotPasswordPage() {
    const params = useParams()
    const locale = (params?.locale as string) || "fr"
    const [email, setEmail] = useState("")
    const [sent, setSent] = useState(false)
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(false)

    const submit = async (event: React.FormEvent) => {
        event.preventDefault()
        setLoading(true)
        setError("")
        try {
            const response = await fetch(`${API_BASE_URL}/auth/password/forgot`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email.trim(), language: locale }),
            })
            if (!response.ok) {
                // 503 = SMTP non configuré côté serveur : on le dit, on ne fait pas semblant.
                setError((await parseApiErrorResponse(response, "Demande impossible pour le moment.")).message)
                return
            }
            setSent(true)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="mx-auto flex min-h-screen max-w-md items-center px-4">
            <Card className="w-full">
                <CardHeader><CardTitle>Mot de passe oublié</CardTitle></CardHeader>
                <CardContent>
                    {sent ? (
                        <div className="space-y-4">
                            <p className="text-sm text-[#374151]">
                                Si un compte existe pour cette adresse, un lien de réinitialisation vient d&apos;être envoyé.
                                Vérifiez votre boîte de réception (et les indésirables). Le lien est valable 60 minutes.
                            </p>
                            <a href={`/${locale}/login`} className="text-sm underline">Retour à la connexion</a>
                        </div>
                    ) : (
                        <form onSubmit={submit} className="space-y-4">
                            <p className="text-sm text-[#6B7280]">
                                Saisissez l&apos;adresse e-mail de votre compte : nous vous enverrons un lien pour choisir
                                un nouveau mot de passe.
                            </p>
                            {error && (
                                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>
                            )}
                            <div className="space-y-2">
                                <Label htmlFor="email">Adresse e-mail</Label>
                                <Input id="email" type="email" required value={email}
                                    onChange={event => setEmail(event.target.value)} placeholder="vous@exemple.com" />
                            </div>
                            <Button type="submit" disabled={loading || !email.trim()}
                                className="w-full justify-center bg-black text-white hover:bg-black/90">
                                {loading ? "Envoi…" : "Envoyer le lien"}
                            </Button>
                            <a href={`/${locale}/login`} className="block text-center text-sm underline">Retour à la connexion</a>
                        </form>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
