"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { UserPlus, Users, Trash2 } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface Staff {
    id: number
    user_id: number
    full_name?: string | null
    email?: string | null
    phone_number?: string | null
    primary_role?: string | null
    additional_roles: string[]
    department_id?: number | null
    department_name?: string | null
    job_title?: string | null
    status: string
    is_active: boolean
    generated_password?: string | null
}
interface Department { id: number; name: string }

const ROLE_KEYS = ["director", "principal", "department_head", "pedagogy_coordinator", "educator", "teacher", "secretary", "registrar", "receptionist", "accountant", "cashier", "staff"]
const STATUSES = ["active", "inactive", "suspended", "on_leave"]

export default function PersonnelPage() {
    const t = useTranslations("personnel")
    const { token } = useAuth()
    const [staff, setStaff] = useState<Staff[]>([])
    const [departments, setDepartments] = useState<Department[]>([])
    const [form, setForm] = useState({ full_name: "", email: "", phone_number: "", primary_role: "staff", additional_roles: [] as string[], department_id: "", job_title: "", status: "active" })
    const [error, setError] = useState<string | null>(null)
    const [notice, setNotice] = useState<string | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])
    const roleLabel = (r?: string | null) => r ? (ROLE_KEYS.includes(r) ? t(`roles.${r}` as "roles.staff") : r) : "—"

    const load = useCallback(async () => {
        if (!headers) return
        const [s, d] = await Promise.all([
            fetch(`${API_BASE_URL}/personnel`, { headers }),
            fetch(`${API_BASE_URL}/platform/departments`, { headers }),
        ])
        if (s.ok) setStaff(await s.json())
        if (d.ok) setDepartments(await d.json())
    }, [headers])

    useEffect(() => { void load() }, [load])

    const toggleAdditional = (role: string) => setForm(f => ({ ...f, additional_roles: f.additional_roles.includes(role) ? f.additional_roles.filter(r => r !== role) : [...f.additional_roles, role] }))

    const create = async () => {
        if (!headers || !form.full_name.trim() || !form.email.trim()) return
        setError(null); setNotice(null)
        const res = await fetch(`${API_BASE_URL}/personnel`, {
            method: "POST", headers,
            body: JSON.stringify({
                full_name: form.full_name.trim(), email: form.email.trim(), phone_number: form.phone_number || null,
                primary_role: form.primary_role, additional_roles: form.additional_roles,
                department_id: form.department_id ? Number(form.department_id) : null, job_title: form.job_title || null, status: form.status,
            }),
        })
        if (res.ok) {
            const created: Staff = await res.json()
            if (created.generated_password) setNotice(`${t("passwordGenerated")} ${created.generated_password}`)
            setForm({ full_name: "", email: "", phone_number: "", primary_role: "staff", additional_roles: [], department_id: "", job_title: "", status: "active" })
            void load()
        } else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const changeStatus = async (s: Staff, status: string) => {
        if (!headers) return
        if ((await fetch(`${API_BASE_URL}/personnel/${s.id}`, { method: "PATCH", headers, body: JSON.stringify({ status, is_active: status === "active" }) })).ok) void load()
    }
    const remove = async (s: Staff) => {
        if (!headers || !window.confirm(t("confirmDelete"))) return
        if ((await fetch(`${API_BASE_URL}/personnel/${s.id}`, { method: "DELETE", headers })).ok) void load()
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("title")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("subtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}
            {notice && <div className="rounded-xl border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800 dark:border-green-900 dark:bg-[#23332a] dark:text-green-100">{notice}</div>}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>{t("addStaff")}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-3">
                    <input value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} placeholder={t("fullName")} className="apple-input" />
                    <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder={t("email")} className="apple-input" />
                    <input value={form.phone_number} onChange={e => setForm({ ...form, phone_number: e.target.value })} placeholder={t("phone")} className="apple-input" />
                    <select value={form.primary_role} onChange={e => setForm({ ...form, primary_role: e.target.value })} className="apple-select">{ROLE_KEYS.map(r => <option key={r} value={r}>{roleLabel(r)}</option>)}</select>
                    <select value={form.department_id} onChange={e => setForm({ ...form, department_id: e.target.value })} className="apple-select"><option value="">{t("noDepartment")}</option>{departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select>
                    <input value={form.job_title} onChange={e => setForm({ ...form, job_title: e.target.value })} placeholder={t("function")} className="apple-input" />
                    <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} className="apple-select">{STATUSES.map(st => <option key={st} value={st}>{t(st as "active")}</option>)}</select>
                    <div className="md:col-span-3">
                        <p className="mb-1 text-xs font-medium text-[#6B7280]">{t("additionalRoles")}</p>
                        <div className="flex flex-wrap gap-2">
                            {ROLE_KEYS.map(r => (
                                <button key={r} type="button" onClick={() => toggleAdditional(r)} className={`rounded-full border px-3 py-1 text-xs ${form.additional_roles.includes(r) ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"}`}>{roleLabel(r)}</button>
                            ))}
                        </div>
                    </div>
                    <Button onClick={create} className="bg-black text-white hover:bg-black/90 md:col-span-3"><UserPlus className="mr-2 h-4 w-4" /> {t("add")}</Button>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle className="flex items-center gap-2"><Users className="h-4 w-4" /> {t("title")} ({staff.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("fullName")}</th><th className="px-3 py-2">{t("email")}</th><th className="px-3 py-2">{t("primaryRole")}</th><th className="px-3 py-2">{t("department")}</th><th className="px-3 py-2">{t("function")}</th><th className="px-3 py-2">{t("status")}</th><th className="px-3 py-2 text-right">{t("actions")}</th></tr></thead>
                        <tbody>
                            {staff.length === 0 ? <tr><td colSpan={7} className="px-3 py-6 text-center text-[#6B7280]">{t("empty")}</td></tr> : staff.map(s => (
                                <tr key={s.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{s.full_name}</td>
                                    <td className="px-3 py-2">{s.email}</td>
                                    <td className="px-3 py-2">{roleLabel(s.primary_role)}{s.additional_roles.length > 0 && <span className="text-[#9CA3AF]"> +{s.additional_roles.length}</span>}</td>
                                    <td className="px-3 py-2">{s.department_name || "—"}</td>
                                    <td className="px-3 py-2">{s.job_title || "—"}</td>
                                    <td className="px-3 py-2">
                                        <select value={s.status} onChange={e => changeStatus(s, e.target.value)} className="apple-select !py-1 text-xs">{STATUSES.map(st => <option key={st} value={st}>{t(st as "active")}</option>)}</select>
                                    </td>
                                    <td className="px-3 py-2 text-right"><Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => remove(s)}><Trash2 className="h-4 w-4" /></Button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}
