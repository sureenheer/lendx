"use client"

import { useDemoContext } from "@/lib/demo-context"
import LenderView from "@/components/lendx/lender-view"
import BorrowerView from "@/components/lendx/borrower-view"
import LXLogo from "@/components/icons/lx-logo"

export default function DashboardPage() {
  const { viewMode } = useDemoContext()

  return (
    <div className="min-h-screen py-sides">
      <div className="mb-8 flex items-center gap-4">
        <LXLogo className="size-16 text-2xl" />
        <div>
          <h1 className="text-3xl font-display">LendX</h1>
          <p className="text-sm text-muted-foreground uppercase tracking-wide">Financial Inclusion for All</p>
        </div>
      </div>

      {viewMode === "lender" ? <LenderView /> : <BorrowerView />}
    </div>
  )
}
