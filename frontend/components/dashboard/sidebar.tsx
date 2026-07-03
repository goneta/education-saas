"use client"

import { FormEvent, useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import { usePathname, useParams, useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { normalizeLocale } from "@/lib/i18n"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import {
    BookOpen,
    BriefcaseBusiness,
    BrainCircuit,
    Calendar,
    ChevronDown,
    ChevronRight,
    ClipboardCheck,
    CreditCard,
    HelpCircle,
    Home,
    LogOut,
    MessageSquare,
    Settings,
    UserCircle,
    Users,
    GraduationCap,
    BarChart3,
    FileText,
    Lock,
    Mail,
    Receipt,
    RefreshCw,
    Share2,
    ShieldCheck,
    WalletCards,
    Bus,
    Truck,
    Route as RouteIcon,
    MapPin,
    UserCog,
    Navigation,
    ScanLine,
    Wrench,
    Building2,
    DoorOpen,
    Webhook,
    BellRing,
    FileCheck2,
    CalendarCheck,
} from "lucide-react"

interface SidebarProps {
    isResizablePanel?: boolean;
    forceVisible?: boolean;
    onNavigate?: () => void;
}

export function Sidebar({ isResizablePanel = false, forceVisible = false, onNavigate }: SidebarProps) {
    const pathname = usePathname()
    const params = useParams()
    const router = useRouter()
    const locale = normalizeLocale(params.locale as string)
    const t = useTranslations("navigation")
    const accountT = useTranslations("account")
    const appT = useTranslations("app")
    const { token, user, logout } = useAuth()

    // State to track open sections. Initially empty means all closed? 
    // Or maybe we want them open by default? 
    // User asked "section should open... reveals items", implying start closed.
    // Let's start with all CLOSED except maybe 'Overview' which has no title.
    const [openSections, setOpenSections] = useState<string[]>([])
    const [accountMenuOpen, setAccountMenuOpen] = useState(false)
    const [addAccountOpen, setAddAccountOpen] = useState(false)
    const [roleOptions, setRoleOptions] = useState<string[]>([])
    const [accountStatus, setAccountStatus] = useState("")
    const [newAccount, setNewAccount] = useState({
        full_name: "",
        email: "",
        password: "",
        role: "teacher",
        role_keys: "",
    })
    const accountMenuRef = useRef<HTMLDivElement | null>(null)

    const sidebarItemClass = "flex w-full items-center gap-3 rounded-[16px] px-3 py-2.5 text-left text-[16px] font-normal text-[#111827] transition hover:bg-[#F5F5F7] dark:text-[#f4f7fb] dark:hover:bg-[#30373d]"
    const accountLinks = [
        { href: `/${locale}/dashboard/account/overview`, label: accountT("overview"), icon: UserCircle },
        { href: `/${locale}/dashboard/account/renewals`, label: accountT("renewals"), icon: RefreshCw },
        { href: `/${locale}/dashboard/account/security`, label: accountT("security"), icon: Lock },
        { href: `/${locale}/dashboard/account/sessions`, label: accountT("sessions"), icon: ShieldCheck },
        { href: `/${locale}/dashboard/account/contact`, label: accountT("contact"), icon: UserCircle },
        { href: `/${locale}/dashboard/account/payment-methods`, label: accountT("paymentMethods"), icon: CreditCard },
        { href: `/${locale}/dashboard/account/credit`, label: accountT("credit"), icon: WalletCards },
        { href: `/${locale}/dashboard/account/invoices`, label: accountT("invoices"), icon: Receipt },
        { href: `/${locale}/dashboard/account/preferences`, label: accountT("preferences"), icon: Settings },
        { href: `/${locale}/dashboard/account/email-notifications`, label: accountT("emailNotifications"), icon: Mail },
        { href: `/${locale}/dashboard/account/team-members`, label: accountT("teamMembers"), icon: Users },
        { href: `/${locale}/dashboard/account/refer`, label: accountT("refer"), icon: Share2 },
    ]

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
                { href: `/${locale}/dashboard/buildings`, label: t("buildings"), icon: Building2 },
                { href: `/${locale}/dashboard/rooms`, label: t("rooms"), icon: DoorOpen },
                { href: `/${locale}/dashboard/personnel`, label: t("personnel"), icon: UserCog },
                { href: `/${locale}/dashboard/hr/leave`, label: t("leave"), icon: Calendar },
                { href: `/${locale}/dashboard/communication`, label: t("announcements"), icon: MessageSquare },
            ]
        },
        {
            title: t("academics"),
            items: [
                { href: `/${locale}/dashboard/education/classes`, label: t("classes"), icon: BookOpen },
                { href: `/${locale}/dashboard/education/subjects`, label: t("subjects"), icon: BookOpen },
                { href: `/${locale}/dashboard/education/timetable`, label: t("timetable"), icon: Calendar },
                { href: `/${locale}/dashboard/education/pedagogy`, label: t("pedagogy"), icon: GraduationCap },
                { href: `/${locale}/dashboard/education/internships`, label: t("internships"), icon: BriefcaseBusiness },
                { href: `/${locale}/dashboard/grades/assessments`, label: t("grades"), icon: ClipboardCheck },
                { href: `/${locale}/dashboard/library`, label: t("library"), icon: BookOpen },
                { href: `/${locale}/dashboard/portal`, label: t("portal"), icon: Users },
                { href: `/${locale}/dashboard/documents`, label: t("documents"), icon: FileText },
            ]
        },
        {
            title: t("operations"),
            items: [
                { href: `/${locale}/dashboard/operations`, label: t("operations"), icon: Settings },
                { href: `/${locale}/dashboard/enterprise`, label: t("enterprise"), icon: BarChart3 },
                { href: `/${locale}/dashboard/emploi`, label: "Emploi et CV", icon: BriefcaseBusiness },
                { href: `/${locale}/dashboard/emploi-recruteur`, label: "Espace recruteur", icon: BriefcaseBusiness },
                { href: `/${locale}/dashboard/emploi-admin`, label: "Admin Emploi", icon: ShieldCheck },
            ]
        },
        {
            title: t("smartTransport"),
            items: [
                { href: `/${locale}/dashboard/transport`, label: t("transportDashboard"), icon: BarChart3 },
                { href: `/${locale}/dashboard/transport/drivers`, label: t("drivers"), icon: UserCog },
                { href: `/${locale}/dashboard/transport/vehicles`, label: t("vehicles"), icon: Bus },
                { href: `/${locale}/dashboard/transport/routes`, label: t("routes"), icon: RouteIcon },
                { href: `/${locale}/dashboard/transport/stops`, label: t("stops"), icon: MapPin },
                { href: `/${locale}/dashboard/transport/assignments`, label: t("transportAssignments"), icon: Truck },
                { href: `/${locale}/dashboard/transport/tracking`, label: t("tracking"), icon: Navigation },
                { href: `/${locale}/dashboard/transport/boarding`, label: t("boarding"), icon: ScanLine },
                { href: `/${locale}/dashboard/transport/fleet-ops`, label: t("fleetOps"), icon: Wrench },
            ]
        },
        {
            title: t("finance"),
            items: [
                { href: `/${locale}/dashboard/finance`, label: t("finance"), icon: CreditCard },
                { href: `/${locale}/dashboard/finance/payroll`, label: t("payroll"), icon: Receipt },
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
                { href: `/${locale}/dashboard/ai-command-center`, label: t("aiCommandCenter"), icon: BrainCircuit },
                { href: `/${locale}/dashboard/ai-credits`, label: t("aiCredits"), icon: CreditCard },
                { href: `/${locale}/dashboard/levels`, label: t("schoolLevels"), icon: GraduationCap },
                { href: `/${locale}/dashboard/extensibility`, label: t("integrations"), icon: Webhook },
                { href: `/${locale}/dashboard/automations`, label: t("automations"), icon: BellRing },
                { href: `/${locale}/dashboard/settings`, label: t("settings"), icon: Settings },
            ]
        }
    ]

    // Role-based dashboards (#8): Teacher / Student / Parent never see the admin
    // menus (Gestion, Scolarité admin, Finances admin, Opérations, Système).
    // Each gets a curated menu of existing routes. All other roles (Super Admin,
    // School Admin and operational staff) keep the full menu unchanged.
    const role = String(user?.role || "").toLowerCase()
    const overviewSection = sidebarSections[0]

    const teacherMenu = [
        overviewSection,
        {
            title: t("academics"),
            items: [
                { href: `/${locale}/dashboard/education/classes`, label: t("classes"), icon: BookOpen },
                { href: `/${locale}/dashboard/education/subjects`, label: t("subjects"), icon: BookOpen },
                { href: `/${locale}/dashboard/education/timetable`, label: t("timetable"), icon: Calendar },
                { href: `/${locale}/dashboard/education/pedagogy`, label: t("pedagogy"), icon: GraduationCap },
                { href: `/${locale}/dashboard/grades/assessments`, label: t("grades"), icon: ClipboardCheck },
                { href: `/${locale}/dashboard/remediation`, label: t("remediation"), icon: GraduationCap },
                { href: `/${locale}/dashboard/documents`, label: t("documents"), icon: FileText },
                { href: `/${locale}/dashboard/library`, label: t("library"), icon: BookOpen },
                { href: `/${locale}/dashboard/portal`, label: t("portal"), icon: Users },
            ],
        },
        {
            title: t("finance"),
            items: [
                { href: `/${locale}/dashboard/finance/my-payslips`, label: t("myPayslips"), icon: Receipt },
                { href: `/${locale}/dashboard/hr/leave`, label: t("leave"), icon: Calendar },
            ],
        },
        {
            title: t("system"),
            items: [
                { href: `/${locale}/dashboard/ai-command-center`, label: t("aiCommandCenter"), icon: BrainCircuit },
            ],
        },
    ]

    const studentMenu = [
        overviewSection,
        {
            title: t("academics"),
            items: [
                { href: `/${locale}/dashboard/education/timetable`, label: t("timetable"), icon: Calendar },
                { href: `/${locale}/dashboard/grades/assessments`, label: t("grades"), icon: ClipboardCheck },
                { href: `/${locale}/dashboard/documents`, label: t("documents"), icon: FileText },
                { href: `/${locale}/dashboard/my-documents`, label: t("myDocuments"), icon: FileCheck2 },
                { href: `/${locale}/dashboard/study-plan`, label: t("studyPlan"), icon: CalendarCheck },
                { href: `/${locale}/dashboard/library`, label: t("library"), icon: BookOpen },
                { href: `/${locale}/dashboard/education/internships`, label: t("internships"), icon: BriefcaseBusiness },
                { href: `/${locale}/dashboard/portal`, label: t("portal"), icon: Users },
            ],
        },
        {
            title: t("finance"),
            items: [
                { href: `/${locale}/dashboard/finance`, label: t("finance"), icon: CreditCard },
            ],
        },
    ]

    const parentMenu = [
        overviewSection,
        {
            title: t("academics"),
            items: [
                { href: `/${locale}/dashboard/portal`, label: t("portal"), icon: Users },
                { href: `/${locale}/dashboard/grades/assessments`, label: t("grades"), icon: ClipboardCheck },
                { href: `/${locale}/dashboard/documents`, label: t("documents"), icon: FileText },
                { href: `/${locale}/dashboard/my-documents`, label: t("myDocuments"), icon: FileCheck2 },
                { href: `/${locale}/dashboard/study-plan`, label: t("studyPlan"), icon: CalendarCheck },
            ],
        },
        {
            title: t("finance"),
            items: [
                { href: `/${locale}/dashboard/finance`, label: t("finance"), icon: CreditCard },
            ],
        },
    ]

    let visibleSections = sidebarSections
    if (["teacher", "trainer", "instructor", "educator"].includes(role)) visibleSections = teacherMenu
    else if (["student", "pupil"].includes(role)) visibleSections = studentMenu
    else if (["parent", "guardian"].includes(role)) visibleSections = parentMenu

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
    const accountType = user?.account_type || (user?.role === "recruiter" ? "recruiter" : user?.is_external_student ? "external_student" : "school_user")
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

    useEffect(() => {
        if (!accountMenuOpen) return
        const closeOnOutsideClick = (event: MouseEvent | TouchEvent) => {
            if (accountMenuRef.current && !accountMenuRef.current.contains(event.target as Node)) {
                setAccountMenuOpen(false)
            }
        }
        document.addEventListener("mousedown", closeOnOutsideClick)
        document.addEventListener("touchstart", closeOnOutsideClick, { passive: true })
        return () => {
            document.removeEventListener("mousedown", closeOnOutsideClick)
            document.removeEventListener("touchstart", closeOnOutsideClick)
        }
    }, [accountMenuOpen])

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
            setNewAccount({ full_name: "", email: "", password: "", role: "teacher", role_keys: "" })
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
            "h-full min-h-0 w-64 flex-col bg-white font-sans dark:bg-[#1f2427]",
            forceVisible ? "flex" : "hidden md:flex",
            !isResizablePanel && "fixed bottom-0 left-0 top-0 z-[80]",
            isResizablePanel && "relative z-[80] w-full overflow-visible border-r-0"
        )}>
            <div className="flex h-14 items-center border-b border-[#E5E7EB] px-4 lg:h-[60px] lg:px-6 dark:border-[#3a4248]">
                <Link href={`/${locale}`} className="flex items-center gap-2 font-semibold text-[#111827] dark:text-white">
                    <BrainCircuit className="h-6 w-6 text-primary" />
                    <span className="">TeducAI</span>
                </Link>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
                <nav className="grid items-start px-2 text-sm font-medium lg:px-4 space-y-2 mt-4">
                    {visibleSections.map((section, idx) => {
                        const items = section.items.filter(item => {
                            if (accountType === "recruiter") {
                                return item.href.includes("/dashboard/emploi-recruteur")
                            }
                            if (accountType === "external_student") {
                                return item.href.includes("/dashboard/emploi") && !item.href.includes("/dashboard/emploi-recruteur")
                            }
                            if (item.href.includes("/dashboard/emploi-recruteur")) return false
                            if (item.href.includes("/dashboard/emploi-admin") && user?.role !== "super_admin") return false
                            if (item.href.endsWith("/dashboard/emploi")) return user?.role === "student"
                            return true
                        })
                        if (!items.length) return null
                        const isOpen = !section.title || openSections.includes(section.title)

                        return (
                            <div key={idx} className="mb-2">
                                {section.title ? (
                                    <button
                                        onClick={() => toggleSection(section.title)}
                                        className="group flex w-full items-center justify-between rounded-[16px] px-3 py-2.5 text-left text-[16px] font-normal text-[#111827] transition hover:bg-[#F5F5F7] dark:text-[#f4f7fb] dark:hover:bg-[#30373d]"
                                    >
                                        <h4 className="font-normal">
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
                                            {items.map((item) => {
                                                const Icon = item.icon
                                                const isActive = pathname === item.href || (item.href !== `/${locale}/dashboard` && pathname?.startsWith(item.href))
                                                return (
                                                    <Link
                                                        key={item.href}
                                                        href={item.href}
                                                        onClick={onNavigate}
                                                        className={cn(
                                                            sidebarItemClass,
                                                            isActive
                                                                ? "bg-[#F5F5F7] font-medium dark:bg-[#30373d] dark:text-white"
                                                                : ""
                                                        )}
                                                    >
                                                        <Icon className="h-4 w-4 text-current" />
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
                <div ref={accountMenuRef} className="relative z-[120] border-t border-[#E5E7EB] bg-white p-3 dark:border-[#3a4248] dark:bg-[#1f2427]">
                    {accountMenuOpen && (
                        <div className="absolute bottom-[76px] left-3 z-[1000] max-h-[72vh] w-[300px] overflow-y-auto rounded-[24px] border border-[#E5E7EB] bg-white p-3 shadow-[0_22px_60px_rgba(15,23,42,0.18)] dark:border-[#3a4248] dark:bg-[#252525] dark:shadow-[0_24px_80px_rgba(0,0,0,0.48)]">
                            <div className="space-y-1">
                                {accountLinks.map(({ href, label, icon: Icon }) => (
                                    <Link key={href} href={href} onClick={onNavigate} className={sidebarItemClass}><Icon className="h-5 w-5" />{label}</Link>
                                ))}
                                <Link href={`/${locale}/dashboard/help`} onClick={onNavigate} className={sidebarItemClass}><HelpCircle className="h-5 w-5" />Aide</Link>
                                <button type="button" onClick={handleLogout} className={sidebarItemClass}><LogOut className="h-5 w-5" />{appT("logout")}</button>
                                <button type="button" onClick={() => { setAddAccountOpen(true); setAccountMenuOpen(false) }} className={sidebarItemClass}><Users className="h-5 w-5" />Ajouter un compte</button>
                            </div>
                        </div>
                    )}
                    <button
                        type="button"
                        onClick={() => setAccountMenuOpen(prev => !prev)}
                        className="flex w-full items-center gap-3 rounded-[18px] px-2 py-2 text-left transition hover:bg-[#F5F5F7] dark:hover:bg-[#30373d]"
                    >
                        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#EF4444] text-sm font-semibold text-white">{initials}</span>
                        <span className="min-w-0 flex-1">
                            <span className="block truncate text-[15px] font-semibold text-[#111827] dark:text-white">{displayName}</span>
                            <span className="block truncate text-sm text-[#6B7280]">{user.role}</span>
                        </span>
                        <ChevronRight className="h-5 w-5 text-[#6B7280]" />
                    </button>
                </div>
            )}
            {addAccountOpen && (
                <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/30 p-4">
                    <div className="w-full max-w-xl rounded-[28px] border border-[#E5E7EB] bg-white p-6 shadow-[0_28px_90px_rgba(15,23,42,0.25)] dark:border-[#3b4248] dark:bg-[#202528]">
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
