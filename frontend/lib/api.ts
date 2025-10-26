/**
 * Backend API Client
 * Handles all communication with the FastAPI backend
 */

import type { Pool, LoanApplication, ActiveLoan } from './xrpl/types'

// API base URL from environment variables
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Generic API error class
 */
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public response?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

/**
 * Base API client class with common HTTP methods
 */
class APIClient {
  private baseURL: string

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${this.baseURL}${endpoint}`)

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value)
      })
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.detail || `API error: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    return response.json()
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.detail || `API error: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    return response.json()
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.detail || `API error: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    return response.json()
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.detail || `API error: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    return response.json()
  }
}

// Create API client instance
export const api = new APIClient(API_BASE_URL)

/**
 * Lending Pools API
 */
export const poolsAPI = {
  /**
   * Get all lending pools
   */
  list: async (): Promise<{ pools: Pool[] }> => {
    return api.get('/pools')
  },

  /**
   * Get a specific lending pool by ID
   */
  get: async (poolId: string): Promise<{ pool: Pool }> => {
    return api.get(`/pools/${poolId}`)
  },

  /**
   * Create a new lending pool
   */
  create: async (poolData: {
    name: string
    amount: number
    interest_rate: number
    max_term_days: number
    min_loan_amount: number
    lender_address: string
  }): Promise<{ pool_id: string; message: string }> => {
    return api.post('/pools', poolData)
  },
}

/**
 * Loans API
 */
export const loansAPI = {
  /**
   * Get loan applications, optionally filtered by pool
   */
  listApplications: async (poolId?: string): Promise<{ applications: LoanApplication[] }> => {
    const params = poolId ? { pool_id: poolId } : undefined
    return api.get('/loans/applications', params)
  },

  /**
   * Get active loans, optionally filtered by lender or borrower
   */
  listActive: async (
    lenderAddress?: string,
    borrowerAddress?: string
  ): Promise<{ loans: ActiveLoan[] }> => {
    const params: Record<string, string> = {}
    if (lenderAddress) params.lender_address = lenderAddress
    if (borrowerAddress) params.borrower_address = borrowerAddress

    return api.get('/loans/active', Object.keys(params).length > 0 ? params : undefined)
  },

  /**
   * Apply for a loan from a pool
   */
  apply: async (applicationData: {
    pool_id: string
    amount: number
    purpose: string
    term_days: number
    borrower_address: string
    offered_rate: number
  }): Promise<{ loan_id: string; message: string }> => {
    return api.post('/loans/apply', applicationData)
  },

  /**
   * Approve or reject a loan application
   */
  approve: async (
    loanId: string,
    approved: boolean,
    lenderAddress: string
  ): Promise<{ message: string; loan_id: string }> => {
    return api.post(`/loans/${loanId}/approve`, {
      loan_id: loanId,
      approved,
      lender_address: lenderAddress,
    })
  },
}

/**
 * Balance API
 */
export const balanceAPI = {
  /**
   * Get XRP or token balance for an address
   */
  get: async (
    address: string,
    tokenId?: string
  ): Promise<{ address: string; balance: number; token_id?: string }> => {
    return api.post('/balance', {
      address,
      token_id: tokenId,
    })
  },
}

/**
 * Health Check API
 */
export const healthAPI = {
  /**
   * Check API health
   */
  check: async (): Promise<{
    status: string
    version: string
    pools_count: number
    applications_count: number
    active_loans_count: number
  }> => {
    return api.get('/health')
  },
}

/**
 * Convenience function to check if API is available
 */
export async function checkAPIConnection(): Promise<boolean> {
  try {
    await healthAPI.check()
    return true
  } catch (error) {
    console.error('API connection failed:', error)
    return false
  }
}
