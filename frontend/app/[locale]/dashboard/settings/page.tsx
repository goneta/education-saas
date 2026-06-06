"use client"

import { useCallback, useEffect, useState, type PointerEvent } from "react"
import Image from "next/image"
import { useTranslations } from "next-intl"
import { useParams } from "next/navigation"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ExplainedField, fieldHelp } from "@/components/ui/explained-field"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { tx, humanizeKey } from "@/lib/product-copy"
import { normalizeLocale } from "@/lib/i18n"

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
    levels?: string[]
    subjects: string[]
    programs: string[]
    diplomas?: string[]
    semesters?: string[]
    certifications?: string[]
    assessment_types?: string[]
    academic_years?: string[]
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
interface PermissionModule {
    key: string
    label: string
    category?: string
    actions: string[]
}
interface RoleDefinition {
    id: number
    key: string
    name: string
    category: string | null
    description: string | null
    color: string
    is_system: boolean
    is_active: boolean
    parent_role_key: string | null
    users_count: number
}
interface PermissionCatalog {
    roles: string[]
    role_definitions: RoleDefinition[]
    modules: PermissionModule[]
    actions: string[]
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
interface ManagedUser {
    id: number
    email: string
    full_name: string | null
    role: string
    is_active: boolean
    school_id: number | null
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
    logo_url?: string | null
    registration_number?: string | null
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
    subscription_plan?: string | null
    subscription_status?: string | null
    current_billing_period_end?: string | null
}
interface ActiveContext {
    user: {
        id: number
        email: string
        full_name: string | null
        role: string
        school_id: number | null
    }
    roles: string[]
    active_role: string
    permissions: string[]
}

const MATRIX_ACTIONS = ["view", "create", "edit", "delete", "approve", "export", "full_access"]
const PRIMARY_ROLE_KEYS = [
    "super_admin",
    "school_admin",
    "admin",
    "direction",
    "director",
    "principal",
    "department_head",
    "pedagogy_coordinator",
    "registrar",
    "receptionist",
    "secretary",
    "cashier",
    "accountant",
    "educator",
    "teacher",
    "trainer",
    "instructor",
    "student",
    "pupil",
    "parent",
    "staff",
]

const SUBSCRIPTION_PLANS = {
    free: { label: "Free", monthly: 0, yearly: 0 },
    pro: { label: "Pro", monthly: 99000, yearly: 900000 },
    max: { label: "Max", monthly: 199000, yearly: 1700000 },
}

const SUBSCRIPTION_STATUS_LABELS: Record<string, string> = {
    active: "Actif",
    expired: "Expiré",
    suspended: "Suspendu",
    pending: "En attente",
}

export default function SettingsPage() {
    const { token, user } = useAuth()
    const params = useParams<{ locale: string }>()
    const locale = normalizeLocale(params?.locale)
    const t = useTranslations("settings")
    const [schools, setSchools] = useState<School[]>([])
    const [permissions, setPermissions] = useState<string[]>([])
    const [templates, setTemplates] = useState<Record<string, TemplateSummary>>({})
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
    const [templateChoice, setTemplateChoice] = useState("primary")
    const [catalog, setCatalog] = useState<PermissionCatalog | null>(null)
    const [selectedRole, setSelectedRole] = useState("school_admin")
    const [rolePermissions, setRolePermissions] = useState<RolePermission | null>(null)
    const [permissionDraft, setPermissionDraft] = useState<Set<string>>(new Set())
    const [permissionStatus, setPermissionStatus] = useState("")
    const [roleDefinitions, setRoleDefinitions] = useState<RoleDefinition[]>([])
    const [roleUsers, setRoleUsers] = useState<ManagedUser[]>([])
    const [newRole, setNewRole] = useState({ name: "", description: "", color: "#0F766E", parent_role_key: "" })
    const [users, setUsers] = useState<ManagedUser[]>([])
    const [newUser, setNewUser] = useState({ email: "", full_name: "", password: "SecurePass2026!", role: "staff", role_keys: "" })
    const [userStatus, setUserStatus] = useState("")
    const [countries, setCountries] = useState<Record<string, CountryProfile>>({})
    const [schoolSettings, setSchoolSettings] = useState<SchoolSettings | null>(null)
    const [savedSchoolSettings, setSavedSchoolSettings] = useState<SchoolSettings | null>(null)
    const [activeContext, setActiveContext] = useState<ActiveContext | null>(null)
    const [activeRole, setActiveRole] = useState("")
    const [isEditingSchool, setIsEditingSchool] = useState(false)
    const [settingsStatus, setSettingsStatus] = useState("")
    const [settingsError, setSettingsError] = useState("")
    const [selectedPermissionCategory, setSelectedPermissionCategory] = useState("all")

    const loadSchools = useCallback(async () => {
        if (!token || user?.role !== "super_admin") return
        const res = await fetch(`${API_BASE_URL}/system/schools`, { headers: { Authorization: `Bearer ${token}` } })
        if (res.ok) setSchools(await res.json())
    }, [token, user?.role])

    const loadSystemContext = useCallback(async () => {
        if (!token) return
        const headers = { Authorization: `Bearer ${token}` }
        const [permissionsRes, templatesRes, auditRes, catalogRes, usersRes, countriesRes, settingsRes, activeContextRes] = await Promise.all([
            fetch(`${API_BASE_URL}/system/permissions`, { headers }),
            fetch(`${API_BASE_URL}/system/school-templates`, { headers }),
            fetch(`${API_BASE_URL}/system/audit-logs?limit=20`, { headers }),
            fetch(`${API_BASE_URL}/system/permissions/catalog`, { headers }),
            fetch(`${API_BASE_URL}/system/users`, { headers }),
            fetch(`${API_BASE_URL}/system/localization/countries`, { headers }),
            fetch(`${API_BASE_URL}/system/school-settings`, { headers }),
            fetch(`${API_BASE_URL}/system/active-context`, { headers }),
        ])
        if (permissionsRes.ok) setPermissions(((await permissionsRes.json()) as { permissions: string[] }).permissions)
        if (templatesRes.ok) setTemplates(await templatesRes.json() as Record<string, TemplateSummary>)
        if (auditRes.ok) setAuditLogs(await auditRes.json() as AuditLog[])
        if (catalogRes.ok) {
            const data = await catalogRes.json() as PermissionCatalog
            setCatalog(data)
            setRoleDefinitions(data.role_definitions || [])
            if (data.roles.length && !data.roles.includes(selectedRole)) setSelectedRole(data.roles[0])
        }
        if (usersRes.ok) setUsers(await usersRes.json() as ManagedUser[])
        if (countriesRes.ok) setCountries(((await countriesRes.json()) as { countries: Record<string, CountryProfile> }).countries)
        if (settingsRes.ok) {
            const settings = await settingsRes.json() as SchoolSettings
            setSchoolSettings(settings)
            setSavedSchoolSettings(settings)
        }
        if (activeContextRes.ok) {
            const context = await activeContextRes.json() as ActiveContext
            setActiveContext(context)
            setActiveRole(context.active_role)
        }
    }, [selectedRole, token])

    const loadRolePermissions = useCallback(async () => {
        if (!token || !catalog) return
        const headers = { Authorization: `Bearer ${token}` }
        const [permissionsRes, usersRes] = await Promise.all([
            fetch(`${API_BASE_URL}/system/role-management/roles/${selectedRole}/permissions`, { headers }),
            fetch(`${API_BASE_URL}/system/role-management/roles/${selectedRole}/users`, { headers }),
        ])
        if (permissionsRes.ok) {
            const data = await permissionsRes.json() as RolePermission
            setRolePermissions(data)
            setPermissionDraft(new Set(data.enabled_permissions.filter(permission => permission !== "*")))
        }
        if (usersRes.ok) setRoleUsers(await usersRes.json() as ManagedUser[])
    }, [catalog, selectedRole, token])

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
        const res = await fetch(`${API_BASE_URL}/system/role-management/roles/${selectedRole}/permissions`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ permissions: Array.from(permissionDraft).sort() })
        })
        if (res.ok) {
            const data = await res.json() as RolePermission
            setRolePermissions(data)
            setPermissionDraft(new Set(data.enabled_permissions.filter(permission => permission !== "*")))
            setPermissionStatus("Permissions mises a jour.")
        } else {
            setPermissionStatus("Impossible d'enregistrer ces permissions.")
        }
    }

    const createRole = async () => {
        if (!token || !newRole.name.trim()) return
        const res = await fetch(`${API_BASE_URL}/system/role-management/roles`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                name: newRole.name,
                description: newRole.description,
                color: newRole.color,
                parent_role_key: newRole.parent_role_key || null,
                permissions: newRole.parent_role_key ? [] : Array.from(permissionDraft),
            })
        })
        if (res.ok) {
            setNewRole({ name: "", description: "", color: "#0F766E", parent_role_key: "" })
            await loadSystemContext()
        }
    }

    const duplicateRole = async () => {
        if (!token || !newRole.name.trim()) return
        const key = newRole.name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "")
        const res = await fetch(`${API_BASE_URL}/system/role-management/roles/${selectedRole}/duplicate`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ key, name: newRole.name, description: newRole.description, color: newRole.color })
        })
        if (res.ok) {
            setNewRole({ name: "", description: "", color: "#0F766E", parent_role_key: "" })
            await loadSystemContext()
        }
    }

    const toggleRoleStatus = async (role: RoleDefinition) => {
        if (!token || role.is_system) return
        const res = await fetch(`${API_BASE_URL}/system/role-management/roles/${role.key}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ is_active: !role.is_active })
        })
        if (res.ok) await loadSystemContext()
    }

    const deleteRole = async (role: RoleDefinition) => {
        if (!token || role.is_system) return
        const res = await fetch(`${API_BASE_URL}/system/role-management/roles/${role.key}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) await loadSystemContext()
    }

    const createManagedUser = async () => {
        if (!token || !newUser.email || !newUser.full_name) return
        setUserStatus("Creation...")
        const res = await fetch(`${API_BASE_URL}/system/users`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                email: newUser.email,
                full_name: newUser.full_name,
                password: newUser.password,
                role: newUser.role,
                role_keys: newUser.role_keys.split(",").map(role => role.trim()).filter(Boolean),
            })
        })
        if (res.ok) {
            setNewUser({ email: "", full_name: "", password: "SecurePass2026!", role: "staff", role_keys: "" })
            setUserStatus("Utilisateur cree.")
            await loadSystemContext()
        } else {
            setUserStatus("Creation impossible.")
        }
    }

    const toggleUserStatus = async (managedUser: ManagedUser) => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/system/users/${managedUser.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ is_active: !managedUser.is_active })
        })
        if (res.ok) await loadSystemContext()
    }

    const resetUserPassword = async (managedUser: ManagedUser) => {
        if (!token) return
        const res = await fetch(`${API_BASE_URL}/system/users/${managedUser.id}/reset-password`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ new_password: "SecurePass2026!" })
        })
        setUserStatus(res.ok ? `Mot de passe reinitialise pour ${managedUser.email}.` : "Reinitialisation impossible.")
    }

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

    const updateSchoolSetting = (key: keyof SchoolSettings, value: string) => {
        setSchoolSettings(prev => prev ? { ...prev, [key]: value } : prev)
    }

    const estimatedCoordinates = (settings: SchoolSettings) => {
        const structured = settings.address_structured || {}
        const source = [structured.street, structured.district, structured.city, structured.region, structured.country, settings.name].filter(Boolean).join(" ")
        let hash = 0
        for (let index = 0; index < source.length; index += 1) hash = ((hash << 5) - hash + source.charCodeAt(index)) | 0
        const country = settings.country_code || "CI"
        const base = country === "GB" ? { lat: 51.5074, lng: -0.1278 } : country === "FR" ? { lat: 48.8566, lng: 2.3522 } : { lat: 5.36, lng: -4.0083 }
        return {
            latitude: Number((base.lat + ((Math.abs(hash) % 1000) / 10000 - 0.05)).toFixed(6)),
            longitude: Number((base.lng + ((Math.abs(hash >> 8) % 1000) / 10000 - 0.05)).toFixed(6)),
        }
    }

    const updateAddress = (key: string, value: string) => {
        setSchoolSettings(prev => {
            if (!prev) return prev
            const next = {
                ...prev,
                address_structured: { ...(prev.address_structured || {}), [key]: value }
            }
            if (["street", "district", "city", "region", "postal_code", "country"].includes(key)) {
                const coordinates = estimatedCoordinates(next)
                next.address_structured = { ...next.address_structured, ...coordinates }
            }
            return next
        })
    }

    const updateCoordinates = (latitude: number, longitude: number) => {
        if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return
        setSchoolSettings(prev => prev ? {
            ...prev,
            address_structured: { ...(prev.address_structured || {}), latitude, longitude }
        } : prev)
    }

    const updateMapFromPointer = (clientX: number, clientY: number, target: HTMLDivElement) => {
        const rect = target.getBoundingClientRect()
        const x = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
        const y = Math.min(1, Math.max(0, (clientY - rect.top) / rect.height))
        updateCoordinates(Number((90 - y * 180).toFixed(6)), Number((-180 + x * 360).toFixed(6)))
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

    const persistSchoolSettings = async (nextSettings: SchoolSettings, successMessage = "Parametres enregistres.") => {
        if (!token) return
        setSettingsError("")
        setSettingsStatus("Enregistrement...")
        const res = await fetch(`${API_BASE_URL}/system/school-settings`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(nextSettings)
        })
        if (res.ok) {
            const saved = await res.json() as SchoolSettings
            setSchoolSettings(saved)
            setSavedSchoolSettings(saved)
            setSettingsStatus(successMessage)
            setIsEditingSchool(false)
        } else {
            const error = await res.text()
            setSettingsStatus(`Erreur: ${error.slice(0, 120)}`)
        }
    }

    const saveSchoolSettings = async () => {
        if (!schoolSettings) return
        if (!schoolSettings.name.trim()) {
            setSettingsError("Le nom de l'établissement est obligatoire.")
            return
        }
        if (!schoolSettings.school_type) {
            setSettingsError("Le type d'établissement est obligatoire.")
            return
        }
        if (!schoolSettings.phone?.trim()) {
            setSettingsError("Le numéro de téléphone principal est obligatoire.")
            return
        }
        if (!schoolSettings.email?.trim()) {
            setSettingsError("L'adresse e-mail de l'établissement est obligatoire.")
            return
        }
        const structured = schoolSettings.address_structured || {}
        if (!structured.street || !structured.city || !structured.country) {
            setSettingsError("L'adresse complète doit contenir au minimum la rue, la ville et le pays.")
            return
        }
        await persistSchoolSettings(schoolSettings)
    }

    const startSchoolEdit = () => {
        if (schoolSettings) setSavedSchoolSettings(schoolSettings)
        setSettingsError("")
        setSettingsStatus("")
        setIsEditingSchool(true)
    }

    const cancelSchoolEdit = () => {
        if (savedSchoolSettings) setSchoolSettings(savedSchoolSettings)
        setSettingsError("")
        setSettingsStatus("Modifications annulées.")
        setIsEditingSchool(false)
    }

    const updateSubscription = async (plan: keyof typeof SUBSCRIPTION_PLANS) => {
        if (!schoolSettings) return
        const nextRenewal = new Date()
        nextRenewal.setFullYear(nextRenewal.getFullYear() + 1)
        await persistSchoolSettings({
            ...schoolSettings,
            subscription_plan: plan,
            subscription_status: "active",
            current_billing_period_end: nextRenewal.toISOString(),
        }, `Abonnement ${SUBSCRIPTION_PLANS[plan].label} mis a jour.`)
    }

    const downloadSubscriptionDocument = (type: "invoice" | "receipt") => {
        if (!schoolSettings) return
        const planKey = (schoolSettings.subscription_plan || "free") as keyof typeof SUBSCRIPTION_PLANS
        const plan = SUBSCRIPTION_PLANS[planKey] || SUBSCRIPTION_PLANS.free
        const content = [
            `TeducAI - ${type === "invoice" ? "Facture" : "Recu"} abonnement`,
            `Etablissement: ${schoolSettings.name}`,
            `Plan: ${plan.label}`,
            `Montant annuel: ${plan.yearly.toLocaleString("fr-FR")} FCFA`,
            `Statut: ${SUBSCRIPTION_STATUS_LABELS[schoolSettings.subscription_status || "pending"] || "En attente"}`,
            `Echeance: ${schoolSettings.current_billing_period_end || "-"}`,
        ].join("\n")
        const blob = new Blob([content], { type: "text/plain;charset=utf-8" })
        const url = URL.createObjectURL(blob)
        const link = document.createElement("a")
        link.href = url
        link.download = `teducai-${type}-${schoolSettings.name.replace(/\s+/g, "-").toLowerCase()}.txt`
        document.body.appendChild(link)
        link.click()
        link.remove()
        URL.revokeObjectURL(url)
    }

    useEffect(() => { void loadSchools() }, [loadSchools])
    useEffect(() => { void loadSystemContext() }, [loadSystemContext])
    useEffect(() => { void loadRolePermissions() }, [loadRolePermissions])

    const permissionCategories = catalog ? ["all", ...Array.from(new Set(catalog.modules.map(module => module.category || "Autres"))).sort()] : []
    const visibleModules = catalog?.modules.filter(module => selectedPermissionCategory === "all" || (module.category || "Autres") === selectedPermissionCategory) || []
    const assignedRoles = activeContext?.roles?.length ? activeContext.roles : [user?.role || "staff"]
    const activeRolePermissions = activeRole === activeContext?.active_role ? activeContext?.permissions || permissions : catalog?.defaults?.[activeRole] || []

    return (
        <div className="space-y-6">
            <div>
                <h1 className="apple-page-title">{tx(locale, "settings")}</h1>
                <p className="apple-page-description">Contexte établissement, rôles, permissions, localisation et administration de la plateforme.</p>
            </div>

            <Card>
                <CardHeader><CardTitle>Contexte actif</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid gap-3 text-sm md:grid-cols-4">
                        <Info label="Utilisateur actif" value={activeContext?.user.full_name || user?.full_name || user?.email || "-"} />
                        <Info label="Rôle principal" value={activeContext?.user.role || user?.role || "-"} />
                        <Info label="ID établissement" value={user?.school_id?.toString() || "Plateforme"} />
                        <ExplainedField label="Rôle actif" help="Choisissez le rôle à inspecter. L'interface et les actions sensibles restent contrôlées par les permissions côté API.">
                            <select value={activeRole} onChange={(event) => setActiveRole(event.target.value)} className="apple-select">
                                {assignedRoles.map(role => <option key={role} value={role}>{role}</option>)}
                            </select>
                        </ExplainedField>
                    </div>
                    <div className="rounded-[22px] border border-[#E5E7EB] bg-[#F8FAFC] p-4">
                        <p className="text-sm font-semibold text-[#111827]">Rôles attribués</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                            {assignedRoles.map(role => <span key={role} className="rounded-full border border-[#D1D5DB] bg-white px-3 py-1 text-sm text-[#111827]">{role}</span>)}
                        </div>
                    </div>
                    <div className="rounded-[22px] border border-[#E5E7EB] bg-white p-4">
                        <p className="text-sm font-semibold text-[#111827]">Permissions associées au rôle actif</p>
                        <div className="mt-2 flex max-h-40 flex-wrap gap-2 overflow-y-auto">
                            {activeRolePermissions.length ? activeRolePermissions.map(permission => <span key={permission} className="rounded-md border px-2 py-1 text-xs">{permission}</span>) : <span className="text-sm text-[#6B7280]">Aucune permission spécifique chargée.</span>}
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle>{t("permissions")}</CardTitle></CardHeader>
                <CardContent className="flex flex-wrap gap-2 text-sm">
                    {permissions.map(permission => <span key={permission} className="rounded-md border px-2 py-1">{permission}</span>)}
                </CardContent>
            </Card>

            {schoolSettings && (
                <>
                    <Card>
                        <CardHeader>
                            <div className="flex flex-wrap items-center justify-between gap-3">
                                <CardTitle>Informations de l&apos;établissement</CardTitle>
                                <div className="flex flex-wrap gap-2">
                                    {!isEditingSchool ? (
                                        <Button onClick={startSchoolEdit}>Modifier</Button>
                                    ) : (
                                        <>
                                            <Button onClick={saveSchoolSettings}>Enregistrer</Button>
                                            <Button variant="outline" onClick={cancelSchoolEdit}>Annuler</Button>
                                        </>
                                    )}
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-5">
                            <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
                                <div className="space-y-4">
                                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                                        <ExplainedField label="Nom de l'établissement" required help="Nom officiel utilisé dans toute l'application, les reçus, attestations, bulletins et rapports.">
                                            <input disabled={!isEditingSchool} value={schoolSettings.name} onChange={(event) => updateSchoolSetting("name", event.target.value)} className="apple-input" />
                                        </ExplainedField>
                                        <ExplainedField label="Type d'établissement" required help="Type principal de structure. Il pilote les modèles académiques, niveaux, filières et documents adaptés.">
                                            <select disabled={!isEditingSchool} value={schoolSettings.school_type} onChange={(event) => updateSchoolSetting("school_type", event.target.value)} className="apple-select">
                                                <option value="primary">École primaire</option>
                                                <option value="secondary">Collège</option>
                                                <option value="general">Lycée</option>
                                                <option value="university">Université</option>
                                                <option value="vocational">Centre de formation</option>
                                                <option value="professional">Institut</option>
                                                <option value="technical">Autre</option>
                                            </select>
                                        </ExplainedField>
                                        <ExplainedField label="Téléphone principal" required help="Numéro principal de l'établissement. Il est normalisé selon le pays sélectionné et utilisé dans les documents officiels.">
                                            <input disabled={!isEditingSchool} value={schoolSettings.phone || ""} onChange={(event) => updateSchoolSetting("phone", event.target.value)} className="apple-input" />
                                        </ExplainedField>
                                        <ExplainedField label="Adresse e-mail" required help="Adresse officielle utilisée pour les notifications, contacts administratifs et documents générés.">
                                            <input disabled={!isEditingSchool} type="email" value={schoolSettings.email || ""} onChange={(event) => updateSchoolSetting("email", event.target.value)} className="apple-input" />
                                        </ExplainedField>
                                        <ExplainedField label="Site web" help="Site internet public de l'établissement. Champ facultatif.">
                                            <input disabled={!isEditingSchool} value={schoolSettings.website || ""} onChange={(event) => updateSchoolSetting("website", event.target.value)} className="apple-input" />
                                        </ExplainedField>
                                        <ExplainedField label="Numéro d'enregistrement" help="Numéro administratif, agrément ou identifiant officiel. Champ facultatif.">
                                            <input disabled={!isEditingSchool} value={schoolSettings.registration_number || ""} onChange={(event) => updateSchoolSetting("registration_number", event.target.value)} className="apple-input" />
                                        </ExplainedField>
                                        <ExplainedField label="Logo de l'établissement" help="URL du logo utilisé dans l'interface et les documents. Vous pouvez aussi importer une image locale ci-dessous.">
                                            <input disabled={!isEditingSchool} value={schoolSettings.logo_url || ""} onChange={(event) => updateSchoolSetting("logo_url", event.target.value)} className="apple-input" />
                                        </ExplainedField>
                                        <ExplainedField label="Importer un logo" help="Sélectionnez une image. Elle sera prévisualisée et stockée comme donnée locale encodée pour être immédiatement visible.">
                                            <input disabled={!isEditingSchool} type="file" accept="image/png,image/jpeg,image/webp" className="apple-input pt-2" onChange={(event) => {
                                                const file = event.target.files?.[0]
                                                if (!file) return
                                                const reader = new FileReader()
                                                reader.onload = () => updateSchoolSetting("logo_url", String(reader.result || ""))
                                                reader.readAsDataURL(file)
                                            }} />
                                        </ExplainedField>
                                        <ExplainedField label="Pays" help="Détermine automatiquement la devise, la langue, le fuseau horaire et les formats locaux.">
                                            <select disabled={!isEditingSchool} value={schoolSettings.country_code} onChange={(event) => applyCountryDefaults(event.target.value)} className="apple-select">{Object.entries(countries).map(([code, profile]) => <option key={code} value={code}>{profile.name}</option>)}</select>
                                        </ExplainedField>
                                        <ExplainedField label="Devise" help="Devise utilisée dans les frais, paiements, reçus et rapports financiers.">
                                            <select disabled={!isEditingSchool} value={schoolSettings.default_currency} onChange={(event) => updateSchoolSetting("default_currency", event.target.value)} className="apple-select">{["FCFA", "GBP", "EUR", "USD"].map(currency => <option key={currency} value={currency}>{currency}</option>)}</select>
                                        </ExplainedField>
                                        <ExplainedField label="Langue principale" help="Langue par défaut des interfaces, rapports et documents générés.">
                                            <select disabled={!isEditingSchool} value={schoolSettings.primary_language} onChange={(event) => updateSchoolSetting("primary_language", event.target.value)} className="apple-select"><option value="fr">Français</option><option value="en">English</option><option value="es">Español</option><option value="sw">Kiswahili</option></select>
                                        </ExplainedField>
                                        <ExplainedField label="Fuseau horaire" help="Utilisé pour les horaires, journaux d'audit, clôtures de caisse et notifications.">
                                            <input disabled={!isEditingSchool} value={schoolSettings.timezone} onChange={(event) => updateSchoolSetting("timezone", event.target.value)} className="apple-input" />
                                        </ExplainedField>
                                    </div>
                                    <div className="grid gap-3 md:grid-cols-3">
                                        {["street", "district", "city", "region", "postal_code", "country"].map(key => <ExplainedField key={key} label={humanizeKey(key)} help={fieldHelp(humanizeKey(key), "Adresse complète internationalisée. Les coordonnées GPS sont estimées automatiquement quand l'adresse change.")}><input disabled={!isEditingSchool} value={(schoolSettings.address_structured as Record<string, string> | undefined)?.[key] || ""} onChange={(event) => updateAddress(key, event.target.value)} className="apple-input" /></ExplainedField>)}
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <div className="rounded-[24px] border border-[#E5E7EB] bg-[#F8FAFC] p-4">
                                        <p className="font-semibold text-[#111827]">Logo</p>
                                        <div className="mt-3 flex h-28 items-center justify-center rounded-[20px] border border-dashed border-[#CBD5E1] bg-white">
                                            {schoolSettings.logo_url ? <Image src={schoolSettings.logo_url} alt="Logo établissement" width={240} height={96} unoptimized className="max-h-24 max-w-[80%] object-contain" /> : <span className="text-sm text-[#6B7280]">Aucun logo</span>}
                                        </div>
                                    </div>
                                    <div className="rounded-[24px] border border-[#E5E7EB] bg-white p-4">
                                        <p className="font-semibold text-[#111827]">Localisation</p>
                                        <div className="mt-3 grid gap-3 md:grid-cols-2">
                                            <ExplainedField label="Latitude" help="Coordonnée GPS nord/sud. Peut être saisie manuellement ou mise à jour via la carte.">
                                                <input disabled={!isEditingSchool} type="number" step="0.000001" value={schoolSettings.address_structured?.latitude ?? ""} onChange={(event) => updateCoordinates(Number(event.target.value), Number(schoolSettings.address_structured?.longitude || 0))} className="apple-input" />
                                            </ExplainedField>
                                            <ExplainedField label="Longitude" help="Coordonnée GPS est/ouest. Peut être saisie manuellement ou mise à jour via la carte.">
                                                <input disabled={!isEditingSchool} type="number" step="0.000001" value={schoolSettings.address_structured?.longitude ?? ""} onChange={(event) => updateCoordinates(Number(schoolSettings.address_structured?.latitude || 0), Number(event.target.value))} className="apple-input" />
                                            </ExplainedField>
                                        </div>
                                        <LocationMap
                                            disabled={!isEditingSchool}
                                            latitude={schoolSettings.address_structured?.latitude ?? null}
                                            longitude={schoolSettings.address_structured?.longitude ?? null}
                                            onMove={updateCoordinates}
                                            onPointer={updateMapFromPointer}
                                        />
                                        <p className="mt-3 text-xs text-[#6B7280]">Cliquez ou glissez le marqueur pour ajuster les coordonnées GPS. Cette carte est une prévisualisation intégrée, sans fournisseur externe.</p>
                                    </div>
                                </div>
                            </div>
                            <div className="grid gap-3 text-sm md:grid-cols-3">
                                <Info label="Adresse formatée" value={schoolSettings.formatted_address || "-"} />
                                <Info label="Téléphone international" value={schoolSettings.phone_e164 || "-"} />
                                <Info label="Focus administratif" value={schoolSettings.school_type_profile?.administrative_focus?.join(", ") || "-"} />
                            </div>
                            {settingsError && <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{settingsError}</p>}
                            {settingsStatus && <p className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{settingsStatus}</p>}
                        </CardContent>
                    </Card>

                    <SubscriptionManagement
                        settings={schoolSettings}
                        onChangePlan={updateSubscription}
                        onRenew={() => updateSubscription((schoolSettings.subscription_plan || "pro") as keyof typeof SUBSCRIPTION_PLANS)}
                        onDownload={downloadSubscriptionDocument}
                    />
                </>
            )}

            {catalog && (
                <Card>
                    <CardHeader><CardTitle>Gestion des roles et permissions</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-3 lg:grid-cols-[1fr_1fr_1fr_auto_auto]">
                            <input value={newRole.name} onChange={(event) => setNewRole({ ...newRole, name: event.target.value })} placeholder="Nom du rôle personnalisé" className="apple-input" />
                            <input value={newRole.description} onChange={(event) => setNewRole({ ...newRole, description: event.target.value })} placeholder={tx(locale, "description")} className="apple-input" />
                            <select value={newRole.parent_role_key} onChange={(event) => setNewRole({ ...newRole, parent_role_key: event.target.value })} className="apple-select"><option value="">Sans héritage</option>{catalog.roles.map(role => <option key={role} value={role}>Hériter de {role}</option>)}</select>
                            <Button onClick={createRole}>Creer</Button>
                            <Button variant="outline" onClick={duplicateRole}>Dupliquer</Button>
                        </div>
                        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
                            {roleDefinitions.map(role => (
                                <button key={role.key} onClick={() => setSelectedRole(role.key)} className={`rounded-lg border p-3 text-left text-sm ${selectedRole === role.key ? "border-[#0F766E] bg-[#ECFDF5]" : "border-[#E5E7EB] bg-white"}`}>
                                    <div className="flex items-center justify-between gap-2"><span className="font-semibold text-[#111827]">{role.name}</span><span className="h-3 w-3 rounded-full" style={{ backgroundColor: role.color }} /></div>
                                    <p className="mt-1 text-xs text-[#6B7280]">{role.category || "Role"} - {role.users_count} utilisateur(s)</p>
                                    <p className="mt-1 text-xs text-[#6B7280]">{role.is_system ? "Systeme" : role.is_active ? "Actif" : "Inactif"}</p>
                                </button>
                            ))}
                        </div>
                        <div className="flex flex-wrap items-center gap-3">
                            <select value={selectedRole} onChange={(event) => setSelectedRole(event.target.value)} className="apple-select max-w-xs">{catalog.roles.map(role => <option key={role} value={role}>{role}</option>)}</select>
                            <select value={selectedPermissionCategory} onChange={(event) => setSelectedPermissionCategory(event.target.value)} className="apple-select max-w-xs">
                                {permissionCategories.map(category => <option key={category} value={category}>{category === "all" ? "Toutes les catégories" : category}</option>)}
                            </select>
                            <Button onClick={saveRolePermissions}>{tx(locale, "save")}</Button>
                            {roleDefinitions.find(role => role.key === selectedRole && !role.is_system) && (
                                <>
                                    <Button variant="outline" onClick={() => { const role = roleDefinitions.find(item => item.key === selectedRole); if (role) void toggleRoleStatus(role) }}>Activer / desactiver</Button>
                                    <Button variant="outline" onClick={() => { const role = roleDefinitions.find(item => item.key === selectedRole); if (role) void deleteRole(role) }}>Supprimer</Button>
                                </>
                            )}
                            {permissionStatus && <span className="text-sm text-[#6B7280]">{permissionStatus}</span>}
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {permissionCategories.map(category => <Button key={category} variant={selectedPermissionCategory === category ? "default" : "outline"} size="sm" onClick={() => setSelectedPermissionCategory(category)}>{category === "all" ? "Toutes" : category}</Button>)}
                        </div>
                        <div className="overflow-x-auto rounded-[18px] border border-[#e0e0e0]">
                            <table className="w-full min-w-[980px] text-sm">
                                <thead className="bg-[#f5f5f7]"><tr className="border-b"><th className="px-3 py-3 text-left">Catégorie</th><th className="px-3 py-3 text-left">Module</th>{MATRIX_ACTIONS.map(action => <th key={action} className="px-3 py-3 text-center">{action === "full_access" ? tx(locale, "fullAccess") : humanizeKey(action)}</th>)}</tr></thead>
                                <tbody>{visibleModules.map(module => <tr key={module.key} className="border-b last:border-0"><td className="px-3 py-2 text-[#6e6e73]">{module.category || "Autres"}</td><td className="px-3 py-2 font-medium text-[#1d1d1f]">{module.label}</td>{MATRIX_ACTIONS.map(action => { const permission = `${module.key}:${action}`; return <td key={permission} className="px-3 py-2 text-center"><input type="checkbox" checked={permissionDraft.has(permission)} onChange={() => togglePermission(permission)} className="h-4 w-4 accent-[#0066cc]" /></td> })}</tr>)}</tbody>
                            </table>
                        </div>
                        {rolePermissions && rolePermissions.disabled_permissions.length > 0 && <p className="text-xs text-[#6B7280]">Droits explicitement retires: {rolePermissions.disabled_permissions.join(", ")}</p>}
                        <div className="rounded-lg border bg-[#F8FAFC] p-3 text-sm"><p className="font-medium text-[#111827]">Utilisateurs associes</p><p className="mt-1 text-[#6B7280]">{roleUsers.length ? roleUsers.map(item => item.full_name || item.email).join(", ") : "Aucun utilisateur associe a ce role."}</p></div>
                    </CardContent>
                </Card>
            )}

            {catalog && (
                <Card>
                    <CardHeader><CardTitle>Gestion des utilisateurs</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-3 lg:grid-cols-[1fr_1fr_1fr_0.8fr_1fr_auto]">
                            <input value={newUser.full_name} onChange={(event) => setNewUser({ ...newUser, full_name: event.target.value })} placeholder="Nom complet" className="apple-input" />
                            <input value={newUser.email} onChange={(event) => setNewUser({ ...newUser, email: event.target.value })} placeholder="Email" className="apple-input" />
                            <input value={newUser.password} onChange={(event) => setNewUser({ ...newUser, password: event.target.value })} placeholder="Mot de passe initial" className="apple-input" />
                            <select value={newUser.role} onChange={(event) => setNewUser({ ...newUser, role: event.target.value })} className="apple-select">{catalog.roles.filter(role => PRIMARY_ROLE_KEYS.includes(role)).map(role => <option key={role} value={role}>{role}</option>)}</select>
                            <input value={newUser.role_keys} onChange={(event) => setNewUser({ ...newUser, role_keys: event.target.value })} placeholder="Rôles additionnels séparés par virgule" className="apple-input" />
                            <Button onClick={createManagedUser}>{tx(locale, "create")}</Button>
                        </div>
                        {userStatus && <p className="text-sm text-[#6B7280]">{userStatus}</p>}
                        <div className="overflow-x-auto rounded-lg border"><table className="w-full min-w-[760px] text-sm"><thead className="bg-[#F8FAFC]"><tr className="border-b"><th className="px-3 py-2 text-left">Utilisateur</th><th className="px-3 py-2 text-left">Email</th><th className="px-3 py-2 text-left">Role principal</th><th className="px-3 py-2 text-left">Statut</th><th className="px-3 py-2 text-right">Actions</th></tr></thead><tbody>{users.map(managedUser => <tr key={managedUser.id} className="border-b last:border-0"><td className="px-3 py-2 font-medium">{managedUser.full_name || "-"}</td><td className="px-3 py-2">{managedUser.email}</td><td className="px-3 py-2">{managedUser.role}</td><td className="px-3 py-2">{managedUser.is_active ? "Actif" : "Inactif"}</td><td className="px-3 py-2 text-right"><Button variant="outline" size="sm" onClick={() => toggleUserStatus(managedUser)}>{managedUser.is_active ? "Desactiver" : "Reactiver"}</Button><Button variant="outline" size="sm" className="ml-2" onClick={() => resetUserPassword(managedUser)}>Reset MDP</Button></td></tr>)}</tbody></table></div>
                    </CardContent>
                </Card>
            )}

            <Card>
                <CardHeader><CardTitle>{t("schoolTemplates")}</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex flex-wrap gap-3"><select value={templateChoice} onChange={(e) => setTemplateChoice(e.target.value)} className="apple-select max-w-xs">{Object.keys(templates).map(template => <option key={template} value={template}>{template}</option>)}</select><Button onClick={applyTemplate}>{t("applyTemplate")}</Button></div>
                    {templates[templateChoice] && <div className="grid gap-3 md:grid-cols-3 text-sm"><Info label="Classes" value={templates[templateChoice].classes.join(", ")} /><Info label="Niveaux" value={(templates[templateChoice].levels || []).join(", ")} /><Info label="Matières" value={templates[templateChoice].subjects.join(", ")} /><Info label="Filières / programmes" value={templates[templateChoice].programs.join(", ") || "-"} /><Info label="Diplômes" value={(templates[templateChoice].diplomas || []).join(", ")} /><Info label="Semestres" value={(templates[templateChoice].semesters || []).join(", ")} /><Info label="Certifications" value={(templates[templateChoice].certifications || []).join(", ")} /><Info label="Types d'évaluation" value={(templates[templateChoice].assessment_types || []).join(", ")} /><Info label="Rubriques frais" value={templates[templateChoice].fees.map(fee => fee.name).join(", ")} /></div>}
                </CardContent>
            </Card>

            <Card>
                <CardHeader><CardTitle>{t("auditTrail")}</CardTitle></CardHeader>
                <CardContent>
                    <table className="w-full text-sm"><thead><tr className="border-b"><th className="py-2 text-left">Date</th><th className="py-2 text-left">Action</th><th className="py-2 text-left">Actor</th><th className="py-2 text-left">Status</th></tr></thead><tbody>{auditLogs.map(log => <tr key={log.id} className="border-b last:border-0"><td className="py-2">{new Date(log.created_at).toLocaleString()}</td><td className="py-2">{log.action}</td><td className="py-2">{log.actor_id || "-"}</td><td className="py-2">{log.status_code || "-"}</td></tr>)}</tbody></table>
                </CardContent>
            </Card>

            {user?.role === "super_admin" && (
                <Card>
                    <CardHeader><CardTitle>Schools</CardTitle></CardHeader>
                    <CardContent>
                        <table className="w-full text-sm"><thead><tr className="border-b"><th className="py-2 text-left">School</th><th className="py-2 text-left">Domain</th><th className="py-2 text-left">Type</th><th className="py-2 text-left">Status</th><th className="py-2 text-right">Action</th></tr></thead><tbody>{schools.map(school => <tr key={school.id} className="border-b last:border-0"><td className="py-2 font-medium">{school.name}</td><td className="py-2">{school.domain_prefix}</td><td className="py-2">{school.school_type}</td><td className="py-2">{school.is_active ? "Active" : "Suspended"}</td><td className="py-2 text-right"><Button variant="outline" size="sm" onClick={() => toggleSchool(school)}>{school.is_active ? "Suspend" : "Reactivate"}</Button></td></tr>)}</tbody></table>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}

function Info({ label, value }: { label: string; value: string }) {
    return <div><p className="text-[#6B7280]">{label}</p><p className="font-medium text-[#111827]">{value}</p></div>
}

function LocationMap({
    disabled,
    latitude,
    longitude,
    onMove,
    onPointer,
}: {
    disabled: boolean
    latitude: number | null
    longitude: number | null
    onMove: (latitude: number, longitude: number) => void
    onPointer: (clientX: number, clientY: number, target: HTMLDivElement) => void
}) {
    const safeLatitude = typeof latitude === "number" && Number.isFinite(latitude) ? Math.max(-90, Math.min(90, latitude)) : 5.36
    const safeLongitude = typeof longitude === "number" && Number.isFinite(longitude) ? Math.max(-180, Math.min(180, longitude)) : -4.0083
    const left = ((safeLongitude + 180) / 360) * 100
    const top = ((90 - safeLatitude) / 180) * 100

    const handlePointer = (event: PointerEvent<HTMLDivElement>) => {
        if (disabled) return
        onPointer(event.clientX, event.clientY, event.currentTarget)
    }

    return (
        <div
            role="button"
            tabIndex={disabled ? -1 : 0}
            aria-label="Carte de localisation de l'établissement"
            onClick={handlePointer}
            onKeyDown={(event) => {
                if (disabled) return
                const step = event.shiftKey ? 0.1 : 0.01
                if (event.key === "ArrowUp") onMove(Number((safeLatitude + step).toFixed(6)), safeLongitude)
                if (event.key === "ArrowDown") onMove(Number((safeLatitude - step).toFixed(6)), safeLongitude)
                if (event.key === "ArrowLeft") onMove(safeLatitude, Number((safeLongitude - step).toFixed(6)))
                if (event.key === "ArrowRight") onMove(safeLatitude, Number((safeLongitude + step).toFixed(6)))
            }}
            className={`relative mt-4 h-64 overflow-hidden rounded-[24px] border border-[#CBD5E1] bg-[radial-gradient(circle_at_20%_20%,rgba(59,130,246,0.16),transparent_28%),radial-gradient(circle_at_75%_35%,rgba(16,185,129,0.18),transparent_30%),linear-gradient(135deg,#EFF6FF,#F8FAFC_45%,#ECFDF5)] ${disabled ? "cursor-not-allowed opacity-80" : "cursor-crosshair"}`}
        >
            <div className="absolute inset-0 opacity-60" style={{ backgroundImage: "linear-gradient(#CBD5E1 1px, transparent 1px), linear-gradient(90deg, #CBD5E1 1px, transparent 1px)", backgroundSize: "36px 36px" }} />
            <div className="absolute left-4 top-4 rounded-full bg-white/90 px-3 py-1 text-xs font-medium text-[#111827] shadow-sm">
                {safeLatitude.toFixed(6)}, {safeLongitude.toFixed(6)}
            </div>
            <button
                type="button"
                disabled={disabled}
                aria-label="Déplacer le marqueur GPS"
                onPointerDown={(event) => {
                    if (disabled) return
                    const parent = event.currentTarget.parentElement as HTMLDivElement | null
                    if (!parent) return
                    event.currentTarget.setPointerCapture(event.pointerId)
                    onPointer(event.clientX, event.clientY, parent)
                }}
                onPointerMove={(event) => {
                    if (disabled || !event.buttons) return
                    const parent = event.currentTarget.parentElement as HTMLDivElement | null
                    if (!parent) return
                    onPointer(event.clientX, event.clientY, parent)
                }}
                className="absolute h-8 w-8 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-white bg-black shadow-[0_8px_24px_rgba(0,0,0,0.28)] transition hover:scale-105 disabled:cursor-not-allowed"
                style={{ left: `${left}%`, top: `${top}%` }}
            >
                <span className="sr-only">Marqueur GPS</span>
            </button>
        </div>
    )
}

function SubscriptionManagement({
    settings,
    onChangePlan,
    onRenew,
    onDownload,
}: {
    settings: SchoolSettings
    onChangePlan: (plan: keyof typeof SUBSCRIPTION_PLANS) => void | Promise<void>
    onRenew: () => void | Promise<void>
    onDownload: (type: "invoice" | "receipt") => void
}) {
    const [renderTime, setRenderTime] = useState(0)

    useEffect(() => {
        setRenderTime(Date.now())
    }, [])

    const planKey = ((settings.subscription_plan || "free") in SUBSCRIPTION_PLANS ? settings.subscription_plan || "free" : "free") as keyof typeof SUBSCRIPTION_PLANS
    const plan = SUBSCRIPTION_PLANS[planKey]
    const renewalDate = settings.current_billing_period_end ? new Date(settings.current_billing_period_end) : null
    const daysRemaining = renewalDate && renderTime ? Math.max(0, Math.ceil((renewalDate.getTime() - renderTime) / 86400000)) : 0
    const status = settings.subscription_status || "pending"
    const statusLabel = SUBSCRIPTION_STATUS_LABELS[status] || "En attente"
    const paymentRows = planKey === "free" ? [] : [
        {
            id: "PAY-SAA-001",
            date: renewalDate ? renewalDate.toLocaleDateString("fr-FR") : "-",
            amount: `${plan.yearly.toLocaleString("fr-FR")} FCFA`,
            status: "Payé",
        },
    ]

    return (
        <Card>
            <CardHeader>
                <CardTitle>Gestion des abonnements</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                    <SubscriptionMetric label="Plan actuel" value={plan.label} />
                    <SubscriptionMetric label="Montant payé" value={`${plan.yearly.toLocaleString("fr-FR")} FCFA`} />
                    <SubscriptionMetric label="Prochain renouvellement" value={renewalDate ? renewalDate.toLocaleDateString("fr-FR") : "-"} />
                    <SubscriptionMetric label="Jours restants" value={`${daysRemaining}`} />
                    <SubscriptionMetric label="Statut" value={statusLabel} />
                </div>

                <div className="grid gap-4 lg:grid-cols-3">
                    {Object.entries(SUBSCRIPTION_PLANS).map(([key, item]) => (
                        <button
                            key={key}
                            type="button"
                            onClick={() => onChangePlan(key as keyof typeof SUBSCRIPTION_PLANS)}
                            className={`rounded-[22px] border p-4 text-left transition ${planKey === key ? "border-black bg-black text-white" : "border-[#E5E7EB] bg-white text-[#111827] hover:bg-[#F5F5F7]"}`}
                        >
                            <p className="text-lg font-semibold">{item.label}</p>
                            <p className={`mt-2 text-sm ${planKey === key ? "text-white/80" : "text-[#6B7280]"}`}>{item.monthly.toLocaleString("fr-FR")} FCFA / Mois</p>
                            <p className={`text-sm ${planKey === key ? "text-white/80" : "text-[#6B7280]"}`}>{item.yearly.toLocaleString("fr-FR")} FCFA / An</p>
                        </button>
                    ))}
                </div>

                <div className="grid gap-4 lg:grid-cols-2">
                    <div className="rounded-[22px] border border-[#E5E7EB] bg-white p-4">
                        <div className="flex items-center justify-between gap-3">
                            <div>
                                <h3 className="text-lg font-semibold text-[#111827]">Historique des paiements</h3>
                                <p className="text-sm text-[#6B7280]">Paiements liés à l&apos;abonnement SaaS de l&apos;établissement.</p>
                            </div>
                            <Button variant="outline" onClick={() => onRenew()}>Renouveler</Button>
                        </div>
                        <div className="mt-4 overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead><tr className="border-b"><th className="py-2 text-left">Date</th><th className="py-2 text-left">Montant</th><th className="py-2 text-left">Statut</th></tr></thead>
                                <tbody>
                                    {paymentRows.length ? paymentRows.map(row => (
                                        <tr key={row.id} className="border-b last:border-0"><td className="py-2">{row.date}</td><td className="py-2">{row.amount}</td><td className="py-2">{row.status}</td></tr>
                                    )) : (
                                        <tr><td colSpan={3} className="py-4 text-[#6B7280]">Aucun paiement d&apos;abonnement enregistré.</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div className="rounded-[22px] border border-[#E5E7EB] bg-white p-4">
                        <h3 className="text-lg font-semibold text-[#111827]">Factures et reçus</h3>
                        <p className="mt-1 text-sm text-[#6B7280]">Téléchargez les justificatifs de l&apos;abonnement pour la comptabilité de l&apos;établissement.</p>
                        <div className="mt-5 flex flex-wrap gap-3">
                            <Button onClick={() => onDownload("invoice")}>Télécharger la facture</Button>
                            <Button variant="outline" onClick={() => onDownload("receipt")}>Télécharger le reçu</Button>
                            <Button variant="outline" onClick={() => onChangePlan(planKey === "max" ? "pro" : "max")}>Changer de plan</Button>
                            <Button variant="outline" onClick={() => onChangePlan("max")}>Mettre à niveau</Button>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

function SubscriptionMetric({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-[22px] border border-[#E5E7EB] bg-[#F8FAFC] p-4">
            <p className="text-sm text-[#6B7280]">{label}</p>
            <p className="mt-2 text-xl font-semibold text-[#111827]">{value}</p>
        </div>
    )
}
