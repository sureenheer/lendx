"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Bullet } from "@/components/ui/bullet"
import NumberFlow from "@number-flow/react"
import { Inbox, Clock, CheckCircle2, DollarSign } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useDemoContext } from "@/lib/demo-context"

export default function BorrowerView() {
  const { borrowerStep, setBorrowerStep, setCurrentDashboard, onNotificationAdd, viewMode } = useDemoContext()
  const [showApplyModal, setShowApplyModal] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [loanAmount, setLoanAmount] = useState("100")
  const [loanPurpose, setLoanPurpose] = useState("Buy a new sewing machine for my tailoring business")

  // Set current dashboard to borrower when component mounts
  useEffect(() => {
    if (viewMode === "borrower") {
      setCurrentDashboard("borrower")
    }
  }, [viewMode, setCurrentDashboard])

  const getStats = () => {
    switch (borrowerStep) {
      case "empty":
      case "pending":
        return {
          activeLoans: 0,
          totalRepaid: 0,
          nextPaymentDue: "N/A",
        }
      case "approved":
        return {
          activeLoans: 100,
          totalRepaid: 0,
          nextPaymentDue: "Nov 25, 2025",
        }
      case "payment-made":
        return {
          activeLoans: 90,
          totalRepaid: 10,
          nextPaymentDue: "Dec 25, 2025",
        }
      default:
        return {
          activeLoans: 0,
          totalRepaid: 0,
          nextPaymentDue: "N/A",
        }
    }
  }

  const stats = getStats()

  const handleApplyClick = () => {
    setShowApplyModal(true)
  }

  const handleSubmitApplication = () => {
    setShowApplyModal(false)
    setBorrowerStep("pending")
    if (onNotificationAdd) {
      onNotificationAdd({
        message: "Your $100 loan request has been submitted for review.",
        type: "info",
      })
    }
  }

  const handleMakePaymentClick = () => {
    setShowPaymentModal(true)
  }

  const handleConfirmPayment = () => {
    setShowPaymentModal(false)
    setBorrowerStep("payment-made")
    if (onNotificationAdd) {
      onNotificationAdd({
        message: "Your $10 payment was successful. Thank you!",
        type: "success",
      })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-display">My Loans Dashboard</h2>
      </div>

      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5">
              <Bullet />
              Active Loans
            </CardTitle>
          </CardHeader>
          <CardContent className="bg-accent pt-6">
            <div className="text-3xl font-display">
              <NumberFlow value={stats.activeLoans} prefix="$" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5">
              <Bullet />
              Total Repaid
            </CardTitle>
          </CardHeader>
          <CardContent className="bg-accent pt-6">
            <div className="text-3xl font-display text-success">
              <NumberFlow value={stats.totalRepaid} prefix="$" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2.5">
              <Bullet />
              Next Payment Due
            </CardTitle>
          </CardHeader>
          <CardContent className="bg-accent pt-6">
            <div className="text-xl font-display">{stats.nextPaymentDue}</div>
          </CardContent>
        </Card>
      </div>

      {/* My Loans Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2.5">
            <Bullet />
            My Loans
          </CardTitle>
        </CardHeader>
        <CardContent>
          {borrowerStep === "empty" ? (
            // Empty State
            <div className="h-[300px] flex flex-col items-center justify-center text-center space-y-4">
              <div className="flex size-16 items-center justify-center rounded-full bg-muted">
                <Inbox className="size-8 text-muted-foreground" />
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium">You have no active loans.</p>
                <p className="text-xs text-muted-foreground">Apply for a loan to get started</p>
              </div>
              <Button size="lg" onClick={handleApplyClick}>
                Apply for a New Loan
              </Button>
            </div>
          ) : borrowerStep === "pending" ? (
            // Pending State
            <div className="space-y-4">
              <Card className="border-2 border-warning/50">
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="font-display text-lg">$100 Loan</div>
                      <p className="text-sm text-muted-foreground">{loanPurpose}</p>
                    </div>
                    <Badge className="bg-warning text-warning-foreground">
                      <Clock className="size-3 mr-1" />
                      Pending Approval
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : borrowerStep === "approved" || borrowerStep === "payment-made" ? (
            // Approved/Active State
            <div className="space-y-4">
              <Card className="border-2 border-success/50">
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="font-display text-lg">
                        ${borrowerStep === "payment-made" ? "90" : "100"} Loan
                        {borrowerStep === "payment-made" && (
                          <span className="text-sm text-muted-foreground ml-2">($90 remaining)</span>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{loanPurpose}</p>
                    </div>
                    <Badge className="bg-success text-success-foreground">
                      <CheckCircle2 className="size-3 mr-1" />
                      Active
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Interest Rate:</span>
                      <div className="font-medium">5.2%</div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Term:</span>
                      <div className="font-medium">6 Months</div>
                    </div>
                  </div>

                  {borrowerStep === "approved" && (
                    <Button className="w-full" onClick={handleMakePaymentClick}>
                      <DollarSign className="size-4 mr-2" />
                      Make Payment
                    </Button>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* Apply to Pool Modal */}
      <Dialog open={showApplyModal} onOpenChange={setShowApplyModal}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Apply to the LendX Community Pool</DialogTitle>
            <DialogDescription>Submit your loan request to the community lending pool</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Pool Details */}
            <div className="bg-accent rounded-lg p-4 space-y-2">
              <h3 className="font-medium text-sm">Pool Details</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Available Liquidity:</span>
                  <div className="font-medium">$1,000</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Interest Rate:</span>
                  <div className="font-medium">~5.2%</div>
                </div>
                <div className="col-span-2">
                  <span className="text-muted-foreground">Max. Loan Term:</span>
                  <div className="font-medium">6 Months</div>
                </div>
              </div>
            </div>

            {/* Application Form */}
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="loan-amount" className="text-sm font-medium">
                  Loan Amount (USD)
                </label>
                <Input
                  id="loan-amount"
                  type="number"
                  placeholder="100"
                  value={loanAmount}
                  onChange={(e) => setLoanAmount(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="loan-purpose" className="text-sm font-medium">
                  Loan Purpose
                </label>
                <Textarea
                  id="loan-purpose"
                  placeholder="Why do you need this loan?"
                  rows={3}
                  value={loanPurpose}
                  onChange={(e) => setLoanPurpose(e.target.value)}
                />
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowApplyModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmitApplication}>Submit Request to Pool</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Make Payment Modal */}
      <Dialog open={showPaymentModal} onOpenChange={setShowPaymentModal}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Confirm Repayment</DialogTitle>
            <DialogDescription>Are you sure you want to make your first payment of $10?</DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowPaymentModal(false)}>
              No, Cancel
            </Button>
            <Button className="bg-success hover:bg-success/90 text-success-foreground" onClick={handleConfirmPayment}>
              Yes, Pay $10
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
