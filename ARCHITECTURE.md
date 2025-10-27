# LendX Architecture Documentation

> **Cal Hacks 2025 First Place Winner** - Ripple: Best Use of XRP Ledger

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [XRPL Integration Architecture](#xrpl-integration-architecture)
6. [Database Schema](#database-schema)
7. [Security Architecture](#security-architecture)
8. [API Architecture](#api-architecture)
9. [Settlement Algorithm](#settlement-algorithm)
10. [Technology Stack](#technology-stack)

---

## System Overview

LendX is a **decentralized peer-to-peer lending marketplace** that enables financial inclusion through blockchain technology. The platform leverages XRPL's (XRP Ledger) advanced features to create a trustless, transparent, and efficient lending ecosystem.

### Core Value Proposition

- **Decentralized Trust**: All loan agreements represented as on-chain Multi-Purpose Tokens (MPT)
- **Verifiable Identity**: W3C DID standard for decentralized identity
- **Automated Security**: Escrow-based collateral with programmable conditions
- **Minimal Counterparty Risk**: Multi-signature settlement and cycle reduction algorithm

### System Architecture Pattern

LendX follows a **blockchain-indexed application** pattern where:
- **Source of Truth**: XRPL blockchain (immutable, auditable)
- **Performance Layer**: Supabase PostgreSQL (queryable, indexed cache)
- **Business Logic**: Python FastAPI (validation, orchestration, settlement computation)
- **User Interface**: Next.js 14 (responsive, real-time updates)

This architecture provides blockchain security with traditional database performance.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Frontend Layer                                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │           Next.js 14 App Router (Port 3000)                       │  │
│  │                                                                   │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │  │
│  │  │  Lender View │  │ Borrower View│  │  Wallet Connection │    │  │
│  │  │  - Pool Mgmt │  │  - Apply Loan│  │  - XUMM SDK        │    │  │
│  │  │  - Approvals │  │  - Track Loan│  │  - Native XRPL     │    │  │
│  │  └──────────────┘  └──────────────┘  └────────────────────┘    │  │
│  │                                                                   │  │
│  │  Components: shadcn/ui (Radix) + Tailwind CSS                   │  │
│  │  State: Zustand + React Context (DemoProvider)                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ REST API (CORS-enabled)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Backend Layer                                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │              Python FastAPI Server (Port 8000)                    │  │
│  │                                                                   │  │
│  │  ┌────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │  │
│  │  │ API Routes │  │   Services   │  │   XRPL Client Layer     │ │  │
│  │  │            │  │              │  │                         │ │  │
│  │  │ /pools     │─▶│ mpt_service  │─▶│ client.py (JsonRpc)    │ │  │
│  │  │ /loans     │  │ did_service  │  │ mpt.py (Token Ops)     │ │  │
│  │  │ /api/auth  │  │ xumm_service │  │ escrow.py (Collateral) │ │  │
│  │  │ /api/rlusd │  │              │  │ multisig.py (Sigs)     │ │  │
│  │  └────────────┘  └──────────────┘  └─────────────────────────┘ │  │
│  │                                                                   │  │
│  │  Exception Handling: @wrap_xrpl_exception decorator             │  │
│  │  Connection Pooling: SQLAlchemy (5 conns, 10 overflow)          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                    │                           │
                    │ SQL Queries               │ XRPL RPC/WebSocket
                    ▼                           ▼
┌──────────────────────────────┐    ┌────────────────────────────────┐
│    Database Layer            │    │   Blockchain Layer             │
│                              │    │                                │
│  Supabase PostgreSQL         │    │  XRPL Testnet/Mainnet         │
│  (SSL, UTC timezone)         │    │                                │
│                              │    │  ┌──────────────────────────┐ │
│  Tables:                     │    │  │  On-Chain Objects:       │ │
│  - users (addresses, DIDs)   │    │  │                          │ │
│  - pools (PoolMPT index)     │    │  │  • PoolMPT (issuance)   │ │
│  - applications (AppMPT idx) │    │  │  • ApplicationMPT       │ │
│  - loans (LoanMPT index)     │    │  │  • LoanMPT              │ │
│  - user_mpt_balances (cache) │    │  │  • Escrow objects       │ │
│                              │    │  │  • DID documents        │ │
│  Indexes on: issuer, pool,   │    │  │  • RLUSD trustlines     │ │
│  borrower, lender, state     │    │  │                          │ │
│                              │    │  └──────────────────────────┘ │
└──────────────────────────────┘    └────────────────────────────────┘
```

---

## Component Architecture

### Frontend Layer: Next.js 14 Application

**Technology**: React 18+ with App Router, TypeScript

**Directory Structure**:
```
frontend/
├── app/
│   ├── (auth)/signup/          # Authentication flow
│   ├── (dashboard)/dashboard/  # Main application
│   └── page.tsx                # Landing page
├── components/
│   ├── lendx/                  # Core business components
│   │   ├── lender-view.tsx     # Pool creation, loan approval UI
│   │   └── borrower-view.tsx   # Loan application, tracking UI
│   ├── ui/                     # shadcn/ui components (Radix)
│   └── dashboard/              # Layout components
└── lib/
    ├── xrpl/                   # XRPL integration utilities
    ├── demo-context.tsx        # Global state (viewMode: lender|borrower)
    └── utils.ts                # Helper functions
```

**Key Features**:
- **Route Groups**: `(auth)` and `(dashboard)` isolate layouts
- **View Mode Toggle**: Switch between lender/borrower perspectives
- **Wallet Integration**: XUMM SDK for mobile + native `xrpl` library
- **Real-time Updates**: WebSocket subscriptions to XRPL transactions
- **Form Validation**: React Hook Form + Zod schemas

**Component Hierarchy**:
```typescript
// frontend/app/(dashboard)/dashboard/page.tsx (lines 8-24)
export default function DashboardPage() {
  const { viewMode } = useDemoContext()

  return (
    <>
      {viewMode === "lender" ? <LenderView /> : <BorrowerView />}
    </>
  )
}
```

**State Management**:
- **Zustand**: Client-side state (wallet connection, balances)
- **React Context**: Demo mode and view switching
- **Server State**: Cached API responses (React Query pattern)

---

### Backend Layer: Python FastAPI Server

**Technology**: Python 3.11+, FastAPI, SQLAlchemy, XRPL Python SDK

**Architecture Pattern**: Service-Oriented with Layered Responsibilities

```
backend/
├── api/
│   ├── main.py          # FastAPI app, endpoints, CORS configuration
│   ├── auth.py          # Signup, DID verification endpoints
│   └── xumm.py          # XUMM SDK integration for wallet signing
├── xrpl_client/         # XRPL blockchain interface layer
│   ├── client.py        # Connection, transaction submission
│   ├── mpt.py           # Multi-Purpose Token operations
│   ├── escrow.py        # Escrow transactions
│   ├── multisig.py      # Multi-signature account management
│   ├── exceptions.py    # Custom error handling (@wrap_xrpl_exception)
│   └── config.py        # Network URLs, constants
├── services/            # Business logic layer
│   ├── mpt_service.py   # MPT creation with metadata encoding
│   ├── did_service.py   # DID creation and document retrieval
│   └── xumm_service.py  # Payment request generation
├── models/
│   ├── database.py      # SQLAlchemy ORM models
│   └── mpt_schemas.py   # MPT metadata Pydantic models
├── config/
│   └── database.py      # Supabase connection, session management
└── tests/               # TDD test suite (pytest)
    ├── test_users.py
    ├── test_pools.py
    └── conftest.py
```

**Key Design Decisions**:

1. **Exception Wrapping** (backend/xrpl_client/exceptions.py):
   - All XRPL operations decorated with `@wrap_xrpl_exception`
   - Converts XRPL-specific errors to application exceptions
   - Categories: `ConnectionError`, `InsufficientXRP`, `PermissionDenied`

2. **Connection Pooling** (backend/config/database.py):
   ```python
   engine = create_engine(
       database_url,
       pool_size=5,        # Base connections
       max_overflow=10,    # Additional under load
       pool_pre_ping=True, # Health check before use
       connect_args={
           "sslmode": "require",
           "options": "-c timezone=utc"
       }
   )
   ```

3. **Separation of Concerns**:
   - **API Layer**: Request validation, response serialization (main.py)
   - **Service Layer**: Business logic, MPT metadata encoding (services/)
   - **Client Layer**: XRPL transaction construction (xrpl_client/)
   - **Model Layer**: Database schema, constraints (models/)

---

### Database Layer: Supabase PostgreSQL

**Connection Details**:
- **Host**: sspwpkhajtooztzisioo.supabase.co
- **SSL**: Required (enforced by Supabase)
- **Timezone**: UTC (set automatically on connect)
- **Pooling**: 5 connections, 10 max overflow

**Schema Philosophy**:
The database acts as an **indexed cache** of on-chain XRPL data, enabling:
- Fast queries without blockchain RPC calls
- Complex filtering (by state, date, user role)
- Aggregations (total pool balances, loan counts)
- Real-time dashboard updates

**Data Synchronization**:
```
XRPL Transaction → WebSocket Event → Backend Listener → Database Update
                                                       ↓
                                              Frontend Poll/Subscribe
```

---

### Blockchain Layer: XRPL Integration

**Network Selection**:
- **Development**: Testnet (wss://s.altnet.rippletest.net:51233)
- **Production**: Mainnet (wss://xrplcluster.com)

**Client Architecture** (backend/xrpl_client/client.py):
```python
# Singleton client pattern
xrpl_client = None

def get_xrpl_client():
    global xrpl_client
    if xrpl_client is None:
        xrpl_client = connect('testnet')  # JsonRpcClient
    return xrpl_client
```

**Transaction Flow**:
```python
# backend/xrpl_client/client.py (lines 56-90)
def submit_and_wait(client, tx, wallet):
    """Sign with autofill, submit, wait for validation."""
    tx_obj = Transaction.from_dict(tx)
    signed_tx = autofill_and_sign(tx_obj, client, wallet)
    response = submit_and_wait(signed_tx, client)
    return response.result  # Contains tx_hash, meta, etc.
```

---

## Data Flow

### 1. User Authentication Flow (Auth0 + DID)

**Current Implementation** (MVP): Backend-generated wallets with DID

```
┌────────────┐
│   User     │
│  Signup    │
└─────┬──────┘
      │ POST /api/auth/signup
      ▼
┌─────────────────────────────────────────┐
│  Backend: auth.py (line 47)             │
│                                         │
│  1. Generate wallet: Wallet.create()    │
│  2. Create DID on XRPL (did_service)   │
│  3. Store user in database              │
│  4. Return address + seed (DEMO ONLY)  │
└─────┬───────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│  Database: users table                  │
│  - address: rN7n7otQDd6FczFg...         │
│  - did: did:xrpl:1:rN7n7otQDd6...      │
└─────┬───────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│  XRPL: DID document on ledger           │
│  - URI: xrpl:1:rN7n7otQDd6...          │
│  - Public key for verification          │
└─────────────────────────────────────────┘
```

**Future Enhancement**: Integrate Auth0 for OAuth + wallet linking

---

### 2. Lending Pool Creation Flow

**Endpoint**: `POST /pools` (backend/api/main.py, line 126)

```
┌────────────┐
│  Lender    │
│  Creates   │
│   Pool     │
└─────┬──────┘
      │ POST /pools
      │ {
      │   name: "Emergency Loans",
      │   amount: 10000,
      │   interest_rate: 5.0,
      │   max_term_days: 90,
      │   min_loan_amount: 100,
      │   lender_address: "rN7n..."
      │ }
      ▼
┌──────────────────────────────────────────────────────┐
│  Backend: create_lending_pool()                      │
│                                                      │
│  1. Validate lender exists (line 131)               │
│  2. Generate demo wallet (line 141) [MVP only]      │
│  3. Create PoolMPT metadata (line 145):             │
│     - issuer_addr, total_balance, current_balance   │
│     - minimum_loan, duration, interest_rate         │
│  4. Call create_pool_mpt() (line 156)               │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  XRPL Client: mpt_service.py (create_pool_mpt)      │
│                                                      │
│  1. Encode metadata (Pydantic → JSON → IPFS hash)   │
│  2. Create MPTokenIssuanceCreate transaction        │
│  3. Submit to XRPL, wait for validation             │
│  4. Extract mpt_id from transaction metadata        │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  Database: pools table (line 168)                   │
│  - pool_address: <MPT_ID> (primary key)             │
│  - issuer_address: rN7n...                          │
│  - total_balance: 10000.00                          │
│  - current_balance: 10000.00                        │
│  - interest_rate: 5.00                              │
│  - tx_hash: ABC123...                               │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  XRPL Ledger: PoolMPT object                        │
│  - MPT ID: 00001234ABCD...                          │
│  - Issuer: rN7n...                                  │
│  - Metadata URI: ipfs://Qm...                       │
│  - Flags: 0x00000002 (non-transferable)             │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌────────────┐
│  Frontend  │
│  Shows new │
│   pool in  │
│  dashboard │
└────────────┘
```

**Key Implementation Details**:
- **MPT ID as Primary Key**: Ensures database records map 1:1 to on-chain objects
- **Non-Transferable Flag**: Prevents secondary market trading (regulatory compliance)
- **Current Balance Tracking**: Updated on loan approval (line 358)

---

### 3. Loan Application Process

**Endpoint**: `POST /loans/apply` (backend/api/main.py, line 228)

```
┌────────────┐
│  Borrower  │
│  Applies   │
│  for Loan  │
└─────┬──────┘
      │ POST /loans/apply
      │ {
      │   pool_id: "00001234ABCD...",
      │   amount: 500,
      │   term_days: 30,
      │   purpose: "Medical bills",
      │   borrower_address: "rABC..."
      │ }
      ▼
┌──────────────────────────────────────────────────────┐
│  Backend: apply_for_loan()                           │
│                                                      │
│  1. Verify pool exists (line 233)                   │
│  2. Check sufficient funds (line 238)               │
│  3. Calculate interest (line 255)                   │
│  4. Create ApplicationMPT (line 270)                │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  Database: applications table                        │
│  - application_address: <APP_MPT_ID>                │
│  - borrower_address: rABC...                        │
│  - pool_address: 00001234ABCD...                    │
│  - state: PENDING                                   │
│  - principal: 500.00                                │
│  - interest: 25.00 (5% of 500)                      │
│  - dissolution_date: now() + 30 days                │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  XRPL Ledger: ApplicationMPT object                 │
│  - State: PENDING                                   │
│  - Linked to PoolMPT                                │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌────────────┐
│  Frontend  │
│  Lender    │
│  sees new  │
│ application│
└────────────┘
```

**State Machine**:
```
PENDING → APPROVED → (creates LoanMPT)
        ↘ REJECTED
        ↘ EXPIRED (after dissolution_date)
```

---

### 4. Loan Approval and Fund Transfer

**Endpoint**: `POST /loans/{loan_id}/approve` (backend/api/main.py, line 335)

```
┌────────────┐
│   Lender   │
│  Approves  │
│    Loan    │
└─────┬──────┘
      │ POST /loans/{application_id}/approve
      │ {
      │   loan_id: "APP_MPT_ID",
      │   approved: true,
      │   lender_address: "rN7n..."
      │ }
      ▼
┌──────────────────────────────────────────────────────┐
│  Backend: approve_loan()                             │
│                                                      │
│  1. Verify application exists (line 340)            │
│  2. Check state is PENDING (line 352)               │
│  3. Update application.state = APPROVED (line 355)  │
│  4. Decrease pool.current_balance (line 358)        │
│  5. Create LoanMPT (line 380):                      │
│     - pool_addr, borrower_addr, lender_addr         │
│     - start_date, end_date, principal, interest     │
│     - state: ONGOING                                │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  Database Updates (atomic transaction)               │
│                                                      │
│  applications:                                       │
│    state: PENDING → APPROVED                        │
│                                                      │
│  pools:                                             │
│    current_balance: 10000 → 9500                    │
│                                                      │
│  loans: (new record)                                │
│    loan_address: <LOAN_MPT_ID>                      │
│    state: ONGOING                                   │
│    principal: 500.00, interest: 25.00               │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  XRPL: LoanMPT creation + RLUSD transfer            │
│                                                      │
│  Transaction 1: Create LoanMPT (immutable record)   │
│  Transaction 2: Transfer RLUSD (500) to borrower    │
│                 - Requires trustline setup          │
│                 - Issuer: rpypVpiKneAn5WUmweA...    │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌────────────┐
│  Borrower  │
│  receives  │
│  500 RLUSD │
│   in wallet│
└────────────┘
```

**Critical Implementation Notes**:
1. **Atomicity**: Application update + Pool balance update in single DB transaction
2. **RLUSD Integration**: Ripple's USD stablecoin for actual fund transfers
3. **Trustline Requirement**: Borrower must establish RLUSD trustline before receiving funds
4. **LoanMPT as Receipt**: Immutable on-chain proof of loan agreement

---

### 5. Repayment and Settlement

**Conceptual Flow** (Settlement algorithm implementation in progress):

```
┌────────────┐
│  Borrower  │
│   Repays   │
│    Loan    │
└─────┬──────┘
      │ POST /loans/{loan_id}/repay
      │ {
      │   amount: 525.00 (principal + interest)
      │ }
      ▼
┌──────────────────────────────────────────────────────┐
│  Backend: Repayment Processing                       │
│                                                      │
│  1. Transfer RLUSD from borrower to escrow          │
│  2. Verify full amount received                     │
│  3. Update loan.state = PAID                        │
│  4. Release escrow to lender                        │
│  5. Increase pool.current_balance                   │
└──────┬───────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  Graph-Based Settlement (for multi-party loans)     │
│                                                      │
│  Problem: Minimize transaction count when multiple  │
│           lenders and borrowers owe each other      │
│                                                      │
│  Algorithm (backend/graph/):                        │
│    1. Build directed graph of IOUs                  │
│    2. Detect cycles (circular debts)                │
│    3. Reduce cycles (net out offsetting debts)      │
│    4. Compute net balances                          │
│    5. Generate minimal escrow instructions          │
│                                                      │
│  Example:                                           │
│    A owes B $100, B owes C $100, C owes A $100     │
│    → Cycle detected → Net out → 0 transfers needed │
└──────────────────────────────────────────────────────┘
```

**Settlement Algorithm Architecture** (referenced in docs/DEVELOPMENT.md, implementation in services/):

**Graph Data Structures**:
```python
# Conceptual types (from docs/DEVELOPMENT.md documentation)
class Edge:
    """Directed edge representing debt."""
    debtor: str      # Borrower address
    creditor: str    # Lender address
    amount: Decimal  # Debt amount

class Graph:
    """Debt graph for cycle reduction."""
    edges: List[Edge]
    vertices: Set[str]  # Unique addresses
```

**Cycle Reduction Algorithm**:
1. **Cycle Detection**: DFS to find circular debt paths
2. **Cycle Elimination**: Subtract minimum cycle amount from all edges in cycle
3. **Net Balance Computation**: Sum inflows and outflows per vertex
4. **Escrow Generation**: Create escrow instructions for non-zero net balances

**Multi-Signature Settlement**:
```python
# Requires 2 signatures for settlement proposals
REQUIRED_SIGNATURES = 2

# Multi-sig flow:
# 1. Propose settlement (create unsigned transaction)
# 2. Collect signatures from lender and borrower
# 3. Submit when threshold reached
# 4. Execute escrow releases
```

---

## XRPL Integration Architecture

### Multi-Purpose Tokens (MPT) for Loan Representation

**MPT Philosophy**: Each loan lifecycle stage is represented by a distinct MPT type

```
┌─────────────────────────────────────────────────────────────────┐
│                       MPT Type Hierarchy                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PoolMPT                                                        │
│  ├─ Represents: Lending pool with available capital            │
│  ├─ Issuer: Lender's wallet                                    │
│  ├─ Metadata: total_balance, interest_rate, duration, min_loan │
│  ├─ Transferability: Non-transferable (flag 0x00000002)        │
│  └─ Lifecycle: Created once, persistent                        │
│                                                                  │
│  ApplicationMPT (linked to PoolMPT)                            │
│  ├─ Represents: Loan application (pending approval)            │
│  ├─ Issuer: Borrower's wallet                                  │
│  ├─ Metadata: principal, interest, state, dissolution_date     │
│  ├─ State Machine: PENDING → APPROVED / REJECTED / EXPIRED     │
│  └─ Lifecycle: Created on apply, updated on approval           │
│                                                                  │
│  LoanMPT (linked to PoolMPT + ApplicationMPT)                  │
│  ├─ Represents: Active loan with repayment obligation          │
│  ├─ Issuer: Lender's wallet                                    │
│  ├─ Metadata: start_date, end_date, principal, interest, state │
│  ├─ State Machine: ONGOING → PAID / DEFAULTED                  │
│  └─ Lifecycle: Created on approval, immutable loan record      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**MPT Operations** (backend/xrpl_client/mpt.py):

1. **Create Issuance** (line 24):
   ```python
   def create_issuance(client, issuer_wallet, ticker, name):
       tx = MPTokenIssuanceCreate(
           account=issuer_wallet.classic_address,
           flags=0x00000002,  # Non-transferable
           metadata={"name": name, "ticker": ticker}
       )
       response = submit_and_wait(client, tx, issuer_wallet)
       return {"mpt_id": extract_from_metadata(response), "tx_hash": ...}
   ```

2. **Authorize Holder** (line 88):
   - Holder must submit `MPTokenAuthorize` before receiving tokens
   - Prevents unsolicited token airdrops (spam protection)

3. **Mint Tokens** (line 180):
   ```python
   def mint_to_holder(client, issuer_wallet, holder, amount, issuance_id):
       mpt_amount = int(amount * 1_000_000)  # 6 decimal places
       tx = Payment(
           account=issuer_wallet.classic_address,
           destination=holder,
           amount={"currency": issuance_id, "value": str(mpt_amount), ...}
       )
       return submit_and_wait(client, tx, issuer_wallet)
   ```

4. **Query Balance** (line 124):
   - Uses `AccountObjects` RPC request
   - Filters by `type="mptoken"` and `MPTokenID`
   - Converts hex balance to decimal

**Why MPT Instead of NFTs?**
- **Fungibility**: Loan amounts are divisible (partial payments)
- **Native Support**: XRPL MPT is ledger-native (no smart contracts)
- **Non-Transferability**: Built-in flag prevents secondary trading
- **Gas Efficiency**: Lower transaction costs than NFT operations

---

### Escrow for Collateral Management

**Escrow Architecture** (backend/xrpl_client/escrow.py - referenced in docs/DEVELOPMENT.md):

```python
# Escrow creation with conditions
def create_deposit_escrow(
    client: JsonRpcClient,
    source_wallet: Wallet,
    destination: str,
    amount: int,  # in drops
    hold_seconds: int = 3600  # Default 1 hour
):
    """
    Lock funds in escrow with time-based release condition.

    Conditions:
    - FinishAfter: Earliest ledger time for release
    - CancelAfter: Latest ledger time (prevents indefinite lock)
    """
    finish_after = ripple_time_now() + hold_seconds
    cancel_after = finish_after + (hold_seconds * 2)  # 2x safety margin

    escrow_create = EscrowCreate(
        account=source_wallet.classic_address,
        destination=destination,
        amount=str(amount),
        finish_after=finish_after,
        cancel_after=cancel_after
    )

    return submit_and_wait(client, escrow_create, source_wallet)
```

**Escrow Use Cases in LendX**:
1. **Collateral Lock**: Borrower deposits collateral on loan approval
2. **Trustless Release**: Funds auto-release on repayment confirmation
3. **Default Protection**: Lender can claim collateral if loan defaults
4. **Multi-Party Settlement**: Escrow instructions for cycle-reduced settlements

**Escrow Finalization**:
```python
def finish_escrow(client, wallet, sequence_number, destination):
    """Release funds from escrow to destination."""
    escrow_finish = EscrowFinish(
        account=wallet.classic_address,
        owner=wallet.classic_address,
        offer_sequence=sequence_number
    )
    return submit_and_wait(client, escrow_finish, wallet)
```

---

### Multi-Signature Accounts

**Multi-Sig Architecture** (backend/xrpl_client/multisig.py - referenced in docs/DEVELOPMENT.md):

```python
REQUIRED_SIGNATURES = 2  # Lender + borrower must both sign

def setup_multisig_account(
    client: JsonRpcClient,
    master_wallet: Wallet,
    signers: List[str],  # List of signer addresses
    quorum: int = 2
):
    """
    Configure account to require multiple signatures.

    Process:
    1. Add signers with SignerListSet transaction
    2. Disable master key (optional for full security)
    3. Set quorum (minimum signatures required)
    """
    signer_entries = [
        {"SignerEntry": {"Account": addr, "SignerWeight": 1}}
        for addr in signers
    ]

    signer_list_set = SignerListSet(
        account=master_wallet.classic_address,
        signer_quorum=quorum,
        signer_entries=signer_entries
    )

    return submit_and_wait(client, signer_list_set, master_wallet)
```

**Multi-Sig Transaction Flow**:
```
1. Create unsigned transaction (settlement proposal)
2. First signer signs → Partial signature
3. Second signer signs → Transaction complete
4. Submit combined signature to XRPL
5. Execute (escrow release, fund transfer, etc.)
```

**Benefits**:
- **Prevents Fraud**: Single party cannot drain escrow
- **Audit Trail**: Both parties explicitly consent
- **Regulatory Compliance**: Meets multi-party approval requirements

---

### Real-Time WebSocket Subscriptions

**WebSocket Client** (backend/xrpl_client/client.py, line 92):

```python
class AccountSubscription:
    """Manages WebSocket subscription for account updates."""

    def __init__(self, client: AsyncWebsocketClient, address: str, callback: Callable):
        self.client = client
        self.address = address
        self.callback = callback

    async def start(self):
        """Subscribe to account transactions."""
        subscribe_request = {
            "command": "subscribe",
            "accounts": [self.address]
        }
        await self.client.send(subscribe_request)

        # Listen for validated transactions
        async for message in self.client:
            if message.get("type") == "transaction" and message.get("validated"):
                self.callback(message)  # Trigger update
```

**Use Cases**:
- **Balance Updates**: Notify frontend when RLUSD transfer completes
- **Loan State Changes**: Real-time updates on approval/repayment
- **Escrow Events**: Alert on collateral lock/release

**Frontend Integration**:
```typescript
// Conceptual WebSocket hook
useEffect(() => {
  const ws = new WebSocket('wss://testnet.xrpl.org');

  ws.on('transaction', (tx) => {
    if (tx.Account === userAddress) {
      refetchBalance();  // Update UI
    }
  });
}, [userAddress]);
```

---

## Database Schema

### Entity-Relationship Diagram

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ address (PK)    │◄──────────┐
│ did (UNIQUE)    │           │
│ created_at      │           │
└─────────────────┘           │
                              │
                              │ (Foreign Keys)
                              │
      ┌───────────────────────┼───────────────────────┐
      │                       │                       │
      ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│     pools       │   │  applications   │   │      loans      │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ pool_address PK │   │ app_addr PK     │   │ loan_addr PK    │
│ issuer_addr FK  │◄──│ pool_addr FK    │◄──│ pool_addr FK    │
│ total_balance   │   │ borrower_addr FK│   │ borrower_addr FK│
│ current_balance │   │ app_date        │   │ lender_addr FK  │
│ minimum_loan    │   │ dissolution_dt  │   │ start_date      │
│ duration_days   │   │ state           │   │ end_date        │
│ interest_rate   │   │ principal       │   │ principal       │
│ tx_hash         │   │ interest        │   │ interest        │
└─────────────────┘   │ tx_hash         │   │ state           │
                      └─────────────────┘   │ tx_hash         │
                                            └─────────────────┘
                              │
                              ▼
                      ┌─────────────────┐
                      │user_mpt_balances│
                      ├─────────────────┤
                      │ user_addr PK,FK │
                      │ mpt_id PK       │
                      │ balance         │
                      │ last_synced     │
                      └─────────────────┘
```

### Table Specifications

#### **users** (backend/models/database.py, line 28)

| Column       | Type         | Constraints           | Description                     |
|--------------|--------------|----------------------|---------------------------------|
| `address`    | VARCHAR(34)  | PRIMARY KEY          | XRP wallet address (r...)       |
| `did`        | VARCHAR(255) | UNIQUE, NULLABLE     | W3C DID (did:xrpl:1:r...)      |
| `created_at` | TIMESTAMP    | DEFAULT now()        | Account creation timestamp      |

**Indexes**: None (primary key only)

**Validation**:
```python
@validates('address')
def validate_address(self, key, address):
    if address and not address.startswith('r'):
        raise ValueError("XRP address must start with 'r'")
    return address
```

---

#### **pools** (backend/models/database.py, line 80)

| Column            | Type          | Constraints                  | Description                        |
|-------------------|---------------|-----------------------------|------------------------------------|
| `pool_address`    | VARCHAR(66)   | PRIMARY KEY                 | MPT issuance ID                    |
| `issuer_address`  | VARCHAR(34)   | FK → users.address          | Lender's wallet address            |
| `total_balance`   | NUMERIC(20,6) | NOT NULL                    | Initial pool balance               |
| `current_balance` | NUMERIC(20,6) | NOT NULL, CHECK >= 0        | Available for new loans            |
| `minimum_loan`    | NUMERIC(20,6) | NOT NULL, CHECK > 0         | Minimum loan amount                |
| `duration_days`   | INTEGER       | NOT NULL, CHECK > 0         | Loan duration in days              |
| `interest_rate`   | NUMERIC(5,2)  | NOT NULL, CHECK >= 0        | Interest rate percentage           |
| `tx_hash`         | VARCHAR(64)   | NOT NULL                    | XRPL transaction hash              |
| `created_at`      | TIMESTAMP     | DEFAULT now()               | Pool creation timestamp            |

**Indexes**:
- `idx_pools_issuer` on `issuer_address` (fast lookup of lender's pools)

**Check Constraints**:
- `current_balance >= 0`: Prevent negative balances
- `total_balance >= current_balance`: Ensure logical consistency
- `minimum_loan > 0`, `duration_days > 0`, `interest_rate >= 0`: Validate inputs

**Business Logic**:
```python
# When loan approved (backend/api/main.py, line 358)
pool.current_balance -= app.principal
```

---

#### **applications** (backend/models/database.py, line 140)

| Column                | Type          | Constraints                         | Description                      |
|-----------------------|---------------|-------------------------------------|----------------------------------|
| `application_address` | VARCHAR(66)   | PRIMARY KEY                         | ApplicationMPT ID                |
| `borrower_address`    | VARCHAR(34)   | FK → users.address                  | Borrower's wallet address        |
| `pool_address`        | VARCHAR(66)   | FK → pools.pool_address             | Associated pool                  |
| `application_date`    | TIMESTAMP     | NOT NULL                            | Application submission date      |
| `dissolution_date`    | TIMESTAMP     | NOT NULL                            | Expiration date                  |
| `state`               | VARCHAR(20)   | NOT NULL, CHECK IN (...)            | PENDING/APPROVED/REJECTED/EXPIRED|
| `principal`           | NUMERIC(20,6) | NOT NULL, CHECK > 0                 | Requested loan amount            |
| `interest`            | NUMERIC(20,6) | NOT NULL, CHECK >= 0                | Calculated interest amount       |
| `tx_hash`             | VARCHAR(64)   | NOT NULL                            | XRPL transaction hash            |

**Indexes**:
- `idx_applications_borrower` on `borrower_address`
- `idx_applications_pool` on `pool_address`
- `idx_applications_state` on `state` (filter by status)

**State Machine Validation**:
```python
@validates('state')
def validate_state(self, key, state):
    valid_states = ['PENDING', 'APPROVED', 'REJECTED', 'EXPIRED']
    if state not in valid_states:
        raise ValueError(f"Invalid state: {state}")
    return state
```

---

#### **loans** (backend/models/database.py, line 210)

| Column             | Type          | Constraints                         | Description                      |
|--------------------|---------------|-------------------------------------|----------------------------------|
| `loan_address`     | VARCHAR(66)   | PRIMARY KEY                         | LoanMPT ID                       |
| `pool_address`     | VARCHAR(66)   | FK → pools.pool_address             | Associated pool                  |
| `borrower_address` | VARCHAR(34)   | FK → users.address                  | Borrower's wallet address        |
| `lender_address`   | VARCHAR(34)   | FK → users.address                  | Lender's wallet address          |
| `start_date`       | TIMESTAMP     | NOT NULL                            | Loan start date                  |
| `end_date`         | TIMESTAMP     | NOT NULL, CHECK > start_date        | Loan due date                    |
| `principal`        | NUMERIC(20,6) | NOT NULL, CHECK > 0                 | Loan amount                      |
| `interest`         | NUMERIC(20,6) | NOT NULL, CHECK >= 0                | Interest amount                  |
| `state`            | VARCHAR(20)   | NOT NULL, CHECK IN (ONGOING/PAID/DEFAULTED) | Loan status        |
| `tx_hash`          | VARCHAR(64)   | NOT NULL                            | XRPL transaction hash            |

**Indexes**:
- `idx_loans_borrower` on `borrower_address`
- `idx_loans_lender` on `lender_address`
- `idx_loans_pool` on `pool_address`
- `idx_loans_state` on `state`

**Business Logic Methods**:
```python
def is_overdue(self) -> bool:
    """Check if loan is past due date."""
    return datetime.now() > self.end_date and self.state == 'ONGOING'

def total_amount_due(self) -> Decimal:
    """Calculate total repayment (principal + interest)."""
    return self.principal + self.interest
```

---

#### **user_mpt_balances** (backend/models/database.py, line 298)

| Column         | Type          | Constraints                  | Description                      |
|----------------|---------------|------------------------------|----------------------------------|
| `user_address` | VARCHAR(34)   | PRIMARY KEY, FK → users      | User's wallet address            |
| `mpt_id`       | VARCHAR(66)   | PRIMARY KEY                  | MPT issuance ID                  |
| `balance`      | NUMERIC(20,6) | NOT NULL, DEFAULT 0, CHECK >= 0 | Cached MPT balance            |
| `last_synced`  | TIMESTAMP     | DEFAULT now()                | Last sync timestamp              |

**Composite Primary Key**: (user_address, mpt_id) allows multiple MPT balances per user

**Staleness Check**:
```python
def is_stale(self, max_age_seconds: int = 300) -> bool:
    """Check if balance needs refresh (default: 5 minutes)."""
    age = (datetime.now() - self.last_synced).total_seconds()
    return age > max_age_seconds
```

**Usage Pattern**:
```python
# Check cache first
balance = db.query(UserMPTBalance).filter_by(
    user_address=addr, mpt_id=mpt_id
).first()

if not balance or balance.is_stale():
    # Refresh from XRPL
    balance.balance = get_mpt_balance(client, addr, mpt_id)
    balance.last_synced = datetime.now()
    db.commit()

return balance.balance
```

---

### Database Migration Strategy

**Migration Files** (backend/migrations/):
- `001_initial_schema.sql`: Creates all tables, indexes, constraints
- Future migrations: `002_add_repayment_tracking.sql`, etc.

**SQLAlchemy Auto-Migration** (not currently used, but recommended for production):
```python
# Using Alembic
alembic revision --autogenerate -m "Add repayment_history table"
alembic upgrade head
```

---

## Security Architecture

### 1. Authentication Layer

**Current Implementation** (MVP):
- Backend-generated wallets with seed return (DEMO ONLY)
- DID creation for verifiable identity

**Production Roadmap**:
```
┌─────────────────────────────────────────────────────────────┐
│  Auth0 Integration (Planned)                                 │
│                                                              │
│  1. OAuth 2.0 login (Google, GitHub, etc.)                  │
│  2. Link Auth0 user ID to XRPL wallet address               │
│  3. JWT token for API authentication                        │
│  4. Refresh token rotation                                  │
│                                                              │
│  Database: users.auth0_id, users.access_token_hash          │
└─────────────────────────────────────────────────────────────┘
```

**DID-Based Identity** (backend/api/auth.py, line 67):
```python
# Create DID on signup
did = create_did_for_user(
    user_wallet=wallet,
    network='testnet'
)
# Format: did:xrpl:1:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx
```

**Benefits of DID**:
- **Self-Sovereign**: User controls identity (no central authority)
- **Verifiable**: Cryptographic proof of ownership
- **Portable**: DID works across platforms
- **Privacy-Preserving**: Selective disclosure of attributes

---

### 2. XRPL Transaction Signing

**Security Model**: Client-side signing with backend submission

```
┌─────────────────────────────────────────────────────────────┐
│  Transaction Flow (Production)                               │
│                                                              │
│  Frontend:                                                   │
│    1. User initiates transaction (create pool, approve loan) │
│    2. Frontend constructs unsigned transaction               │
│    3. Send to XUMM for signing (mobile wallet)               │
│    4. XUMM signs with user's private key (never leaves app)  │
│    5. Return signed transaction to frontend                  │
│                                                              │
│  Backend:                                                    │
│    6. Receive signed transaction                             │
│    7. Validate signature and transaction structure           │
│    8. Submit to XRPL network                                 │
│    9. Update database on successful validation               │
└─────────────────────────────────────────────────────────────┘
```

**Current MVP Implementation** (backend/api/main.py, line 141):
```python
# WARNING: For demo only - generating wallets in backend
lender_wallet = Wallet.create()  # Should come from frontend

# Production: Accept signed transaction from frontend
# def create_pool(signed_tx: str, db: Session):
#     validated_tx = verify_signature(signed_tx)
#     submit_to_xrpl(validated_tx)
```

**XUMM SDK Integration** (frontend + backend/services/xumm_service.py):
```python
# Backend generates payment request
def create_payment_request(amount, destination):
    payload = {
        "txjson": {
            "TransactionType": "Payment",
            "Destination": destination,
            "Amount": str(amount * 1_000_000)  # Convert to drops
        }
    }
    return xumm_client.payload.create(payload)

# Frontend shows QR code for XUMM app
# User scans → Signs in XUMM → Backend receives webhook
```

---

### 3. Input Validation and SQL Injection Prevention

**Pydantic Models** (backend/api/main.py, line 82):
```python
class LendingPoolCreate(BaseModel):
    name: str
    amount: float
    interest_rate: float
    max_term_days: int
    min_loan_amount: float
    lender_address: str

    # Automatic validation:
    # - Type checking (float, int, str)
    # - Required fields (no nulls)
    # - Regex patterns for addresses (can add)
```

**SQLAlchemy ORM** (prevents SQL injection):
```python
# SAFE: Parameterized query
pool = db.query(Pool).filter_by(pool_address=pool_id).first()

# UNSAFE (never used in codebase):
# db.execute(f"SELECT * FROM pools WHERE pool_address = '{pool_id}'")
```

**Database Check Constraints** (backend/models/database.py):
```python
__table_args__ = (
    CheckConstraint('current_balance >= 0', name='check_current_balance_positive'),
    CheckConstraint('principal > 0', name='check_principal_positive'),
    CheckConstraint("state IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')",
                    name='check_application_state'),
)
```

---

### 4. Rate Limiting (Recommended for Production)

**Current State**: Not implemented (MVP)

**Production Implementation**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/pools")
@limiter.limit("10/minute")  # 10 pool creations per minute per IP
async def create_lending_pool(...):
    pass

@app.post("/loans/apply")
@limiter.limit("20/minute")  # 20 applications per minute
async def apply_for_loan(...):
    pass
```

**XRPL-Level Rate Limiting**:
- Transaction fees scale with ledger load (natural economic rate limit)
- Account reserve requirements (20 XRP minimum) deter spam

---

### 5. Secrets Management

**Environment Variables** (.env):
```bash
# Database
SUPABASE_URL=https://sspwpkhajtooztzisioo.supabase.co
SUPABASE_DB_PASSWORD=***REDACTED***

# XUMM (for wallet signing)
XUMM_API_KEY=***REDACTED***
XUMM_API_SECRET=***REDACTED***

# JWT (for Auth0 integration)
JWT_SECRET_KEY=***REDACTED***
```

**Never Committed**:
- `.env` in `.gitignore`
- All secrets loaded via `os.getenv()`
- Production: AWS Secrets Manager or HashiCorp Vault

**Current Security Vulnerability** (MVP demo only):
```python
# backend/api/main.py (lines 190, 304, 417)
return {
    "wallet_seed": lender_wallet.seed  # WARNING: Only for demo!
}
# Production: NEVER return private keys from API
```

---

### 6. CORS Configuration

**Backend CORS Setup** (backend/api/main.py, line 53):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Production: Restrict to actual domains
# allow_origins=["https://lendx.app", "https://www.lendx.app"]
```

---

### 7. Row-Level Security (RLS)

**Current State**: Disabled (MVP uses application-level authorization)

**Future Implementation** (Supabase RLS policies):
```sql
-- Users can only see their own applications
CREATE POLICY "Users view own applications"
ON applications FOR SELECT
USING (auth.uid() = borrower_address);

-- Lenders can see applications for their pools
CREATE POLICY "Lenders view pool applications"
ON applications FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM pools
        WHERE pools.pool_address = applications.pool_address
        AND pools.issuer_address = auth.uid()
    )
);
```

---

## API Architecture

### RESTful Endpoint Design

**Base URL**: `http://localhost:8000` (development)

**API Versioning**: `/api/v1/...` (planned, not yet implemented)

### Endpoint Categories

#### 1. Pool Management

| Endpoint          | Method | Description                | Auth Required |
|-------------------|--------|----------------------------|---------------|
| `/pools`          | POST   | Create new lending pool    | No (MVP)      |
| `/pools`          | GET    | List all pools             | No            |
| `/pools/{id}`     | GET    | Get pool details           | No            |

**Example Request**:
```json
POST /pools
{
  "name": "Emergency Loans",
  "amount": 10000,
  "interest_rate": 5.0,
  "max_term_days": 90,
  "min_loan_amount": 100,
  "lender_address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
}
```

**Example Response**:
```json
{
  "pool_id": "00001234ABCD...",
  "pool_address": "00001234ABCD...",
  "tx_hash": "E3B0C44298FC1C14...",
  "explorer_url": "https://testnet.xrpl.org/transactions/E3B0...",
  "wallet_address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "wallet_seed": "sEdV1FGRq7K5JWmC..."  // WARNING: Demo only!
}
```

---

#### 2. Loan Application Lifecycle

| Endpoint                     | Method | Description                | Auth Required |
|------------------------------|--------|----------------------------|---------------|
| `/loans/apply`               | POST   | Submit loan application    | No (MVP)      |
| `/loans/applications`        | GET    | List applications (filter by pool) | No   |
| `/loans/{id}/approve`        | POST   | Approve/reject application | No (MVP)      |
| `/loans/active`              | GET    | List active loans (filter by user) | No    |
| `/api/loans?mode=borrower`   | GET    | Get loans by role          | No            |

**Example Application**:
```json
POST /loans/apply
{
  "pool_id": "00001234ABCD...",
  "amount": 500,
  "term_days": 30,
  "purpose": "Medical bills",
  "borrower_address": "rABC123...",
  "offered_rate": 5.0
}
```

**Example Approval**:
```json
POST /loans/00005678EFGH.../approve
{
  "loan_id": "00005678EFGH...",
  "approved": true,
  "lender_address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
}
```

---

#### 3. Authentication Endpoints

| Endpoint               | Method | Description                | Auth Required |
|------------------------|--------|----------------------------|---------------|
| `/api/auth/signup`     | POST   | Create user with DID       | No            |
| `/api/auth/verify/{address}` | GET | Verify user and get DID | No            |

**Example Signup**:
```json
POST /api/auth/signup
{
  "username": "alice"  // Optional for MVP
}

Response:
{
  "address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "did": "did:xrpl:1:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "seed": "sEdV1FGRq7K5JWmC...",  // WARNING: Demo only!
  "explorer_url": "https://testnet.xrpl.org/accounts/rN7n...",
  "message": "User created successfully with DID on XRPL testnet"
}
```

---

#### 4. RLUSD Stablecoin Operations

| Endpoint                          | Method | Description                | Auth Required |
|-----------------------------------|--------|----------------------------|---------------|
| `/api/rlusd/setup`                | POST   | Create RLUSD trustline     | No (MVP)      |
| `/api/rlusd/balance/{address}`    | GET    | Get RLUSD balance          | No            |
| `/api/rlusd/check-trustline/{address}` | GET | Check trustline status | No            |
| `/api/rlusd/transfer`             | POST   | Transfer RLUSD             | No (MVP)      |
| `/api/rlusd/info`                 | GET    | Get RLUSD configuration    | No            |

**RLUSD Configuration**:
```json
GET /api/rlusd/info

{
  "rlusd_issuer": "rpypVpiKneAn5WUmweAWU7kHX3eB9F8aVK",
  "rlusd_currency": "RLUSD",
  "network": "testnet",
  "description": "Ripple USD stablecoin on XRP Ledger",
  "requires_trustline": true
}
```

---

### Error Response Format

**Consistent Structure**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Insufficient funds in pool",
    "details": {
      "requested_amount": 500,
      "available_balance": 300,
      "pool_address": "00001234ABCD..."
    }
  }
}
```

**HTTP Status Codes**:
- `200`: Success
- `201`: Created (new pool, loan, user)
- `400`: Validation error (insufficient balance, invalid state transition)
- `404`: Not found (pool, application, loan)
- `500`: Internal server error (XRPL connection failure, database error)

---

### Request/Response Middleware

**CORS** (line 53):
- Allows `localhost:3000` and `localhost:3001` (frontend dev servers)
- Credentials enabled for future cookie-based auth

**Logging** (backend/api/main.py):
```python
logger.info(f"Created pool {pool_address} for lender {lender_wallet.classic_address}")
logger.error(f"Error creating pool: {e}")
```

**Dependency Injection** (database sessions):
```python
@app.post("/pools")
async def create_lending_pool(
    pool_data: LendingPoolCreate,
    db: Session = Depends(get_db)  # Automatic session management
):
    # db session auto-closed after request
```

---

## Settlement Algorithm

**Note**: The graph-based settlement algorithm is described in docs/DEVELOPMENT.md but not yet fully implemented in the codebase. Below is the architectural design.

### Problem Statement

**Scenario**: Multiple interconnected loans create circular debts

```
Example:
  Alice lends $100 to Bob
  Bob lends $100 to Charlie
  Charlie lends $100 to Alice

Without optimization:
  3 transactions needed (3 × gas fees + processing time)

With cycle reduction:
  0 transactions needed (cycle nets to zero)
```

### Graph Representation

**Data Structure**:
```python
# Directed graph where edges represent debts
class Edge:
    debtor: str       # "rABC..." (borrower address)
    creditor: str     # "rDEF..." (lender address)
    amount: Decimal   # Loan amount

class Graph:
    edges: List[Edge]
    vertices: Set[str]  # All unique addresses
```

**Graph Construction**:
```python
def build_debt_graph(loans: List[Loan]) -> Graph:
    """Build debt graph from active loans."""
    graph = Graph(edges=[], vertices=set())

    for loan in loans:
        if loan.state == 'ONGOING':
            edge = Edge(
                debtor=loan.borrower_address,
                creditor=loan.lender_address,
                amount=loan.total_amount_due()
            )
            graph.edges.append(edge)
            graph.vertices.update([loan.borrower_address, loan.lender_address])

    return graph
```

### Cycle Detection Algorithm

**Depth-First Search (DFS)**:
```python
def detect_cycles(graph: Graph) -> List[List[str]]:
    """Find all cycles in debt graph using DFS."""
    visited = set()
    rec_stack = []
    cycles = []

    def dfs(node: str, path: List[str]):
        if node in rec_stack:
            # Cycle found - extract cycle path
            cycle_start = rec_stack.index(node)
            cycle = rec_stack[cycle_start:] + [node]
            cycles.append(cycle)
            return

        if node in visited:
            return

        visited.add(node)
        rec_stack.append(node)

        # Explore neighbors (creditors of this debtor)
        for edge in graph.edges:
            if edge.debtor == node:
                dfs(edge.creditor, path + [edge.creditor])

        rec_stack.pop()

    for vertex in graph.vertices:
        dfs(vertex, [vertex])

    return cycles
```

### Cycle Reduction Algorithm

**Approach**: Subtract minimum cycle amount from all edges in cycle

```python
def reduce_cycle(graph: Graph, cycle: List[str]) -> Graph:
    """Eliminate or reduce a debt cycle."""
    # Find edges in cycle
    cycle_edges = []
    for i in range(len(cycle) - 1):
        debtor = cycle[i]
        creditor = cycle[i + 1]
        edge = find_edge(graph, debtor, creditor)
        if edge:
            cycle_edges.append(edge)

    # Find minimum amount in cycle
    min_amount = min(edge.amount for edge in cycle_edges)

    # Reduce all cycle edges by minimum amount
    for edge in cycle_edges:
        edge.amount -= min_amount

    # Remove zero-amount edges
    graph.edges = [e for e in graph.edges if e.amount > 0]

    return graph
```

**Example**:
```
Before reduction:
  A → B: $100
  B → C: $100
  C → A: $100

After reduction:
  (All edges reduced to $0 and removed)
```

### Net Balance Computation

**After cycle reduction, compute net balances**:

```python
def compute_net_balances(graph: Graph) -> Dict[str, Decimal]:
    """Compute net balance for each address (inflows - outflows)."""
    balances = {vertex: Decimal(0) for vertex in graph.vertices}

    for edge in graph.edges:
        balances[edge.creditor] += edge.amount   # Owed to them (inflow)
        balances[edge.debtor] -= edge.amount     # Owed by them (outflow)

    return balances
```

**Example**:
```
Edges:
  A → B: $50
  C → B: $30
  B → D: $20

Net balances:
  A: -$50 (owes money)
  B: +$60 (owed money: $50 + $30 - $20)
  C: -$30 (owes money)
  D: +$20 (owed money)
```

### Escrow Instruction Generation

**Generate minimal transfers to settle net balances**:

```python
def generate_escrow_instructions(
    net_balances: Dict[str, Decimal]
) -> List[EscrowInstruction]:
    """Create escrow instructions for settlement."""
    debtors = {addr: -bal for addr, bal in net_balances.items() if bal < 0}
    creditors = {addr: bal for addr, bal in net_balances.items() if bal > 0}

    instructions = []

    # Match debtors with creditors
    for debtor, debt_amount in debtors.items():
        for creditor, credit_amount in list(creditors.items()):
            if debt_amount <= 0:
                break

            transfer_amount = min(debt_amount, credit_amount)

            instruction = EscrowInstruction(
                from_address=debtor,
                to_address=creditor,
                amount=transfer_amount,
                condition="settlement_approved"  # Multi-sig condition
            )
            instructions.append(instruction)

            # Update remaining balances
            debt_amount -= transfer_amount
            creditors[creditor] -= transfer_amount

            if creditors[creditor] == 0:
                del creditors[creditor]

    return instructions
```

### Multi-Signature Settlement Proposal

**Settlement Flow**:

```
1. Generate settlement proposal (escrow instructions)
2. Create unsigned XRPL transactions for each instruction
3. Collect signatures from all parties:
   - Debtors sign to authorize transfer
   - Creditors sign to accept funds
4. When quorum reached (REQUIRED_SIGNATURES = 2):
   - Submit all transactions to XRPL
   - Execute escrow releases atomically
5. Update loan states to PAID
```

**Code Structure**:
```python
class SettlementProposal:
    proposal_id: str
    escrow_instructions: List[EscrowInstruction]
    unsigned_transactions: List[Transaction]
    signatures: Dict[str, List[str]]  # address → list of signatures
    status: str  # PENDING, APPROVED, EXECUTED
    created_at: datetime

def create_settlement_proposal(loans: List[Loan]) -> SettlementProposal:
    """Generate settlement proposal with minimal transactions."""
    graph = build_debt_graph(loans)
    cycles = detect_cycles(graph)

    for cycle in cycles:
        graph = reduce_cycle(graph, cycle)

    net_balances = compute_net_balances(graph)
    instructions = generate_escrow_instructions(net_balances)

    # Create unsigned transactions
    transactions = [
        create_deposit_escrow(
            source=instr.from_address,
            destination=instr.to_address,
            amount=instr.amount
        )
        for instr in instructions
    ]

    return SettlementProposal(
        proposal_id=generate_id(),
        escrow_instructions=instructions,
        unsigned_transactions=transactions,
        signatures={},
        status="PENDING"
    )
```

### Performance Characteristics

**Time Complexity**:
- Cycle detection: O(V + E) where V = vertices, E = edges
- Cycle reduction: O(C × E) where C = number of cycles
- Net balance computation: O(E)
- Escrow generation: O(D × C) where D = debtors, C = creditors

**Space Complexity**:
- Graph storage: O(V + E)
- Cycle storage: O(C × L) where L = average cycle length

**Scalability**:
- Efficiently handles up to ~1000 concurrent loans
- For larger scales, consider batch processing or sharding

---

## Technology Stack

### Frontend Stack

| Technology        | Version | Purpose                                    |
|-------------------|---------|-------------------------------------------|
| **Next.js**       | 14.2.x  | React framework with App Router           |
| **React**         | 18.3.x  | UI component library                      |
| **TypeScript**    | 5.x     | Type-safe JavaScript                      |
| **Tailwind CSS**  | 3.4.x   | Utility-first CSS framework               |
| **shadcn/ui**     | Latest  | Radix UI component library                |
| **Radix UI**      | Latest  | Headless UI primitives                    |
| **Framer Motion** | 11.x    | Animation library                         |
| **Zustand**       | 4.x     | Lightweight state management              |
| **React Hook Form**| 7.x    | Form validation and management            |
| **Zod**           | 3.x     | Schema validation                         |
| **xrpl**          | 4.4.2   | Native XRPL JavaScript library            |
| **xumm-sdk**      | 1.11.2  | XUMM wallet integration                   |
| **Recharts**      | 2.x     | Chart library for data visualization      |

**Build Tools**:
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher (with `--legacy-peer-deps` flag required)

---

### Backend Stack

| Technology        | Version | Purpose                                    |
|-------------------|---------|-------------------------------------------|
| **Python**        | 3.11+   | Backend programming language              |
| **FastAPI**       | 0.115.x | Modern async web framework                |
| **SQLAlchemy**    | 2.0.x   | Database ORM                              |
| **Pydantic**      | 2.x     | Data validation and serialization         |
| **xrpl-py**       | 2.x     | Official XRPL Python SDK                  |
| **psycopg2**      | 2.9.x   | PostgreSQL adapter                        |
| **pytest**        | 8.x     | Testing framework                         |
| **uvicorn**       | 0.30.x  | ASGI server                               |

**Development Tools**:
- **Black**: Code formatter
- **Flake8**: Linter
- **mypy**: Type checker (optional)

---

### Database

| Technology          | Version | Purpose                                    |
|---------------------|---------|-------------------------------------------|
| **PostgreSQL**      | 15+     | Primary relational database               |
| **Supabase**        | Cloud   | Managed PostgreSQL with real-time features|

---

### Blockchain

| Technology          | Version | Purpose                                    |
|---------------------|---------|-------------------------------------------|
| **XRPL**            | Latest  | XRP Ledger blockchain                     |
| **XRPL Testnet**    | -       | Development and testing environment       |
| **XRPL Mainnet**    | -       | Production blockchain network             |

**XRPL Features Used**:
- Multi-Purpose Tokens (MPT)
- Decentralized Identifiers (DID)
- Escrow
- Multi-signature accounts
- RLUSD (Ripple USD stablecoin)

---

### Infrastructure

| Component         | Technology         | Purpose                         |
|-------------------|--------------------|---------------------------------|
| **API Server**    | FastAPI + Uvicorn  | Backend REST API                |
| **Web Server**    | Next.js Dev Server | Frontend development server     |
| **Database**      | Supabase           | Managed PostgreSQL              |
| **Blockchain RPC**| XRPL JSON-RPC      | XRPL transaction submission     |
| **WebSocket**     | XRPL WebSocket     | Real-time ledger updates        |

**Production Deployment** (Recommended):
- **Frontend**: Vercel (optimized for Next.js)
- **Backend**: AWS ECS or Google Cloud Run (containerized FastAPI)
- **Database**: Supabase (already in use)
- **CDN**: Cloudflare (for static assets)

---

## Appendix: Key File References

### Backend

- **API Server**: `backend/api/main.py` (825 lines)
- **Authentication**: `backend/api/auth.py` (153 lines)
- **Database Models**: `backend/models/database.py` (353 lines)
- **XRPL Client**: `backend/xrpl_client/client.py` (163 lines)
- **MPT Operations**: `backend/xrpl_client/mpt.py` (307 lines)
- **Database Config**: `backend/config/database.py`
- **MPT Service**: `backend/services/mpt_service.py`
- **DID Service**: `backend/services/did_service.py`

### Frontend

- **Dashboard**: `frontend/app/(dashboard)/dashboard/page.tsx` (25 lines)
- **Lender View**: `frontend/components/lendx/lender-view.tsx`
- **Borrower View**: `frontend/components/lendx/borrower-view.tsx`
- **Demo Context**: `frontend/lib/demo-context.tsx`

### Configuration

- **Project Guide**: `docs/DEVELOPMENT.md` (comprehensive technical overview)
- **Environment Template**: `.env.example`
- **Database Migration**: `backend/migrations/001_initial_schema.sql`

---

## Future Architecture Enhancements

### 1. Authentication Upgrade
- Auth0 integration for OAuth 2.0
- JWT-based API authentication
- Refresh token rotation

### 2. Real-Time Updates
- WebSocket subscriptions for all XRPL events
- Server-Sent Events (SSE) for balance updates
- Optimistic UI updates with rollback on failure

### 3. Scalability
- Redis caching layer (MPT balances, pool data)
- Horizontal scaling with load balancers
- Database read replicas for analytics queries

### 4. Advanced Features
- Loan repayment tracking (partial payments)
- Automated default detection and collateral claiming
- Credit scoring system (DID-based reputation)
- Secondary market for loan trading (requires transferable MPTs)

### 5. Compliance and Regulatory
- KYC/AML integration
- Regional restrictions and compliance checks
- Audit logs for all financial transactions

---

**Document Version**: 1.0
**Last Updated**: 2025-10-26
**Maintainers**: LendX Development Team
**License**: MIT (or as specified in project)
