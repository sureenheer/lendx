/**
 * XRPL Wallet Integration
 * Handles wallet connection using Xumm SDK and native XRPL library
 */

import { XummSdk } from 'xumm-sdk'
import { Client, Wallet as XRPLWallet, dropsToXrp } from 'xrpl'
import type { WalletState, XummPayloadResponse, XummSignResult, TrustlineStatus } from './types'

// Lazy initialization of Xumm SDK to avoid build errors with missing credentials
let xumm: XummSdk | null = null

function getXummSdk(): XummSdk {
  if (!xumm) {
    const apiKey = process.env.NEXT_PUBLIC_XUMM_API_KEY
    const apiSecret = process.env.NEXT_PUBLIC_XUMM_API_SECRET

    if (!apiKey || !apiSecret) {
      throw new Error('Xumm API credentials not configured. Please add NEXT_PUBLIC_XUMM_API_KEY and NEXT_PUBLIC_XUMM_API_SECRET to .env.local')
    }

    xumm = new XummSdk(apiKey, apiSecret)
  }
  return xumm
}

// RLUSD issuer address (replace with actual issuer)
const RLUSD_ISSUER = process.env.NEXT_PUBLIC_RLUSD_ISSUER || 'rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx'
const RLUSD_CURRENCY = 'RLUSD'

/**
 * Connect wallet using Xumm mobile app via backend proxy
 * Creates a sign-in payload and waits for user approval
 */
export async function connectWallet(): Promise<WalletState> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    // Create sign-in payload via backend
    const createResponse = await fetch(`${apiUrl}/api/xumm/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!createResponse.ok) {
      throw new Error('Failed to create Xumm payload')
    }

    const { payload } = await createResponse.json()

    // Open QR code in new window or show to user
    console.log('Xumm Sign-In QR:', payload.qr_url)
    console.log('Xumm Sign-In URL:', payload.deeplink)

    // Open the sign-in URL (will redirect to Xumm app if on mobile)
    if (typeof window !== 'undefined') {
      window.open(payload.deeplink, '_blank')
    }

    // Poll for payload status
    const maxAttempts = 60 // 60 seconds timeout
    let attempts = 0
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000)) // Wait 1 second
      
      const statusResponse = await fetch(`${apiUrl}/api/xumm/payload/${payload.uuid}`)
      if (!statusResponse.ok) {
        throw new Error('Failed to check payload status')
      }
      
      const { status } = await statusResponse.json()
      
      if (status.signed && status.account) {
        // Get wallet balance
        const balance = await getWalletBalance(status.account)
        
        return {
          connected: true,
          address: status.account,
          publicKey: null,
          balance: {
            xrp: balance.xrp,
            rlusd: balance.rlusd
          }
        }
      }
      
      if (status.cancelled || status.expired) {
        throw new Error('Sign-in cancelled or expired')
      }
      
      attempts++
    }
    
    throw new Error('Sign-in timeout')
  } catch (error) {
    console.error('Failed to connect wallet:', error)
    throw error
  }
}

/**
 * Disconnect wallet and clear state
 */
export function disconnectWallet(): void {
  // Clear any stored wallet state
  if (typeof window !== 'undefined') {
    localStorage.removeItem('lendx_wallet_address')
    localStorage.removeItem('lendx_wallet_connected')
  }
}

/**
 * Sign transaction using Xumm via backend proxy
 * Creates a payload with the transaction and waits for user signature
 */
export async function signTransaction(txJson: any): Promise<string> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    // Create transaction payload via backend
    const createResponse = await fetch(`${apiUrl}/api/xumm/transaction`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tx_json: txJson })
    })

    if (!createResponse.ok) {
      throw new Error('Failed to create Xumm payload')
    }

    const { payload } = await createResponse.json()

    // Show QR code or deep link to user
    console.log('Xumm Transaction QR:', payload.qr_url)
    console.log('Xumm Transaction URL:', payload.deeplink)

    // Open the signing URL
    if (typeof window !== 'undefined') {
      window.open(payload.deeplink, '_blank')
    }

    // Poll for payload status
    const maxAttempts = 60 // 60 seconds timeout
    let attempts = 0
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000)) // Wait 1 second
      
      const statusResponse = await fetch(`${apiUrl}/api/xumm/payload/${payload.uuid}`)
      if (!statusResponse.ok) {
        throw new Error('Failed to check payload status')
      }
      
      const { status } = await statusResponse.json()
      
      if (status.signed && status.txid) {
        return status.txid
      }
      
      if (status.cancelled || status.expired) {
        throw new Error('Transaction cancelled or expired')
      }
      
      attempts++
    }
    
    throw new Error('Transaction timeout')
  } catch (error) {
    console.error('Failed to sign transaction:', error)
    throw error
  }
}

/**
 * Get wallet balance (XRP + RLUSD)
 * Queries XRPL for XRP balance and trust lines for RLUSD
 */
export async function getWalletBalance(address: string): Promise<{
  xrp: string
  rlusd: string
}> {
  try {
    // Connect to XRPL testnet
    const client = new Client('wss://s.altnet.rippletest.net:51233')
    await client.connect()

    try {
      // Get account info for XRP balance
      const accountInfo = await client.request({
        command: 'account_info',
        account: address,
        ledger_index: 'validated'
      })

      const xrpBalance = dropsToXrp(accountInfo.result.account_data.Balance.toString())

      // Get trust lines for RLUSD balance
      let rlusdBalance = '0'
      try {
        const trustlines = await client.request({
          command: 'account_lines',
          account: address,
          ledger_index: 'validated'
        })

        const rlusdLine = trustlines.result.lines.find(
          (line: any) => line.currency === RLUSD_CURRENCY && line.account === RLUSD_ISSUER
        )

        if (rlusdLine) {
          rlusdBalance = rlusdLine.balance
        }
      } catch (e) {
        // No trust lines yet
        console.log('No RLUSD trust line found')
      }

      return {
        xrp: String(xrpBalance),
        rlusd: rlusdBalance
      }
    } finally {
      await client.disconnect()
    }
  } catch (error) {
    console.error('Failed to get wallet balance:', error)
    return {
      xrp: '0',
      rlusd: '0'
    }
  }
}

/**
 * Check if wallet has RLUSD trust line
 */
export async function checkRLUSDTrustline(address: string): Promise<TrustlineStatus> {
  try {
    const client = new Client('wss://s.altnet.rippletest.net:51233')
    await client.connect()

    try {
      const trustlines = await client.request({
        command: 'account_lines',
        account: address,
        ledger_index: 'validated'
      })

      const rlusdLine = trustlines.result.lines.find(
        (line: any) => line.currency === RLUSD_CURRENCY && line.account === RLUSD_ISSUER
      ) as any

      if (rlusdLine) {
        return {
          hasTrustline: true,
          balance: rlusdLine.balance,
          limit: rlusdLine.limit,
          currency: RLUSD_CURRENCY,
          issuer: RLUSD_ISSUER
        }
      }

      return {
        hasTrustline: false
      }
    } finally {
      await client.disconnect()
    }
  } catch (error) {
    console.error('Failed to check trust line:', error)
    return {
      hasTrustline: false
    }
  }
}
