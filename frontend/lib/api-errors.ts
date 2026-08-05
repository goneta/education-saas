// Shared parser for API error responses. FastAPI returns `detail` either as a
// plain string (HTTPException) or as an ARRAY of {loc, msg, type} objects for
// 422 validation errors — passing that array to `new Error()` is what used to
// render "[object Object]" in the UI. This module turns ANY error payload into
// a readable message plus per-field errors, so forms can highlight the exact
// field and the user never sees an unreadable blob.

export interface ParsedApiError {
    /** Human-readable global message (never "[object Object]"). */
    message: string
    /** API field name (snake_case, last loc segment) -> message. */
    fieldErrors: Record<string, string>
}

interface ValidationItem {
    loc?: unknown[]
    msg?: string
    type?: string
}

function isValidationItem(value: unknown): value is ValidationItem {
    return Boolean(value && typeof value === "object" && ("msg" in (value as object) || "loc" in (value as object)))
}

/** Best-effort French label for the raw Pydantic message. */
function readableMessage(item: ValidationItem): string {
    const msg = item.msg || "Valeur invalide"
    const map: [RegExp, string][] = [
        [/field required/i, "Champ obligatoire"],
        [/none is not an allowed value/i, "Champ obligatoire"],
        [/value is not a valid email/i, "Adresse e-mail invalide"],
        [/invalid date/i, "Date invalide"],
        [/value is not a valid integer/i, "Nombre invalide"],
        [/ensure this value has at least (\d+) characters/i, "Trop court"],
        [/string should have at least (\d+) characters/i, "Trop court"],
    ]
    for (const [pattern, label] of map) {
        if (pattern.test(msg)) return label
    }
    return msg
}

function fieldNameOf(item: ValidationItem): string | null {
    if (!Array.isArray(item.loc) || item.loc.length === 0) return null
    // loc looks like ["body", "profile", "date_of_birth"]; the last string
    // segment is the field. Skip purely positional segments.
    for (let i = item.loc.length - 1; i >= 0; i--) {
        const segment = item.loc[i]
        if (typeof segment === "string" && segment !== "body" && segment !== "query") return segment
    }
    return null
}

/**
 * Parse a (already JSON-decoded) error payload from the API.
 * Always returns a readable message; never "[object Object]".
 */
export function parseApiError(payload: unknown, fallback: string): ParsedApiError {
    const fieldErrors: Record<string, string> = {}
    if (payload && typeof payload === "object") {
        const detail = (payload as { detail?: unknown }).detail
        if (typeof detail === "string" && detail.trim()) {
            return { message: detail, fieldErrors }
        }
        if (Array.isArray(detail)) {
            const lines: string[] = []
            for (const raw of detail) {
                if (!isValidationItem(raw)) continue
                const field = fieldNameOf(raw)
                const message = readableMessage(raw)
                if (field) {
                    if (!fieldErrors[field]) fieldErrors[field] = message
                    lines.push(`${field.replace(/_/g, " ")} : ${message}`)
                } else {
                    lines.push(message)
                }
            }
            if (lines.length) {
                return { message: lines.join(" · "), fieldErrors }
            }
        }
        if (detail && typeof detail === "object") {
            const msg = (detail as { msg?: unknown; message?: unknown }).msg
                ?? (detail as { message?: unknown }).message
            if (typeof msg === "string" && msg.trim()) return { message: msg, fieldErrors }
            try {
                return { message: JSON.stringify(detail), fieldErrors }
            } catch {
                /* fall through */
            }
        }
        const message = (payload as { message?: unknown }).message
        if (typeof message === "string" && message.trim()) return { message, fieldErrors }
    }
    if (typeof payload === "string" && payload.trim()) return { message: payload, fieldErrors }
    return { message: fallback, fieldErrors }
}

/** Convenience: parse a fetch Response that is known to be !ok. */
export async function parseApiErrorResponse(response: Response, fallback: string): Promise<ParsedApiError> {
    const payload = await response.json().catch(() => null)
    const parsed = parseApiError(payload, fallback)
    if (parsed.message === fallback && response.status === 401) {
        return { message: "Votre session a expiré. Veuillez vous reconnecter.", fieldErrors: {} }
    }
    return parsed
}
