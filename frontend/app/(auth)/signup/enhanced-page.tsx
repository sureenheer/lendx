"use client"

import { useState, useEffect } from "react"
import { useUser } from '@auth0/nextjs-auth0'
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import LXLogo from "@/components/icons/lx-logo"
import { CheckCircle2, Wallet, ShieldCheck, LayoutDashboard, Loader2, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { apiClient, DIDCreationResponse } from "@/lib/api"

export default function EnhancedSignUpPage() {
  const { user, error, isLoading } = useUser()
  const router = useRouter()

  const [step1Complete, setStep1Complete] = useState(false)
  const [step2Complete, setStep2Complete] = useState(false)
  const [step3Complete, setStep3Complete] = useState(false)

  const [isCreatingDID, setIsCreatingDID] = useState(false)
  const [isVerifying, setIsVerifying] = useState(false)
  const [didCreationData, setDidCreationData] = useState<DIDCreationResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState("")

  const [userProfile, setUserProfile] = useState<any>(null)
  const [needsDIDCreation, setNeedsDIDCreation] = useState(false)

  // Check user status on mount and when user changes
  useEffect(() => {
    if (user && !isLoading) {
      checkUserStatus()
    }
  }, [user, isLoading])

  const checkUserStatus = async () => {
    try {
      const response = await apiClient.getAuthStatus()
      if (response.success && response.data) {
        const { hasStoredProfile, hasDID, needsDIDCreation: needsCreation } = response.data
        setUserProfile(response.data.user)
        setNeedsDIDCreation(needsCreation)

        if (hasStoredProfile && hasDID) {
          setStep1Complete(true)
          setStep2Complete(true)
          // If user already has everything, redirect to dashboard
          router.push("/dashboard")
        } else if (hasStoredProfile && !hasDID) {
          setStep1Complete(true)
          setNeedsDIDCreation(true)
        }
      }
    } catch (error) {
      console.error("Failed to check user status:", error)
    }
  }

  const handleAuth0Login = () => {
    window.location.href = '/api/auth/login'
  }

  const handleCreateDIDAndWallet = async () => {
    if (!user) {
      setErrorMessage("Please log in first")
      return
    }

    setIsCreatingDID(true)
    setErrorMessage("")

    try {
      // First try to register the user (create DID + wallet)
      let response = await apiClient.register()

      // If user already exists, try creating DID for existing user
      if (!response.success && response.error?.includes('already has a DID')) {
        response = await apiClient.createDID()
      }

      if (response.success && response.data) {
        setDidCreationData(response.data)
        setStep1Complete(true)
        setStep2Complete(true) // Since credential is issued automatically
        setNeedsDIDCreation(false)
      } else {
        setErrorMessage(response.error || "Failed to create DID and wallet")
      }
    } catch (error) {
      console.error("DID creation failed:", error)
      setErrorMessage("Failed to create DID and wallet. Please try again.")
    } finally {
      setIsCreatingDID(false)
    }
  }

  const handleAdditionalVerification = async () => {
    setIsVerifying(true)
    setErrorMessage("")

    try {
      // Issue additional business credential as example
      const response = await apiClient.issueBusinessCredential({
        businessName: "Sample Business",
        businessType: "Technology",
        registrationNumber: "SAMPLE123"
      })

      if (response.success) {
        setStep3Complete(true)
      } else {
        setErrorMessage(response.error || "Failed to complete verification")
      }
    } catch (error) {
      console.error("Additional verification failed:", error)
      setErrorMessage("Failed to complete verification. Please try again.")
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
        <Alert className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Authentication error: {error.message}
          </AlertDescription>
        </Alert>
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
              {user ? "Complete your profile with DID and XRPL wallet" : "Sign in to get started with LendX"}
            </p>
          </div>
        </div>

        {errorMessage && (
          <Alert className="border-red-200 bg-red-50">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <AlertDescription className="text-red-700">
              {errorMessage}
            </AlertDescription>
          </Alert>
        )}

        {/* Stepper */}
        <div className="space-y-8">
          {/* Step 1: Auth0 Login or DID Creation */}
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
                  <CardTitle>
                    {user ? "Step 1: Create DID & XRPL Wallet" : "Step 1: Sign In"}
                  </CardTitle>
                  <CardDescription>
                    {user
                      ? "Create your decentralized identity and XRPL wallet for secure transactions."
                      : "Sign in with your Google account to get started."
                    }
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {!user ? (
                <Button onClick={handleAuth0Login} className="w-full">
                  Sign In with Google
                </Button>
              ) : !step1Complete ? (
                <Button
                  onClick={handleCreateDIDAndWallet}
                  className="w-full"
                  disabled={isCreatingDID}
                >
                  {isCreatingDID ? (
                    <>
                      <Loader2 className="size-4 mr-2 animate-spin" />
                      Creating DID & Wallet...
                    </>
                  ) : (
                    "Create DID & XRPL Wallet"
                  )}
                </Button>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-green-500">
                    <CheckCircle2 className="size-5" />
                    <span className="font-medium">DID & Wallet Created!</span>
                  </div>
                  {didCreationData && (
                    <div className="p-4 rounded-lg bg-muted/50 border border-border space-y-2">
                      <p className="text-sm font-mono text-muted-foreground break-all">
                        <strong>DID:</strong> {didCreationData.did}
                      </p>
                      <p className="text-sm font-mono text-muted-foreground break-all">
                        <strong>XRPL Address:</strong> {didCreationData.xrplAddress}
                      </p>
                    </div>
                  )}
                  {user && (
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
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Step 2: Automatic Verification */}
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
                  <CardTitle>Step 2: Basic Verification</CardTitle>
                  <CardDescription>
                    Automatic verification credential issued with your DID.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {step2Complete ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-green-500">
                    <CheckCircle2 className="size-5" />
                    <span className="font-medium">Verified!</span>
                  </div>
                  <div className="p-4 rounded-lg bg-muted/50 border border-border">
                    <p className="text-sm text-muted-foreground">
                      Basic user verification credential has been issued and stored in your DID.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-lg bg-muted/50 border border-border">
                  <p className="text-sm text-muted-foreground">
                    Complete Step 1 to receive your verification credential.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Step 3: Additional Verification (Optional) */}
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
                  <CardTitle>Step 3: Enhanced Verification (Optional)</CardTitle>
                  <CardDescription>
                    Add business or income verification for higher trust score.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {!step3Complete ? (
                <Button
                  onClick={handleAdditionalVerification}
                  disabled={!step2Complete || isVerifying}
                  className="w-full"
                  variant="outline"
                >
                  {isVerifying ? (
                    <>
                      <Loader2 className="size-4 mr-2 animate-spin" />
                      Adding Verification...
                    </>
                  ) : (
                    "Add Business Verification (Demo)"
                  )}
                </Button>
              ) : (
                <div className="flex items-center gap-2 text-green-500">
                  <CheckCircle2 className="size-5" />
                  <span className="font-medium">Enhanced Verification Complete!</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Step 4: Access Dashboard */}
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