"use client"
import React, { createContext, useContext, useState } from 'react'

interface V0ContextType {
  isV0: boolean
  setIsV0: (isV0: boolean) => void
}

const V0Context = createContext<V0ContextType | undefined>(undefined)

export function V0Provider({ children, isV0: initialIsV0 = false }: { children: React.ReactNode; isV0?: boolean }) {
  const [isV0, setIsV0] = useState(initialIsV0)

  return <V0Context.Provider value={{ isV0, setIsV0 }}>{children}</V0Context.Provider>
}

export function useV0Context() {
  const context = useContext(V0Context)
  if (!context) {
    throw new Error('useV0Context must be used within V0Provider')
  }
  return context
}

export function useIsV0() {
  const { isV0 } = useV0Context()
  return isV0
}
