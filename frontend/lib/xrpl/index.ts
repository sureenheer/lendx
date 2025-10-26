/**
 * XRPL Integration Layer
 * Main export file for all XRPL functionality
 */

// Export all types
export type * from './types'

// Export wallet functions
export {
  connectWallet,
  disconnectWallet,
  signTransaction,
  getWalletBalance,
  checkRLUSDTrustline,
} from './wallet'

// Export transaction functions
export {
  createLendingPool,
  createDirectLoan,
  createRepayment,
  setupRLUSDTrustline,
  applyForLoan,
  approveLoan,
  getActivePools,
  getLoanApplications,
  getActiveLoans,
} from './transactions'

// Export hooks
export {
  useWallet,
  useRLUSDTrustline,
  useWalletBalanceRefresh,
  useWalletReady,
} from './hooks'

// Export credentials manager
export { CredentialManager } from './credentials'

// Re-export commonly used XRPL types and utilities
export { xrpToDrops, dropsToXrp } from 'xrpl'
export type { Payment, TrustSet, Client } from 'xrpl'
