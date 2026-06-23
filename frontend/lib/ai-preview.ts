export function formatPreviewContent(value: unknown): string {
    if (value === null || value === undefined) return ""
    if (typeof value === "string") return value
    if (Array.isArray(value)) return formatArray(value)
    if (typeof value === "object") return formatObject(value as Record<string, unknown>)
    return String(value)
}

function formatArray(rows: unknown[]): string {
    if (!rows.length) return "_Aucune donnee._"
    if (rows.every(row => row && typeof row === "object" && !Array.isArray(row))) {
        const objects = rows as Record<string, unknown>[]
        const columns = Array.from(new Set(objects.flatMap(row => Object.keys(row)))).slice(0, 8)
        if (columns.length) {
            const header = `| ${columns.join(" |")} |`
            const divider = `| ${columns.map(() => "---").join(" | ")} |`
            const body = objects.map(row => `| ${columns.map(column => cleanCell(row[column])).join(" | ")} |`)
            return [header, divider, ...body].join("\n")
        }
    }
    return rows.map(item => `- ${cleanCell(item)}`).join("\n")
}

function formatObject(value: Record<string, unknown>): string {
    const sections: string[] = []
    for (const [key, item] of Object.entries(value)) {
        const title = humanize(key)
        if (Array.isArray(item)) {
            sections.push(`## ${title}\n\n${formatArray(item)}`)
        } else if (item && typeof item === "object") {
            sections.push(`## ${title}\n\n${formatObject(item as Record<string, unknown>)}`)
        } else if (item !== null && item !== undefined && item !== "") {
            sections.push(`**${title}:** ${cleanCell(item)}`)
        }
    }
    return sections.join("\n\n") || "```json\n" + JSON.stringify(value, null, 2) + "\n```"
}

function humanize(value: string): string {
    return value.replace(/_/g, " ").replace(/\b\w/g, letter => letter.toUpperCase())
}

function cleanCell(value: unknown): string {
    if (value === null || value === undefined) return ""
    if (Array.isArray(value)) return value.map(cleanCell).join(", ")
    if (typeof value === "object") return JSON.stringify(value)
    return String(value).replace(/\|/g, "\\|").replace(/\n/g, " ")
}
