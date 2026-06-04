import type { ReactNode } from "react"
import { Info } from "lucide-react"

import { cn } from "@/lib/utils"

interface ExplainedFieldProps {
  label: string
  help: string
  required?: boolean
  children: ReactNode
  className?: string
}

export function ExplainedField({ label, help, required, children, className }: ExplainedFieldProps) {
  return (
    <label className={cn("group block space-y-2 text-sm", className)}>
      <span className="flex items-center gap-2 text-[14px] font-medium text-[#1d1d1f]">
        {label}{required ? " *" : ""}
        <span className="relative inline-flex" tabIndex={0}>
          <Info className="size-4 text-[#0066cc]" aria-hidden="true" />
          <span className="pointer-events-none absolute left-1/2 top-6 z-20 w-72 -translate-x-1/2 rounded-[14px] border border-[#e0e0e0] bg-white px-4 py-3 text-left text-xs font-normal leading-5 text-[#333333] opacity-0 shadow-[rgba(0,0,0,0.08)_0_12px_36px] transition group-hover:opacity-100 group-focus-within:opacity-100">
            {help}
          </span>
        </span>
      </span>
      {children}
    </label>
  )
}

export function fieldHelp(label: string, details?: string) {
  return details || `${label}: saisissez une valeur exacte et vérifiable. Ce champ alimente les rapports, les contrôles et les documents générés automatiquement.`
}
