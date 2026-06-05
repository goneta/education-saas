"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { usePathname, useParams, useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { normalizeLocale } from "@/lib/i18n"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import {
    Bell,
    BookOpen,
    BrainCircuit,
    Calendar,
    Check,
    ChevronDown,
    ChevronRight,
    ClipboardCheck,
    CreditCard,
    HelpCircle,
    Home,
    LogOut,
    MessageSquare,
    Plus,
    Settings,
    ShieldCheck,
    UserCircle,
    Users,
    GraduationCap,
    BarChart3,
} from "lucide-react"

interface SidebarProps {
    isResizablePanel?: boolean;
}

export function Sidebar({ isResizablePanel = false }: SidebarProps) {
    const pathname = usePathname()
    const params = useParams()
    const router = useRouter()
    const locale = normalizeLocale(params.locale as string)
    const t = useTranslations("navigation")
    const { token, user, logout } = useAuth()

    // State to track open sections. Initially empty means all closed? 
    // Or maybe we want them open by default? 
    // User asked "section should open... reveals items", implying start closed.
    // Let's start with all CLOSED except maybe 'Overview' which has no title.
    const [openSections, setOpenSections] = useState<string[]>([])
    const [accountMenuOpen, setAccountMenuOpen] = useState(false)
    const [switcherOpen, setSwitcherOpen] = useState(false)
    const [addAccountOpen, setAddAccountOpen] = useState(false)
    const [roleOptions, setRoleOptions] = useState<string[]>([])
    const [accountStatus, setAccountStatus] = useState("")
    const [newAccount, setNewAccount] = useState({
        full_name: "",
        email: "",
        password: "SecurePass2026!",
        role: "teacher",
        role_keys: "",
    })

    const toggleSection = (title: string) => {
        setOpenSections(prev =>
            prev.includes(title)
                ? prev.filter(t => t !== title)
                : [...prev, title]
        )
    }

    const sidebarSections = [
        {
            title: "",
            items: [
                { href: `/${locale}/dashboard`, label: t("overview"), icon: Home },
            ]
        },
        {
            title: t("management"),
            items: [
                { href: `/${locale}/dashboard/students`, label: t("students"), icon: Users },
                { href: `/${locale}/dashboard/teachers`, label: t("teachers"), icon: GraduationCap },
            ]
        },
        {
            title: t("academics"),
            items: [
                { href: `/${locale}/dashboard/education/classes`, label: t("classes"), icon: BookOpen },
                { href: `/${locale}/dashboard/education/subjects`, label: t("subjects"), icon: BookOpen },
                { href: `/${locale}/dashboard/education/timetable`, label: t("timetable"), icon: Calendar },
                { href: `/${locale}/dashboard/education/pedagogy`, label: t("pedagogy"), icon: GraduationCap },
                { href: `/${locale}/dashboard/grades/assessments`, label: t("grades"), icon: ClipboardCheck },
                { href: `/${locale}/dashboard/library`, label: t("library"), icon: BookOpen },
                { href: `/${locale}/dashboard/portal`, label: t("portal"), icon: Users },
            ]
        },
        {
            title: t("operations"),
            items: [
                { href: `/${locale}/dashboard/operations`, label: t("operations"), icon: Settings },
                { href: `/${locale}/dashboard/enterprise`, label: t("enterprise"), icon: BarChart3 },
            ]
        },
        {
            title: t("finance"),
            items: [
                { href: `/${locale}/dashboard/finance`, label: t("finance"), icon: CreditCard },
                { href: `/${locale}/dashboard/finance/fees`, label: t("fees"), icon: CreditCard },
                { href: `/${locale}/dashboard/finance/reports`, label: t("reports"), icon: BarChart3 },
                { href: `/${locale}/dashboard/finance/cash-journal`, label: t("cashJournal"), icon: ClipboardCheck },
                { href: `/${locale}/dashboard/finance/forecasts`, label: t("forecasts"), icon: BarChart3 },
                { href: `/${locale}/dashboard/finance/settings`, label: t("feeSettings"), icon: Settings },
                { href: `/${locale}/dashboard/finance/sms`, label: t("sms"), icon: MessageSquare },
            ]
        },
        {
            title: t("system"),
            items: [
                { href: `/${locale}/dashboard/settings`, label: t("settings"), icon: Settings },
            ]
        }
    ]

    const accountRolePresets = useMemo(() => [
        { key: "school_admin", label: "Administrateur d'établissement" },
        { key: "director", label: "Directeur" },
        { key: "principal", label: "Proviseur" },
        { key: "teacher", label: "Enseignant / Formateur" },
        { key: "parent", label: "Parent d'élève" },
        { key: "student", label: "Élève / Étudiant" },
        { key: "receptionist", label: "Réceptionniste" },
        { key: "accountant", label: "Comptable" },
        { key: "pedagogy_coordinator", label: "Coordinateur" },
        { key: "secretary", label: "Secrétaire" },
        { key: "registrar", label: "Responsable des admissions" },
    ], [])

    const availableRoles = useMemo(() => {
        const known = new Set(accountRolePresets.map(role => role.key))
        const configured = roleOptions
            .filter(role => !known.has(role))
            .map(role => ({ key: role, label: role.replace(/_/g, " ") }))
        return [...accountRolePresets, ...configured]
    }, [accountRolePresets, roleOptions])

    const displayName = user?.full_name || user?.email || "Utilisateur"
    const initials = displayName
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map(part => part[0]?.toUpperCase())
        .join("") || "TU"

    useEffect(() => {
        if (!token || !addAccountOpen) return
        fetch(`${API_BASE_URL}/system/permissions/catalog`, {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then(response => response.ok ? response.json() : null)
            .then(data => {
                if (Array.isArray(data?.roles)) setRoleOptions(data.roles)
            })
            .catch(() => undefined)
    }, [addAccountOpen, token])

    const createAccount = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!token) return
        setAccountStatus("Création du compte...")
        const roleKeys = newAccount.role_keys.split(",").map(role => role.trim()).filter(Boolean)
        if (!roleKeys.includes(newAccount.role)) roleKeys.push(newAccount.role)
        const res = await fetch(`${API_BASE_URL}/system/users`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                email: newAccount.email,
                full_name: newAccount.full_name,
                password: newAccount.password,
                role: newAccount.role,
                role_keys: roleKeys,
            }),
        })
        if (res.ok) {
            setAccountStatus("Compte créé avec les rôles sélectionnés.")
            setNewAccount({ full_name: "", email: "", password: "SecurePass2026!", role: "teacher", role_keys: "" })
        } else {
            const error = await res.text()
            setAccountStatus(`Création impossible: ${error.slice(0, 120)}`)
        }
    }

    const handleLogout = () => {
        logout()
        router.push(`/${locale}/login`)
    }

    return (
        <div className={cn(
            "hidden md:flex w-64 h-full flex-col bg-white",
            !isResizablePanel && "fixed top-0 left-0 bottom-0 z-30",
            isResizablePanel && "w-full border-r-0"
        )}>
            <div className="flex h-14 items-center border-b border-[#E5E7EB] px-4 lg:h-[60px] lg:px-6">
                <Link href={`/${locale}`} className="flex items-center gap-2 font-semibold text-[#111827]">
                    <BrainCircuit className="h-6 w-6 text-primary" />
                    <span className="">TeducAI</span>
                </Link>
            </div>
            <div className="flex-1 overflow-y-auto">
                <nav className="grid items-start px-2 text-sm font-medium lg:px-4 space-y-2 mt-4">
                    {sidebarSections.map((section, idx) => {
                        const isOpen = !section.title || openSections.includes(section.title)

                        return (
                            <div key={idx} className="mb-2">
                                {section.title ? (
                                    <button
                                        onClick={() => toggleSection(section.title)}
                                        className="flex w-full items-center justify-between px-4 py-2 hover:bg-gray-50 rounded-md transition-colors group"
                                    >
                                        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400 group-hover:text-gray-600">
                                            {section.title}
                                        </h4>
                                        <ChevronDown className={cn(
                                            "h-4 w-4 text-gray-400 transition-transform duration-200",
                                            isOpen ? "transform rotate-180" : ""
                                        )} />
                                    </button>
                                ) : (
                                    // For items without a section title (Overview), strictly wrap? 
                                    // Actually the design usually just lists them.
                                    // But we need to maintain the loop structure.
                                    null
                                )}

                                <div className={cn(
                                    "grid transition-all duration-300 ease-in-out",
                                    isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                                )}>
                                    <div className="overflow-hidden">
                                        <div className="space-y-1 mt-1">
                                            {section.items.map((item) => {
                                                const Icon = item.icon
                                                const isActive = pathname === item.href || (item.href !== `/${locale}/dashboard` && pathname?.startsWith(item.href))
                                                return (
                                                    <Link
                                                        key={item.href}
                                                        href={item.href}
                                                        className={cn(
                                                            "flex items-center gap-3 rounded-lg px-3 py-2 transition-all",
                                                            isActive
                                                                ? "bg-[#F0F1F3] text-[#111827] font-medium"
                                                                : "text-[#6B7280] hover:text-[#111827]"
                                                        )}
                                                    >
                                                        <Icon className="h-4 w-4" />
                                                        {item.label}
                                                    </Link>
                                                )
                                            })}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </nav>
            </div>
            {user && (
                <div className="relative border-t border-[#E5E7EB] p-3">
                    {accountMenuOpen && (
                        <div className="absolute bottom-[76px] left-3 z-50 w-[280px] rounded-[24px] border border-[#E5E7EB] bg-white p-3 shadow-[0_22px_60px_rgba(15,23,42,0.18)]">
                            <button
                                type="button"
                                onClick={() => setSwitcherOpen(prev => !prev)}
                                className="flex w-full items-center gap-3 rounded-[18px] bg-[#F5F5F7] px-3 py-3 text-left transition hover:bg-[#EEEEF1]"
                            >
                                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#EF4444] text-sm font-semibold text-white">{initials}</span>
                                <span className="min-w-0 flex-1">
                                    <span className="block truncate text-[15px] font-semibold text-[#111827]">{displayName}</span>
                                    <span className="block truncate text-sm text-[#6B7280]">{user.role}</span>
                                </span>
                                <ChevronRight className="h-5 w-5 text-[#111827]" />
                            </button>
                            {switcherOpen && (
                                <div className="absolute bottom-[190px] left-[260px] z-[60] w-[320px] rounded-[24px] border border-[#E5E7EB] bg-white p-4 shadow-[0_22px_60px_rgba(15,23,42,0.18)]">
                                    <div className="flex items-center gap-3 text-[#4B5563]">
                                        <UserCircle className="h-6 w-6" />
                                        <span className="truncate text-[15px]">{user.email}</span>
                                    </div>
                                    <div className="mt-4 flex items-center gap-3 border-b border-[#E5E7EB] pb-4">
                                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#EF4444] text-xs font-semibold text-white">{initials}</span>
                                        <span className="min-w-0 flex-1 truncate font-semibold text-[#111827]">{displayName}</span>
                                        <Check className="h-5 w-5 text-[#111827]" />
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => { setAddAccountOpen(true); setSwitcherOpen(false); setAccountMenuOpen(false) }}
                                        className="mt-3 flex w-full items-center gap-3 rounded-[16px] px-2 py-3 text-left text-[16px] text-[#111827] transition hover:bg-[#F5F5F7]"
                                    >
                                        <Plus className="h-6 w-6" />
                                        + Ajouter un compte
                                    </button>
                                </div>
                            )}
                            <div className="mt-3 space-y-1 border-t border-[#E5E7EB] pt-3">
                                <Link href={`/${locale}/dashboard/settings`} className="flex items-center gap-3 rounded-[16px] px-3 py-2.5 text-[#111827] transition hover:bg-[#F5F5F7]"><UserCircle className="h-5 w-5" />Mon Profil</Link>
                                <Link href={`/${locale}/dashboard/settings`} className="flex items-center gap-3 rounded-[16px] px-3 py-2.5 text-[#111827] transition hover:bg-[#F5F5F7]"><Settings className="h-5 w-5" />Paramètres du compte</Link>
                                <Link href={`/${locale}/dashboard/enterprise`} className="flex items-center gap-3 rounded-[16px] px-3 py-2.5 text-[#111827] transition hover:bg-[#F5F5F7]"><Bell className="h-5 w-5" />Notifications</Link>
                                <button type="button" onClick={() => setSwitcherOpen(prev => !prev)} className="flex w-full items-center justify-between rounded-[16px] px-3 py-2.5 text-left text-[#111827] transition hover:bg-[#F5F5F7]"><span className="flex items-center gap-3"><ShieldCheck className="h-5 w-5" />Changer de compte</span><ChevronRight className="h-4 w-4" /></button>
                                <Link href={`/${locale}/pricing`} className="flex items-center gap-3 rounded-[16px] px-3 py-2.5 text-[#111827] transition hover:bg-[#F5F5F7]"><CreditCard className="h-5 w-5" />Mettre à niveau</Link>
                                <Link href={`/${locale}/contact`} className="flex items-center gap-3 rounded-[16px] px-3 py-2.5 text-[#111827] transition hover:bg-[#F5F5F7]"><HelpCircle className="h-5 w-5" />Aide</Link>
                                <button type="button" onClick={handleLogout} className="flex w-full items-center gap-3 rounded-[16px] px-3 py-2.5 text-left text-[#111827] transition hover:bg-[#F5F5F7]"><LogOut className="h-5 w-5" />Déconnexion</button>
                            </div>
                            <button
                                type="button"
                                onClick={() => { setAddAccountOpen(true); setAccountMenuOpen(false) }}
                                className="mt-3 flex w-full items-center gap-3 rounded-[16px] border border-[#E5E7EB] px-3 py-2.5 text-left text-[#111827] transition hover:bg-[#F5F5F7]"
                            >
                                <Plus className="h-5 w-5" />
                                + Ajouter un compte
                            </button>
                        </div>
                    )}
                    <button
                        type="button"
                        onClick={() => setAccountMenuOpen(prev => !prev)}
                        className="flex w-full items-center gap-3 rounded-[18px] px-2 py-2 text-left transition hover:bg-[#F5F5F7]"
                    >
                        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#EF4444] text-sm font-semibold text-white">{initials}</span>
                        <span className="min-w-0 flex-1">
                            <span className="block truncate text-[15px] font-semibold text-[#111827]">{displayName}</span>
                            <span className="block truncate text-sm text-[#6B7280]">{user.role}</span>
                        </span>
                        <ChevronRight className="h-5 w-5 text-[#6B7280]" />
                    </button>
                </div>
            )}
            {addAccountOpen && (
                <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/30 p-4">
                    <div className="w-full max-w-xl rounded-[28px] bg-white p-6 shadow-[0_28px_90px_rgba(15,23,42,0.25)]">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <h2 className="text-2xl font-semibold text-[#111827]">Ajouter un compte</h2>
                                <p className="mt-1 text-sm text-[#6B7280]">Créez rapidement un utilisateur avec le rôle principal et les rôles additionnels de l’établissement.</p>
                            </div>
                            <button type="button" onClick={() => setAddAccountOpen(false)} className="rounded-full px-3 py-1 text-2xl leading-none text-[#6B7280] hover:bg-[#F5F5F7]">×</button>
                        </div>
                        <form onSubmit={createAccount} className="mt-5 grid gap-3">
                            <input value={newAccount.full_name} onChange={event => setNewAccount({ ...newAccount, full_name: event.target.value })} required placeholder="Nom complet" className="apple-input" title="Nom complet: saisissez le nom officiel affiché dans les comptes, rapports et journaux d'audit." />
                            <input type="email" value={newAccount.email} onChange={event => setNewAccount({ ...newAccount, email: event.target.value })} required placeholder="Email" className="apple-input" title="Email: identifiant de connexion et adresse utilisée pour les notifications du compte." />
                            <input value={newAccount.password} onChange={event => setNewAccount({ ...newAccount, password: event.target.value })} required placeholder="Mot de passe initial" className="apple-input" title="Mot de passe initial: il doit respecter la politique de sécurité et pourra être réinitialisé par l'administrateur." />
                            <select value={newAccount.role} onChange={event => setNewAccount({ ...newAccount, role: event.target.value })} className="apple-select" title="Rôle principal: détermine les permissions de base appliquées au compte.">
                                {availableRoles.map(role => <option key={role.key} value={role.key}>{role.label}</option>)}
                            </select>
                            <input value={newAccount.role_keys} onChange={event => setNewAccount({ ...newAccount, role_keys: event.target.value })} placeholder="Rôles additionnels séparés par virgule" className="apple-input" title="Rôles additionnels: ajoutez ici des rôles personnalisés ou secondaires, séparés par virgule." />
                            {accountStatus && <p className="text-sm text-[#6B7280]">{accountStatus}</p>}
                            <div className="mt-2 flex flex-wrap justify-end gap-3">
                                <button type="button" onClick={() => setAddAccountOpen(false)} className="rounded-full border border-[#D1D5DB] px-5 py-2.5 text-[#111827] hover:bg-[#F5F5F7]">Annuler</button>
                                <button type="submit" className="rounded-full bg-black px-5 py-2.5 font-medium text-white hover:bg-black/90">Créer le compte</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
