import * as React from "react"
import { cn } from "@/lib/utils"
import { helpForLabel, localizeUiText } from "@/lib/ui-localization"

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>

const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, type, placeholder, title, "aria-label": ariaLabel, ...props }, ref) => {
        const localizedPlaceholder = typeof placeholder === "string" ? localizeUiText(placeholder) : placeholder
        const inferredLabel = (typeof ariaLabel === "string" && ariaLabel) || (typeof localizedPlaceholder === "string" && localizedPlaceholder) || props.name
        return (
            <input
                type={type}
                placeholder={localizedPlaceholder}
                title={title || helpForLabel(String(inferredLabel || "Ce champ"))}
                aria-label={ariaLabel}
                className={cn(
                    "flex h-11 w-full rounded-full border border-[#e0e0e0] bg-white px-5 py-2 text-[15px] text-[#1d1d1f] placeholder:text-[#7a7a7a] transition focus:border-[#0066cc] focus:outline-none focus:ring-4 focus:ring-[#0066cc]/15 disabled:cursor-not-allowed disabled:opacity-50",
                    className
                )}
                ref={ref}
                {...props}
            />
        )
    }
)
Input.displayName = "Input"

export { Input }
