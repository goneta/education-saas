"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { DoorOpen, Eye, Plus, Trash2, X } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

interface Room { id: number; name: string; room_type: string; capacity?: number | null; building_id?: number | null; is_active: boolean }
interface Building { id: number; name: string }
interface RoomClass { id: number; name: string; level?: string | null }

const ROOM_TYPES = ["classroom", "laboratory", "computer_room", "workshop", "gym", "other"]

export default function RoomsPage() {
    const t = useTranslations("facilities")
    const { token } = useAuth()
    const [rooms, setRooms] = useState<Room[]>([])
    const [buildings, setBuildings] = useState<Building[]>([])
    const [counts, setCounts] = useState<Record<number, number>>({})
    const [form, setForm] = useState({ building_id: "", name: "", capacity: "", room_type: "classroom" })
    const [error, setError] = useState<string | null>(null)
    const [viewing, setViewing] = useState<{ room: Room; classes: RoomClass[] } | null>(null)

    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : undefined, [token])

    const load = useCallback(async () => {
        if (!headers) return
        const [r, b] = await Promise.all([
            fetch(`${API_BASE_URL}/facilities/rooms`, { headers }),
            fetch(`${API_BASE_URL}/facilities/buildings`, { headers }),
        ])
        const roomList: Room[] = r.ok ? await r.json() : []
        setRooms(roomList)
        if (b.ok) setBuildings(await b.json())
        // Nb Classes per room.
        const entries = await Promise.all(roomList.map(async room => {
            const res = await fetch(`${API_BASE_URL}/facilities/rooms/${room.id}/classes`, { headers })
            return [room.id, res.ok ? (await res.json()).count : 0] as const
        }))
        setCounts(Object.fromEntries(entries))
    }, [headers])

    useEffect(() => { void load() }, [load])

    const create = async () => {
        if (!headers || !form.building_id || !form.name.trim() || !form.capacity) return
        setError(null)
        const res = await fetch(`${API_BASE_URL}/facilities/rooms`, {
            method: "POST", headers,
            body: JSON.stringify({ building_id: Number(form.building_id), name: form.name.trim(), capacity: Number(form.capacity), room_type: form.room_type }),
        })
        if (res.ok) { setForm({ building_id: "", name: "", capacity: "", room_type: "classroom" }); void load() }
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const remove = async (room: Room) => {
        if (!headers || !window.confirm(t("confirmDelete"))) return
        const res = await fetch(`${API_BASE_URL}/facilities/rooms/${room.id}`, { method: "DELETE", headers })
        if (res.ok) void load()
        else setError((await res.json().catch(() => ({}))).detail || "—")
    }

    const view = async (room: Room) => {
        if (!headers) return
        const res = await fetch(`${API_BASE_URL}/facilities/rooms/${room.id}/classes`, { headers })
        setViewing({ room, classes: res.ok ? (await res.json()).classes : [] })
    }

    const buildingName = (id?: number | null) => buildings.find(b => b.id === id)?.name || "—"
    const typeLabel = (rt: string) => ROOM_TYPES.includes(rt) ? t(rt as "classroom") : rt

    const columns: FilterColumn<Room>[] = [
        { key: "name", label: t("name"), accessor: r => r.name },
        { key: "building", label: t("building"), accessor: r => buildingName(r.building_id) },
        { key: "type", label: t("type"), accessor: r => typeLabel(r.room_type) },
    ]
    const filter = useTableFilter(rooms, columns, { storageKey: "rooms" })

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827] dark:text-white">{t("roomsTitle")}</h1>
                <p className="mt-1 text-sm text-[#6B7280] dark:text-[#c7d0da]">{t("roomsSubtitle")}</p>
            </div>
            {error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-[#3a2528] dark:text-red-100">{error}</div>}

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle>{t("addRoom")}</CardTitle></CardHeader>
                <CardContent className="grid gap-3 md:grid-cols-5">
                    <select value={form.building_id} onChange={e => setForm({ ...form, building_id: e.target.value })} className="apple-select"><option value="">{t("building")}…</option>{buildings.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</select>
                    <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder={t("name")} className="apple-input" />
                    <input type="number" min={1} value={form.capacity} onChange={e => setForm({ ...form, capacity: e.target.value })} placeholder={t("capacity")} className="apple-input" />
                    <select value={form.room_type} onChange={e => setForm({ ...form, room_type: e.target.value })} className="apple-select">{ROOM_TYPES.map(rt => <option key={rt} value={rt}>{t(rt as "classroom")}</option>)}</select>
                    <Button onClick={create} className="bg-black text-white hover:bg-black/90"><Plus className="mr-2 h-4 w-4" /> {t("add")}</Button>
                </CardContent>
            </Card>

            <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm dark:border-[#3b4248] dark:bg-[#202528]">
                <CardHeader><CardTitle className="flex items-center gap-2"><DoorOpen className="h-4 w-4" /> {t("roomsTitle")} ({rooms.length})</CardTitle></CardHeader>
                <CardContent className="overflow-x-auto">
                    <div className="mb-3"><TableFilter {...filter.controls} /></div>
                    <table className="w-full text-left text-sm">
                        <thead><tr className="border-b border-[#E5E7EB] text-[#6B7280] dark:border-[#3b4248]"><th className="px-3 py-2">{t("name")}</th><th className="px-3 py-2">{t("building")}</th><th className="px-3 py-2">{t("type")}</th><th className="px-3 py-2">{t("capacity")}</th><th className="px-3 py-2">{t("nbClasses")}</th><th className="px-3 py-2 text-right">{t("actions")}</th></tr></thead>
                        <tbody>
                            {filter.filtered.length === 0 ? <tr><td colSpan={6} className="px-3 py-6 text-center text-[#6B7280]">{t("empty")}</td></tr> : filter.filtered.map(room => (
                                <tr key={room.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]">
                                    <td className="px-3 py-2 font-medium">{room.name}</td>
                                    <td className="px-3 py-2">{buildingName(room.building_id)}</td>
                                    <td className="px-3 py-2">{typeLabel(room.room_type)}</td>
                                    <td className="px-3 py-2">{room.capacity ?? "—"}</td>
                                    <td className="px-3 py-2">{counts[room.id] ?? 0}</td>
                                    <td className="px-3 py-2 text-right"><div className="flex justify-end gap-1"><Button variant="ghost" size="sm" onClick={() => view(room)} title={t("view")}><Eye className="h-4 w-4" /></Button><Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => remove(room)}><Trash2 className="h-4 w-4" /></Button></div></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>

            {viewing && (
                <div className="fixed inset-0 z-[1300] flex items-center justify-center bg-black/40 p-4" onClick={() => setViewing(null)}>
                    <div className="w-full max-w-md rounded-[20px] bg-white p-5 shadow-xl dark:bg-[#202528]" onClick={e => e.stopPropagation()}>
                        <div className="mb-3 flex items-center justify-between"><h3 className="font-semibold">{t("classesInRoom")} — {viewing.room.name}</h3><button onClick={() => setViewing(null)}><X className="h-4 w-4" /></button></div>
                        {viewing.classes.length === 0 ? <p className="text-sm text-[#6B7280]">{t("empty")}</p> : (
                            <div className="max-h-[50vh] overflow-y-auto">
                                <table className="w-full text-left text-sm"><thead><tr className="border-b text-[#6B7280]"><th className="py-2">{t("name")}</th><th className="py-2">{t("level")}</th></tr></thead>
                                    <tbody>{viewing.classes.map(c => <tr key={c.id} className="border-b border-[#F0F1F3] dark:border-[#2a3035]"><td className="py-2 font-medium">{c.name}</td><td className="py-2">{c.level || "—"}</td></tr>)}</tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
