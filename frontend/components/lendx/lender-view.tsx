"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Bullet } from "@/components/ui/bullet"
import { Badge } from "@/components/ui/badge"
import NumberFlow from "@number-flow/react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { User, CheckCircle2, XCircle, FileText, Inbox, TrendingUp, Loader2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useDemoContext } from "@/lib/demo-context"
import { useWallet, createLendingPool, createDirectLoan, type LendingPoolTransaction, type LoanTransaction } from "@/lib/xrpl"

type LenderStep = "empty" | "pool-created" | "funded" | "loan-request" | "loan-approved"

export default function LenderView() {
  const { lenderStep, setLenderStep, setCurrentDashboard, onNotificationAdd, viewMode } = useDemoContext()
  const { connected, address, signTransaction } = useWallet()
  const [showCreatePoolModal, setShowCreatePoolModal] = useState(false)
  const [showWithdrawModal, setShowWithdrawModal] = useState(false)
  const [showProfileModal, setShowProfileModal] = useState(false)
  const [poolName, setPoolName] = useState("My First Pool")
  const [poolAmount, setPoolAmount] = useState("1000")
  const [poolRate, setPoolRate] = useState("5.2")
  const [maxLoanTerm, setMaxLoanTerm] = useState("180")
  const [minLoanAmount, setMinLoanAmount] = useState("50")
  const [withdrawAmount, setWithdrawAmount] = useState("")
  const [isCreatingPool, setIsCreatingPool] = useState(false)
  const [isApprovingLoan, setIsApprovingLoan] = useState(false)

  useEffect(() => {
    if (viewMode === "lender") {
      setCurrentDashboard("lender")
    }
  }, [viewMode, setCurrentDashboard])

  const getStats = () => {
    switch (lenderStep) {
      case "empty":
        return {
          totalPool: 0,
          activeLoans: 0,
          avgAPY: 0,
        }
      case "pool-created":
      case "funded":
      case "loan-request":
        return {
          totalPool: 1000,
          activeLoans: 0,
          avgAPY: 5.2,
        }
      case "loan-approved":
        return {
          totalPool: 1000,
          activeLoans: 100,
          avgAPY: 5.2,
        }
      default:
        return {
          totalPool: 0,
          activeLoans: 0,
          avgAPY: 0,
        }
    }
  }

  const stats = getStats()

  const borrowerRequest =
    lenderStep === "loan-request"
      ? {
          id: "1",
          name: "Amara K.",
          did: "did:xrpl:rAmara...",
          reasoning: "Requesting $100 to buy a new sewing machine for my tailoring business.",
        }
      : null

  const handleCreatePoolClick = () => {
    setShowCreatePoolModal(true)
  }

  const handleConfirmCreatePool = async () => {
    // DEMO MODE: No wallet required
    try {
      setIsCreatingPool(true)

      // Simulate transaction delay
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Generate mock transaction hash
      const mockTxHash = `0x${Math.random().toString(16).substring(2, 66)}`

      setShowCreatePoolModal(false)
      setLenderStep("pool-created")

      if (onNotificationAdd) {
        onNotificationAdd({
          message: `You have successfully created "${poolName}" with $${poolAmount}. Transaction: ${mockTxHash}`,
          type: "success",
        })
      }
    } catch (error) {
      console.error("Failed to create pool:", error)
      if (onNotificationAdd) {
        onNotificationAdd({
          message: "Failed to create lending pool. Please try again.",
          type: "warning",
        })
      }
    } finally {
      setIsCreatingPool(false)
    }
  }

  const handleWithdrawClick = () => {
    setShowWithdrawModal(true)
  }

  const handleConfirmWithdraw = () => {
    setShowWithdrawModal(false)
    if (onNotificationAdd) {
      onNotificationAdd({
        message: `You have successfully withdrawn $${withdrawAmount} from your pool.`,
        type: "success",
      })
    }
  }

  const handleApprove = async () => {
    // DEMO MODE: No wallet required
    try {
      setIsApprovingLoan(true)

      // Simulate transaction delay
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Generate mock transaction hash
      const mockTxHash = `0x${Math.random().toString(16).substring(2, 66)}`

      setLenderStep("loan-approved")

      if (onNotificationAdd) {
        onNotificationAdd({
          message: `You have approved the $100 loan to Amara K. Transaction: ${mockTxHash}`,
          type: "success",
        })
      }
    } catch (error) {
      console.error("Failed to approve loan:", error)
      if (onNotificationAdd) {
        onNotificationAdd({
          message: "Failed to approve loan. Please try again.",
          type: "warning",
        })
      }
    } finally {
      setIsApprovingLoan(false)
    }
  }

  const handleReject = () => {
    setLenderStep("pool-created")
    if (onNotificationAdd) {
      onNotificationAdd({
        message: "You have rejected the loan request from Amara K.",
        type: "warning",
      })
    }
  }

  const availableLiquidity = lenderStep === "loan-approved" ? 900 : stats.totalPool

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-display">Lender Pool Dashboard</h2>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5">
              <Bullet />
              Total Value in Pools
            </CardTitle>
          </CardHeader>
          <CardContent className="bg-accent pt-6">
            <div className="text-3xl font-display">
              <NumberFlow value={stats.totalPool} prefix="$" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5">
              <Bullet />
              Total Active Loans
            </CardTitle>
          </CardHeader>
          <CardContent className="bg-accent pt-6">
            <div className="text-3xl font-display text-warning">
              <NumberFlow value={stats.activeLoans} prefix="$" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5">
              <Bullet />
              Average Pool APY
            </CardTitle>
          </CardHeader>
          <CardContent className="bg-accent pt-6">
            <div className="text-3xl font-display text-success">
              <NumberFlow value={stats.avgAPY} suffix="%" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* My Pools Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2.5">
            <Bullet />
            My Pools
          </CardTitle>
        </CardHeader>
        <CardContent>
          {lenderStep === "empty" ? (
            <div className="h-[300px] flex flex-col items-center justify-center text-center space-y-4">
              <div className="flex size-16 items-center justify-center rounded-full bg-muted">
                <TrendingUp className="size-8 text-muted-foreground" />
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium">You have not created any pools.</p>
              </div>
              <Button size="lg" onClick={handleCreatePoolClick}>
                + Create a New Pool
              </Button>
            </div>
          ) : (
            // Pool Card
            <Card className="border-2">
              <CardContent className="p-4 space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-display text-lg">{poolName}</h3>
                    <p className="text-sm text-muted-foreground">Created today</p>
                  </div>
                  <Badge className="bg-success text-success-foreground">Active</Badge>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Total Value:</span>
                    <div className="font-medium">${stats.totalPool}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Available:</span>
                    <div className="font-medium text-success">${availableLiquidity}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Rate:</span>
                    <div className="font-medium">{poolRate}%</div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1 bg-transparent" onClick={handleWithdrawClick}>
                    Withdraw Funds
                  </Button>
                  <Button variant="outline" className="flex-1 bg-transparent" disabled>
                    Close Pool
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>

      {/* Pending Loan Requests Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2.5">
            <Bullet />
            Pending Loan Requests
          </CardTitle>
        </CardHeader>
        <CardContent>
          {borrowerRequest ? (
            <ScrollArea className="h-[400px] pr-4">
              <div className="space-y-4">
                <Card className="border-2">
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                        <User className="size-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium">{borrowerRequest.name}</div>
                        <div className="text-xs font-mono text-muted-foreground truncate">{borrowerRequest.did}</div>
                      </div>
                    </div>

                    <p className="text-sm text-muted-foreground leading-relaxed">{borrowerRequest.reasoning}</p>

                    <div className="flex flex-wrap gap-2 pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 min-w-[100px] bg-transparent"
                        onClick={() => setShowProfileModal(true)}
                      >
                        View Profile
                      </Button>
                      <Button
                        size="sm"
                        className="bg-success hover:bg-success/90 text-success-foreground"
                        onClick={handleApprove}
                      >
                        <CheckCircle2 className="size-4 mr-1" />
                        Approve
                      </Button>
                      <Button size="sm" variant="destructive" onClick={handleReject}>
                        <XCircle className="size-4 mr-1" />
                        Reject
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </ScrollArea>
          ) : (
            <div className="h-[400px] flex flex-col items-center justify-center text-center space-y-4">
              <div className="flex size-16 items-center justify-center rounded-full bg-muted">
                <Inbox className="size-8 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">No pending loan requests.</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Pool Modal */}
      <Dialog open={showCreatePoolModal} onOpenChange={setShowCreatePoolModal}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Create New Loan Pool</DialogTitle>
            <DialogDescription>Set up your lending pool to start earning yield</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="pool-name" className="text-sm font-medium">
                Pool Name
              </label>
              <Input
                id="pool-name"
                placeholder="My First Pool"
                value={poolName}
                onChange={(e) => setPoolName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="pool-amount" className="text-sm font-medium">
                Initial Deposit Amount (USD)
              </label>
              <Input
                id="pool-amount"
                type="number"
                placeholder="1000"
                value={poolAmount}
                onChange={(e) => setPoolAmount(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="pool-rate" className="text-sm font-medium">
                Offered Interest Rate (%)
              </label>
              <Input
                id="pool-rate"
                type="number"
                step="0.1"
                placeholder="5.2"
                value={poolRate}
                onChange={(e) => setPoolRate(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="max-loan-term" className="text-sm font-medium">
                Max. Loan Term (Days)
              </label>
              <Input
                id="max-loan-term"
                type="number"
                placeholder="180"
                value={maxLoanTerm}
                onChange={(e) => setMaxLoanTerm(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="min-loan-amount" className="text-sm font-medium">
                Minimum Loan Amount (USD)
              </label>
              <Input
                id="min-loan-amount"
                type="number"
                placeholder="50"
                value={minLoanAmount}
                onChange={(e) => setMinLoanAmount(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowCreatePoolModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleConfirmCreatePool}>Create & Fund Pool</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Withdraw Funds Modal */}
      <Dialog open={showWithdrawModal} onOpenChange={setShowWithdrawModal}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Withdraw Funds</DialogTitle>
            <DialogDescription>
              You have ${availableLiquidity} in available liquidity. You can only withdraw funds if there are no active
              loans.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="withdraw-amount" className="text-sm font-medium">
                Amount to Withdraw (USD)
              </label>
              <Input
                id="withdraw-amount"
                type="number"
                placeholder="0.00"
                value={withdrawAmount}
                onChange={(e) => setWithdrawAmount(e.target.value)}
                max={availableLiquidity}
              />
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowWithdrawModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirmWithdraw}
              disabled={!withdrawAmount || Number.parseFloat(withdrawAmount) <= 0}
            >
              Withdraw
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Profile Modal */}
      <Dialog open={showProfileModal} onOpenChange={setShowProfileModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Borrower Profile: Amara K.</DialogTitle>
          </DialogHeader>
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Decentralized Identity (DID)</label>
              <div className="font-mono text-sm bg-muted p-3 rounded-md break-all">did:xrpl:rAmara...</div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Status</label>
              <div className="flex items-center gap-2">
                <Badge className="bg-success text-success-foreground">
                  <CheckCircle2 className="size-3 mr-1" />
                  Verified
                </Badge>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Credentials</label>
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
                      <FileText className="size-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">Bangkok Business Guild</div>
                      <div className="text-sm text-muted-foreground mt-1">Type: Small Business Owner</div>
                      <div className="text-xs text-muted-foreground mt-2">Issued: January 15, 2025</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Business Information</label>
              <div className="text-sm space-y-1">
                <p>
                  <span className="font-medium">Business:</span> Amara's Tailoring Services
                </p>
                <p>
                  <span className="font-medium">Location:</span> Bangkok, Thailand
                </p>
                <p>
                  <span className="font-medium">Years in Business:</span> 3 years
                </p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowProfileModal(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
