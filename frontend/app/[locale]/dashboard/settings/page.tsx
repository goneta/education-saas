"use client"

import type { ReactNode } from "react"
import { useCallback, useEffect, useState } from "react"
import { useTranslations } from "next-intl"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface School {
    id: number
    name: string
    domain_prefix: string
    school_type: string
    address: string | null
    is_active: boolean
}
interface TemplateSummary {
    classes: string[]
    subjects: string[]
    programs: string[]
    fees: Array<{ name: string; amount: number; order: number; required: boolean }>
}
interface AuditLog {
    id: number
    action: string
    path: string | null
    status_code: number | null
    actor_id: number | null
    created_at: string
}
interface PermissionCatalog {
    roles: string[]
    permissions: string[]
    defaults: Record<string, string[]>
}
interface RolePermission {
    role: string
    base_permissions: string[]
    enabled_permissions: string[]
    disabled_permissions: string[]
    available_permissions: string[]
}
interface CountryProfile {
    name: string
    currency: string
    currency_code: string
    locale: string
    timezone: string
    date_format: string
    time_format: string
    phone_code: string
}
interface SchoolSettings {
    name: string
    school_type: string
    country_code: string
    default_currency: string
    currency_code: string
    primary_language: string
    timezone: string
    date_format: string
    time_format: string
    phone: string | null
    phone_country_code: string | null
    phone_e164: string | null
    email: string | null
    website?: string | null
    formatted_address: string | null
    address_structured?: {
        street?: string
        district?: string
        city?: string
        region?: string
        postal_code?: string
        country?: string
        latitude?: number | null
        longitude?: number | null
    } | null
    localization_profile?: CountryProfile
    school_type_profile?: { administrative_focus?: string[] }
}

export default function SettingsPage() {
    const { token, user } = useAuth()
    const t = useTranslations("settings")
    const [schools, setSchools] = useState<School[]>([])
    const [permissions, setPermissions] = useState<string[]>([])
    const [templates, setTemplates] = useState<Record<string, TemplateSummary>>({})
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
    const [templateChoice, setTemplateChoice] = useState("primary")
    const [catalog, setCatalog] = useState<PermissionCatalog | null>(null)
    const [selectedRole, setSelectedRole] = useState("cashier")
    const [rolePermissions, setRolePermissions] = useState<RolePermission | null>(null)
    const [permissionDraft, setPermissionDraft] = useState<Set<string>>(new Set())
    const [permissionStatus, setPermissionStatus] = useState("")
    const [countries, setCountries] = useState<Record<string, CountryProfile>>({})
    const [schoolSettings, setSchoolSettings] = useState<SchoolSettings | null>(null)
    const [settingsStatus, setSettingsStatus] = useState("")

    const loadSchools = useCallback(async () => {
        if (!token || user?.role !== "super_admin") return
        const res = await fetch(`${API_BASE_URL}/system/schools`, { headers: { Authorization: `Bearer ${token}` } })
        if (res.ok) setSchools(await res.json())
    }, [token, user?.role])

    const loadSystemContext = useCallback(async () => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        const [permissionsRes, templatesRes, auditRes] = await Promise.all([
            fetch(`${API_BASE_URL}/system/permissions`, { headers }),
            fetch(`${API_BASE_URL}/system/school-templates`, { headers }),
            fetch(`${API_BASE_URL}/system/audit-logs?limit=20`, { headers }),
        ])
        if (permissionsRes.ok) {
            const data = await permissionsRes.json() as { permissions: string[] }
            setPermissions(data.permissions)
        }
        if (templatesRes.ok) setTemplates(await templatesRes.json() as Record<string, TemplateSummary>)
        if (auditRes.ok) setAuditLogs(await auditRes.json() as AuditLog[])
        const catalogRes = await fetch(`${API_BASE_URL}/system/permissions/catalog`, { headers })
        if (catalogRes.ok) setCatalog(await catalogRes.json() as PermissionCatalog)
        const countriesRes = await fetch(`${API_BASE_URL}/system/localization/countries`, { headers })
        if (countriesRes.ok) {
            const data = await countriesRes.json() as { countries: Record<string, CountryProfile> }
            setCountries(data.countries)
        }
        const settingsRes = await fetch(`${API_BASE_URL}/system/school-settings`, { headers })
        if (settingsRes.ok) setSchoolSettings(await settingsRes.json() as SchoolSettings)
    }, [token])

    const loadRolePermissions = useCallback(async () => {
        if (!token || !catalog) return
        const res = await fetch(`${API_BASE_URL}/system/role-permissions/${selectedRole}`, { headers: { Authorization: `Bearer ${token}` } })
        if (res.ok) {
            const data = await res.json() as RolePermission
            setRolePermissions(data)
            setPermissionDraft(new Set(data.enabled_permissions.filter(permission => permission !== "*")))
        }
    }, [catalog, selectedRole, token])

    const toggleSchool = async (school: School) => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/system/schools/${school.id}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ is_active: !school.is_active })
        })
        if (res.ok) void loadSchools()
    }

    const applyTemplate = async () => {
        if (!token || !user?.school_id) return
        await fetch(`${API_BASE_URL}/system/schools/${user.school_id}/apply-template`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ template: templateChoice })
        })
    }

    const togglePermission = (permission: string) => {
        setPermissionDraft(prev => {
            const next = new Set(prev)
            if (next.has(permission)) next.delete(permission)
            else next.add(permission)
            return next
        })
    }

    const saveRolePermissions = async () => {
        if (!token) return
        setPermissionStatus("Enregistrement...")
        const res = await fetch(`${API_BASE_URL}/system/role-permissions/${selectedRole}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ permissions: Array.from(permissionDraft).sort() })
        })
        if (res.ok) {
            const data = await res.json() as RolePermission
            setRolePermissions(data)
            setPermissionDraft(new Set(data.enabled_permissions.filter(permission => permission !== "*")))
            setPermissionStatus("Permissions mises à jour.")
        } else {
            setPermissionStatus("Impossible d'enregistrer ces permissions.")
        }
    }

    const updateSchoolSetting = (key: keyof SchoolSettings, value: string) => {
        setSchoolSettings(prev => prev ? { ...prev, [key]: value } : prev)
    }

    const updateAddress = (key: string, value: string) => {
        setSchoolSettings(prev => prev ? {
            ...prev,
            address_structured: { ...(prev.address_structured || {}), [key]: value }
        } : prev)
    }

    const applyCountryDefaults = (countryCode: string) => {
        const profile = countries[countryCode]
        setSchoolSettings(prev => prev && profile ? {
            ...prev,
            country_code: countryCode,
            default_currency: profile.currency,
            currency_code: profile.currency_code,
            primary_language: profile.locale,
            timezone: profile.timezone,
            date_format: profile.date_format,
            time_format: profile.time_format,
            phone_country_code: countryCode,
            address_structured: { ...(prev.address_structured || {}), country: profile.name }
        } : prev)
    }

    const saveSchoolSettings = async () => {
        if (!token || !schoolSettings) return
        setSettingsStatus("Enregistrement...")
        const res = await fetch(`${API_BASE_URL}/system/school-settings`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(schoolSettings)
        })
        if (res.ok) {
            setSchoolSettings(await res.json() as SchoolSettings)
            setSettingsStatus("Parametres enregistres.")
        } else {
            const error = await res.text()
            setSettingsStatus(`Erreur: ${error.slice(0, 120)}`)
        }
    }

    useEffect(() => { void loadSchools() }, [loadSchools])
    useEffect(() => { void loadSystemContext() }, [loadSystemContext])
    useEffect(() => { void loadRolePermissions() }, [loadRolePermissions])

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">Settings</h1>
                <p className="text-sm text-[#6B7280] mt-1">Tenant context, school status and platform administration.</p>
            </div>

            <Card>
                <CardHeader><CardTitle>{t("activeContext")}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-3 text-sm">
                    <Info label="User" value={user?.full_name || "-"} />
                    <Info label="Role" value={user?.role || "-"} />
                    <Info label="School ID" value={user?.school_id?.toString() || "Platform"} />
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle>{t("permissions")}</CardTitle></CardHeader>
                <CardContent className="flex flex-wrap gap-2 text-sm">
                    {permissions.map(permission => <span key={permission} className="rounded-md border px-2 py-1">{permission}</span>)}
                </CardContent>
            </Card>

            {schoolSettings && (
                <Card>
                    <CardHeader><CardTitle>Configuration internationale</CardTitle></CardHeader>
                    <CardContent className="space-y-5">
                        <div className="grid gap-3 md:grid-cols-4">
                            <Field label="Pays">
                                <select value={schoolSettings.country_code} onChange={(event) => applyCountryDefaults(event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm">
                                    {Object.entries(countries).map(([code, profile]) => <option key={code} value={code}>{profile.name}</option>)}
                                </select>
                            </Field>
                            <Field label="Devise">
                                <select value={schoolSettings.default_currency} onChange={(event) => updateSchoolSetting("default_currency", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm">
                                    {["FCFA", "GBP", "EUR", "USD"].map(currency => <option key={currency} value={currency}>{currency}</option>)}
                                </select>
                            </Field>
                            <Field label="Langue principale">
                                <select value={schoolSettings.primary_language} onChange={(event) => updateSchoolSetting("primary_language", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm">
                                    <option value="fr">Francais</option>
                                    <option value="en">English</option>
                                    <option value="es">Espanol</option>
                                    <option value="sw">Kiswahili</option>
                                </select>
                            </Field>
                            <Field label="Type etablissement">
                                <select value={schoolSettings.school_type} onChange={(event) => updateSchoolSetting("school_type", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm">
                                    {["primary", "secondary", "general", "technical", "vocational", "professional", "university"].map(type => <option key={type} value={type}>{type}</option>)}
                                </select>
                            </Field>
                            <Field label="Fuseau horaire"><input value={schoolSettings.timezone} onChange={(event) => updateSchoolSetting("timezone", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></Field>
                            <Field label="Format date"><input value={schoolSettings.date_format} onChange={(event) => updateSchoolSetting("date_format", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></Field>
                            <Field label="Format heure"><input value={schoolSettings.time_format} onChange={(event) => updateSchoolSetting("time_format", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></Field>
                            <Field label="Telephone"><input value={schoolSettings.phone || ""} onChange={(event) => updateSchoolSetting("phone", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></Field>
                        </div>
                        <div className="grid gap-3 md:grid-cols-3">
                            <Field label="Rue"><input value={schoolSettings.address_structured?.street || ""} onChange={(event) => updateAddress("street", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></Field>
                            <Field label="Quartier"><input value={schoolSettings.address_structured?.district || ""} onChange={(event) => updateAddress("district", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></Field>
                            <Field label="Ville"><input value={schoolSettings.address_structured?.city || ""} onChange={(event) => updateAddress("city", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></Field>
                            <Field label="Region / Etat"><input value={schoolSettings.address_structured?.region || ""} onChange={(event) => updateAddress("region", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></Field>
                            <Field label="Code postal"><input value={schoolSettings.address_structured?.postal_code || ""} onChange={(event) => updateAddress("postal_code", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></Field>
                            <Field label="Pays adresse"><input value={schoolSettings.address_structured?.country || ""} onChange={(event) => updateAddress("country", event.target.value)} className="w-full rounded-md border px-3 py-2 text-sm" /></Field>
                        </div>
                        <div className="grid gap-3 md:grid-cols-3 text-sm">
                            <Info label="Adresse formatee" value={schoolSettings.formatted_address || "-"} />
                            <Info label="Telephone international" value={schoolSettings.phone_e164 || "-"} />
                            <Info label="Focus administratif" value={schoolSettings.school_type_profile?.administrative_focus?.join(", ") || "-"} />
                        </div>
                        <div className="flex items-center gap-3">
                            <Button onClick={saveSchoolSettings}>Enregistrer les parametres</Button>
                            {settingsStatus && <span className="text-sm text-[#6B7280]">{settingsStatus}</span>}
                        </div>
                    </CardContent>
                </Card>
            )}

            {catalog && (
                <Card>
                    <CardHeader><CardTitle>Matrice des droits</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex flex-wrap items-center gap-3">
                            <select value={selectedRole} onChange={(event) => setSelectedRole(event.target.value)} className="border rounded-md px-3 py-2 text-sm">
                                {catalog.roles.map(role => <option key={role} value={role}>{role}</option>)}
                            </select>
                            <Button onClick={saveRolePermissions}>Enregistrer</Button>
                            {permissionStatus && <span className="text-sm text-[#6B7280]">{permissionStatus}</span>}
                        </div>
                        <div className="grid gap-2 md:grid-cols-3">
                            {catalog.permissions.map(permission => (
                                <label key={permission} className="flex min-h-10 items-center gap-2 rounded-md border px-3 py-2 text-sm">
                                    <input
                                        type="checkbox"
                                        checked={permissionDraft.has(permission)}
                                        onChange={() => togglePermission(permission)}
                                        className="h-4 w-4"
                                    />
                                    <span>{permission}</span>
                                </label>
                            ))}
                        </div>
                        {rolePermissions && rolePermissions.disabled_permissions.length > 0 && (
                            <p className="text-xs text-[#6B7280]">Droits explicitement retirés: {rolePermissions.disabled_permissions.join(", ")}</p>
                        )}
                    </CardContent>
                </Card>
            )}

            <Card>
                <CardHeader><CardTitle>{t("schoolTemplates")}</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex flex-wrap gap-3">
                        <select value={templateChoice} onChange={(e) => setTemplateChoice(e.target.value)} className="border rounded-md px-3 py-2 text-sm">
                            {Object.keys(templates).map(template => <option key={template} value={template}>{template}</option>)}
                        </select>
                        <Button onClick={applyTemplate}>{t("applyTemplate")}</Button>
                    </div>
                    {templates[templateChoice] && (
                        <div className="grid gap-3 md:grid-cols-3 text-sm">
                            <Info label="Classes" value={templates[templateChoice].classes.join(", ")} />
                            <Info label="Subjects" value={templates[templateChoice].subjects.join(", ")} />
                            <Info label="Fee rubrics" value={templates[templateChoice].fees.map(fee => fee.name).join(", ")} />
                        </div>
                    )}
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle>{t("auditTrail")}</CardTitle></CardHeader>
                <CardContent>
                    <table className="w-full text-sm">
                        <thead><tr className="border-b"><th className="py-2 text-left">Date</th><th className="py-2 text-left">Action</th><th className="py-2 text-left">Actor</th><th className="py-2 text-left">Status</th></tr></thead>
                        <tbody>{auditLogs.map(log => <tr key={log.id} className="border-b last:border-0"><td className="py-2">{new Date(log.created_at).toLocaleString()}</td><td className="py-2">{log.action}</td><td className="py-2">{log.actor_id || "-"}</td><td className="py-2">{log.status_code || "-"}</td></tr>)}</tbody>
                    </table>
                </CardContent>
            </Card>

            {user?.role === "super_admin" && (
                <Card>
                    <CardHeader><CardTitle>Schools</CardTitle></CardHeader>
                    <CardContent>
                        <table className="w-full text-sm">
                            <thead><tr className="border-b"><th className="py-2 text-left">School</th><th className="py-2 text-left">Domain</th><th className="py-2 text-left">Type</th><th className="py-2 text-left">Status</th><th className="py-2 text-right">Action</th></tr></thead>
                            <tbody>{schools.map(school => <tr key={school.id} className="border-b last:border-0"><td className="py-2 font-medium">{school.name}</td><td className="py-2">{school.domain_prefix}</td><td className="py-2">{school.school_type}</td><td className="py-2">{school.is_active ? "Active" : "Suspended"}</td><td className="py-2 text-right"><Button variant="outline" size="sm" onClick={() => toggleSchool(school)}>{school.is_active ? "Suspend" : "Reactivate"}</Button></td></tr>)}</tbody>
                        </table>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}

function Info({ label, value }: { label: string; value: string }) {
    return <div><p className="text-[#6B7280]">{label}</p><p className="font-medium text-[#111827]">{value}</p></div>
}

function Field({ label, children }: { label: string; children: ReactNode }) {
    return <label className="space-y-1 text-sm"><span className="text-[#6B7280]">{label}</span>{children}</label>
}
