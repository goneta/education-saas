"use client"

// Uniform "missing prerequisite data" behavior for EVERY creation form.
//
// Never render an empty DB-fed dropdown without explanation: wrap it in
// <RequireOptions>. While loading it shows a muted placeholder; when the list
// is empty it replaces the field with an explicit callout naming the missing
// data + quick-create buttons; otherwise it renders the field untouched.
// Forms must also disable their submit while a REQUIRED list is empty —
// `missingRequired(...)` computes that in one line.

import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"

export interface QuickAction {
    /** Button label, e.g. "Créer une classe". */
    label: string
    /** Absolute app path (locale included by the caller), e.g. `/fr/dashboard/education/classes`. */
    href: string
}

export function MissingDependency({ message, actions }: { message: string; actions: QuickAction[] }) {
    const router = useRouter()
    return (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-800 dark:bg-[#3a3125] dark:text-amber-100">
            <p>{message}</p>
            {actions.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                    {actions.map(action => (
                        <Button key={action.href + action.label} type="button" size="sm" variant="outline"
                            onClick={() => router.push(action.href)}>
                            {action.label}
                        </Button>
                    ))}
                </div>
            )}
        </div>
    )
}

export function RequireOptions({
    loaded,
    count,
    message,
    actions,
    children,
}: {
    /** false while the list is still being fetched (renders nothing yet). */
    loaded: boolean
    /** number of available options once loaded */
    count: number
    /** explicit sentence naming the missing data */
    message: string
    actions: QuickAction[]
    children: React.ReactNode
}) {
    if (!loaded) return <div className="h-10 animate-pulse rounded-md bg-[#F3F4F6] dark:bg-[#2a3035]" />
    if (count === 0) return <MissingDependency message={message} actions={actions} />
    return <>{children}</>
}

/**
 * True when at least one REQUIRED list is loaded-and-empty — use it to
 * disable the form's submit button: `disabled={missingRequired([...])}`.
 */
export function missingRequired(lists: { loaded: boolean; count: number; required?: boolean }[]): boolean {
    return lists.some(list => list.required !== false && list.loaded && list.count === 0)
}
