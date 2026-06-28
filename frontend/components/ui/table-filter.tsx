"use client"

import { useEffect, useMemo, useState } from "react"
import { Search } from "lucide-react"
import { useTranslations } from "next-intl"

import { matchesText } from "@/lib/normalize"

/**
 * Universal table/list/grid filtering, shared across the whole app so every
 * collection page behaves identically: a column selector + a debounced,
 * accent- and case-insensitive search-as-you-type field. No search button.
 *
 * Usage:
 *   const columns = [
 *     { key: "name", label: t("name"), accessor: (r) => r.full_name },
 *     { key: "email", label: t("email"), accessor: (r) => r.email },
 *   ]
 *   const filter = useTableFilter(rows, columns, { storageKey: "teachers" })
 *   <TableFilter {...filter.controls} />
 *   {filter.filtered.map(...)}
 *
 * It is presentation-only over a client-held dataset; it composes with existing
 * pagination/sorting/exports/bulk actions because it simply narrows the array
 * those features already operate on. For very large server-paged datasets, drive
 * `controls.query` into an API request instead (the same component, controlled).
 */

const ALL_COLUMNS = "__all__"

export interface FilterColumnDef {
    key: string
    label: string
}

export interface FilterColumn<T> extends FilterColumnDef {
    /** Value to search for this column on a given row. */
    accessor: (row: T) => unknown
}

export interface TableFilterControls {
    columns: FilterColumnDef[]
    column: string
    query: string
    onColumnChange: (key: string) => void
    onQueryChange: (value: string) => void
}

interface TableFilterState<T> {
    filtered: T[]
    controls: TableFilterControls
    /** Active normalized query (post-debounce), e.g. for "x results" labels. */
    activeQuery: string
}

function readStored(storageKey?: string): { column: string; query: string } | null {
    if (!storageKey || typeof window === "undefined") return null
    try {
        const raw = window.sessionStorage.getItem(`teducai_filter_${storageKey}`)
        return raw ? JSON.parse(raw) : null
    } catch {
        return null
    }
}

export function useTableFilter<T>(
    rows: T[],
    columns: FilterColumn<T>[],
    options?: { debounceMs?: number; storageKey?: string },
): TableFilterState<T> {
    const stored = useMemo(() => readStored(options?.storageKey), [options?.storageKey])
    const [column, setColumn] = useState<string>(stored?.column ?? ALL_COLUMNS)
    const [rawQuery, setRawQuery] = useState<string>(stored?.query ?? "")
    const [debounced, setDebounced] = useState<string>(rawQuery)

    // Debounce so rapid keystrokes don't thrash large lists (or API calls).
    useEffect(() => {
        const id = setTimeout(() => setDebounced(rawQuery), options?.debounceMs ?? 200)
        return () => clearTimeout(id)
    }, [rawQuery, options?.debounceMs])

    // Preserve the selected filter across navigation within the session.
    useEffect(() => {
        if (!options?.storageKey || typeof window === "undefined") return
        try {
            window.sessionStorage.setItem(
                `teducai_filter_${options.storageKey}`,
                JSON.stringify({ column, query: rawQuery }),
            )
        } catch {
            /* ignore quota / privacy-mode errors */
        }
    }, [column, rawQuery, options?.storageKey])

    const filtered = useMemo(() => {
        if (!debounced.trim()) return rows
        const active = column === ALL_COLUMNS ? columns : columns.filter(definition => definition.key === column)
        if (active.length === 0) return rows
        return rows.filter(row => active.some(definition => matchesText(definition.accessor(row), debounced)))
    }, [rows, columns, column, debounced])

    const controls: TableFilterControls = {
        columns: columns.map(({ key, label }) => ({ key, label })),
        column,
        query: rawQuery,
        onColumnChange: setColumn,
        onQueryChange: setRawQuery,
    }

    return { filtered, controls, activeQuery: debounced }
}

export function TableFilter({ columns, column, query, onColumnChange, onQueryChange }: TableFilterControls) {
    const t = useTranslations("filters")

    return (
        <div className="flex w-full flex-col gap-2 sm:flex-row sm:items-center">
            <select
                value={column}
                onChange={event => onColumnChange(event.target.value)}
                aria-label={t("column")}
                className="h-10 shrink-0 rounded-xl border border-[#dfe3e8] bg-transparent px-3 text-sm outline-none focus:border-black dark:border-[#4a535b] dark:focus:border-white sm:w-44"
            >
                <option value={ALL_COLUMNS}>{t("allColumns")}</option>
                {columns.map(definition => (
                    <option key={definition.key} value={definition.key}>{definition.label}</option>
                ))}
            </select>
            <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#9aa3ad]" />
                <input
                    type="search"
                    value={query}
                    onChange={event => onQueryChange(event.target.value)}
                    placeholder={t("searchPlaceholder")}
                    className="h-10 w-full rounded-xl border border-[#dfe3e8] bg-transparent pl-9 pr-3 text-sm outline-none focus:border-black dark:border-[#4a535b] dark:focus:border-white"
                />
            </div>
        </div>
    )
}
