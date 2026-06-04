import * as React from "react"
import { cn } from "@/lib/utils"

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>

const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, type, ...props }, ref) => {
        return (
            <input
                type={type}
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
