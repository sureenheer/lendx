/**
 * XRPL Integration Types
 * TypeScript interfaces for LendX lending operations
 */

/**
 * Lending pool data structure
 */
export interface Pool {
  id: string
  name: string
  amount: number
  available: number
  interest_rate: number
  max_term_days: number
  min_loan_amount: number
  lender_address: string
  status: 'active' | 'closed' | 'paused'
  created_at: number
}

/**
 * Loan application data structure
 */
export interface LoanApplication {
  id: string
  pool_id: string
  amount: number
  purpose: string
  term_days: number
  borrower_address: string
  offered_rate: number
  status: 'pending' | 'approved' | 'rejected'
  applied_at: number
}

/**
 * Active loan data structure
 */
export interface ActiveLoan {
  id: string
  pool_id: string
  amount: number
  purpose: string
  term_days: number
  borrower_address: string
  lender_address: string
  offered_rate: number
  status: 'active' | 'paid' | 'defaulted'
  applied_at: number
  approved_at: number
}

/**
 * Transaction data for creating a lending pool
 */
export interface LendingPoolTransaction {
  poolId: string
  amount: string
  lender: string
}

/**
 * Transaction data for creating a direct loan
 */
export interface LoanTransaction {
  amount: string
  borrower: string
  lender: string
  interestRate: number
  termDays: number
}

/**
 * Wallet connection state
 */
export interface WalletState {
  connected: boolean
  address: string | null
  publicKey: string | null
  balance: {
    xrp: string | null
    rlusd: string | null
  }
}

/**
 * XUMM payload response
 */
export interface XummPayloadResponse {
  uuid: string
  next: {
    always: string
    no_push_msg_received?: string
  }
  refs: {
    qr_png: string
    qr_matrix: string
    qr_uri_quality_opts: string[]
    websocket_status: string
  }
  pushed: boolean
}

/**
 * XUMM sign result
 */
export interface XummSignResult {
  signed: boolean
  txid?: string
  account?: string
  error?: string
}

/**
 * Trust line status
 */
export interface TrustlineStatus {
  hasTrustline: boolean
  balance?: string
  limit?: string
  currency?: string
  issuer?: string
}
