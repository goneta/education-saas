"use client"

import { useEffect, useMemo, useState } from "react"
import { useParams } from "next/navigation"
import { ShieldCheck, ShieldAlert, ShieldX, Loader2 } from "lucide-react"

import { API_BASE_URL } from "@/lib/config"
import { normalizeLocale } from "@/lib/i18n"

interface VerifyResult {
    valid: boolean
    status: string
    uuid?: string
    document_type?: string | null
    title?: string | null
    reference?: string | null
    school_name?: string | null
    issued_to?: string | null
    date_generated?: string | null
    payload?: Record<string, unknown> | null
    verify_url?: string
}

const STRINGS: Record<string, Record<string, string>> = {
    fr: {
        title: "Vérification de document", checking: "Vérification en cours…",
        valid: "Document authentique", revoked: "Document révoqué", invalid: "Document introuvable",
        validDesc: "Ce document a été émis par TeducAI et n'a pas été modifié.",
        revokedDesc: "Ce document existe mais a été révoqué par l'établissement.",
        invalidDesc: "Aucun document ne correspond à cette référence.",
        type: "Type", reference: "Référence", school: "Établissement", issuedTo: "Délivré à",
        date: "Date de génération", status: "Statut", details: "Détails", id: "Identifiant",
    },
    en: {
        title: "Document verification", checking: "Verifying…",
        valid: "Authentic document", revoked: "Revoked document", invalid: "Document not found",
        validDesc: "This document was issued by TeducAI and has not been altered.",
        revokedDesc: "This document exists but was revoked by the institution.",
        invalidDesc: "No document matches this reference.",
        type: "Type", reference: "Reference", school: "Institution", issuedTo: "Issued to",
        date: "Date generated", status: "Status", details: "Details", id: "Identifier",
    },
}

const DOC_TYPE_LABELS: Record<string, Record<string, string>> = {
    fr: { invoice: "Facture", receipt: "Reçu", report_card: "Bulletin scolaire", certificate: "Certificat", diploma: "Diplôme", payslip: "Bulletin de salaire" },
    en: { invoice: "Invoice", receipt: "Receipt", report_card: "Report card", certificate: "Certificate", diploma: "Diploma", payslip: "Payslip" },
}

export default function VerifyPage() {
    const params = useParams()
    const locale = normalizeLocale(String(params?.locale || "fr"))
    const uuid = String(params?.uuid || "")
    const t = STRINGS[locale] || STRINGS.en
    const [result, setResult] = useState<VerifyResult | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!uuid) return
        void (async () => {
            setLoading(true)
            try {
                const res = await fetch(`${API_BASE_URL}/verify/${encodeURIComponent(uuid)}`)
                setResult(res.ok ? await res.json() : { valid: false, status: "not_found" })
            } catch {
                setResult({ valid: false, status: "error" })
            } finally { setLoading(false) }
        })()
    }, [uuid])

    const state = useMemo(() => {
        if (!result) return "loading"
        if (result.valid) return "valid"
        if (result.status === "revoked") return "revoked"
        return "invalid"
    }, [result])

    const typeLabel = (result?.document_type && (DOC_TYPE_LABELS[locale] || DOC_TYPE_LABELS.en)[result.document_type]) || result?.document_type || "—"
    const fmtDate = (d?: string | null) => d ? new Date(d).toLocaleDateString(locale) : "—"

    const banner = {
        valid: { icon: ShieldCheck, color: "text-emerald-600", bg: "bg-emerald-50 dark:bg-emerald-950/40", ring: "ring-emerald-200 dark:ring-emerald-900", title: t.valid, desc: t.validDesc },
        revoked: { icon: ShieldAlert, color: "text-amber-600", bg: "bg-amber-50 dark:bg-amber-950/40", ring: "ring-amber-200 dark:ring-amber-900", title: t.revoked, desc: t.revokedDesc },
        invalid: { icon: ShieldX, color: "text-red-600", bg: "bg-red-50 dark:bg-red-950/40", ring: "ring-red-200 dark:ring-red-900", title: t.invalid, desc: t.invalidDesc },
    }[state === "loading" ? "invalid" : state]

    const rows: [string, string][] = result && result.valid ? [
        [t.type, typeLabel],
        [t.reference, result.reference || "—"],
        [t.school, result.school_name || "—"],
        [t.issuedTo, result.issued_to || "—"],
        [t.date, fmtDate(result.date_generated)],
        [t.status, result.status],
        [t.id, result.uuid || uuid],
    ] : []

    return (
        <div className="flex min-h-screen items-center justify-center bg-[#F6F7F9] px-4 py-12 dark:bg-[#16191c]">
            <div className="w-full max-w-lg">
                <div className="mb-6 text-center">
                    <div className="text-2xl font-bold tracking-tight text-[#111827] dark:text-white">TeducAI</div>
                    <div className="text-sm text-[#6B7280]">{t.title}</div>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center gap-2 rounded-2xl border border-[#E5E7EB] bg-white p-10 text-sm text-[#6B7280] shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                        <Loader2 className="h-4 w-4 animate-spin" /> {t.checking}
                    </div>
                ) : (
                    <div className="overflow-hidden rounded-2xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                        <div className={`flex items-center gap-3 p-6 ring-1 ${banner.bg} ${banner.ring}`}>
                            <banner.icon className={`h-8 w-8 ${banner.color}`} />
                            <div>
                                <p className="text-lg font-semibold text-[#111827] dark:text-white">{banner.title}</p>
                                <p className="text-sm text-[#6B7280] dark:text-[#c7d0da]">{banner.desc}</p>
                            </div>
                        </div>
                        {rows.length > 0 && (
                            <dl className="divide-y divide-[#EEF0F2] p-2 dark:divide-[#2a3035]">
                                {rows.map(([label, value]) => (
                                    <div key={label} className="flex items-start justify-between gap-4 px-4 py-3 text-sm">
                                        <dt className="text-[#6B7280]">{label}</dt>
                                        <dd className="max-w-[60%] break-words text-right font-medium text-[#111827] dark:text-[#eef3f8]">{value}</dd>
                                    </div>
                                ))}
                            </dl>
                        )}
                    </div>
                )}
                <p className="mt-4 text-center text-xs text-[#94A3B8]">TeducAI · {t.title}</p>
            </div>
        </div>
    )
}
