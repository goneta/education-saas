// Client HTTP partagé — conçu pour qu'une erreur ne puisse PAS être avalée.
//
// Le balayage de l'audit a trouvé 277 endroits où un échec réseau ou serveur
// disparaissait sans bruit : `if (res.ok) setX(...)` sans `else`,
// `.then(r => r.ok ? r.json() : [])`, `.catch(() => undefined)`.
//
// Le plus toxique est le ternaire : il transforme un 500 ou un 403 en **liste
// vide**. Combiné aux garde-fous « dépendance manquante », l'application dit
// alors à l'utilisateur « Aucune classe n'existe, créez-en une » alors que les
// classes existent et que c'est la requête qui a échoué. L'utilisateur est
// activement induit en erreur, et crée des doublons.
//
// Ces fonctions séparent explicitement les trois états qu'un écran doit
// distinguer : en cours de chargement, échec (avec un message lisible), et
// succès (dont « succès avec zéro élément », qui est une information, pas une
// panne).

import { API_BASE_URL } from "@/lib/config"
import { parseApiErrorResponse } from "@/lib/api-errors"

export interface ListState<T> {
    /** Données reçues. Tableau vide UNIQUEMENT si le serveur a répondu vide. */
    data: T[]
    /** Message lisible si la requête a échoué ; null en cas de succès. */
    error: string | null
    /** true quand le serveur a répondu correctement (même avec zéro élément). */
    loaded: boolean
}

function authHeaders(token: string | null | undefined, extra?: HeadersInit): HeadersInit {
    return { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(extra || {}) }
}

/**
 * Requête JSON qui LÈVE une erreur lisible si le serveur refuse.
 * À utiliser quand l'appelant gère déjà try/catch et affiche l'erreur.
 */
export async function fetchJson<T>(
    path: string,
    { token, fallbackMessage = "Requête impossible.", ...init }: RequestInit & { token?: string | null; fallbackMessage?: string } = {},
): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        headers: authHeaders(token, init.headers),
    })
    if (!response.ok) {
        throw new Error((await parseApiErrorResponse(response, fallbackMessage)).message)
    }
    return response.json() as Promise<T>
}

/**
 * Charge une liste en distinguant « vide » de « en échec ».
 *
 * Ne lève jamais : renvoie toujours un `ListState` exploitable, pour que les
 * écrans qui alimentent des listes déroulantes puissent afficher un vrai
 * message d'erreur au lieu d'un encart « aucune donnée » mensonger.
 */
export async function fetchList<T>(
    path: string,
    { token, fallbackMessage = "Chargement impossible.", ...init }: RequestInit & { token?: string | null; fallbackMessage?: string } = {},
): Promise<ListState<T>> {
    try {
        const response = await fetch(`${API_BASE_URL}${path}`, {
            ...init,
            headers: authHeaders(token, init.headers),
        })
        if (!response.ok) {
            return { data: [], error: (await parseApiErrorResponse(response, fallbackMessage)).message, loaded: false }
        }
        const payload = await response.json()
        // Certains endpoints renvoient {items: [...]} ou {data: [...]}.
        const rows = Array.isArray(payload)
            ? payload
            : Array.isArray(payload?.items) ? payload.items
            : Array.isArray(payload?.data) ? payload.data
            : []
        return { data: rows as T[], error: null, loaded: true }
    } catch (reason) {
        // Réseau coupé, DNS, CORS : c'est un échec, pas une liste vide.
        const message = reason instanceof Error && reason.message
            ? `${fallbackMessage} (${reason.message})`
            : fallbackMessage
        return { data: [], error: message, loaded: false }
    }
}

/** État initial pratique pour `useState<ListState<T>>(emptyList())`. */
export function emptyList<T>(): ListState<T> {
    return { data: [], error: null, loaded: false }
}
