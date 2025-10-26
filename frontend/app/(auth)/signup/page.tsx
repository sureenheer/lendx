"use client"

import { useState, useEffect } from "react"
// import { useUser } from '@auth0/nextjs-auth0/client'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import LXLogo from "@/components/icons/lx-logo"
import { CheckCircle2, Wallet, ShieldCheck, LayoutDashboard, Loader2, AlertCircle } from "lucide-react"
import { useRouter } from "next/navigation"
import { useWallet } from "@/lib/xrpl"
import { CredentialManager } from "@/lib/xrpl"

export default function SignUpPage() {
  const router = useRouter()
  // const { user, error, isLoading } = useUser()
  const user = null; // Temporarily disable Auth0
  const error = null;
  const isLoading = false;
  const { connected, loading, address, did, generateNewWallet, fundWallet, getBalance, balance } = useWallet()

  const [step1Complete, setStep1Complete] = useState(false)
  const [step2Complete, setStep2Complete] = useState(false)
  const [step3Complete, setStep3Complete] = useState(false)
  const [walletData, setWalletData] = useState<any>(null)
  const [vcStatus, setVcStatus] = useState("")
  const [isCreatingWallet, setIsCreatingWallet] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [isFunding, setIsFunding] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")

  // Check if user is logged in and redirect to next step
  useEffect(() => {
    // For demo purposes, automatically complete step 1
    if (!step1Complete) {
      setStep1Complete(true)
    }
  }, [])

  const handleAuth0Login = () => {
    // For demo, just complete step 1
    setStep1Complete(true)
  }

  const handleCreateWallet = async () => {
    // Remove Auth0 requirement for demo
    // if (!user) {
    //   setErrorMessage("Please log in first")
    //   return
    // }

    try {
      setIsCreatingWallet(true)
      setErrorMessage("")

      // Generate new XRPL wallet (equivalent to Wallet(seed="s...", sequence=0))
      const wallet = await generateNewWallet()
      setWalletData(wallet)
      setStep2Complete(true)

      // Automatically fund wallet on testnet
      setIsFunding(true)
      await fundWallet()
      await getBalance()
      setIsFunding(false)

    } catch (error) {
      console.error("Wallet creation failed:", error)
      setErrorMessage("Failed to create XRPL wallet. Please try again.")
    } finally {
      setIsCreatingWallet(false)
      setIsFunding(false)
    }
  }

  const handleVerification = async () => {
    if (!did) return

    try {
      setIsVerifying(true)
      const credentialManager = CredentialManager.getInstance()
      const credential = await credentialManager.issueVerifiedUserCredential(did)
      setStep3Complete(true)
      setVcStatus(`Verified User Credential issued by LendX Trust Authority`)
    } catch (error) {
      console.error("Verification failed:", error)
      setErrorMessage("Verification failed. Please try again.")
    } finally {
      setIsVerifying(false)
    }
  }

  const handleGoToDashboard = () => {
    router.push("/dashboard")
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4">
        <Loader2 className="size-8 animate-spin mb-4" />
        <p>Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4">
        <div className="max-w-md p-4 border border-red-200 bg-red-50 rounded-lg flex items-center gap-3">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <p className="text-red-700">
            Authentication error: {error.message}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-sides">
      <div className="max-w-3xl w-full space-y-12">
        {/* Header */}
        <div className="flex flex-col items-center gap-6 text-center">
          <LXLogo className="size-20 text-3xl" />
          <div>
            <h1 className="text-4xl font-display mb-2">Create Your Account</h1>
            <p className="text-lg text-muted-foreground">
              {user ? "Complete your XRPL wallet setup" : "Sign in with Google to get started"}
            </p>
          </div>
        </div>

        {errorMessage && (
          <div className="p-4 border border-red-200 bg-red-50 rounded-lg flex items-center gap-3">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <p className="text-red-700">
              {errorMessage}
            </p>
          </div>
        )}

        {/* Stepper */}
        <div className="space-y-8">
          {/* Step 1: Auth0 Login */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  {step1Complete ? (
                    <CheckCircle2 className="size-6 text-green-500" />
                  ) : (
                    <ShieldCheck className="size-6 text-primary" />
                  )}
                </div>
                <div>
                  <CardTitle>Step 1: Sign In with Google</CardTitle>
                  <CardDescription>
                    Authenticate with your Google account to get started.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {!user ? (
                <Button onClick={handleAuth0Login} className="w-full">
                  Sign In with Google
                </Button>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-green-500">
                    <CheckCircle2 className="size-5" />
                    <span className="font-medium">Signed In!</span>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50 border border-border">
                    <p className="text-sm text-muted-foreground">
                      <strong>Email:</strong> {user.email}
                    </p>
                    {user.name && (
                      <p className="text-sm text-muted-foreground">
                        <strong>Name:</strong> {user.name}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Step 2: Create XRPL Wallet */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  {step2Complete ? (
                    <CheckCircle2 className="size-6 text-green-500" />
                  ) : (
                    <Wallet className="size-6 text-primary" />
                  )}
                </div>
                <div>
                  <CardTitle>Step 2: Create XRPL Wallet</CardTitle>
                  <CardDescription>
                    Generate your secure XRPL wallet and DID for blockchain transactions.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {!step2Complete ? (
                <Button
                  onClick={handleCreateWallet}
                  disabled={!step1Complete || isCreatingWallet || isFunding}
                  className="w-full"
                >
                  {isCreatingWallet ? (
                    <>
                      <Loader2 className="size-4 mr-2 animate-spin" />
                      Creating Wallet...
                    </>
                  ) : isFunding ? (
                    <>
                      <Loader2 className="size-4 mr-2 animate-spin" />
                      Funding Wallet...
                    </>
                  ) : (
                    "Create XRPL Wallet"
                  )}
                </Button>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-green-500">
                    <CheckCircle2 className="size-5" />
                    <span className="font-medium">Wallet Created!</span>
                  </div>
                  {walletData && (
                    <div className="p-4 rounded-lg bg-muted/50 border border-border space-y-2">
                      <p className="text-sm font-mono text-muted-foreground break-all">
                        <strong>Address:</strong> {walletData.address}
                      </p>
                      <p className="text-sm font-mono text-muted-foreground break-all">
                        <strong>DID:</strong> {walletData.did}
                      </p>
                      {balance && (
                        <p className="text-sm text-muted-foreground">
                          <strong>Balance:</strong> {(parseInt(balance) / 1000000).toFixed(6)} XRP
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Step 3: Verification */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  {step3Complete ? (
                    <CheckCircle2 className="size-6 text-green-500" />
                  ) : (
                    <ShieldCheck className="size-6 text-primary" />
                  )}
                </div>
                <div>
                  <CardTitle>Step 3: Get Verified (Optional)</CardTitle>
                  <CardDescription>
                    Get a verified credential to build trust in the marketplace.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {!step3Complete ? (
                <Button
                  onClick={handleVerification}
                  disabled={!step2Complete || isVerifying}
                  className="w-full"
                  variant="outline"
                >
                  {isVerifying ? (
                    <>
                      <Loader2 className="size-4 mr-2 animate-spin" />
                      Getting Verified...
                    </>
                  ) : (
                    "Get Verified User Credential"
                  )}
                </Button>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-green-500">
                    <CheckCircle2 className="size-5" />
                    <span className="font-medium">Verified!</span>
                  </div>
                  {vcStatus && (
                    <div className="p-4 rounded-lg bg-muted/50 border border-border">
                      <p className="text-sm text-muted-foreground">{vcStatus}</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Step 4: Dashboard Access */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <LayoutDashboard className="size-6 text-primary" />
                </div>
                <div>
                  <CardTitle>Step 4: Access Dashboard</CardTitle>
                  <CardDescription>
                    Start lending and borrowing on the LendX platform.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Button
                onClick={handleGoToDashboard}
                disabled={!step2Complete}
                className="w-full"
              >
                Go to Dashboard
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
