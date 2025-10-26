"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import LXLogo from "@/components/icons/lx-logo"
import { CheckCircle2, Wallet, ShieldCheck, LayoutDashboard, Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useWallet } from "@/lib/xrpl"
import { CredentialManager } from "@/lib/xrpl"

export default function SignUpPage() {
  const router = useRouter()
  const { connected, loading, address, did, connectWallet, generateDID } = useWallet()
  const [step1Complete, setStep1Complete] = useState(false)
  const [step2Complete, setStep2Complete] = useState(false)
  const [didStatus, setDidStatus] = useState("")
  const [vcStatus, setVcStatus] = useState("")
  const [isConnecting, setIsConnecting] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)

  const handleStep1 = async () => {
    try {
      setIsConnecting(true)
      await connectWallet()
      generateDID()
      setStep1Complete(true)
      setDidStatus(did || `did:xrpl:${address}`)
    } catch (error) {
      console.error("Wallet connection failed:", error)
      // Handle error - show toast or alert
    } finally {
      setIsConnecting(false)
    }
  }

  const handleStep2 = async () => {
    if (!did) return

    try {
      setIsVerifying(true)
      const credentialManager = CredentialManager.getInstance()
      const credential = await credentialManager.issueVerifiedUserCredential(did)
      setStep2Complete(true)
      setVcStatus(`Verified User Credential issued by LendX Trust Authority`)
    } catch (error) {
      console.error("Verification failed:", error)
    } finally {
      setIsVerifying(false)
    }
  }

  const handleStep3 = () => {
    router.push("/dashboard")
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-sides">
      <div className="max-w-3xl w-full space-y-12">
        {/* Header */}
        <div className="flex flex-col items-center gap-6 text-center">
          <LXLogo className="size-20 text-3xl" />
          <div>
            <h1 className="text-4xl font-display mb-2">Create Your Account</h1>
            <p className="text-lg text-muted-foreground">Complete these steps to lend and borrow on LendX</p>
          </div>
        </div>

        {/* Stepper */}
        <div className="space-y-8">
          {/* Step 1 */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  {step1Complete ? (
                    <CheckCircle2 className="size-6 text-green-500" />
                  ) : (
                    <Wallet className="size-6 text-primary" />
                  )}
                </div>
                <div>
                  <CardTitle>Step 1: Connect Wallet & Create ID</CardTitle>
                  <CardDescription>
                    Connect your wallet to create your secure Decentralized Identity (DID).
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {!step1Complete ? (
                <Button
                  onClick={handleStep1}
                  className="w-full"
                  disabled={isConnecting}
                >
                  {isConnecting ? (
                    <>
                      <Loader2 className="size-4 mr-2 animate-spin" />
                      Connecting Wallet...
                    </>
                  ) : (
                    "Connect & Create DID"
                  )}
                </Button>
              ) : (
                <div className="flex items-center gap-2 text-green-500">
                  <CheckCircle2 className="size-5" />
                  <span className="font-medium">Identity Created!</span>
                </div>
              )}
              {(didStatus || connected) && (
                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <p className="text-sm font-mono text-muted-foreground break-all">
                    {didStatus || (address ? `did:xrpl:${address}` : "Generating DID...")}
                  </p>
                  {address && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Wallet: {address}
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Step 2 */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  {step2Complete ? (
                    <CheckCircle2 className="size-6 text-green-500" />
                  ) : (
                    <ShieldCheck className="size-6 text-primary" />
                  )}
                </div>
                <div>
                  <CardTitle>Step 2: Get Verified</CardTitle>
                  <CardDescription>Verify your identity to build trust and access the marketplace.</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {!step2Complete ? (
                <Button
                  onClick={handleStep2}
                  disabled={!step1Complete || isVerifying}
                  className="w-full"
                >
                  {isVerifying ? (
                    <>
                      <Loader2 className="size-4 mr-2 animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    "Get 'Verified User' Credential"
                  )}
                </Button>
              ) : (
                <div className="flex items-center gap-2 text-green-500">
                  <CheckCircle2 className="size-5" />
                  <span className="font-medium">Verified!</span>
                </div>
              )}
              {vcStatus && (
                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <p className="text-sm text-muted-foreground">{vcStatus}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Step 3 */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <LayoutDashboard className="size-6 text-primary" />
                </div>
                <div>
                  <CardTitle>Step 3: Access Dashboard</CardTitle>
                  <CardDescription>
                    Once verified, you can access the dashboard to create loan pools or apply for loans.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Button onClick={handleStep3} disabled={!step2Complete} className="w-full">
                Go to Dashboard
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
