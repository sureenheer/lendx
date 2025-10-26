"use client"

/**
 * Demo Context Provider
 * Manages demo flow state for lender and borrower views
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'

// Type definitions for demo steps
type LenderStep = 'empty' | 'pool-created' | 'funded' | 'loan-request' | 'loan-approved'
type BorrowerStep = 'empty' | 'browsing' | 'pending' | 'approved' | 'payment-made'
type ViewMode = 'lender' | 'borrower'

// Pool type
interface Pool {
  id: string
  name: string
  liquidity: number
  interestRate: number
  maxTerm: number
  minLoan: number
  maxLoan: number
  lender: string
}

// Notification type
interface Notification {
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  timestamp?: number
}

// Context interface
interface DemoContextType {
  // Lender state
  lenderStep: LenderStep
  setLenderStep: (step: LenderStep) => void

  // Borrower state
  borrowerStep: BorrowerStep
  setBorrowerStep: (step: BorrowerStep) => void

  // View mode
  viewMode: ViewMode
  setViewMode: (mode: ViewMode) => void

  // Current dashboard view
  currentDashboard: string
  setCurrentDashboard: (dashboard: string) => void

  // Pools
  pools: Pool[]
  addPool: (pool: Pool) => void
  selectedPool: Pool | null
  setSelectedPool: (pool: Pool | null) => void

  // Notification handler
  onNotificationAdd: (notification: Notification) => void

  // Notifications list
  notifications: Notification[]
  clearNotifications: () => void

  // Handle next action in demo flow
  handleNextAction?: () => void
}

const DemoContext = createContext<DemoContextType | undefined>(undefined)

/**
 * DemoProvider component
 * Wraps the application to provide demo state management
 */
export function DemoProvider({ children }: { children: React.ReactNode }) {
  // State
  const [lenderStep, setLenderStep] = useState<LenderStep>('empty')
  const [borrowerStep, setBorrowerStep] = useState<BorrowerStep>('empty')
  const [viewMode, setViewMode] = useState<ViewMode>('lender')
  const [currentDashboard, setCurrentDashboard] = useState('overview')
  const [notifications, setNotifications] = useState<Notification[]>([])
  
  // Initial demo pools
  const [pools, setPools] = useState<Pool[]>([
    {
      id: 'pool-1',
      name: 'Community Growth Pool',
      liquidity: 5000,
      interestRate: 4.5,
      maxTerm: 180,
      minLoan: 50,
      maxLoan: 1000,
      lender: 'Community'
    },
    {
      id: 'pool-2',
      name: 'Small Business Fund',
      liquidity: 3000,
      interestRate: 5.2,
      maxTerm: 120,
      minLoan: 100,
      maxLoan: 500,
      lender: 'Sarah Chen'
    },
    {
      id: 'pool-3',
      name: 'Quick Loans Pool',
      liquidity: 2000,
      interestRate: 6.8,
      maxTerm: 60,
      minLoan: 25,
      maxLoan: 300,
      lender: 'QuickFund'
    }
  ])
  
  const [selectedPool, setSelectedPool] = useState<Pool | null>(null)

  // Add notification handler
  const onNotificationAdd = useCallback((notification: Notification) => {
    const newNotification = {
      ...notification,
      timestamp: Date.now(),
    }

    setNotifications((prev) => [...prev, newNotification])

    // Log notification for debugging
    console.log('[LendX Notification]:', newNotification)

    // Auto-remove notification after 5 seconds
    setTimeout(() => {
      setNotifications((prev) =>
        prev.filter((n) => n.timestamp !== newNotification.timestamp)
      )
    }, 5000)
  }, [])

  // Clear all notifications
  const clearNotifications = useCallback(() => {
    setNotifications([])
  }, [])

  // Add pool with notification
  const addPool = useCallback((pool: Pool) => {
    setPools((prev) => [...prev, pool])
    
    // Notify about new pool creation
    onNotificationAdd({
      message: `New lending pool "${pool.name}" created with $${pool.liquidity} at ${pool.interestRate}% APR`,
      type: "success",
    })
  }, [onNotificationAdd])

  // Auto-sync flows: when borrower applies, notify lender
  useEffect(() => {
    if (borrowerStep === 'pending' && lenderStep === 'pool-created') {
      // Borrower just applied, show loan request to lender
      setLenderStep('loan-request')
      
      // Notify about new loan request
      onNotificationAdd({
        message: "New loan request received from borrower!",
        type: "info",
      })
    }
  }, [borrowerStep, lenderStep, onNotificationAdd])

  // Auto-sync flows: when lender approves, notify borrower
  useEffect(() => {
    if (lenderStep === 'loan-approved' && borrowerStep === 'pending') {
      // Lender just approved, update borrower
      setBorrowerStep('approved')
      
      // Notify borrower about approval
      onNotificationAdd({
        message: "Your loan has been approved by the lender!",
        type: "success",
      })
    }
  }, [lenderStep, borrowerStep, onNotificationAdd])

  // Handle next action in demo flow
  const handleNextAction = useCallback(() => {
    if (viewMode === 'lender') {
      if (lenderStep === 'pool-created') {
        setLenderStep('loan-request')
      }
    } else if (viewMode === 'borrower') {
      if (borrowerStep === 'pending') {
        setBorrowerStep('approved')
      }
    }
  }, [viewMode, lenderStep, borrowerStep])

  const value: DemoContextType = {
    lenderStep,
    setLenderStep,
    borrowerStep,
    setBorrowerStep,
    viewMode,
    setViewMode,
    currentDashboard,
    setCurrentDashboard,
    pools,
    addPool,
    selectedPool,
    setSelectedPool,
    onNotificationAdd,
    notifications,
    clearNotifications,
    handleNextAction,
  }

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>
}

/**
 * Hook to access demo context
 * Must be used within DemoProvider
 */
export function useDemoContext() {
  const context = useContext(DemoContext)
  if (!context) {
    throw new Error('useDemoContext must be used within DemoProvider')
  }
  return context
}
