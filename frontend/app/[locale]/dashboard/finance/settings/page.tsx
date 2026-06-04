"use client"

import { useCallback, useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ExplainedField } from "@/components/ui/explained-field"
import { normalizeLocale } from "@/lib/i18n"
import { tx } from "@/lib/product-copy"

interface FeeSchedule {
    id: number
    name: string
    amount: number
    category_order: number
    is_required: boolean
    is_current: boolean
    level: string | null
    class_id: number | null
}

export default function FeeSettingsPage() {
    const { token } = useAuth()
    const params = useParams<{ locale: string }>()
    const locale = normalizeLocale(params?.locale)
    const [rows, setRows] = useState<FeeSchedule[]>([])
    const [form, setForm] = useState({ name: "", amount: "", category_order: "0", is_required: true, level: "", class_id: "", academic_year_id: "" })
    const [copy, setCopy] = useState({ source: "", target: "" })
    const [message, setMessage] = useState<string | null>(null)

    const loadRows = useCallback(async () => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/finance/fee-schedules`, { headers: { Authorization: `Bearer ${token}` } })
        if (res.ok) setRows(await res.json())
    }, [token])

    const save = async () => {
        if (!token || !form.name || !form.amount) return
        const res = await fetch(`${API_BASE_URL}/finance/fee-schedules`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                name: form.name,
                amount: Number(form.amount),
                category_order: Number(form.category_order || 0),
                is_required: form.is_required,
                level: form.level || null,
                class_id: form.class_id ? Number(form.class_id) : null,
                academic_year_id: form.academic_year_id ? Number(form.academic_year_id) : null
            })
        })
        if (res.ok) {
            setForm({ name: "", amount: "", category_order: "0", is_required: true, level: "", class_id: "", academic_year_id: "" })
            void loadRows()
        }
    }

    const copyYear = async () => {
        if (!token || !copy.source || !copy.target) return
        const res = await fetch(`${API_BASE_URL}/finance/fee-schedules/copy-year?source_academic_year_id=${copy.source}&target_academic_year_id=${copy.target}`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` }
        })
        setMessage(res.ok ? "Previous year amounts copied where missing." : "Copy failed.")
        if (res.ok) void loadRows()
    }

    useEffect(() => { void loadRows() }, [loadRows])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="apple-page-title">{tx(locale, "feeSettings")}</h1>
                <p className="apple-page-description">{tx(locale, "feeSettingsDescription")}</p>
            </div>

            <Card><CardHeader><CardTitle>{tx(locale, "addFeeRubric")}</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-4">
                <ExplainedField label={tx(locale, "name")} required help="Nom officiel de la rubrique de frais tel qu'il apparaîtra sur les factures, reçus et rapports."><input placeholder={tx(locale, "name")} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "amount")} required help="Montant attendu dans la devise de l'établissement. Format: nombre positif, sans séparateur de milliers."><input type="number" placeholder={tx(locale, "amount")} value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "order")} help="Ordre d'affichage et de priorité de la rubrique dans les listes et documents."><input type="number" placeholder={tx(locale, "order")} value={form.category_order} onChange={(e) => setForm({ ...form, category_order: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "level")} help="Niveau concerné: CP1, 6ème, Terminale, Licence 1, BTS 1, etc. Laisser vide pour global."><input placeholder={tx(locale, "level")} value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "classId")} help="Identifiant de classe si la rubrique s'applique à une classe précise. Laisser vide pour tout le niveau."><input type="number" placeholder={tx(locale, "classId")} value={form.class_id} onChange={(e) => setForm({ ...form, class_id: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "academicYearId")} help="Identifiant de l'année académique. Permet la reprise automatique des montants d'une année à l'autre."><input type="number" placeholder={tx(locale, "academicYearId")} value={form.academic_year_id} onChange={(e) => setForm({ ...form, academic_year_id: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "required")} help="Cochez si ce frais est obligatoire pour l'inscription ou la scolarité. Les impayés seront calculés dessus."><span className="flex h-11 items-center gap-2"><input type="checkbox" checked={form.is_required} onChange={(e) => setForm({ ...form, is_required: e.target.checked })} className="h-4 w-4 accent-[#0066cc]" /> {tx(locale, "required")}</span></ExplainedField>
                <Button onClick={save}>{tx(locale, "save")}</Button>
            </CardContent></Card>

            <Card><CardHeader><CardTitle>{tx(locale, "copyPreviousYear")}</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-4">
                <ExplainedField label={tx(locale, "sourceYearId")} help="Année académique source contenant les montants existants à reprendre."><input type="number" placeholder={tx(locale, "sourceYearId")} value={copy.source} onChange={(e) => setCopy({ ...copy, source: e.target.value })} className="apple-input" /></ExplainedField>
                <ExplainedField label={tx(locale, "targetYearId")} help="Année académique cible qui recevra les montants si aucune rubrique équivalente n'existe déjà."><input type="number" placeholder={tx(locale, "targetYearId")} value={copy.target} onChange={(e) => setCopy({ ...copy, target: e.target.value })} className="apple-input" /></ExplainedField>
                <Button onClick={copyYear}>{tx(locale, "copyAmounts")}</Button>
                {message && <p className="text-sm text-[#6B7280] self-center">{message}</p>}
            </CardContent></Card>

            <Card><CardHeader><CardTitle>{tx(locale, "configuredRubrics")}</CardTitle></CardHeader><CardContent>
                <table className="apple-table"><thead><tr><th>{tx(locale, "order")}</th><th>{tx(locale, "name")}</th><th>{tx(locale, "level")}</th><th className="text-right">{tx(locale, "amount")}</th><th>{tx(locale, "type")}</th></tr></thead>
                    <tbody>{rows.map(row => <tr key={row.id}><td>{row.category_order}</td><td>{row.name}</td><td>{row.level || "-"}</td><td className="text-right">{row.amount.toLocaleString()} FCFA</td><td>{row.is_required ? tx(locale, "required") : "Optionnel"}</td></tr>)}</tbody>
                </table>
            </CardContent></Card>
        </div>
    )
}
