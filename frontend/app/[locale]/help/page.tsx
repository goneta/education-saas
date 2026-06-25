"use client"

import { HelpContent } from "../dashboard/help/page"

export default function StandaloneHelpPage() {
  return (
    <main className="min-h-screen bg-[#F8FAFC] text-[#111827] dark:bg-[#111827] dark:text-white">
      <HelpContent embedded />
    </main>
  )
}
