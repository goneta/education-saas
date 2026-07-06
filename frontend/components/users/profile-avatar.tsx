"use client"

import { useEffect, useRef, useState } from "react"
import { Camera } from "lucide-react"

import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"

const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/webp"]
const MAX_BYTES = 2 * 1024 * 1024

interface ProfileAvatarProps {
    userId: number
    name: string
    photoUrl?: string | null
    editable?: boolean
    onChanged?: () => void | Promise<void>
}

export function ProfileAvatar({ userId, name, photoUrl, editable = true, onChanged }: ProfileAvatarProps) {
    const { token } = useAuth()
    const inputRef = useRef<HTMLInputElement | null>(null)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [busy, setBusy] = useState(false)

    useEffect(() => {
        if (!token || !photoUrl) {
            setImageUrl(null)
            return
        }
        let active = true
        let objectUrl: string | null = null
        fetch(`${API_BASE_URL}${photoUrl}`, {
            headers: { Authorization: `Bearer ${token}` },
            cache: "no-store",
        })
            .then(response => response.ok ? response.blob() : null)
            .then(blob => {
                if (!active || !blob) return
                objectUrl = URL.createObjectURL(blob)
                setImageUrl(objectUrl)
            })
            .catch(() => setImageUrl(null))
        return () => {
            active = false
            if (objectUrl) URL.revokeObjectURL(objectUrl)
        }
    }, [photoUrl, token])

    const upload = async (file: File) => {
        if (!token) return
        if (!ALLOWED_TYPES.includes(file.type) || file.size > MAX_BYTES) {
            window.dispatchEvent(new CustomEvent("teducai:notice", {
                detail: { type: "error", message: "La photo doit être une image PNG, JPEG ou WebP de 2 Mo maximum." },
            }))
            return
        }
        setBusy(true)
        const form = new FormData()
        form.append("photo", file)
        const response = await fetch(`${API_BASE_URL}/system/users/${userId}/profile-photo`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: form,
        })
        setBusy(false)
        if (!response.ok) {
            const data = await response.json().catch(() => null)
            window.dispatchEvent(new CustomEvent("teducai:notice", {
                detail: { type: "error", message: data?.detail || "Impossible d'enregistrer la photo." },
            }))
            return
        }
        await onChanged?.()
    }

    return (
        <div className="relative h-10 w-10 shrink-0">
            <button
                type="button"
                disabled={!editable || busy}
                onClick={event => {
                    event.stopPropagation()
                    inputRef.current?.click()
                }}
                // Marks this as a data-cell control, not a row action. The table
                // enhancer scans button titles for "modifier"/"edit"/… to detect
                // and HIDE legacy action cells; without this flag the avatar's
                // "Modifier la photo de profil" title makes it hide the whole name
                // cell, shifting every column left. See dashboard-ux-enhancer.
                data-teducai-ignore="true"
                className="group relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-full bg-[#E8EEF5] font-semibold text-[#334155] disabled:cursor-default dark:bg-[#343b41] dark:text-[#f4f7fb]"
                title={editable ? "Modifier la photo de profil" : name}
            >
                {imageUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={imageUrl} alt={`Photo de ${name}`} className="h-full w-full object-cover" />
                ) : (
                    name.trim().charAt(0).toUpperCase() || "?"
                )}
                {editable && (
                    <span className="absolute inset-0 hidden items-center justify-center bg-black/55 text-white group-hover:flex">
                        <Camera className="h-4 w-4" />
                    </span>
                )}
            </button>
            <input
                ref={inputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={event => {
                    const file = event.target.files?.[0]
                    event.currentTarget.value = ""
                    if (file) void upload(file)
                }}
            />
        </div>
    )
}
