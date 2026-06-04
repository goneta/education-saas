import { cloneElement, isValidElement, type ReactNode } from "react"

import { cn } from "@/lib/utils"
import { localizeUiText } from "@/lib/ui-localization"

interface ExplainedFieldProps {
  label: string
  help: string
  required?: boolean
  children: ReactNode
  className?: string
}

export function ExplainedField({ label, help, required, children, className }: ExplainedFieldProps) {
  const localizedLabel = localizeUiText(label)
  const describedChildren = isValidElement<{ title?: string; "aria-label"?: string }>(children)
    ? cloneElement(children, {
        title: children.props.title || help,
        "aria-label": children.props["aria-label"] || localizedLabel,
      })
    : children

  return (
    <label className={cn("block space-y-2 text-sm", className)}>
      <span className="block text-[14px] font-medium text-[#1d1d1f]">
        {localizedLabel}{required ? " *" : ""}
      </span>
      {describedChildren}
    </label>
  )
}

export function fieldHelp(label: string, details?: string) {
  return details || `${label}: saisissez une valeur exacte et verifiable. Ce champ alimente les rapports, les controles et les documents generes automatiquement.`
}
