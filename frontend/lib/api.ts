"use client";

import { getAccessToken } from '@auth0/nextjs-auth0';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface DIDCreationResponse {
  did: string;
  didDocument: any;
  xrplAddress: string;
  verifiableCredential: any;
}

export interface UserProfile {
  id: string;
  auth0Id: string;
  email: string;
  name?: string;
  picture?: string;
  did?: string;
  xrplAddress?: string;
  createdAt: string;
  updatedAt: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async getHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    try {
      // Get access token from Auth0
      const { accessToken } = await getAccessToken();
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`;
      }
    } catch (error) {
      console.warn('Failed to get access token:', error);
    }

    return headers;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const headers = await this.getHeaders();

      const response = await fetch(url, {
        headers,
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  // Auth endpoints
  async getProfile(): Promise<ApiResponse<{ user: UserProfile; needsDIDCreation: boolean }>> {
    return this.request('/api/auth/me');
  }

  async register(): Promise<ApiResponse<DIDCreationResponse>> {
    return this.request('/api/auth/register', {
      method: 'POST',
    });
  }

  async createDID(): Promise<ApiResponse<DIDCreationResponse>> {
    return this.request('/api/auth/create-did', {
      method: 'POST',
    });
  }

  async getAuthStatus(): Promise<ApiResponse<{
    authenticated: boolean;
    user: any;
    hasStoredProfile: boolean;
    hasDID: boolean;
    needsDIDCreation: boolean;
    xrplAddress?: string;
  }>> {
    return this.request('/api/auth/status');
  }

  // DID endpoints
  async getDIDDocument(did?: string): Promise<ApiResponse<any>> {
    const endpoint = did ? `/api/did/document/${did}` : '/api/did/document';
    return this.request(endpoint);
  }

  async issueCredential(credentialType: string, credentialData: any): Promise<ApiResponse<any>> {
    return this.request('/api/did/credentials/issue', {
      method: 'POST',
      body: JSON.stringify({
        credentialType,
        credentialData,
      }),
    });
  }

  async verifyCredential(credential: any): Promise<ApiResponse<{ valid: boolean; credential: any }>> {
    return this.request('/api/did/credentials/verify', {
      method: 'POST',
      body: JSON.stringify({ credential }),
    });
  }

  async getCredentials(): Promise<ApiResponse<any[]>> {
    return this.request('/api/did/credentials');
  }

  async issueBusinessCredential(businessData: {
    businessName: string;
    businessType: string;
    registrationNumber?: string;
    documents?: any[];
  }): Promise<ApiResponse<any>> {
    return this.request('/api/did/credentials/business', {
      method: 'POST',
      body: JSON.stringify(businessData),
    });
  }

  async issueIncomeCredential(incomeData: {
    monthlyIncome: number;
    currency: string;
    source: string;
    documents?: any[];
  }): Promise<ApiResponse<any>> {
    return this.request('/api/did/credentials/income', {
      method: 'POST',
      body: JSON.stringify(incomeData),
    });
  }

  async deactivateDID(): Promise<ApiResponse<void>> {
    return this.request('/api/did/deactivate', {
      method: 'DELETE',
    });
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{
    status: string;
    timestamp: string;
    services: {
      auth0: boolean;
      xrpl: boolean;
      overall: boolean;
    };
    version: string;
  }>> {
    return this.request('/health');
  }
}

export const apiClient = new ApiClient();
export default apiClient;