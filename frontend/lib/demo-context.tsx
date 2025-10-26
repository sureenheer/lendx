"use client"

/**
 * Demo Context Provider
 * Manages demo flow state for lender and borrower views
 */

import React, { createContext, useContext, useState, useCallback } from 'react'

// Type definitions for demo steps
type LenderStep = 'empty' | 'pool-created' | 'funded' | 'loan-request' | 'loan-approved'
type BorrowerStep = 'empty' | 'pending' | 'approved' | 'payment-made'
type ViewMode = 'lender' | 'borrower'

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
