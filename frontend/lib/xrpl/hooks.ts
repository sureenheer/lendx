/**
 * XRPL React Hooks
 * Zustand store and React hooks for XRPL wallet state management
 */

'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { WalletState } from './types'
import { connectWallet as connectWalletFn, disconnectWallet as disconnectWalletFn, getWalletBalance, checkRLUSDTrustline, signTransaction as signTransactionFn } from './wallet'
import { setupRLUSDTrustline } from './transactions'
import { useEffect, useState } from 'react'

/**
 * Extended wallet store interface with actions
 */
interface WalletStore extends WalletState {
  isConnecting: boolean
  error: string | null
  did: string | null
  loading: boolean
  connect: () => Promise<void>
  disconnect: () => void
  signTransaction: (tx: any) => Promise<string>
  refreshBalance: () => Promise<void>
  setError: (error: string | null) => void
  connectWallet: () => Promise<void>
  generateDID: () => void
}

/**
 * Zustand store for XRPL wallet state
 * Persists wallet address in localStorage
 */
export const useWallet = create<WalletStore>()(
  persist(
    (set, get) => ({
      // State
      connected: false,
      address: null,
      publicKey: null,
      balance: {
        xrp: null,
        rlusd: null,
      },
      isConnecting: false,
      error: null,
      did: null,
      loading: false,

      // Actions
      connect: async () => {
        set({ isConnecting: true, error: null })

        try {
          const walletState = await connectWalletFn()
          set({
            ...walletState,
            isConnecting: false,
            error: null,
          })
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to connect wallet'
          set({
            isConnecting: false,
            error: errorMessage,
            connected: false,
          })
          throw error
        }
      },

      disconnect: () => {
        disconnectWalletFn()
        set({
          connected: false,
          address: null,
          publicKey: null,
          balance: {
            xrp: null,
            rlusd: null,
          },
          error: null,
        })
      },

      signTransaction: async (tx: any) => {
        const { address } = get()
        if (!address) {
          throw new Error('Wallet not connected')
        }

        try {
          set({ error: null })
          const txHash = await signTransactionFn(tx)
          return txHash
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to sign transaction'
          set({ error: errorMessage })
          throw error
        }
      },

      refreshBalance: async () => {
        const { address } = get()
        if (!address) {
          return
        }

        try {
          const balance = await getWalletBalance(address)
          set({
            balance: {
              xrp: balance.xrp,
              rlusd: balance.rlusd,
            },
          })
        } catch (error) {
          console.error('Failed to refresh balance:', error)
        }
      },

      setError: (error: string | null) => {
        set({ error })
      },

      // Aliases for signup page compatibility
      connectWallet: async () => {
        await get().connect()
      },

      generateDID: () => {
        const { address } = get()
        if (address) {
          set({ did: `did:xrpl:${address}` })
        }
      },
    }),
    {
      name: 'lendx-wallet',
      partialize: (state) => ({
        address: state.address,
        connected: state.connected,
      }),
    }
  )
)

/**
 * Hook to check if user has RLUSD trust line
 * Returns trust line status and setup function
 */
export function useRLUSDTrustline(address: string | null) {
  const [hasTrustline, setHasTrustline] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isSettingUp, setIsSettingUp] = useState(false)

  useEffect(() => {
    if (!address) {
      setHasTrustline(false)
      return
    }

    let mounted = true

    const checkTrustline = async () => {
      setIsLoading(true)
      try {
        const status = await checkRLUSDTrustline(address)
        if (mounted) {
          setHasTrustline(status.hasTrustline)
        }
      } catch (error) {
        console.error('Failed to check trust line:', error)
        if (mounted) {
          setHasTrustline(false)
        }
      } finally {
        if (mounted) {
          setIsLoading(false)
        }
      }
    }

    checkTrustline()

    return () => {
      mounted = false
    }
  }, [address])

  const setup = async () => {
    if (!address) {
      throw new Error('Wallet not connected')
    }

    setIsSettingUp(true)
    try {
      await setupRLUSDTrustline(address)
      setHasTrustline(true)
    } catch (error) {
      console.error('Failed to setup trust line:', error)
      throw error
    } finally {
      setIsSettingUp(false)
    }
  }

  return {
    hasTrustline,
    isLoading,
    isSettingUp,
    setup,
  }
}

/**
 * Hook to periodically refresh wallet balance
 */
export function useWalletBalanceRefresh(intervalMs: number = 30000) {
  const { address, refreshBalance } = useWallet()

  useEffect(() => {
    if (!address) {
      return
    }

    // Refresh immediately
    refreshBalance()

    // Setup interval for periodic refresh
    const interval = setInterval(() => {
      refreshBalance()
    }, intervalMs)

    return () => {
      clearInterval(interval)
    }
  }, [address, intervalMs, refreshBalance])
}

/**
 * Hook to check if wallet is ready for transactions
 */
export function useWalletReady() {
  const { connected, address, balance } = useWallet()
  const { hasTrustline, isLoading } = useRLUSDTrustline(address)

  const isReady = connected && !!address && hasTrustline && !isLoading
  const needsTrustline = connected && !!address && !hasTrustline && !isLoading

  return {
    isReady,
    needsTrustline,
    hasBalance: balance.rlusd !== null && parseFloat(balance.rlusd || '0') > 0,
  }
}
