import Link from "next/link"
import { Button } from "@/components/ui/button"
import LXLogo from "@/components/icons/lx-logo"

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-sides">
      <div className="max-w-4xl w-full text-center space-y-12">
        {/* Logo and Branding */}
        <div className="flex flex-col items-center gap-6">
          <LXLogo className="size-24 text-4xl" />
          <div>
            <h1 className="text-6xl font-display mb-2">LendX</h1>
            <p className="text-lg text-muted-foreground uppercase tracking-wide">Financial Inclusion for All</p>
          </div>
        </div>

        {/* Hero Message */}
        <div className="space-y-6">
          <h2 className="text-4xl md:text-5xl font-bold text-balance leading-tight">
            Decentralized Lending for Emerging Markets
          </h2>
          <p className="text-xl text-muted-foreground text-balance max-w-2xl mx-auto">
            Connect lenders with small businesses through secure, blockchain-powered microloans. Build credit, earn
            yield, and drive financial inclusion.
          </p>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Button asChild size="lg" className="min-w-[200px] text-lg h-14">
            <Link href="/dashboard">Log In</Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="min-w-[200px] text-lg h-14 bg-transparent">
            <Link href="/signup">Sign Up</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
