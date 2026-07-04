"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { BadgeCheck, FileCheck2, FileSignature, FileText, Printer, Receipt, RefreshCw } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface Child { student_id: number; full_name?: string | null; registration_number?: string | null }
interface PaymentRow { payment_id: number; fee_title?: string | null; amount: number; payment_date?: string | null; method?: string | null; receipt_number?: string | null }
interface SignatureInfo { id: number; signer_name?: string | null; signer_role?: string | null; signed_at?: string | null; code: string; valid: boolean; tampered: boolean }
interface DocRow { id: number; reference: string; doc_type?: string | null; title?: string | null; created_at: string; payload?: DocPayload | null; signatures?: SignatureInfo[] }
interface DocPayload {
    reference: string
    doc_type: string
    issued_at?: string
    school?: { name?: string | null; address?: string | null; phone?: string | null; email?: string | null; logo_url?: string | null }
    student?: { full_name?: string | null; registration_number?: string | null; date_of_birth?: string | null; gender?: string | null }
    enrollment?: { class_name?: string | null; level?: string | null; academic_year?: string | null }
    payment?: { fee_title?: string | null; amount?: number; method?: string | null; payment_date?: string | null; receipt_number?: string | null; fee_amount?: number; outstanding_after?: number }
}

function printDocument(payload: DocPayload, bodyText: string, verifyHint: string, signatures: SignatureInfo[] = [], signedByLabel = "") {
    const win = window.open("", "_blank", "width=820,height=1000")
    if (!win) return
    const s = payload.student || {}
    const sc = payload.school || {}
    const en = payload.enrollment || {}
    const pay = payload.payment
    const issued = payload.issued_at ? new Date(payload.issued_at).toLocaleDateString() : ""
    const paymentBlock = pay ? `
        <table style="width:100%;border-collapse:collapse;margin:18px 0;font-size:14px">
            <tr><td style="padding:6px 0;color:#6B7280">Frais</td><td style="text-align:right;font-weight:600">${pay.fee_title || "—"}</td></tr>
            <tr><td style="padding:6px 0;color:#6B7280">Montant payé</td><td style="text-align:right;font-weight:600">${(pay.amount || 0).toLocaleString()} FCFA</td></tr>
            <tr><td style="padding:6px 0;color:#6B7280">Méthode</td><td style="text-align:right">${pay.method || "—"}</td></tr>
            <tr><td style="padding:6px 0;color:#6B7280">Date</td><td style="text-align:right">${pay.payment_date ? new Date(pay.payment_date).toLocaleDateString() : "—"}</td></tr>
            <tr><td style="padding:6px 0;color:#6B7280">N° reçu</td><td style="text-align:right">${pay.receipt_number || "—"}</td></tr>
            <tr><td style="padding:6px 0;color:#6B7280">Reste à payer</td><td style="text-align:right;font-weight:600">${(pay.outstanding_after ?? 0).toLocaleString()} FCFA</td></tr>
        </table>` : ""
    win.document.write(`<!doctype html><html><head><title>${payload.reference}</title></head>
    <body style="font-family:Georgia,serif;color:#111827;max-width:700px;margin:40px auto;padding:0 24px">
        <div style="text-align:center;border-bottom:2px solid #111827;padding-bottom:16px">
            ${sc.logo_url ? `<img src="${sc.logo_url}" style="height:56px;margin-bottom:8px" />` : ""}
            <h2 style="margin:4px 0">${sc.name || ""}</h2>
            <p style="margin:2px 0;font-size:13px;color:#6B7280">${[sc.address, sc.phone, sc.email].filter(Boolean).join(" · ")}</p>
        </div>
        <h1 style="text-align:center;font-size:22px;margin:32px 0;text-transform:uppercase;letter-spacing:1px">${bodyText.split("\n")[0]}</h1>
        <p style="font-size:15px;line-height:1.9;text-align:justify">${bodyText.split("\n").slice(1).join("<br/>")}</p>
        <table style="width:100%;border-collapse:collapse;margin:18px 0;font-size:14px">
            <tr><td style="padding:6px 0;color:#6B7280">Élève</td><td style="text-align:right;font-weight:600">${s.full_name || "—"}</td></tr>
            <tr><td style="padding:6px 0;color:#6B7280">Matricule</td><td style="text-align:right">${s.registration_number || "—"}</td></tr>
            ${en.class_name ? `<tr><td style="padding:6px 0;color:#6B7280">Classe</td><td style="text-align:right">${en.class_name}${en.level ? ` (${en.level})` : ""}</td></tr>` : ""}
            ${en.academic_year ? `<tr><td style="padding:6px 0;color:#6B7280">Année académique</td><td style="text-align:right">${en.academic_year}</td></tr>` : ""}
        </table>
        ${paymentBlock}
        <p style="margin-top:40px;font-size:14px">Fait le ${issued}</p>
        ${signatures.filter(s => s.valid).map(s => `
        <div style="margin-top:18px;border:1px solid #D1D5DB;border-radius:8px;padding:10px 14px;font-size:12px">
            <p style="margin:2px 0;font-weight:600">✓ ${signedByLabel} ${s.signer_name || ""} — ${s.signed_at ? new Date(s.signed_at).toLocaleString() : ""}</p>
            <p style="margin:2px 0;color:#6B7280">Code de signature : ${s.code}</p>
        </div>`).join("")}
        <div style="margin-top:56px;display:flex;justify-content:space-between;align-items:flex-end">
            <div style="font-size:11px;color:#6B7280">
                <p style="margin:2px 0">Réf. ${payload.reference}</p>
                <p style="margin:2px 0">${verifyHint}</p>
            </div>
            <div style="text-align:center;font-size:13px"><p style="border-top:1px solid #111827;padding-top:6px;min-width:180px">Signature / Cachet</p></div>
        </div>
        <script>window.onload = () => window.print()</script>
    </body></html>`)
    win.document.close()
}

export default function MyDocumentsPage() {
    const t = useTranslations("selfDocs")
    const { token } = useAuth()
    const [children, setChildren] = useState<Child[]>([])
    const [studentId, setStudentId] = useState<number | null>(null)
    const [payments, setPayments] = useState<PaymentRow[]>([])
    const [docs, setDocs] = useState<DocRow[]>([])
    const [busy, setBusy] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])
    const sidQs = studentId ? `?student_id=${studentId}` : ""

    const bodyFor = useCallback((docType: string, payload: DocPayload) => {
        const year = payload.enrollment?.academic_year || ""
        if (docType === "receipt") return `${t("receiptTitle")}\n${t("receiptBody")}`
        const key = docType === "attestation" ? "attestationBody" : "certificateBody"
        const title = docType === "attestation" ? t("attestationTitle") : t("certificateTitle")
        return `${title}\n${t(key, { year })}`
    }, [t])

    const loadChildren = useCallback(async () => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/self-documents/children`, { headers })
        if (res.ok) {
            const rows: Child[] = await res.json()
            setChildren(rows)
            if (rows.length && !studentId) setStudentId(rows[0].student_id)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [headers])

    const loadData = useCallback(async () => {
        if (!headers || studentId === null) return
        const [payRes, docRes] = await Promise.all([
            fetch(`${API_BASE_URL}/self-documents/my-payments${sidQs}`, { headers }),
            fetch(`${API_BASE_URL}/self-documents/mine${sidQs}`, { headers }),
        ])
        if (payRes.ok) setPayments(await payRes.json())
        if (docRes.ok) setDocs(await docRes.json())
    }, [headers, studentId, sidQs])

    useEffect(() => { void loadChildren() }, [loadChildren])
    useEffect(() => { void loadData() }, [loadData])

    const generate = async (kind: "certificate" | "attestation" | `receipt/${number}`) => {
        if (!headers) return
        setBusy(kind); setError(null)
        try {
            const res = await fetch(`${API_BASE_URL}/self-documents/${kind}${sidQs}`, { method: "POST", headers })
            if (!res.ok) { setError((await res.json().catch(() => ({}))).detail || "—"); return }
            const payload: DocPayload = await res.json()
            printDocument(payload, bodyFor(payload.doc_type, payload), t("verifyHint"))
            void loadData()
        } finally {
            setBusy(null)
        }
    }

    const reprint = (doc: DocRow) => {
        if (doc.payload) printDocument(doc.payload, bodyFor(doc.payload.doc_type, doc.payload), t("verifyHint"), doc.signatures || [], t("signedBy"))
    }

    const sign = async (doc: DocRow) => {
        if (!headers) return
        setBusy(`sign-${doc.id}`); setError(null)
        try {
            const res = await fetch(`${API_BASE_URL}/self-documents/${doc.id}/sign`, { method: "POST", headers })
            if (!res.ok) { setError((await res.json().catch(() => ({}))).detail || "—"); return }
            void loadData()
        } finally {
            setBusy(null)
        }
    }

    const mySignature = (doc: DocRow) => (doc.signatures || []).find(s => s.valid)

    const docTypeLabel = (type?: string | null) =>
        type === "receipt" ? t("receiptTitle") : type === "attestation" ? t("attestationTitle") : t("certificateTitle")

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            {children.length > 1 && (
                <div className="max-w-sm">
                    <label className="text-xs text-[#6B7280] dark:text-[#c7d0da]">{t("selectChild")}
                        <select value={studentId ?? ""} onChange={e => setStudentId(Number(e.target.value))} className="apple-select mt-1 w-full">
                            {children.map(c => <option key={c.student_id} value={c.student_id}>{c.full_name || c.registration_number || `#${c.student_id}`}</option>)}
                        </select>
                    </label>
                </div>
            )}

            <div className="grid gap-4 md:grid-cols-2">
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><FileCheck2 className="h-4 w-4" /> {t("certificateTitle")}</CardTitle>
                        <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("certificateHint")}</p>
                    </CardHeader>
                    <CardContent>
                        <Button onClick={() => generate("certificate")} disabled={busy !== null || studentId === null} className="bg-black text-white hover:bg-black/90">
                            {busy === "certificate" ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Printer className="mr-2 h-4 w-4" />}{t("generate")}
                        </Button>
                    </CardContent>
                </Card>
                <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><FileText className="h-4 w-4" /> {t("attestationTitle")}</CardTitle>
                        <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("attestationHint")}</p>
                    </CardHeader>
                    <CardContent>
                        <Button onClick={() => generate("attestation")} disabled={busy !== null || studentId === null} className="bg-black text-white hover:bg-black/90">
                            {busy === "attestation" ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Printer className="mr-2 h-4 w-4" />}{t("generate")}
                        </Button>
                    </CardContent>
                </Card>
            </div>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><Receipt className="h-4 w-4" /> {t("receiptsTitle")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("receiptsHint")}</p>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("fee")}</th><th className="px-3 py-2">{t("amount")}</th><th className="px-3 py-2">{t("date")}</th><th className="px-3 py-2">{t("method")}</th><th className="px-3 py-2"></th></tr></thead>
                            <tbody>
                                {payments.length === 0 ? <tr><td colSpan={5} className="px-3 py-6 text-center text-[#6B7280]">{t("noPayments")}</td></tr> : payments.map(p => (
                                    <tr key={p.payment_id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                        <td className="px-3 py-2 font-medium">{p.fee_title || "—"}</td>
                                        <td className="px-3 py-2">{p.amount.toLocaleString()} FCFA</td>
                                        <td className="px-3 py-2">{p.payment_date ? new Date(p.payment_date).toLocaleDateString() : "—"}</td>
                                        <td className="px-3 py-2">{p.method || "—"}</td>
                                        <td className="px-3 py-2 text-right">
                                            <Button size="sm" variant="outline" onClick={() => generate(`receipt/${p.payment_id}`)} disabled={busy !== null}>
                                                <Printer className="mr-1 h-3 w-3" /> {t("receiptButton")}
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><BadgeCheck className="h-4 w-4" /> {t("historyTitle")}</CardTitle>
                    <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("historyHint")}</p>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("docType")}</th><th className="px-3 py-2">{t("reference")}</th><th className="px-3 py-2">{t("date")}</th><th className="px-3 py-2">{t("signatureCol")}</th><th className="px-3 py-2"></th></tr></thead>
                            <tbody>
                                {docs.length === 0 ? <tr><td colSpan={5} className="px-3 py-6 text-center text-[#6B7280]">{t("noDocuments")}</td></tr> : docs.map(d => (
                                    <tr key={d.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                        <td className="px-3 py-2 font-medium">{docTypeLabel(d.doc_type)}</td>
                                        <td className="px-3 py-2 font-mono text-xs">{d.reference}</td>
                                        <td className="px-3 py-2">{new Date(d.created_at).toLocaleString()}</td>
                                        <td className="px-3 py-2">
                                            {mySignature(d) ? (
                                                <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800" title={mySignature(d)!.code}>
                                                    ✓ {mySignature(d)!.signer_name}
                                                </span>
                                            ) : (
                                                <Button size="sm" variant="outline" onClick={() => sign(d)} disabled={busy !== null}>
                                                    {busy === `sign-${d.id}` ? <RefreshCw className="mr-1 h-3 w-3 animate-spin" /> : <FileSignature className="mr-1 h-3 w-3" />} {t("sign")}
                                                </Button>
                                            )}
                                        </td>
                                        <td className="px-3 py-2 text-right">
                                            <Button size="sm" variant="outline" onClick={() => reprint(d)}><Printer className="mr-1 h-3 w-3" /> {t("reprint")}</Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
