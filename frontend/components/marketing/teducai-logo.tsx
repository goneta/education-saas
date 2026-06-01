import { BrainCircuit, GraduationCap } from "lucide-react"

import { cn } from "@/lib/utils"

type TeducAILogoProps = {
  className?: string
  markClassName?: string
  showTagline?: boolean
}

export function TeducAILogo({
  className,
  markClassName,
  showTagline = false,
}: TeducAILogoProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div
        className={cn(
          "relative flex h-11 w-11 items-center justify-center rounded-xl bg-[#0F766E] text-white shadow-sm",
          markClassName
        )}
        aria-hidden="true"
      >
        <GraduationCap className="absolute h-6 w-6 translate-x-1 translate-y-1 opacity-95" />
        <BrainCircuit className="absolute h-5 w-5 -translate-x-2 -translate-y-2 text-[#A7F3D0]" />
      </div>
      <div className="leading-tight">
        <p className="text-xl font-bold tracking-normal text-[#0F172A]">TeducAI</p>
        {showTagline ? (
          <p className="text-xs font-medium text-[#64748B]">
            Gestion scolaire intelligente
          </p>
        ) : null}
      </div>
    </div>
  )
}
