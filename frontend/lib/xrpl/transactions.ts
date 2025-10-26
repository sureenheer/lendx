/**
 * XRPL Transaction Builders
 * Creates and manages lending transactions on XRPL
 */

import { Payment, TrustSet, xrpToDrops } from 'xrpl'
import type { LendingPoolTransaction, LoanTransaction } from './types'
import { signTransaction } from './wallet'

// RLUSD issuer configuration
const RLUSD_ISSUER = process.env.NEXT_PUBLIC_RLUSD_ISSUER || 'rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx'
const RLUSD_CURRENCY = 'RLUSD'

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Create lending pool
 * Calls backend API to register pool and returns transaction hash
 */
export async function createLendingPool(poolData: LendingPoolTransaction): Promise<string> {
  try {
    // Call backend API to create pool
    const response = await fetch(`${API_BASE_URL}/pools`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: 'My Lending Pool',
        amount: parseFloat(poolData.amount) / 1_000_000, // Convert drops to XRP
        interest_rate: 5.2,
        max_term_days: 180,
        min_loan_amount: 50,
        lender_address: poolData.lender,
      }),
    })

    if (!response.ok) {
      throw new Error('Failed to create lending pool')
    }

    const result = await response.json()

    // Return mock transaction hash for demo
    // In production, this would involve actual XRPL transaction
    return `pool_creation_${result.pool_id}`
  } catch (error) {
    console.error('Error creating lending pool:', error)
    throw error
  }
}

/**
 * Create direct loan payment transaction
 * Sends RLUSD from lender to borrower
 */
export async function createDirectLoan(loanData: LoanTransaction): Promise<string> {
  try {
    // Create RLUSD Payment transaction
    const payment: Payment = {
      TransactionType: 'Payment',
      Account: loanData.lender,
      Destination: loanData.borrower,
      Amount: {
        currency: RLUSD_CURRENCY,
        issuer: RLUSD_ISSUER,
        value: (parseFloat(loanData.amount) / 1_000_000).toString(), // Convert drops to RLUSD
      },
    }

    // Sign and submit transaction
    const txHash = await signTransaction(payment)

    return txHash
  } catch (error) {
    console.error('Error creating direct loan:', error)
    throw error
  }
}

/**
 * Create loan repayment transaction
 * Sends RLUSD from borrower back to lender
 */
export async function createRepayment(
  borrowerAddress: string,
  lenderAddress: string,
  amount: number
): Promise<string> {
  try {
    // Create RLUSD Payment transaction for repayment
    const payment: Payment = {
      TransactionType: 'Payment',
      Account: borrowerAddress,
      Destination: lenderAddress,
      Amount: {
        currency: RLUSD_CURRENCY,
        issuer: RLUSD_ISSUER,
        value: amount.toString(),
      },
    }

    // Sign and submit transaction
    const txHash = await signTransaction(payment)

    return txHash
  } catch (error) {
    console.error('Error creating repayment:', error)
    throw error
  }
}

/**
 * Setup RLUSD trust line
 * Required before receiving RLUSD tokens
 */
export async function setupRLUSDTrustline(walletAddress: string): Promise<string> {
  try {
    // Create TrustSet transaction
    const trustSet: TrustSet = {
      TransactionType: 'TrustSet',
      Account: walletAddress,
      LimitAmount: {
        currency: RLUSD_CURRENCY,
        issuer: RLUSD_ISSUER,
        value: '1000000000', // Max trust line limit
      },
    }

    // Sign and submit transaction
    const txHash = await signTransaction(trustSet)

    return txHash
  } catch (error) {
    console.error('Error setting up RLUSD trust line:', error)
    throw error
  }
}

/**
 * Apply for a loan from a pool
 * Calls backend API to create loan application
 */
export async function applyForLoan(
  poolId: string,
  amount: number,
  purpose: string,
  termDays: number,
  borrowerAddress: string
): Promise<{ loanId: string; message: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/loans/apply`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pool_id: poolId,
        amount,
        purpose,
        term_days: termDays,
        borrower_address: borrowerAddress,
        offered_rate: 5.2,
      }),
    })

    if (!response.ok) {
      throw new Error('Failed to apply for loan')
    }

    const result = await response.json()
    return result
  } catch (error) {
    console.error('Error applying for loan:', error)
    throw error
  }
}

/**
 * Approve a loan application
 * Calls backend API and creates payment transaction
 */
export async function approveLoan(
  loanId: string,
  lenderAddress: string
): Promise<string> {
  try {
    // Call backend API to approve loan
    const response = await fetch(`${API_BASE_URL}/loans/${loanId}/approve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        loan_id: loanId,
        approved: true,
        lender_address: lenderAddress,
      }),
    })

    if (!response.ok) {
      throw new Error('Failed to approve loan')
    }

    const result = await response.json()

    // Return mock transaction hash for demo
    return `loan_approval_${loanId}`
  } catch (error) {
    console.error('Error approving loan:', error)
    throw error
  }
}

/**
 * Get active pools from backend
 */
export async function getActivePools(): Promise<any[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/pools`)

    if (!response.ok) {
      throw new Error('Failed to fetch pools')
    }

    const result = await response.json()
    return result.pools
  } catch (error) {
    console.error('Error fetching pools:', error)
    throw error
  }
}

/**
 * Get loan applications for a pool
 */
export async function getLoanApplications(poolId?: string): Promise<any[]> {
  try {
    const url = poolId
      ? `${API_BASE_URL}/loans/applications?pool_id=${poolId}`
      : `${API_BASE_URL}/loans/applications`

    const response = await fetch(url)

    if (!response.ok) {
      throw new Error('Failed to fetch loan applications')
    }

    const result = await response.json()
    return result.applications
  } catch (error) {
    console.error('Error fetching loan applications:', error)
    throw error
  }
}

/**
 * Get active loans for a user
 */
export async function getActiveLoans(
  lenderAddress?: string,
  borrowerAddress?: string
): Promise<any[]> {
  try {
    const params = new URLSearchParams()
    if (lenderAddress) params.append('lender_address', lenderAddress)
    if (borrowerAddress) params.append('borrower_address', borrowerAddress)

    const url = `${API_BASE_URL}/loans/active${params.toString() ? `?${params.toString()}` : ''}`

    const response = await fetch(url)

    if (!response.ok) {
      throw new Error('Failed to fetch active loans')
    }

    const result = await response.json()
    return result.loans
  } catch (error) {
    console.error('Error fetching active loans:', error)
    throw error
  }
}
