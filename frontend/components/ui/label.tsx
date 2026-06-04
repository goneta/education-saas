"use client"

import * as React from "react"
import * as LabelPrimitive from "@radix-ui/react-label"
import { Info } from "lucide-react"

import { cn } from "@/lib/utils"
import { helpForLabel, localizeUiText } from "@/lib/ui-localization"

function Label({
  className,
  children,
  ...props
}: React.ComponentProps<typeof LabelPrimitive.Root>) {
  const text = typeof children === "string" ? children : undefined
  const localized = text ? localizeUiText(text) : children
  const help = text ? helpForLabel(localized as string) : undefined

  return (
    <LabelPrimitive.Root
      data-slot="label"
      className={cn(
        "group/label flex items-center gap-2 text-sm leading-none font-medium select-none group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50 peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
        className
      )}
      {...props}
    >
      {localized}
      {help && (
        <span className="relative inline-flex" tabIndex={0}>
          <Info className="size-4 text-[#0066cc]" aria-hidden="true" />
          <span className="pointer-events-none absolute left-1/2 top-6 z-50 w-72 -translate-x-1/2 rounded-[14px] border border-[#e0e0e0] bg-white px-4 py-3 text-left text-xs font-normal leading-5 text-[#333333] opacity-0 shadow-[rgba(0,0,0,0.08)_0_12px_36px] transition group-hover/label:opacity-100 group-focus-within/label:opacity-100">
            {help}
          </span>
        </span>
      )}
    </LabelPrimitive.Root>
  )
}

export { Label }
