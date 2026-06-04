import * as React from "react"
import { cn } from "@/lib/utils"
import { helpForLabel, localizeUiText } from "@/lib/ui-localization"

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ className, placeholder, title, "aria-label": ariaLabel, ...props }, ref) => {
        const localizedPlaceholder = typeof placeholder === "string" ? localizeUiText(placeholder) : placeholder
        const inferredLabel = (typeof ariaLabel === "string" && ariaLabel) || (typeof localizedPlaceholder === "string" && localizedPlaceholder) || props.name || "Message"
        return (
            <textarea
                placeholder={localizedPlaceholder}
                title={title || helpForLabel(String(inferredLabel))}
                aria-label={typeof ariaLabel === "string" ? localizeUiText(ariaLabel) : ariaLabel || localizeUiText(String(inferredLabel))}
                className={cn(
                    "flex min-h-[80px] w-full rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-sm text-[#111827] placeholder:text-[#6B7280] focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50",
                    className
                )}
                ref={ref}
                {...props}
            />
        )
    }
)
Textarea.displayName = "Textarea"

export { Textarea }
