/**
 * Utility Functions
 * Common utilities for styling, formatting, and helpers
 */

import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Combines class names with Tailwind CSS class merging
 * Used by shadcn/ui components
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format currency amounts with proper symbols and decimals
 */
export function formatCurrency(
  amount: number,
  currency: 'XRP' | 'RLUSD' | 'USD' = 'USD',
  decimals: number = 2
): string {
  const currencySymbol = currency === 'XRP' ? 'XRP' : '$'

  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(amount)

  return currency === 'XRP' ? `${formatted} XRP` : `${currencySymbol}${formatted}`
}

/**
 * Format XRPL address to shortened version
 * Example: rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx -> rN7n7o...FBBEx
 */
export function formatAddress(address: string, startChars: number = 6, endChars: number = 4): string {
  if (!address || address.length < startChars + endChars) {
    return address
  }

  return `${address.slice(0, startChars)}...${address.slice(-endChars)}`
}

/**
 * Format transaction hash to shortened version
 */
export function formatTxHash(hash: string): string {
  return formatAddress(hash, 8, 6)
}

/**
 * Format date to readable string
 */
export function formatDate(timestamp: number | Date, format: 'short' | 'long' = 'short'): string {
  const date = typeof timestamp === 'number' ? new Date(timestamp) : timestamp

  if (format === 'long') {
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

/**
 * Format interest rate percentage
 */
export function formatInterestRate(rate: number, decimals: number = 2): string {
  return `${rate.toFixed(decimals)}%`
}

/**
 * Calculate loan repayment amount with interest
 */
export function calculateRepaymentAmount(
  principal: number,
  interestRate: number,
  termDays: number
): number {
  // Simple interest calculation: P * (1 + r * t)
  // where r is annual rate, t is time in years
  const years = termDays / 365
  const totalAmount = principal * (1 + (interestRate / 100) * years)

  return Math.round(totalAmount * 100) / 100
}

/**
 * Calculate interest amount only
 */
export function calculateInterest(
  principal: number,
  interestRate: number,
  termDays: number
): number {
  const totalAmount = calculateRepaymentAmount(principal, interestRate, termDays)
  return totalAmount - principal
}

/**
 * Validate XRPL address format
 */
export function isValidXRPLAddress(address: string): boolean {
  // XRPL classic addresses start with 'r' and are 25-35 characters
  const classicAddressRegex = /^r[1-9A-HJ-NP-Za-km-z]{24,34}$/
  return classicAddressRegex.test(address)
}

/**
 * Sleep utility for delays
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text
  }

  return text.slice(0, maxLength - 3) + '...'
}

/**
 * Convert XRP drops to XRP
 */
export function dropsToXRP(drops: string | number): string {
  const dropsNum = typeof drops === 'string' ? parseFloat(drops) : drops
  return (dropsNum / 1_000_000).toFixed(6)
}

/**
 * Convert XRP to drops
 */
export function xrpToDrops(xrp: string | number): string {
  const xrpNum = typeof xrp === 'string' ? parseFloat(xrp) : xrp
  return Math.floor(xrpNum * 1_000_000).toString()
}
