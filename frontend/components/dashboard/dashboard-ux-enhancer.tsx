"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { usePathname, useParams } from "next/navigation"
import { CircleHelp, X } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { normalizeLocale } from "@/lib/i18n"
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog"
import type { ConfirmationRequest } from "@/lib/confirmation"

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
    [/emploi-recruteur/, "employment", "employment"],
    [/emploi-admin/, "employment", "employment"],
    [/dashboard\/emploi/, "employment", "employment"],
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

const SECTION_TITLE_TRANSLATIONS: Record<string, string> = {
    "debiteurs": "Débiteurs",
    "liste des frais": "Liste des frais",
    "paiements": "Paiements",
    "lignes previsionnelles": "Lignes prévisionnelles",
    "rubriques configurees": "Rubriques configurées",
    "programs list": "Liste des programmes",
    "approbations": "Approbations",
    "classes management": "Gestion des classes",
    "subject list": "Liste des matières",
    "administrative requests": "Demandes administratives",
    "assignments": "Devoirs",
    "course materials": "Supports de cours",
    "create assignment": "Créer un devoir",
    "share course material": "Partager un support de cours",
    "ajouter une entreprise partenaire": "Ajouter une entreprise partenaire",
    "entreprises partenaires": "Entreprises partenaires",
    "creer un stage": "Créer un stage",
    "stages": "Stages",
    "suivi quotidien entreprise": "Suivi quotidien entreprise",
    "carnet de stage eleve": "Carnet de stage élève",
    "evaluation du stage": "Évaluation du stage",
    "documents de stage": "Documents de stage",
    "eleves disponibles": "Élèves disponibles",
    "assessment list": "Liste des évaluations",
    "book inventory": "Inventaire des livres",
    "emploi du temps publie": "Emploi du temps publié",
    "documents disponibles": "Documents disponibles",
    "factures et soldes": "Factures et soldes",
    "notifications": "Notifications",
    "stages en entreprise": "Stages en entreprise",
    "ajouter un document": "Ajouter un document",
    "documents": "Documents",
    "student list": "Liste des élèves",
    "teacher list": "Liste des enseignants",
    "recent activity": "Activité récente",
    "agents ia specialises": "Agents IA spécialisés",
    "executer une commande": "Exécuter une commande",
    "historique credits utilisateur": "Historique des crédits utilisateur",
    "transactions credits ecole": "Transactions de crédits école",
    "usage ia utilisateur": "Usage IA utilisateur",
    "comptes de paiement ecole": "Comptes de paiement école",
    "acheter des credits ia": "Acheter des crédits IA",
    "paiements scolaires separes": "Paiements scolaires séparés",
}

const UI_COPY_TRANSLATIONS: Record<string, string> = {
    "add class": "Ajouter une classe",
    "add teacher": "Ajouter un enseignant",
    "add student": "Ajouter un élève",
    "add fee": "Ajouter des frais",
    "add document": "Ajouter un document",
    "add payroll": "Ajouter une paie",
    "add canteen": "Ajouter une cantine",
    "add admission": "Ajouter une admission",
    "add admissions": "Ajouter des admissions",
    "add exam": "Ajouter un examen",
    "add exams": "Ajouter des examens",
    "add forecast": "Ajouter un prévisionnel",
    "add fee rubric": "Ajouter une rubrique de frais",
    "copy amounts": "Copier les montants",
    "copy previous year": "Copier l'année précédente",
    "submit closure": "Valider la clôture",
    "refresh": "Actualiser",
    "apply": "Appliquer",
    "print": "Imprimer",
    "save": "Enregistrer",
    "cancel": "Annuler",
    "close": "Fermer",
    "delete": "Supprimer",
    "edit": "Modifier",
    "view": "Afficher",
    "download": "Télécharger",
    "no teachers found. add your first teacher!": "Aucun enseignant trouvé. Ajoutez votre premier enseignant !",
    "no students found. add your first student!": "Aucun élève trouvé. Ajoutez votre premier élève !",
    "no classes found. add your first class!": "Aucune classe trouvée. Ajoutez votre première classe !",
    "no data available": "Aucune donnée à afficher",
    "no data to display": "Aucune donnée à afficher",
    "no records found": "Aucun enregistrement trouvé",
    "total students": "Total des élèves",
    "classes today": "Classes aujourd'hui",
    "active classes": "Classes actives",
    "registered students": "Élèves inscrits",
    "scheduled classes": "Classes planifiées",
    "currently in session": "Actuellement en cours",
}

function escapeHtml(value: string) {
    return value.replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char] || char))
}

function normalizeCopyKey(value: string) {
    return value.trim().toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/\s*\(\d+\)\s*$/, "").replace(/\s+/g, " ")
}

function translateSectionTitle(value: string) {
    const count = value.match(/\s*(\(\d+\))\s*$/)?.[1] || ""
    const translated = SECTION_TITLE_TRANSLATIONS[normalizeCopyKey(value)]
    return translated ? `${translated}${count ? ` ${count}` : ""}` : null
}

function translateUiCopy(value: string) {
    return UI_COPY_TRANSLATIONS[normalizeCopyKey(value)] || null
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

function hasExistingAction(row: HTMLTableRowElement, patterns: RegExp[]) {
    return Array.from(row.querySelectorAll<HTMLButtonElement | HTMLAnchorElement>("button,a"))
        .filter(element => !element.dataset.teducaiAction)
        .some(element => patterns.some(pattern => pattern.test(`${element.textContent || ""} ${element.getAttribute("title") || ""} ${element.getAttribute("aria-label") || ""}`)))
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

function isInteractiveElement(element: HTMLElement | null) {
    return Boolean(element?.closest("button,a,input,select,textarea,label,[data-teducai-action]"))
}

function sectionContainerForHeading(heading: HTMLElement) {
    let current = heading.parentElement
    while (current && current.tagName !== "MAIN") {
        const hasUsefulContent = Boolean(current.querySelector("table,form,ul,ol,input,select,textarea,[data-teducai-collapsible-content]"))
        const headingCount = current.querySelectorAll("h2,h3,h4,[data-teducai-section-title]").length
        const isSectionLike = ["SECTION", "ARTICLE", "DIV"].includes(current.tagName)
        if (isSectionLike && hasUsefulContent && headingCount <= 1) return current
        if (isSectionLike && hasUsefulContent && headingCount > 1) return null
        current = current.parentElement
    }
    return null
}

function directHeaderRoot(container: HTMLElement, heading: HTMLElement) {
    let current: HTMLElement = heading
    while (current.parentElement && current.parentElement !== container) current = current.parentElement
    return current
}

function translateElementText(element: HTMLElement) {
    const current = element.textContent?.trim() || ""
    const translated = translateSectionTitle(current) || translateUiCopy(current)
    if (translated && translated !== current && !element.querySelector("svg")) {
        element.textContent = translated
        return
    }

    Array.from(element.childNodes).forEach(node => {
        if (node.nodeType !== Node.TEXT_NODE) return
        const text = node.textContent || ""
        const copy = text.trim()
        const nodeTranslation = translateUiCopy(copy)
        if (nodeTranslation) node.textContent = text.replace(copy, nodeTranslation)
    })
}

function translateDashboardCopy() {
    document.querySelectorAll<HTMLElement>("main h1, main h2, main h3, main h4, main th, main button, main p, main span, main [data-teducai-section-title]").forEach(translateElementText)
}

function ensureSectionToggle(container: HTMLElement, expanded: boolean) {
    const toggles = Array.from(container.children).filter(
        (child): child is HTMLElement => child instanceof HTMLElement && child.dataset.teducaiSectionToggle === "true"
    )
    toggles.slice(1).forEach(toggle => toggle.remove())
    const toggle = toggles[0] || document.createElement("span")
    if (!toggle.dataset.teducaiSectionToggle) {
        toggle.dataset.teducaiSectionToggle = "true"
        toggle.className = "teducai-section-chevron"
        toggle.setAttribute("aria-hidden", "true")
    }
    const nextText = expanded ? "⌃" : "⌄"
    if (toggle.textContent !== nextText) toggle.textContent = nextText
    if (toggle.parentElement !== container) container.appendChild(toggle)
}

function sectionStorageKey(container: HTMLElement, heading: HTMLElement) {
    const title = normalizeCopyKey(heading.textContent || "")
    const index = Array.from(document.querySelectorAll<HTMLElement>("main h2, main h3, main h4, main [data-teducai-section-title]")).indexOf(heading)
    return `teducai:accordion:${window.location.pathname}:${title || "section"}:${Math.max(index, 0)}`
}

function persistedSectionOpen(container: HTMLElement, heading: HTMLElement, fallback: boolean) {
    const key = container.dataset.teducaiAccordionKey || sectionStorageKey(container, heading)
    container.dataset.teducaiAccordionKey = key
    const saved = window.localStorage.getItem(key)
    if (saved === "open") return true
    if (saved === "closed") return false
    return fallback
}

function enhanceCollapsibleSections() {
    document.querySelectorAll<HTMLElement>("main h2, main h3, main h4, main [data-teducai-section-title]").forEach(heading => {
        const translated = translateSectionTitle(heading.textContent?.trim() || "")
        if (translated && heading.textContent?.trim() !== translated) heading.textContent = translated

        const container = sectionContainerForHeading(heading)
        if (!container) return
        if (container.dataset.teducaiCollapsible === "false" || container.closest("[data-teducai-collapsible='false']")) return
        const headerRoot = directHeaderRoot(container, heading)
        if (container.dataset.teducaiCollapsible === "true") {
            ensureSectionToggle(container, container.dataset.teducaiCollapsed === "false")
            return
        }
        const contentNodes = Array.from(container.children).filter((child): child is HTMLElement => child instanceof HTMLElement && child !== headerRoot)
        if (!contentNodes.length) return

        container.dataset.teducaiCollapsible = "true"
        const defaultOpen = persistedSectionOpen(container, heading, container.dataset.teducaiDefaultOpen === "true")
        container.dataset.teducaiCollapsed = defaultOpen ? "false" : "true"
        contentNodes.forEach(child => { child.dataset.teducaiCollapsibleContent = "true" })

        const clickable = headerRoot
        clickable.dataset.teducaiCollapseHeading = "true"
        clickable.setAttribute("role", "button")
        clickable.setAttribute("tabindex", "0")
        clickable.setAttribute("aria-expanded", defaultOpen ? "true" : "false")
        clickable.setAttribute("title", "Cliquer pour ouvrir ou refermer cette section")
        clickable.classList.add("teducai-collapse-heading")
        ensureSectionToggle(container, defaultOpen)
    })
}

function toggleSection(header: HTMLElement) {
    const container = header.closest<HTMLElement>("[data-teducai-collapsible='true']")
    if (!container) return
    const collapsed = container.dataset.teducaiCollapsed !== "false"
    container.dataset.teducaiCollapsed = collapsed ? "false" : "true"
    header.setAttribute("aria-expanded", collapsed ? "true" : "false")
    if (container.dataset.teducaiAccordionKey) {
        window.localStorage.setItem(container.dataset.teducaiAccordionKey, collapsed ? "open" : "closed")
    }
    ensureSectionToggle(container, collapsed)
}

function isPlaceholderRow(row: HTMLTableRowElement) {
    const cells = directCells(row)
    if (cells.length !== 1) return false
    const text = (row.textContent || "").trim().toLowerCase()
    return cells[0].colSpan > 1 || /^(aucun|aucune|chargement|no data|no records|loading)/i.test(text)
}

function tableRows(table: HTMLTableElement) {
    return Array.from(table.querySelectorAll<HTMLTableRowElement>("tbody tr")).filter(row => !isPlaceholderRow(row))
}

function applyTableView(table: HTMLTableElement) {
    const toolbar = document.querySelector<HTMLElement>(`[data-teducai-list-toolbar="${table.dataset.teducaiTableId}"]`)
    if (!toolbar) return
    const query = (toolbar.querySelector<HTMLInputElement>("[data-teducai-list-search]")?.value || "").trim().toLowerCase()
    const pageSizeValue = toolbar.querySelector<HTMLSelectElement>("[data-teducai-page-size]")?.value || "10"
    const pageSize = pageSizeValue === "all" ? Number.MAX_SAFE_INTEGER : Number(pageSizeValue)
    const rows = tableRows(table)
    const matches = rows.filter(row => !query || (row.textContent || "").toLowerCase().includes(query))
    Array.from(table.querySelectorAll<HTMLTableRowElement>("tbody tr")).filter(isPlaceholderRow).forEach(row => {
        row.dataset.teducaiPlaceholderRow = "true"
        row.style.display = matches.length === 0 && !query ? "" : "none"
    })
    const maxPage = Math.max(1, Math.ceil(matches.length / pageSize))
    const requestedPage = Number(toolbar.dataset.teducaiPage || "1")
    const page = Math.min(Math.max(1, requestedPage), maxPage)
    toolbar.dataset.teducaiPage = String(page)
    const start = (page - 1) * pageSize
    const visible = new Set(matches.slice(start, start + pageSize))
    rows.forEach(row => {
        row.style.display = visible.has(row) ? "" : "none"
    })
    const status = toolbar.querySelector<HTMLElement>("[data-teducai-list-status]")
    if (status) status.textContent = `${matches.length} résultat(s) · page ${page}/${maxPage}`
    toolbar.querySelector<HTMLButtonElement>("[data-teducai-page='previous']")!.disabled = page <= 1
    toolbar.querySelector<HTMLButtonElement>("[data-teducai-page='next']")!.disabled = page >= maxPage
}

function ensureTableToolbar(table: HTMLTableElement, tableIndex: number) {
    const tableId = table.dataset.teducaiTableId || `table-${tableIndex}`
    table.dataset.teducaiTableId = tableId
    if (document.querySelector(`[data-teducai-list-toolbar="${tableId}"]`)) return
    const toolbar = document.createElement("div")
    toolbar.dataset.teducaiListToolbar = tableId
    toolbar.dataset.teducaiPage = "1"
    toolbar.className = "teducai-list-toolbar"
    toolbar.innerHTML = `
        <label class="teducai-list-search">
            <span class="sr-only">Rechercher dans la liste</span>
            <input type="search" data-teducai-list-search placeholder="Rechercher dans la liste..." />
        </label>
        <div class="teducai-list-controls">
            <select data-teducai-page-size title="Nombre de lignes par page">
                <option value="10">10 / page</option>
                <option value="25">25 / page</option>
                <option value="50">50 / page</option>
                <option value="all">Tout afficher</option>
            </select>
            <button type="button" data-teducai-view="table" title="Vue tableau">Tableau</button>
            <button type="button" data-teducai-view="card" title="Vue cartes">Cartes</button>
            <button type="button" data-teducai-list-reset title="Réinitialiser la recherche et la pagination">Réinitialiser</button>
            <button type="button" data-teducai-page="previous" title="Page précédente">‹</button>
            <span data-teducai-list-status></span>
            <button type="button" data-teducai-page="next" title="Page suivante">›</button>
        </div>`
    const wrapper = table.parentElement || table
    wrapper.parentElement?.insertBefore(toolbar, wrapper)
    const preferredView = localStorage.getItem("teducai_list_view") || "table"
    table.classList.toggle("teducai-card-view", preferredView === "card")
    toolbar.querySelectorAll<HTMLElement>("[data-teducai-view]").forEach(button => {
        button.dataset.active = String(button.dataset.teducaiView === preferredView)
    })
    Array.from(table.querySelectorAll<HTMLTableCellElement>("thead th")).forEach((header, index) => {
        if (header.dataset.teducaiActionsHead || header.dataset.teducaiSelectHead) return
        header.dataset.teducaiSortIndex = String(index)
        header.title = "Trier cette colonne"
        header.classList.add("cursor-pointer")
    })
    applyTableView(table)
}

function sortTable(table: HTMLTableElement, columnIndex: number, direction: "asc" | "desc") {
    const body = table.tBodies[0]
    if (!body) return
    tableRows(table)
        .sort((left, right) => {
            const leftValue = left.cells[columnIndex]?.textContent?.trim() || ""
            const rightValue = right.cells[columnIndex]?.textContent?.trim() || ""
            return leftValue.localeCompare(rightValue, "fr", { numeric: true, sensitivity: "base" }) * (direction === "asc" ? 1 : -1)
        })
        .forEach(row => body.appendChild(row))
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
    const [confirmBulkDelete, setConfirmBulkDelete] = useState(false)
    const [confirmationRequest, setConfirmationRequest] = useState<(ConfirmationRequest & { resolve: (value: boolean) => void }) | null>(null)

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
            ensureTableToolbar(table, tableIndex)
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
                if (isPlaceholderRow(row)) {
                    row.dataset.teducaiPlaceholderRow = "true"
                    return
                }
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
                const actions = Object.entries(ACTIONS).filter(([key, action]) => {
                    if (!can(action.permission)) return false
                    if (key === "edit") return hasExistingAction(row, [/edit/i, /modifier/i])
                    if (key === "delete") return hasExistingAction(row, [/delete/i, /supprimer/i, /trash/i])
                    return true
                })
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
        translateDashboardCopy()
        enhanceCollapsibleSections()
        enhanceTables()
        const observer = new MutationObserver(() => {
            translateDashboardCopy()
            enhanceCollapsibleSections()
            enhanceTables()
        })
        const main = document.querySelector("main")
        if (main) observer.observe(main, { childList: true, subtree: true })
        return () => observer.disconnect()
    }, [enhanceTables, pathname])

    useEffect(() => {
        const receiveConfirmation = (event: Event) => {
            const detail = (event as CustomEvent<ConfirmationRequest & { resolve: (value: boolean) => void }>).detail
            if (detail) setConfirmationRequest(detail)
        }
        window.addEventListener("teducai:confirm", receiveConfirmation)
        return () => window.removeEventListener("teducai:confirm", receiveConfirmation)
    }, [])

    useEffect(() => {
        const onClick = (event: MouseEvent) => {
            const target = event.target as HTMLElement
            const toolbar = target.closest<HTMLElement>("[data-teducai-list-toolbar]")
            if (toolbar) {
                const table = document.querySelector<HTMLTableElement>(`table[data-teducai-table-id="${toolbar.dataset.teducaiListToolbar}"]`)
                if (!table) return
                const viewButton = target.closest<HTMLElement>("[data-teducai-view]")
                if (viewButton) {
                    const view = viewButton.dataset.teducaiView || "table"
                    localStorage.setItem("teducai_list_view", view)
                    table.classList.toggle("teducai-card-view", view === "card")
                    toolbar.querySelectorAll<HTMLElement>("[data-teducai-view]").forEach(button => {
                        button.dataset.active = String(button.dataset.teducaiView === view)
                    })
                    return
                }
                const pageButton = target.closest<HTMLButtonElement>("[data-teducai-page]")
                if (pageButton) {
                    const current = Number(toolbar.dataset.teducaiPage || "1")
                    toolbar.dataset.teducaiPage = String(pageButton.dataset.teducaiPage === "next" ? current + 1 : current - 1)
                    applyTableView(table)
                    return
                }
                if (target.closest("[data-teducai-list-reset]")) {
                    const search = toolbar.querySelector<HTMLInputElement>("[data-teducai-list-search]")
                    const size = toolbar.querySelector<HTMLSelectElement>("[data-teducai-page-size]")
                    if (search) search.value = ""
                    if (size) size.value = "10"
                    toolbar.dataset.teducaiPage = "1"
                    applyTableView(table)
                    return
                }
            }
            const sortHeader = target.closest<HTMLTableCellElement>("[data-teducai-sort-index]")
            if (sortHeader) {
                const table = sortHeader.closest("table")
                if (!table) return
                const nextDirection = sortHeader.dataset.teducaiSortDirection === "asc" ? "desc" : "asc"
                table.querySelectorAll<HTMLElement>("[data-teducai-sort-index]").forEach(header => delete header.dataset.teducaiSortDirection)
                sortHeader.dataset.teducaiSortDirection = nextDirection
                sortTable(table, Number(sortHeader.dataset.teducaiSortIndex), nextDirection)
                applyTableView(table)
                return
            }
            const sectionToggle = target.closest<HTMLElement>("[data-teducai-section-toggle]")
            if (sectionToggle) {
                const container = sectionToggle.closest<HTMLElement>("[data-teducai-collapsible='true']")
                const header = container ? Array.from(container.children).find(
                    (child): child is HTMLElement => child instanceof HTMLElement && child.dataset.teducaiCollapseHeading === "true"
                ) : null
                if (header) toggleSection(header)
                return
            }
            const collapseHeader = target.closest<HTMLElement>("[data-teducai-collapse-heading]")
            if (collapseHeader && !isInteractiveElement(target)) {
                toggleSection(collapseHeader)
                return
            }
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
            if (action === "edit") clickExistingAction(row, [/edit/i, /modifier/i])
            if (action === "delete") clickExistingAction(row, [/delete/i, /supprimer/i, /trash/i])
        }
        const onInput = (event: Event) => {
            const target = event.target as HTMLElement
            const toolbar = target.closest<HTMLElement>("[data-teducai-list-toolbar]")
            if (!toolbar || (!target.matches("[data-teducai-list-search]") && !target.matches("[data-teducai-page-size]"))) return
            const table = document.querySelector<HTMLTableElement>(`table[data-teducai-table-id="${toolbar.dataset.teducaiListToolbar}"]`)
            if (!table) return
            toolbar.dataset.teducaiPage = "1"
            applyTableView(table)
        }
        document.addEventListener("click", onClick)
        document.addEventListener("input", onInput)
        document.addEventListener("change", onInput)
        const onKeyDown = (event: KeyboardEvent) => {
            if (!["Enter", " "].includes(event.key)) return
            const target = event.target as HTMLElement
            const collapseHeader = target.closest<HTMLElement>("[data-teducai-collapse-heading]")
            if (!collapseHeader) return
            event.preventDefault()
            toggleSection(collapseHeader)
        }
        document.addEventListener("keydown", onKeyDown)
        return () => {
            document.removeEventListener("click", onClick)
            document.removeEventListener("input", onInput)
            document.removeEventListener("change", onInput)
            document.removeEventListener("keydown", onKeyDown)
        }
    }, [])

    const helpUrl = `/${locale}/dashboard/help?section=${helpSection}`
    const embeddedHelpUrl = `/${locale}/help?section=${helpSection}`
    const openHelp = () => {
        const mode = (localStorage.getItem("teducai_help_mode") as HelpMode) || helpMode
        if (mode === "page") window.location.href = helpUrl
        else setHelpFrame(embeddedHelpUrl)
    }

    const bulkRows = () => Array.from(document.querySelectorAll<HTMLInputElement>("main [data-teducai-row-select]:checked")).map(input => input.closest("tr")).filter(Boolean) as HTMLTableRowElement[]
    const bulkExport = (format: "pdf" | "csv" | "xlsx") => bulkRows().forEach(row => exportRow(row, format))
    const bulkPrint = () => bulkRows().forEach(printRow)
    const bulkDelete = () => {
        if (!can("delete")) return
        setConfirmBulkDelete(true)
    }
    const confirmSelectedDeletion = () => {
        bulkRows().forEach(row => clickExistingAction(row, [/delete/i, /supprimer/i, /trash/i]))
        setConfirmBulkDelete(false)
    }

    return (
        <>
            <ConfirmationDialog
                open={confirmBulkDelete}
                onOpenChange={setConfirmBulkDelete}
                title="Supprimer les éléments sélectionnés"
                description={`Vous allez demander la suppression définitive de ${selectedCount} élément(s). Chaque module appliquera ses règles métier et ses permissions.`}
                confirmLabel="Supprimer définitivement"
                destructive
                onConfirm={confirmSelectedDeletion}
            />
            <ConfirmationDialog
                open={Boolean(confirmationRequest)}
                onOpenChange={open => {
                    if (!open && confirmationRequest) confirmationRequest.resolve(false)
                    if (!open) setConfirmationRequest(null)
                }}
                title={confirmationRequest?.title || "Confirmer l'action"}
                description={confirmationRequest?.description || ""}
                confirmLabel={confirmationRequest?.confirmLabel}
                destructive={confirmationRequest?.destructive}
                onConfirm={() => {
                    confirmationRequest?.resolve(true)
                    setConfirmationRequest(null)
                }}
            />
            <style>{`
                .teducai-row-action{display:inline-flex;height:32px;width:32px;align-items:center;justify-content:center;border-radius:9999px;color:#111827;transition:background .2s ease,color .2s ease}
                .teducai-row-action:hover{background:#F0F1F3;color:#000}
                .teducai-row-action svg{height:16px;width:16px}
                [data-teducai-collapsible="true"]{position:relative;transition:background .22s ease,border-color .22s ease,box-shadow .22s ease}
                [data-teducai-collapsible="true"][data-teducai-collapsed="false"]{background:rgba(255,255,255,.96)}
                .teducai-collapse-heading{width:100%;padding-right:44px;cursor:pointer;outline:none}
                .teducai-collapse-heading:focus-visible{box-shadow:0 0 0 3px rgba(0,122,255,.24);border-radius:18px}
                .teducai-section-chevron{position:absolute;right:26px;top:26px;z-index:2;display:inline-flex;height:20px;width:20px;align-items:center;justify-content:center;border-radius:0;background:transparent;color:#667085;font-size:24px;font-weight:500;line-height:1;transition:color .22s ease,transform .22s ease}
                [data-teducai-collapsible="true"][data-teducai-collapsed="false"] .teducai-section-chevron{transform:rotate(0deg)}
                [data-teducai-collapsible="true"]:hover .teducai-section-chevron{color:#111827}
                [data-teducai-collapsible-content="true"]{max-height:6000px;opacity:1;overflow:hidden;transition:max-height .28s ease,opacity .22s ease,margin .22s ease,padding .22s ease}
                [data-teducai-collapsible="true"][data-teducai-collapsed="true"] [data-teducai-collapsible-content="true"]{max-height:0!important;opacity:0!important;margin-top:0!important;margin-bottom:0!important;padding-top:0!important;padding-bottom:0!important;pointer-events:none}
                .dark [data-teducai-collapsible="true"],
                .dark [data-teducai-collapsible="true"][data-teducai-collapsed="false"]{background:#202528!important;border-color:#3b4248!important;color:#f4f7fb!important}
                .dark [data-teducai-collapsible="true"] .teducai-collapse-heading,
                .dark [data-teducai-collapsible="true"] [data-teducai-collapsible-content="true"]{background:transparent!important;color:#f4f7fb!important}
                .dark [data-teducai-collapsible="true"] .teducai-section-chevron{color:#aeb8c4}
                .dark [data-teducai-collapsible="true"]:hover .teducai-section-chevron{color:#fff}
                .dark .teducai-row-action{color:#e7edf5}
                .dark .teducai-row-action:hover{background:#343b41;color:#fff}
                .dark [data-teducai-action-cell] > div{background:#2a3035!important}
                .dark [data-teducai-download-menu]{border-color:#3b4248!important;background:#252b30!important;color:#f4f7fb!important}
                .teducai-list-toolbar{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;margin:0 0 14px;padding:12px;border:1px solid #e5e7eb;border-radius:18px;background:#fff}
                .teducai-list-search{min-width:min(100%,280px);flex:1}
                .teducai-list-search input,.teducai-list-controls select{min-height:42px;width:100%;border:1px solid #d1d5db;border-radius:14px;background:#fff;padding:0 14px;color:#111827;outline:none}
                .teducai-list-controls{display:flex;flex-wrap:wrap;align-items:center;gap:8px}
                .teducai-list-controls select{width:auto}
                .teducai-list-controls button{min-height:38px;border:1px solid #d1d5db;border-radius:12px;padding:0 12px;background:#fff;color:#111827}
                .teducai-list-controls button[data-active="true"]{background:#111827;color:#fff;border-color:#111827}
                .teducai-list-controls button:disabled{cursor:not-allowed;opacity:.4}
                [data-teducai-list-status]{font-size:12px;color:#667085}
                .dark .teducai-list-toolbar{border-color:#3b4248;background:#202528}
                .dark .teducai-list-search input,.dark .teducai-list-controls select,.dark .teducai-list-controls button{border-color:#4b5563;background:#171b1f;color:#f4f7fb}
                .dark .teducai-list-controls button[data-active="true"]{background:#4b5563;border-color:#64748b}
                .dark [data-teducai-list-status]{color:#cbd5e1}
                table.teducai-card-view thead{display:none}
                table.teducai-card-view tbody{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
                table.teducai-card-view tr{display:block;border:1px solid #e5e7eb!important;border-radius:18px;background:#fff;padding:12px}
                table.teducai-card-view td{display:flex!important;align-items:center;justify-content:space-between;gap:14px;border:0!important;padding:8px!important;text-align:right!important;white-space:normal!important}
                table.teducai-card-view td::before{content:attr(data-label);font-size:12px;font-weight:600;color:#667085;text-align:left}
                table.teducai-card-view td[data-teducai-action-cell]{border-top:1px solid #e5e7eb!important;margin-top:6px;padding-top:12px!important}
                table.teducai-card-view td[data-teducai-action-cell]::before{content:""}
                .dark table.teducai-card-view tr{border-color:#3b4248!important;background:#202528}
                .dark table.teducai-card-view td::before{color:#cbd5e1}
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
                <div className={helpMode === "drawer" ? "fixed inset-y-0 right-0 z-[1500] w-full max-w-xl bg-white shadow-2xl dark:bg-[#111827]" : "fixed inset-0 z-[1500] flex items-center justify-center bg-black/45 p-4"}>
                    <div className={helpMode === "drawer" ? "flex h-full flex-col" : "flex h-[86vh] w-full max-w-5xl flex-col overflow-hidden rounded-[28px] bg-white shadow-2xl dark:bg-[#111827]"}>
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
