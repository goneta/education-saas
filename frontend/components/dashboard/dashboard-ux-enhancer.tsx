"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { usePathname, useParams } from "next/navigation"
import { CircleHelp, X } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"

type HelpMode = "page" | "modal" | "drawer"

const ACTIONS = {
    print: { title: "Imprimer", icon: "print", permission: "print" },
    view: { title: "Afficher les détails", icon: "eye", permission: "view" },
    download: { title: "Télécharger", icon: "download", permission: "download" },
    edit: { title: "Modifier", icon: "edit", permission: "edit" },
    delete: { title: "Supprimer", icon: "trash", permission: "delete" },
} as const

const ICONS: Record<string, string> = {
    print: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 14h12v8H6z"/></svg>',
    eye: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>',
    download: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/></svg>',
    edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
    trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>',
}

const MODULE_BY_PATH: Array<[RegExp, string, string]> = [
    [/ai-command-center/, "ai_automation", "ai_first_erp"],
    [/ai-credits/, "ai_automation", "ai_credits"],
    [/students/, "students", "students"],
    [/teachers/, "teachers", "teachers"],
    [/education\/timetable/, "timetable", "timetable"],
    [/education\/internships/, "internships", "internships"],
    [/education\/classes/, "classes", "classes"],
    [/education\/subjects/, "subjects", "academics"],
    [/grades/, "grades", "academics"],
    [/finance\/cash-journal/, "accounting", "finance"],
    [/finance\/fees|finance\/settings/, "finance_fees", "finance"],
    [/finance/, "payments", "finance"],
    [/operations/, "operations", "enterprise"],
    [/enterprise/, "enterprise", "enterprise"],
    [/documents/, "files", "documents"],
    [/settings/, "settings", "settings"],
    [/library/, "library", "academics"],
    [/portal/, "portal", "students"],
]

function escapeHtml(value: string) {
    return value.replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char] || char))
}

function rowCells(row: HTMLTableRowElement) {
    return Array.from(row.children)
        .filter((cell): cell is HTMLTableCellElement => cell instanceof HTMLTableCellElement)
        .filter(cell => !cell.dataset.teducaiActionCell && !cell.dataset.teducaiSelectCell && !cell.dataset.teducaiLegacyActionCell && !cell.dataset.teducaiDuplicateSelectCell)
        .map(cell => cell.textContent?.trim() || "")
}

function tableHeaders(row: HTMLTableRowElement) {
    const table = row.closest("table")
    const headers = table ? Array.from(table.querySelectorAll<HTMLTableCellElement>("thead th"))
        .filter(th => !th.dataset.teducaiActionsHead && !th.dataset.teducaiSelectHead && !th.dataset.teducaiLegacyActionHead && !th.dataset.teducaiDuplicateSelectHead)
        .map(th => th.textContent?.trim() || "") : []
    return headers.filter(header => !["", "Actions", "Action"].includes(header))
}

function exportRow(row: HTMLTableRowElement, format: "csv" | "xlsx" | "pdf") {
    const headers = tableHeaders(row)
    const values = rowCells(row)
    if (format === "pdf") {
        const html = `<html><head><title>TeducAI</title><style>body{font-family:system-ui;padding:24px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px;text-align:left}</style></head><body><h1>Détail TeducAI</h1><table>${values.map((value, index) => `<tr><th>${escapeHtml(headers[index] || `Champ ${index + 1}`)}</th><td>${escapeHtml(value)}</td></tr>`).join("")}</table></body></html>`
        const printWindow = window.open("", "_blank")
        printWindow?.document.write(html)
        printWindow?.document.close()
        printWindow?.print()
        return
    }
    const separator = format === "csv" ? "," : "\t"
    const content = [headers.join(separator), values.map(value => `"${value.replace(/"/g, '""')}"`).join(separator)].join("\n")
    const blob = new Blob([content], { type: format === "csv" ? "text/csv;charset=utf-8" : "application/vnd.ms-excel;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = `teducai-row.${format === "xlsx" ? "xls" : format}`
    anchor.click()
    URL.revokeObjectURL(url)
}

function printRow(row: HTMLTableRowElement) {
    exportRow(row, "pdf")
}

function showRowDetails(row: HTMLTableRowElement) {
    const headers = tableHeaders(row)
    const values = rowCells(row)
    const overlay = document.createElement("div")
    overlay.className = "fixed inset-0 z-[1400] flex items-center justify-center bg-black/30 p-4"
    overlay.innerHTML = `
        <div class="max-h-[86vh] w-full max-w-2xl overflow-y-auto rounded-[28px] bg-white p-6 shadow-[0_30px_90px_rgba(15,23,42,0.25)]">
            <div class="flex items-start justify-between gap-4">
                <div><h2 class="text-2xl font-semibold text-[#111827]">Détails de l'enregistrement</h2><p class="text-sm text-[#6B7280]">Consultation en lecture seule.</p></div>
                <button type="button" data-close class="rounded-full px-3 py-1 text-2xl hover:bg-[#F5F5F7]">×</button>
            </div>
            <div class="mt-5 grid gap-3">${values.map((value, index) => `<div class="rounded-[18px] border border-[#E5E7EB] p-3"><p class="text-xs uppercase tracking-[0.08em] text-[#6B7280]">${escapeHtml(headers[index] || `Champ ${index + 1}`)}</p><p class="mt-1 font-medium text-[#111827]">${escapeHtml(value || "-")}</p></div>`).join("")}</div>
        </div>`
    overlay.addEventListener("click", event => {
        if (event.target === overlay || (event.target as HTMLElement).dataset.close !== undefined) overlay.remove()
    })
    document.body.appendChild(overlay)
}

function clickExistingAction(row: HTMLTableRowElement, patterns: RegExp[]) {
    const candidates = Array.from(row.querySelectorAll<HTMLButtonElement | HTMLAnchorElement>("button,a"))
        .filter(element => !element.dataset.teducaiAction)
    const target = candidates.find(element => patterns.some(pattern => pattern.test(`${element.textContent || ""} ${element.getAttribute("title") || ""} ${element.getAttribute("aria-label") || ""}`)))
    target?.click()
    return Boolean(target)
}

function directCells(row: HTMLTableRowElement) {
    return Array.from(row.children).filter((cell): cell is HTMLTableCellElement => cell instanceof HTMLTableCellElement)
}

function normalizeHeader(value: string) {
    return value.trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")
}

function isActionHeader(cell: HTMLTableCellElement) {
    return /^(actions?|operations?)$/.test(normalizeHeader(cell.textContent || ""))
}

function isCheckboxOnlyCell(cell: HTMLTableCellElement) {
    const inputs = Array.from(cell.querySelectorAll("input[type='checkbox']"))
    if (inputs.length !== 1) return false
    return (cell.textContent || "").trim() === ""
}

function isLegacyActionCell(cell: HTMLTableCellElement) {
    if (cell.dataset.teducaiActionCell) return false
    const buttons = Array.from(cell.querySelectorAll("button,a"))
        .filter(element => !(element as HTMLElement).dataset.teducaiAction)
    if (!buttons.length) return false
    const actionText = buttons.map(element => `${element.textContent || ""} ${element.getAttribute("title") || ""} ${element.getAttribute("aria-label") || ""}`).join(" ")
    return /view|afficher|edit|modifier|delete|supprimer|trash|print|imprimer|download|telecharger|télécharger/i.test(actionText)
}

function hideCell(cell: HTMLTableCellElement, marker: "teducaiLegacyAction" | "teducaiDuplicateSelect") {
    if (marker === "teducaiLegacyAction") cell.dataset.teducaiLegacyActionCell = "true"
    if (marker === "teducaiDuplicateSelect") cell.dataset.teducaiDuplicateSelectCell = "true"
    cell.classList.add("hidden")
    cell.setAttribute("aria-hidden", "true")
}

function hideHead(cell: HTMLTableCellElement, marker: "teducaiLegacyAction" | "teducaiDuplicateSelect") {
    if (marker === "teducaiLegacyAction") cell.dataset.teducaiLegacyActionHead = "true"
    if (marker === "teducaiDuplicateSelect") cell.dataset.teducaiDuplicateSelectHead = "true"
    cell.classList.add("hidden")
    cell.setAttribute("aria-hidden", "true")
}

function normalizeExistingTable(table: HTMLTableElement) {
    const headerRow = table.querySelector<HTMLTableRowElement>("thead tr")
    const headerCells = headerRow ? directCells(headerRow) : []
    const actionIndexes = new Set<number>()
    const checkboxIndexes = new Set<number>()
    let hasSelectionColumn = false

    headerCells.forEach((cell, index) => {
        if (cell.dataset.teducaiActionsHead || cell.dataset.teducaiSelectHead) return
        if (isActionHeader(cell)) {
            actionIndexes.add(index)
            hideHead(cell, "teducaiLegacyAction")
        } else if (isCheckboxOnlyCell(cell)) {
            if (!hasSelectionColumn && index === 0) {
                hasSelectionColumn = true
                cell.dataset.teducaiSelectHead = "true"
                cell.querySelector<HTMLInputElement>("input[type='checkbox']")?.setAttribute("data-teducai-select-all", "true")
            } else {
                checkboxIndexes.add(index)
                hideHead(cell, "teducaiDuplicateSelect")
            }
        }
    })

    Array.from(table.querySelectorAll<HTMLTableRowElement>("tbody tr")).forEach(row => {
        const cells = directCells(row)
        cells.forEach((cell, index) => {
            if (cell.dataset.teducaiActionCell || cell.dataset.teducaiSelectCell) return
            if (actionIndexes.has(index) || isLegacyActionCell(cell)) {
                hideCell(cell, "teducaiLegacyAction")
            } else if (checkboxIndexes.has(index)) {
                hideCell(cell, "teducaiDuplicateSelect")
            }
        })

        const firstCell = directCells(row)[0]
        if (firstCell && isCheckboxOnlyCell(firstCell) && !firstCell.dataset.teducaiDuplicateSelectCell) {
            firstCell.dataset.teducaiSelectCell = "true"
            firstCell.querySelector<HTMLInputElement>("input[type='checkbox']")?.setAttribute("data-teducai-row-select", "true")
        }
    })
}

function roleAllowsFallback(role: string | undefined, action: string) {
    if (["super_admin", "school_admin", "admin"].includes(role || "")) return true
    if (["parent", "student", "pupil"].includes(role || "")) return ["view", "download", "print"].includes(action)
    if (["teacher", "trainer", "instructor"].includes(role || "")) return ["view", "download", "print", "edit"].includes(action)
    return action !== "delete"
}

export function DashboardUxEnhancer() {
    const { user, token } = useAuth()
    const pathname = usePathname()
    const params = useParams()
    const locale = normalizeLocale(params.locale as string)
    const [permissions, setPermissions] = useState<string[]>([])
    const [helpMode, setHelpMode] = useState<HelpMode>("page")
    const [selectedCount, setSelectedCount] = useState(0)
    const [helpFrame, setHelpFrame] = useState<string | null>(null)

    const [moduleKey, helpSection] = useMemo(() => {
        const match = MODULE_BY_PATH.find(([pattern]) => pattern.test(pathname || ""))
        return [match?.[1] || "dashboard", match?.[2] || "dashboard"]
    }, [pathname])

    const can = useCallback((action: string) => {
        if (permissions.includes("*")) return true
        if (permissions.includes(`${moduleKey}:${action}`)) return true
        if (permissions.includes(`${moduleKey}:full_access`)) return true
        const aliases: Record<string, string[]> = { view: ["read"], edit: ["write"], print: ["export"], download: ["export"] }
        if ((aliases[action] || []).some(alias => permissions.includes(`${moduleKey}:${alias}`))) return true
        return roleAllowsFallback(user?.role, action)
    }, [moduleKey, permissions, user?.role])

    useEffect(() => {
        setHelpMode((localStorage.getItem("teducai_help_mode") as HelpMode) || "page")
        if (!token) return
        fetch(`${API_BASE_URL}/system/active-context`, { headers: { Authorization: `Bearer ${token}` } })
            .then(response => response.ok ? response.json() : null)
            .then(data => setPermissions(Array.isArray(data?.permissions) ? data.permissions : []))
            .catch(() => setPermissions([]))
    }, [token])

    const enhanceTables = useCallback(() => {
        const tables = Array.from(document.querySelectorAll<HTMLTableElement>("main table"))
        tables.forEach((table, tableIndex) => {
            normalizeExistingTable(table)
            table.dataset.teducaiEnhanced = "true"
            const headerRow = table.querySelector("thead tr")
            if (headerRow && !headerRow.querySelector("[data-teducai-select-head]")) {
                const selectHead = document.createElement("th")
                selectHead.dataset.teducaiSelectHead = "true"
                selectHead.className = "px-3 py-2"
                selectHead.innerHTML = '<input type="checkbox" title="Sélectionner toutes les lignes" data-teducai-select-all class="h-4 w-4 accent-black" />'
                headerRow.insertBefore(selectHead, headerRow.firstChild)
            }
            if (headerRow && !headerRow.querySelector("[data-teducai-actions-head]")) {
                const actionHead = document.createElement("th")
                actionHead.dataset.teducaiActionsHead = "true"
                actionHead.className = "px-3 py-2 text-right"
                actionHead.textContent = "Actions"
                headerRow.appendChild(actionHead)
            }
            Array.from(table.querySelectorAll<HTMLTableRowElement>("tbody tr")).forEach((row, rowIndex) => {
                if (row.dataset.teducaiEnhanced === "true") return
                row.dataset.teducaiEnhanced = "true"
                row.dataset.teducaiRowKey = row.dataset.teducaiRowKey || `${tableIndex}-${rowIndex}-${row.textContent?.slice(0, 24) || rowIndex}`
                if (!row.querySelector("[data-teducai-select-cell]")) {
                    const selectCell = document.createElement("td")
                    selectCell.dataset.teducaiSelectCell = "true"
                    selectCell.className = "px-3 py-2"
                    selectCell.innerHTML = '<input type="checkbox" title="Sélectionner cette ligne" data-teducai-row-select class="h-4 w-4 accent-black" />'
                    row.insertBefore(selectCell, row.firstChild)
                }
                const cell = document.createElement("td")
                cell.dataset.teducaiActionCell = "true"
                cell.className = "px-3 py-2 text-right"
                const actions = Object.entries(ACTIONS).filter(([, action]) => can(action.permission))
                cell.innerHTML = `<div class="inline-flex items-center gap-1 rounded-full bg-white/80 p-1">${actions.map(([key, action]) => {
                    if (key === "download") {
                        return `<span class="relative inline-flex"><button type="button" data-teducai-action="${key}" title="${action.title}" class="teducai-row-action">${ICONS[action.icon]}</button><span data-teducai-download-menu class="hidden absolute right-0 top-9 z-[1300] w-32 rounded-2xl border border-[#E5E7EB] bg-white p-1 text-left text-xs shadow-xl"><button data-teducai-export="pdf" class="block w-full rounded-xl px-3 py-2 hover:bg-[#F5F5F7]">PDF</button><button data-teducai-export="csv" class="block w-full rounded-xl px-3 py-2 hover:bg-[#F5F5F7]">CSV</button><button data-teducai-export="xlsx" class="block w-full rounded-xl px-3 py-2 hover:bg-[#F5F5F7]">Excel</button></span></span>`
                    }
                    return `<button type="button" data-teducai-action="${key}" title="${action.title}" class="teducai-row-action">${ICONS[action.icon]}</button>`
                }).join("")}</div>`
                row.appendChild(cell)
                const labels = tableHeaders(row)
                Array.from(row.children).forEach((child, childIndex) => {
                    if (child instanceof HTMLTableCellElement && !child.dataset.label) {
                        child.dataset.label = child.dataset.teducaiActionCell ? "Actions" : child.dataset.teducaiSelectCell ? "" : labels[Math.max(0, childIndex - 1)] || `Champ ${childIndex}`
                    }
                })
            })
        })
        setSelectedCount(document.querySelectorAll("main [data-teducai-row-select]:checked").length)
    }, [can])

    useEffect(() => {
        enhanceTables()
        const observer = new MutationObserver(() => enhanceTables())
        const main = document.querySelector("main")
        if (main) observer.observe(main, { childList: true, subtree: true })
        return () => observer.disconnect()
    }, [enhanceTables, pathname])

    useEffect(() => {
        const onClick = (event: MouseEvent) => {
            const target = event.target as HTMLElement
            const row = target.closest("tr") as HTMLTableRowElement | null
            if (target.closest("[data-teducai-select-all]")) {
                const table = target.closest("table")
                table?.querySelectorAll<HTMLInputElement>("[data-teducai-row-select]").forEach(input => { input.checked = (target as HTMLInputElement).checked })
                setSelectedCount(document.querySelectorAll("main [data-teducai-row-select]:checked").length)
                return
            }
            if (target.closest("[data-teducai-row-select]")) {
                setSelectedCount(document.querySelectorAll("main [data-teducai-row-select]:checked").length)
                return
            }
            const exportButton = target.closest("[data-teducai-export]") as HTMLElement | null
            if (exportButton && row) {
                exportRow(row, exportButton.dataset.teducaiExport as "pdf" | "csv" | "xlsx")
                exportButton.closest("[data-teducai-download-menu]")?.classList.add("hidden")
                return
            }
            const button = target.closest("[data-teducai-action]") as HTMLElement | null
            if (!button || !row) return
            const action = button.dataset.teducaiAction
            if (action === "print") printRow(row)
            if (action === "view") showRowDetails(row)
            if (action === "download") button.parentElement?.querySelector("[data-teducai-download-menu]")?.classList.toggle("hidden")
            if (action === "edit" && !clickExistingAction(row, [/edit/i, /modifier/i])) alert("Aucun formulaire de modification direct n'est disponible pour cette ligne.")
            if (action === "delete") {
                if (!confirm("Confirmer la suppression de cet élément ? Cette action sera auditée si le module backend autorise la suppression.")) return
                if (!clickExistingAction(row, [/delete/i, /supprimer/i, /trash/i])) alert("Suppression impossible: élément protégé ou action backend non disponible pour ce module.")
            }
        }
        document.addEventListener("click", onClick)
        return () => document.removeEventListener("click", onClick)
    }, [])

    const helpUrl = `/${locale}/dashboard/help?section=${helpSection}`
    const openHelp = () => {
        const mode = (localStorage.getItem("teducai_help_mode") as HelpMode) || helpMode
        if (mode === "page") window.location.href = helpUrl
        else setHelpFrame(helpUrl)
    }

    const bulkRows = () => Array.from(document.querySelectorAll<HTMLInputElement>("main [data-teducai-row-select]:checked")).map(input => input.closest("tr")).filter(Boolean) as HTMLTableRowElement[]
    const bulkExport = (format: "pdf" | "csv" | "xlsx") => bulkRows().forEach(row => exportRow(row, format))
    const bulkPrint = () => bulkRows().forEach(printRow)
    const bulkDelete = () => {
        if (!can("delete") || !confirm(`Supprimer ${selectedCount} élément(s) sélectionné(s) ?`)) return
        bulkRows().forEach(row => clickExistingAction(row, [/delete/i, /supprimer/i, /trash/i]))
    }

    return (
        <>
            <style>{`
                .teducai-row-action{display:inline-flex;height:32px;width:32px;align-items:center;justify-content:center;border-radius:9999px;color:#111827;transition:background .2s ease,color .2s ease}
                .teducai-row-action:hover{background:#F0F1F3;color:#000}
                .teducai-row-action svg{height:16px;width:16px}
                @media (max-width: 767px){
                    html,body{overflow-x:hidden}
                    main table{display:block;width:100%;min-width:0!important;border:0!important}
                    main table thead{display:none}
                    main table tbody{display:grid;gap:12px;width:100%}
                    main table tr{display:block;width:100%;border:1px solid #E5E7EB!important;border-radius:24px;background:#fff;padding:12px;box-shadow:0 8px 24px rgba(15,23,42,.05)}
                    main table td{display:flex!important;align-items:flex-start;justify-content:space-between;gap:16px;width:100%;border:0!important;padding:8px 4px!important;text-align:right!important;white-space:normal!important}
                    main table td::before{content:attr(data-label);max-width:42%;text-align:left;font-size:12px;font-weight:600;color:#6B7280}
                    main table td[data-teducai-select-cell]::before{content:"Sélection"}
                    main table td[data-teducai-action-cell]{justify-content:flex-end;border-top:1px solid #F0F1F3!important;margin-top:6px;padding-top:12px!important}
                    main table td[data-teducai-action-cell]::before{content:""}
                    main form{max-width:100%}
                    main form .grid{grid-template-columns:1fr!important}
                    main input,main select,main textarea,.apple-input,.apple-select{min-height:48px;font-size:16px!important}
                    main button{min-height:44px}
                    [role="dialog"],.fixed.inset-0 .max-w-xl,.fixed.inset-0 .max-w-2xl,.fixed.inset-0 .max-w-5xl{max-width:100%!important;width:100%!important;max-height:100dvh!important;border-radius:0!important}
                }
            `}</style>
            <button
                type="button"
                onClick={openHelp}
                title="Aller dans l’aide pour comprendre comment renseigner les informations de cette page."
                className="fixed bottom-5 right-5 z-[1250] inline-flex items-center gap-2 rounded-full bg-black px-4 py-3 text-sm font-medium text-white shadow-[0_18px_50px_rgba(15,23,42,0.25)] transition hover:bg-black/90"
            >
                <CircleHelp className="h-4 w-4" /> Aide
            </button>
            {selectedCount > 0 && (
                <div className="fixed bottom-20 left-1/2 z-[1240] flex -translate-x-1/2 flex-wrap items-center gap-2 rounded-full border border-[#E5E7EB] bg-white px-4 py-3 text-sm shadow-[0_18px_60px_rgba(15,23,42,0.2)]">
                    <span className="font-medium">{selectedCount} sélectionné(s)</span>
                    <button onClick={bulkPrint} className="rounded-full border px-3 py-1.5 hover:bg-[#F5F5F7]">Imprimer</button>
                    <button onClick={() => bulkExport("pdf")} className="rounded-full border px-3 py-1.5 hover:bg-[#F5F5F7]">PDF</button>
                    <button onClick={() => bulkExport("csv")} className="rounded-full border px-3 py-1.5 hover:bg-[#F5F5F7]">CSV</button>
                    <button onClick={() => bulkExport("xlsx")} className="rounded-full border px-3 py-1.5 hover:bg-[#F5F5F7]">Excel</button>
                    {can("delete") && <button onClick={bulkDelete} className="rounded-full bg-red-600 px-3 py-1.5 text-white hover:bg-red-700">Supprimer</button>}
                </div>
            )}
            {helpFrame && (
                <div className={helpMode === "drawer" ? "fixed inset-y-0 right-0 z-[1500] w-full max-w-xl bg-white shadow-2xl" : "fixed inset-0 z-[1500] flex items-center justify-center bg-black/30 p-4"}>
                    <div className={helpMode === "drawer" ? "flex h-full flex-col" : "flex h-[86vh] w-full max-w-5xl flex-col overflow-hidden rounded-[28px] bg-white shadow-2xl"}>
                        <div className="flex items-center justify-between border-b px-4 py-3">
                            <p className="font-semibold">Aide TeducAI</p>
                            <button onClick={() => setHelpFrame(null)} className="rounded-full p-2 hover:bg-[#F5F5F7]"><X className="h-5 w-5" /></button>
                        </div>
                        <iframe src={helpFrame} className="min-h-0 flex-1 border-0" title="Aide TeducAI" />
                    </div>
                </div>
            )}
        </>
    )
}
