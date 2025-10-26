# LendX Authentication Architecture

**Version**: 1.0
**Last Updated**: 2025-10-26
**Status**: Design Complete, Implementation Pending

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication Flow](#authentication-flow)
3. [Component Architecture](#component-architecture)
4. [API Specification](#api-specification)
5. [Frontend Integration](#frontend-integration)
6. [Security Model](#security-model)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Guide](#deployment-guide)

---

## Overview

LendX implements **wallet-based authentication** using cryptographic signatures instead of traditional passwords. Users authenticate by proving ownership of their XRPL wallet through digital signatures created with their private keys.

### Key Principles

1. **User Sovereignty**: Users control their private keys (never stored in backend)
2. **Passwordless**: No passwords to remember, leak, or crack
3. **Standards-Based**: JWT tokens for session management, XRPL signing for authentication
4. **Defense in Depth**: Multiple security layers (signatures, JWT, RLS, rate limiting)
5. **Good UX**: Sign once, stay logged in (sliding sessions)

### Architecture Decisions

This design is based on four Architecture Decision Records (ADRs):

- **ADR-001**: Authentication Method Selection → JWT with wallet signatures
- **ADR-002**: RLS vs Application-Level Authorization → Layered approach
- **ADR-003**: Wallet Key Management → Users control keys, backend uses Vault/KMS
- **ADR-004**: Session Management → 24-hour sliding sessions with token refresh

---

## Authentication Flow

### 1. Wallet Connection Flow

```
┌─────────────┐                                                    ┌─────────────┐
│   Browser   │                                                    │  Xumm App   │
│  (Frontend) │                                                    │  (Mobile)   │
└──────┬──────┘                                                    └──────┬──────┘
       │                                                                  │
       │ 1. User clicks "Connect Wallet"                                 │
       ├─────────────────────────────────────────────────────────────────┤
       │                                                                  │
       │ 2. Frontend requests challenge from backend                     │
       │ GET /auth/wallet/challenge?address=rN7n7...                     │
       ▼                                                                  │
┌──────────────────────────────────────────────────────────────────────┐ │
│                         Backend (FastAPI)                             │ │
│  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │ 3. Generate challenge message:                                  │ │ │
│  │    - Timestamp: 1729900800                                      │ │ │
│  │    - Nonce: a1b2c3d4e5f6...                                     │ │ │
│  │    - Message: "LendX Authentication\nTimestamp: ...\n..."       │ │ │
│  │                                                                  │ │ │
│  │ 4. Store challenge temporarily (Redis, 5min TTL)                │ │ │
│  │    Key: "challenge:rN7n7..."                                    │ │ │
│  │    Value: { nonce, timestamp, message }                         │ │ │
│  └─────────────────────────────────────────────────────────────────┘ │ │
└──────┬───────────────────────────────────────────────────────────────┘ │
       │                                                                  │
       │ 5. Return challenge message                                     │
       │ { message: "LendX Authentication...", nonce: "..." }            │
       ▼                                                                  │
┌──────────────┐                                                         │
│   Browser    │                                                         │
│              │ 6. Frontend calls Xumm SDK to sign message              │
│              ├─────────────────────────────────────────────────────────┤
│              │                                                          │
│              │ 7. Xumm SDK creates SignIn payload                      │
│              │    (includes challenge message)                         ▼
│              │                                                    ┌──────────┐
│              │                                                    │ Xumm App │
│              │                                                    │          │
│              │ 8. User opens Xumm app (QR or deep link)          │ Reviews  │
│              │                                                    │ message  │
│              │                                                    │          │
│              │ 9. User approves signature in Xumm                │ Signs    │
│              │                                                    │ with     │
│              │                                                    │ private  │
│              │                                                    │ key      │
│              │                                                    └────┬─────┘
│              │ 10. Xumm returns signature                             │
│              │ { signature: "0x...", account: "rN7n7..." }            │
│              │◄────────────────────────────────────────────────────────┤
└──────┬───────┘                                                         │
       │                                                                  │
       │ 11. Frontend sends signature to backend                         │
       │ POST /auth/wallet/login                                         │
       │ { address: "rN7n7...", signature: "0x...", nonce: "..." }       │
       ▼                                                                  │
┌──────────────────────────────────────────────────────────────────────┐ │
│                         Backend (FastAPI)                             │ │
│  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │ 12. Verify signature:                                           │ │ │
│  │     - Retrieve challenge from Redis                             │ │ │
│  │     - Verify signature matches wallet address                   │ │ │
│  │     - Check timestamp (< 5 minutes old)                         │ │ │
│  │     - Verify nonce matches                                      │ │ │
│  │                                                                  │ │ │
│  │ 13. If valid:                                                   │ │ │
│  │     - Check if user exists in DB                                │ │ │
│  │     - Create user if first-time (INSERT INTO users)             │ │ │
│  │     - Generate JWT token:                                       │ │ │
│  │       * sub: wallet_address                                     │ │ │
│  │       * jti: UUID (for revocation)                              │ │ │
│  │       * exp: now + 24 hours                                     │ │ │
│  │       * wallet_address, did, network                            │ │ │
│  │                                                                  │ │ │
│  │ 14. Delete challenge from Redis (one-time use)                  │ │ │
│  └─────────────────────────────────────────────────────────────────┘ │ │
└──────┬───────────────────────────────────────────────────────────────┘ │
       │                                                                  │
       │ 15. Return JWT + user data                                      │
       │ { token: "eyJhbG...", user: { address, did }, expiresAt }       │
       ▼                                                                  │
┌──────────────┐                                                         │
│   Browser    │                                                         │
│              │ 16. Store JWT in localStorage                           │
│              │     key: "lendx_auth_token"                             │
│              │     value: "eyJhbG..."                                  │
│              │                                                          │
│              │ 17. Redirect to dashboard                               │
└──────────────┘                                                         │
```

### 2. Authenticated Request Flow

```
┌──────────────┐
│   Browser    │
│              │ 1. User performs action (e.g., create pool)
│              │ POST /pools { amount: 1000, rate: 5.5% }
│              │ Authorization: Bearer eyJhbG...
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                             │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ 2. JWT Verification Middleware:                                 │ │
│  │    a. Extract token from Authorization header                   │ │
│  │    b. Verify JWT signature (using secret key)                   │ │
│  │    c. Check expiration (exp claim)                              │ │
│  │    d. Check if token blocklisted (Redis check)                  │ │
│  │    e. Extract wallet_address from sub claim                     │ │
│  │                                                                  │ │
│  │ 3. If verification fails → 401 Unauthorized                     │ │
│  │                                                                  │ │
│  │ 4. If token < 1h from expiry:                                   │ │
│  │    - Generate new JWT with fresh 24h expiration                 │ │
│  │    - Add to response header: X-New-Token                        │ │
│  │                                                                  │ │
│  │ 5. Attach wallet_address to request context                     │ │
│  │    request.state.user = wallet_address                          │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ 6. Endpoint Handler:                                            │ │
│  │    @app.post("/pools")                                          │ │
│  │    async def create_pool(                                       │ │
│  │        data: PoolCreate,                                        │ │
│  │        current_user: str = Depends(get_current_user)            │ │
│  │    ):                                                            │ │
│  │        # current_user = "rN7n7..."                              │ │
│  │        # Application-level authorization check                  │ │
│  │        # RLS automatically filters DB queries                   │ │
│  │        pool = Pool(issuer_address=current_user, ...)            │ │
│  │        db.add(pool)                                             │ │
│  │        db.commit()                                              │ │
│  │        return pool.to_dict()                                    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────┬───────────────────────────────────────────────────────────────┘
       │
       │ 7. Response with data + optional X-New-Token header
       ▼
┌──────────────┐
│   Browser    │
│              │ 8. If X-New-Token header present:
│              │    - Update localStorage with new token
│              │
│              │ 9. Display result to user
└──────────────┘
```

### 3. Logout Flow

```
┌──────────────┐
│   Browser    │
│              │ 1. User clicks "Logout"
│              │ POST /auth/logout
│              │ Authorization: Bearer eyJhbG...
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                             │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ 2. Verify JWT (same as authenticated request)                   │ │
│  │                                                                  │ │
│  │ 3. Extract jti (JWT ID) from token                              │ │
│  │    jti = "550e8400-e29b-41d4-a716-446655440000"                 │ │
│  │                                                                  │ │
│  │ 4. Add to blocklist in Redis:                                   │ │
│  │    Key: "blocklist:550e8400-..."                                │ │
│  │    TTL: exp - now (remaining time until expiration)             │ │
│  │    redis.setex(f"blocklist:{jti}", ttl, "1")                    │ │
│  │                                                                  │ │
│  │ 5. (Optional) Log logout event                                  │ │
│  │    logger.info(f"User {wallet_address} logged out")             │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────┬───────────────────────────────────────────────────────────────┘
       │
       │ 6. Return 200 OK
       ▼
┌──────────────┐
│   Browser    │
│              │ 7. Clear localStorage
│              │    localStorage.removeItem("lendx_auth_token")
│              │
│              │ 8. Redirect to home/login page
└──────────────┘
```

---

## Component Architecture

### Backend Components

```
backend/
├── auth/                           # Authentication module
│   ├── __init__.py
│   ├── challenge.py                # Challenge generation/verification
│   │   ├── generate_challenge()   # Create challenge message with nonce
│   │   ├── store_challenge()      # Save to Redis (5min TTL)
│   │   ├── verify_challenge()     # Validate signature against challenge
│   │   └── cleanup_expired()      # Remove old challenges (cron)
│   │
│   ├── jwt.py                      # JWT token management
│   │   ├── generate_jwt()         # Create JWT with wallet address
│   │   ├── verify_jwt()           # Validate JWT signature + expiration
│   │   ├── refresh_jwt()          # Issue new token (sliding session)
│   │   └── decode_jwt()           # Extract claims without verification
│   │
│   ├── blocklist.py                # Token revocation
│   │   ├── blocklist_token()      # Add token to Redis blocklist
│   │   ├── is_blocklisted()       # Check if token revoked
│   │   ├── blocklist_user()       # Revoke all user's tokens
│   │   └── cleanup_expired()      # Redis TTL handles this automatically
│   │
│   ├── middleware.py               # FastAPI middleware
│   │   ├── JWTAuthMiddleware      # Attach user to request context
│   │   └── RateLimitMiddleware    # Prevent brute force
│   │
│   ├── dependencies.py             # FastAPI dependencies
│   │   ├── get_current_user()     # Extract wallet from JWT
│   │   ├── require_auth()         # Raise 401 if not authenticated
│   │   └── optional_auth()        # Allow anonymous + authenticated
│   │
│   └── signature.py                # XRPL signature verification
│       ├── verify_xrpl_signature()# Verify signature matches address
│       └── recover_signer()       # Extract signer from signature
│
├── api/
│   └── auth.py                     # Auth endpoints
│       ├── POST /auth/wallet/challenge
│       ├── POST /auth/wallet/login
│       ├── POST /auth/logout
│       ├── POST /auth/refresh (optional)
│       └── GET  /auth/me (get current user info)
│
└── config/
    ├── redis.py                    # Redis connection for challenges/blocklist
    └── secrets.py                  # Load JWT secret from env/KMS
```

### Frontend Components

```
frontend/
├── lib/
│   ├── auth/
│   │   ├── wallet.ts              # Wallet connection logic
│   │   │   ├── connectWallet()    # Xumm sign-in flow
│   │   │   ├── disconnectWallet() # Logout
│   │   │   └── signMessage()      # Sign challenge
│   │   │
│   │   ├── api.ts                 # Auth API calls
│   │   │   ├── requestChallenge() # GET /auth/wallet/challenge
│   │   │   ├── submitLogin()      # POST /auth/wallet/login
│   │   │   └── logout()           # POST /auth/logout
│   │   │
│   │   ├── hooks.ts               # React hooks
│   │   │   ├── useAuth()          # Auth state + actions
│   │   │   ├── useWallet()        # Wallet state (existing)
│   │   │   └── useRequireAuth()   # Redirect if not logged in
│   │   │
│   │   └── store.ts               # Zustand store for auth state
│   │       ├── authState { token, user, isAuthenticated }
│   │       ├── login()
│   │       ├── logout()
│   │       └── refreshToken()
│   │
│   └── api/
│       └── client.ts              # API client with auth
│           ├── apiRequest()       # Add Authorization header
│           ├── handleTokenRefresh() # Update token from X-New-Token
│           └── handle401()        # Redirect to login on expiry
│
└── app/
    ├── (auth)/
    │   ├── connect/               # Wallet connection page
    │   └── login/                 # Login flow (optional)
    │
    └── (dashboard)/
        └── layout.tsx             # Protected layout (requires auth)
```

---

## API Specification

### Endpoints

#### POST /auth/wallet/challenge

Request a challenge message for wallet signature.

**Request**:
```http
POST /auth/wallet/challenge HTTP/1.1
Content-Type: application/json

{
  "address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "network": "testnet"
}
```

**Response** (200 OK):
```json
{
  "challenge": "LendX Authentication\nTimestamp: 1729900800\nNonce: a1b2c3d4e5f6789\nNetwork: testnet\n\nBy signing this message, you authorize access to your LendX account.\nThis signature will not trigger any blockchain transaction.",
  "nonce": "a1b2c3d4e5f6789",
  "expiresAt": "2025-10-26T10:25:00Z"
}
```

**Errors**:
- `400 Bad Request`: Invalid address format
- `429 Too Many Requests`: Rate limit exceeded (max 5/min per IP)

---

#### POST /auth/wallet/login

Verify wallet signature and issue JWT token.

**Request**:
```http
POST /auth/wallet/login HTTP/1.1
Content-Type: application/json

{
  "address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "signature": "3045022100...",
  "nonce": "a1b2c3d4e5f6789",
  "network": "testnet"
}
```

**Response** (200 OK):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresAt": "2025-10-27T10:20:00Z",
  "user": {
    "address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
    "did": "did:xrpl:testnet:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
    "createdAt": "2025-10-26T09:00:00Z"
  }
}
```

**Errors**:
- `400 Bad Request`: Invalid signature or expired challenge
- `401 Unauthorized`: Signature verification failed
- `429 Too Many Requests`: Rate limit exceeded (max 10/min per IP)

---

#### POST /auth/logout

Revoke current JWT token.

**Request**:
```http
POST /auth/logout HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired token

---

#### GET /auth/me

Get current user information.

**Request**:
```http
GET /auth/me HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "user": {
    "address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
    "did": "did:xrpl:testnet:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
    "createdAt": "2025-10-26T09:00:00Z"
  },
  "session": {
    "expiresAt": "2025-10-27T10:20:00Z",
    "issuedAt": "2025-10-26T10:20:00Z"
  }
}
```

**Errors**:
- `401 Unauthorized`: Not authenticated

---

### Protected Endpoints

All non-auth endpoints require `Authorization: Bearer <token>` header:

```http
GET /pools HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Backend automatically:
1. Verifies JWT
2. Checks blocklist
3. Extracts wallet_address
4. Applies RLS policies (auth.uid() = wallet_address)
5. Optionally refreshes token (X-New-Token header in response)

---

## Frontend Integration

### 1. Zustand Auth Store

```typescript
// frontend/lib/auth/store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  user: {
    address: string
    did: string | null
    createdAt: string
  } | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  login: (address: string, signature: string, nonce: string) => Promise<void>
  logout: () => Promise<void>
  refreshToken: (newToken: string) => void
  setError: (error: string | null) => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (address, signature, nonce) => {
        set({ isLoading: true, error: null })

        try {
          const response = await fetch(`${API_URL}/auth/wallet/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address, signature, nonce, network: 'testnet' }),
          })

          if (!response.ok) {
            throw new Error('Login failed')
          }

          const data = await response.json()

          set({
            token: data.token,
            user: data.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Login failed',
            isAuthenticated: false,
          })
          throw error
        }
      },

      logout: async () => {
        const { token } = get()

        if (token) {
          try {
            await fetch(`${API_URL}/auth/logout`, {
              method: 'POST',
              headers: {
                Authorization: `Bearer ${token}`,
              },
            })
          } catch (error) {
            console.error('Logout API call failed:', error)
          }
        }

        set({
          token: null,
          user: null,
          isAuthenticated: false,
        })
      },

      refreshToken: (newToken) => {
        set({ token: newToken })
      },

      setError: (error) => {
        set({ error })
      },
    }),
    {
      name: 'lendx-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
```

### 2. Wallet Connection Component

```typescript
// frontend/components/auth/ConnectWallet.tsx
'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth/store'
import { connectWallet } from '@/lib/xrpl/wallet'

export function ConnectWallet() {
  const { login, isLoading } = useAuth()
  const [connecting, setConnecting] = useState(false)

  const handleConnect = async () => {
    setConnecting(true)

    try {
      // 1. Connect wallet via Xumm
      const walletState = await connectWallet()

      if (!walletState.address) {
        throw new Error('Failed to get wallet address')
      }

      // 2. Request challenge from backend
      const challengeRes = await fetch(`${API_URL}/auth/wallet/challenge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: walletState.address,
          network: 'testnet',
        }),
      })

      const { challenge, nonce } = await challengeRes.json()

      // 3. Sign challenge with wallet (via Xumm)
      const signature = await signTransaction({
        TransactionType: 'SignIn',
        Account: walletState.address,
        // Challenge message would be displayed to user
      })

      // 4. Submit signature to backend
      await login(walletState.address, signature, nonce)

      // 5. Redirect to dashboard
      window.location.href = '/dashboard'
    } catch (error) {
      console.error('Failed to connect wallet:', error)
      alert('Failed to connect wallet. Please try again.')
    } finally {
      setConnecting(false)
    }
  }

  return (
    <button
      onClick={handleConnect}
      disabled={connecting || isLoading}
      className="btn btn-primary"
    >
      {connecting || isLoading ? 'Connecting...' : 'Connect Wallet'}
    </button>
  )
}
```

### 3. API Client with Auto-Refresh

```typescript
// frontend/lib/api/client.ts
import { useAuth } from '@/lib/auth/store'

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const { token, refreshToken, logout } = useAuth.getState()

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  // Check for refreshed token
  const newToken = response.headers.get('X-New-Token')
  if (newToken) {
    refreshToken(newToken)
    console.log('Token refreshed automatically')
  }

  // Handle expired token
  if (response.status === 401) {
    logout()
    window.location.href = '/auth/connect'
    throw new Error('Session expired')
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Request failed')
  }

  return response.json()
}
```

### 4. Protected Route Component

```typescript
// frontend/components/auth/ProtectedRoute.tsx
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth/store'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/connect')
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return <div>Loading...</div>
  }

  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}
```

---

## Security Model

### Threat Model

| Threat | Mitigation | Status |
|--------|------------|--------|
| **Token theft (XSS)** | CSP headers, input sanitization, httpOnly cookies (future) | Planned |
| **Token theft (network)** | HTTPS only, HSTS headers | Implemented |
| **Signature replay** | Challenge nonce, 5-minute expiration | Implemented |
| **Brute force login** | Rate limiting (10 req/min per IP) | Planned |
| **Session hijacking** | Short expiration (24h), blocklist on logout | Implemented |
| **Compromised JWT secret** | Secret rotation procedure, monitoring | Documented |
| **Insider access** | Service role audit logging, RLS policies | Planned |

### Security Headers

```python
# backend/api/main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lendx.com"],  # Production domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response
```

### Rate Limiting

```python
# backend/auth/middleware.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/wallet/challenge")
@limiter.limit("5/minute")
async def challenge(request: Request, data: ChallengeRequest):
    ...

@app.post("/auth/wallet/login")
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest):
    ...
```

---

## Testing Strategy

### 1. Unit Tests

```python
# backend/tests/test_auth_jwt.py
def test_generate_jwt():
    """Test JWT generation with correct claims."""
    token = generate_jwt("rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx", "testnet")

    decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

    assert decoded["sub"] == "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
    assert decoded["network"] == "testnet"
    assert "jti" in decoded
    assert "exp" in decoded

def test_verify_jwt_expired():
    """Test that expired tokens are rejected."""
    # Generate token that expired 1 hour ago
    token = generate_jwt("rN7n7...", exp=datetime.now() - timedelta(hours=1))

    with pytest.raises(jwt.ExpiredSignatureError):
        verify_jwt(token)

def test_blocklist_token():
    """Test token revocation."""
    token = generate_jwt("rN7n7...")
    decoded = decode_jwt(token)

    # Blocklist the token
    blocklist_token(decoded["jti"], decoded["exp"])

    # Verify it's blocked
    assert is_token_blocklisted(decoded["jti"]) is True

    # Verify verification fails
    with pytest.raises(TokenBlocklistedError):
        verify_jwt(token)
```

### 2. Integration Tests

```python
# backend/tests/test_auth_endpoints.py
def test_login_flow(client):
    """Test complete login flow."""
    # 1. Request challenge
    response = client.post("/auth/wallet/challenge", json={
        "address": "rN7n7...",
        "network": "testnet"
    })
    assert response.status_code == 200
    challenge = response.json()["challenge"]
    nonce = response.json()["nonce"]

    # 2. Sign challenge (mock signature)
    signature = mock_sign_message(challenge, private_key)

    # 3. Submit signature
    response = client.post("/auth/wallet/login", json={
        "address": "rN7n7...",
        "signature": signature,
        "nonce": nonce,
        "network": "testnet"
    })
    assert response.status_code == 200
    token = response.json()["token"]

    # 4. Use token to access protected endpoint
    response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    assert response.json()["user"]["address"] == "rN7n7..."

def test_logout_revokes_token(client):
    """Test that logout blocklists the token."""
    token = login_user(client, "rN7n7...")

    # Logout
    response = client.post("/auth/logout", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200

    # Try to use token again
    response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 401
```

### 3. Security Tests

```python
# backend/tests/test_auth_security.py
def test_signature_replay_attack(client):
    """Verify that challenge can only be used once."""
    challenge_response = client.post("/auth/wallet/challenge", json={
        "address": "rN7n7...",
        "network": "testnet"
    })
    nonce = challenge_response.json()["nonce"]

    signature = mock_sign_message(challenge, private_key)

    # First login succeeds
    response1 = client.post("/auth/wallet/login", json={
        "address": "rN7n7...",
        "signature": signature,
        "nonce": nonce,
        "network": "testnet"
    })
    assert response1.status_code == 200

    # Second login with same signature fails
    response2 = client.post("/auth/wallet/login", json={
        "address": "rN7n7...",
        "signature": signature,
        "nonce": nonce,
        "network": "testnet"
    })
    assert response2.status_code == 400  # Challenge already used

def test_rate_limiting(client):
    """Verify rate limiting prevents brute force."""
    # Make 11 requests (limit is 10/min)
    for i in range(11):
        response = client.post("/auth/wallet/login", json={
            "address": "rN7n7...",
            "signature": "invalid",
            "nonce": "test",
            "network": "testnet"
        })

        if i < 10:
            assert response.status_code in [400, 401]  # Invalid but allowed
        else:
            assert response.status_code == 429  # Rate limited
```

---

## Deployment Guide

### Environment Variables

```bash
# .env (production)

# JWT Configuration
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Redis Configuration (for challenges + blocklist)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=<redis password>

# Database (Supabase)
SUPABASE_DB_PASSWORD=<from Supabase dashboard>
SUPABASE_SERVICE_ROLE_KEY=<from Supabase dashboard>

# XRPL Network
XRPL_NETWORK=mainnet  # or testnet

# Security
ENVIRONMENT=production
ALLOWED_ORIGINS=https://lendx.com,https://www.lendx.com
RATE_LIMIT_ENABLED=true
```

### Infrastructure Requirements

1. **Redis Instance**
   - Used for: Challenge storage, token blocklist
   - Requirements: ~100MB memory, persistence enabled
   - TTL: Automatic cleanup (challenges: 5min, blocklist: 24h max)

2. **Database**
   - Supabase PostgreSQL (existing)
   - Enable RLS before production deployment

3. **Secrets Management**
   - Development: `.env` file (not committed)
   - Production: AWS KMS or Supabase Vault

### Deployment Checklist

- [ ] Generate strong JWT secret (32+ random bytes)
- [ ] Store JWT secret in KMS/Vault
- [ ] Set up Redis instance (persistent)
- [ ] Configure CORS for production domain
- [ ] Enable rate limiting
- [ ] Add security headers
- [ ] Enable HTTPS (enforce with HSTS)
- [ ] Enable RLS on all tables
- [ ] Test login flow end-to-end
- [ ] Test logout revocation
- [ ] Test token refresh
- [ ] Set up monitoring (auth failures, rate limits)
- [ ] Document incident response plan

---

## Monitoring & Observability

### Key Metrics

1. **Authentication Metrics**
   - Login success/failure rate
   - Average time to authenticate
   - Failed signature verifications
   - Rate limit hits

2. **Session Metrics**
   - Active sessions count
   - Session duration (average, p95)
   - Token refresh rate
   - Logout rate

3. **Security Metrics**
   - Blocklisted tokens count
   - Suspicious activity alerts (IP changes, etc.)
   - Challenge expiration rate (users taking too long)

### Logging

```python
import structlog

logger = structlog.get_logger()

# Login event
logger.info("user_login", wallet_address="rN7n7...", ip=request.client.host)

# Logout event
logger.info("user_logout", wallet_address="rN7n7...", jti="550e8400...")

# Failed auth
logger.warning("auth_failed", wallet_address="rN7n7...", reason="invalid_signature")

# Suspicious activity
logger.warning("suspicious_auth", wallet_address="rN7n7...", reason="ip_change", old_ip="1.2.3.4", new_ip="5.6.7.8")
```

---

## Future Enhancements

### Phase 2+ Features

1. **Remember Me** - Longer session duration (30 days) for low-risk operations
2. **HttpOnly Cookies** - Move token from localStorage to secure cookie
3. **Multi-Factor Authentication** - Email/SMS verification for high-value transactions
4. **Active Session Management** - UI to view and revoke individual sessions
5. **Device Fingerprinting** - Detect account takeover via device changes
6. **OAuth Integration** - Allow traditional email/password login alongside wallets
7. **Biometric Auth** - WebAuthn for hardware keys (YubiKey, etc.)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-26
**Next Review**: 2025-11-26
**Owner**: Backend Team
**Status**: Ready for Implementation
