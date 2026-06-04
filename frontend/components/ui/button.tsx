import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"
import { localizeUiText } from "@/lib/ui-localization"

const buttonVariants = cva(
  "inline-flex min-h-11 w-auto items-center justify-center gap-2 whitespace-nowrap rounded-full text-[15px] font-normal tracking-[-0.01em] transition-all active:scale-95 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-black/20 focus-visible:ring-[4px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
  {
    variants: {
      variant: {
        default: "bg-black text-white hover:bg-black/90",
        destructive:
          "bg-destructive text-white hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/60",
        outline:
          "border border-[#0066cc] bg-white text-[#0066cc] hover:bg-[#f5f5f7] dark:bg-input/30 dark:border-input dark:hover:bg-input/50",
        secondary:
          "bg-[#fafafc] text-[#333333] ring-1 ring-[#f0f0f0] hover:bg-white",
        ghost:
          "text-[#0066cc] hover:bg-[#0066cc]/10 hover:text-[#0066cc] dark:hover:bg-accent/50",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-11 px-5 py-2.5 has-[>svg]:px-4",
        sm: "h-9 gap-1.5 px-4 text-sm has-[>svg]:px-3",
        lg: "h-12 px-7 text-[17px] has-[>svg]:px-5",
        icon: "size-11 rounded-full",
        "icon-sm": "size-9 rounded-full",
        "icon-lg": "size-12 rounded-full",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  children,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    >
      {typeof children === "string" ? localizeUiText(children) : children}
    </Comp>
  )
}

export { Button, buttonVariants }
