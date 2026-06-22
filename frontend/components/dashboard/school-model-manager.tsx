"use client"

import { useCallback, useEffect, useState } from "react"
import { CheckCircle2, Circle, Power } from "lucide-react"

import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"


interface CatalogModel {
    id: number
    code: string
    name: string
    description?: string
}

interface Assignment {
    id: number
    school_id: number
    model_code: string
    display_name: string
    is_active: boolean
    ai_enabled: boolean
}

interface OrganizationOption {
    id: number
    name: string
    is_owner: boolean
}

const SCHOOL_TYPES: Record<string, string> = {
    PRIMARY: "primary",
    GENERAL_SECONDARY: "general",
    VOCATIONAL: "vocational",
    TECHNICAL: "technical",
    PROFESSIONAL: "professional",
    UNIVERSITY: "university",
}


export function SchoolModelManager() {
    const { token, user } = useAuth()
    const [catalog, setCatalog] = useState<CatalogModel[]>([])
    const [assignments, setAssignments] = useState<Assignment[]>([])
    const [organizations, setOrganizations] = useState<OrganizationOption[]>([])
    const [selected, setSelected] = useState<string[]>([])
    const [newSchool, setNewSchool] = useState({ name: "", code: "", address: "" })
    const [message, setMessage] = useState("")
    const [saving, setSaving] = useState(false)

    const load = useCallback(async () => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        const [catalogResponse, optionsResponse] = await Promise.all([
            fetch(`${API_BASE_URL}/context/catalog`, { headers }),
            fetch(`${API_BASE_URL}/context/options`, { headers }),
        ])
        if (catalogResponse.ok) setCatalog(await catalogResponse.json())
        if (optionsResponse.ok) {
            const data = await optionsResponse.json()
            const rows = (data.assignments || []) as Assignment[]
            setAssignments(rows)
            setOrganizations((data.organizations || []) as OrganizationOption[])
            setSelected(rows.filter(row => row.is_active).map(row => row.model_code))
        }
    }, [token])

    useEffect(() => {
        void load()
    }, [load])

    const toggleSelection = (code: string) => {
        setSelected(current => current.includes(code) ? current.filter(value => value !== code) : [...current, code])
    }

    const activate = async () => {
        if (!token || !user?.school_id || !selected.length) return
        setSaving(true)
        setMessage("")
        try {
            const response = await fetch(`${API_BASE_URL}/context/assignments`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({ school_id: user.school_id, model_codes: selected, seed_defaults: true }),
            })
            if (!response.ok) throw new Error((await response.json()).detail || "Activation impossible")
            setMessage("Modeles actifs et donnees de reference synchronises.")
            await load()
        } catch (error) {
            setMessage(error instanceof Error ? error.message : "Activation impossible")
        } finally {
            setSaving(false)
        }
    }

    const toggleActive = async (assignment: Assignment) => {
        if (!token) return
        const response = await fetch(`${API_BASE_URL}/context/assignments/${assignment.id}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ is_active: !assignment.is_active }),
        })
        if (response.ok) await load()
    }

    const createSchool = async () => {
        if (!token || !organizations.some(row => row.is_owner) || !newSchool.name || !newSchool.code || !selected.length) return
        setSaving(true)
        setMessage("")
        try {
            const firstModel = selected[0]
            const response = await fetch(`${API_BASE_URL}/context/schools`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({
                    organization_id: organizations.find(row => row.is_owner)?.id,
                    school: {
                        name: newSchool.name,
                        domain_prefix: newSchool.code.toLowerCase().replace(/[^a-z0-9_-]/g, "-"),
                        school_type: SCHOOL_TYPES[firstModel] || "general",
                        address: newSchool.address,
                    },
                    model_codes: selected,
                    seed_defaults: true,
                }),
            })
            if (!response.ok) throw new Error((await response.json()).detail || "Creation impossible")
            setNewSchool({ name: "", code: "", address: "" })
            setMessage("Nouvel etablissement cree dans le groupe.")
            await load()
        } catch (error) {
            setMessage(error instanceof Error ? error.message : "Creation impossible")
        } finally {
            setSaving(false)
        }
    }

    return (
        <section className="space-y-4 border-t border-[#e5e7eb] pt-4 dark:border-[#3b4248]">
            <div>
                <h3 className="font-semibold">Modeles actifs de l&apos;etablissement</h3>
                <p className="text-sm text-[#667085] dark:text-[#b6c0cb]">
                    Selectionnez les cycles geres. Les classes, matieres, programmes, periodes et frais de reference sont crees sans doublon.
                </p>
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {catalog.map(model => {
                    const assignment = assignments.find(row => row.model_code === model.code)
                    const checked = selected.includes(model.code)
                    return (
                        <div key={model.code} className="rounded-2xl border border-[#dfe3e8] p-4 dark:border-[#46505a] dark:bg-[#252b30]">
                            <button type="button" onClick={() => toggleSelection(model.code)} className="flex w-full items-start gap-3 text-left">
                                {checked ? <CheckCircle2 className="mt-0.5 h-5 w-5" /> : <Circle className="mt-0.5 h-5 w-5" />}
                                <span>
                                    <span className="block font-semibold">{model.name}</span>
                                    <span className="block text-sm text-[#667085] dark:text-[#b6c0cb]">{model.description}</span>
                                </span>
                            </button>
                            {assignment && (
                                <button type="button" onClick={() => void toggleActive(assignment)} className="mt-3 inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs">
                                    <Power className="h-3.5 w-3.5" />
                                    {assignment.is_active ? "Desactiver sans supprimer" : "Reactiver"}
                                </button>
                            )}
                        </div>
                    )
                })}
            </div>
            <button type="button" disabled={saving || !selected.length} onClick={() => void activate()} className="rounded-full bg-black px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-50 dark:bg-white dark:text-black">
                {saving ? "Synchronisation..." : "Activer et initialiser"}
            </button>
            {organizations.some(row => row.is_owner) && (
                <div className="rounded-2xl border border-[#dfe3e8] p-4 dark:border-[#46505a] dark:bg-[#252b30]">
                    <h3 className="font-semibold">Ajouter un etablissement au groupe {organizations.find(row => row.is_owner)?.name}</h3>
                    <div className="mt-3 grid gap-3 md:grid-cols-3">
                        <input className="apple-input" placeholder="Nom de l'etablissement" value={newSchool.name} onChange={event => setNewSchool(current => ({ ...current, name: event.target.value }))} />
                        <input className="apple-input" placeholder="Code unique" value={newSchool.code} onChange={event => setNewSchool(current => ({ ...current, code: event.target.value }))} />
                        <input className="apple-input" placeholder="Adresse" value={newSchool.address} onChange={event => setNewSchool(current => ({ ...current, address: event.target.value }))} />
                    </div>
                    <button type="button" disabled={saving || !newSchool.name || !newSchool.code || !selected.length} onClick={() => void createSchool()} className="mt-3 rounded-full border border-black px-5 py-2.5 text-sm font-semibold disabled:opacity-50 dark:border-white">
                        Creer avec les modeles selectionnes
                    </button>
                </div>
            )}
            {message && <p className="text-sm" role="status">{message}</p>}
        </section>
    )
}
