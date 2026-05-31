"use client"

import { useState } from "react"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function SmsPage() {
    const { token } = useAuth()
    const [form, setForm] = useState({ recipient_phone: "", recipient_name: "", event_type: "school_info", message: "", student_id: "" })
    const [status, setStatus] = useState<string | null>(null)

    const send = async () => {
        if (!token || !form.recipient_phone || !form.message) return
        const res = await fetch(`${API_BASE_URL}/finance/sms`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({
                recipient_phone: form.recipient_phone,
                recipient_name: form.recipient_name || null,
                event_type: form.event_type,
                message: form.message,
                student_id: form.student_id ? Number(form.student_id) : null
            })
        })
        setStatus(res.ok ? "SMS queued." : "Unable to queue SMS.")
        if (res.ok) setForm({ recipient_phone: "", recipient_name: "", event_type: "school_info", message: "", student_id: "" })
    }

    return (
        <div className="space-y-6">
            <div><h1 className="text-2xl font-bold text-[#111827]">Parent SMS</h1><p className="text-sm text-[#6B7280] mt-1">Queue payment reminders, school information and absence alerts.</p></div>
            <Card className="max-w-2xl"><CardHeader><CardTitle>Queue Message</CardTitle></CardHeader><CardContent className="space-y-3">
                <div className="grid gap-3 md:grid-cols-2">
                    <input placeholder="Parent phone" value={form.recipient_phone} onChange={(e) => setForm({ ...form, recipient_phone: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                    <input placeholder="Parent name" value={form.recipient_name} onChange={(e) => setForm({ ...form, recipient_name: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                    <select value={form.event_type} onChange={(e) => setForm({ ...form, event_type: e.target.value })} className="border rounded-md px-3 py-2 text-sm">
                        <option value="payment_late">Payment late</option>
                        <option value="school_info">School information</option>
                        <option value="absence">Absence</option>
                        <option value="parent_alert">Parent alert</option>
                    </select>
                    <input type="number" placeholder="Student profile ID" value={form.student_id} onChange={(e) => setForm({ ...form, student_id: e.target.value })} className="border rounded-md px-3 py-2 text-sm" />
                </div>
                <textarea placeholder="Message" value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} className="min-h-32 w-full border rounded-md px-3 py-2 text-sm" />
                <div className="flex items-center gap-3"><Button onClick={send}>Queue SMS</Button>{status && <span className="text-sm text-[#6B7280]">{status}</span>}</div>
            </CardContent></Card>
        </div>
    )
}
