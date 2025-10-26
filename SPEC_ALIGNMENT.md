# LendX Product Specification Alignment Analysis

**Date**: 2025-10-26
**Status**: 🔴 CRITICAL GAPS - Major architectural changes required

---

## Executive Summary

The current implementation has **~20% alignment** with the product specification. While the foundational XRPL client is strong, the **core MPT-based lending architecture is completely missing**. The spec envisions an on-chain, token-based lending system, but the current code uses off-chain tracking with in-memory storage.

**Critical Finding**: The product spec describes using **4 different MPT types** (LoanMPT, ApplicationMPT, PoolMPT, DefaultMPT) as the core data layer, but the current implementation uses **zero MPTs** in the lending flow.

---

## 1. WALLET REPRESENTATION

### Specification
```
Representing Wallets:
- Create our own XRP wallet
- Amount in wallet is just RLUSD?
```

### Current Implementation
- ✅ XRPL wallet creation supported (via xrpl-py Wallet.create())
- ❌ No RLUSD integration
- ❌ No wallet creation in frontend (missing @/lib/xrpl)
- ❌ Xumm SDK imported but not used

### Gap Analysis
**Status**: 🔴 NOT IMPLEMENTED

**Required Changes**:
1. Implement RLUSD trust line setup for wallets
2. Create wallet generation flow in frontend
3. Store wallet seeds securely (encrypted or hardware wallet)
4. Add RLUSD balance queries to backend API
5. Implement Xumm wallet connection for mobile users

**RLUSD Context**: RLUSD is Ripple's USD stablecoin on XRPL. Need to:
- Create trust lines from user wallets to RLUSD issuer
- Handle RLUSD payment transactions instead of XRP
- Query RLUSD balances via account_lines API

---

## 2. ON-CHAIN EVENTS (TESTNET DEMO REQUIREMENTS)

### Specification
```
On chain events (these need to be proven on the testnet demo):
- Creating LoanMPT
- Creating ApplicationMPT
- Creating PoolMPT
- XRP Transactions themselves
- Approving
```

### Current Implementation

| Event | Backend Capability | Frontend Integration | On-Chain Status |
|-------|-------------------|---------------------|----------------|
| Creating LoanMPT | ❌ Not implemented | ❌ Not implemented | ❌ Never created |
| Creating ApplicationMPT | ❌ Not implemented | ❌ Not implemented | ❌ Never created |
| Creating PoolMPT | ❌ Not implemented | ❌ Not implemented | ❌ Never created |
| XRP Transactions | ✅ submit_and_wait() | ❌ Missing wallet lib | ⚠️ Backend only |
| Approving | ❌ Not on-chain | ❌ Local state only | ❌ Not on-chain |

### Gap Analysis
**Status**: 🔴 CRITICAL - 0% of required on-chain events implemented

**Current Situation**:
- Backend has generic MPT functions (create_issuance, mint_to_holder)
- **NONE are used for lending operations**
- Lending pools stored in Python dictionary, not as MPTs
- Loan applications stored in Python dictionary, not as MPTs
- Approvals just update Python dictionaries

**Required Implementation**:

#### A. PoolMPT Creation
```python
# When lender creates pool in POST /api/pool
def create_pool_mpt(lender_wallet, pool_config):
    # 1. Create MPT issuance for this pool
    mpt_id = create_issuance(
        client,
        lender_wallet,
        ticker="POOL",
        metadata={
            "totalBalance": pool_config.amount,
            "interestRate": pool_config.interest_rate,
            "duration": pool_config.duration,
            "minLoan": pool_config.min_loan
        }
    )
    # 2. Store MPT ID in database
    # 3. Return pool address (MPT ID)
```

#### B. ApplicationMPT Creation
```python
# When borrower applies for loan in POST /api/application
def create_application_mpt(borrower_wallet, pool_mpt_id, application_data):
    # 1. Create MPT issuance for this application
    app_mpt_id = create_issuance(
        client,
        borrower_wallet,
        ticker="APP",
        metadata={
            "poolAddress": pool_mpt_id,
            "principal": application_data.principal,
            "interest": application_data.interest,
            "state": "PENDING"
        }
    )
    # 2. Authorize holder (pool issuer) to hold this MPT
    # 3. Return application address
```

#### C. LoanMPT Creation (on approval)
```python
# When lender approves in PUT /api/application
def approve_application_create_loan(lender_wallet, application_mpt_id):
    # 1. Verify ApplicationMPT state == PENDING
    # 2. Create LoanMPT issuance
    loan_mpt_id = create_issuance(
        client,
        lender_wallet,
        ticker="LOAN",
        metadata={
            "poolAddress": pool_mpt_id,
            "borrowerAddress": borrower_address,
            "lenderAddress": lender_address,
            "startDate": now,
            "endDate": now + duration,
            "principal": principal,
            "interest": interest,
            "state": "ONGOING"
        }
    )
    # 3. Mint LOAN tokens to borrower
    # 4. Update ApplicationMPT state to APPROVED
    # 5. Disburse RLUSD from pool to borrower
```

#### D. DefaultMPT Creation
```python
# When loan defaults
def trigger_default(loan_mpt_id):
    # 1. Update LoanMPT metadata state to DEFAULTED
    # 2. Create DefaultMPT or mint existing DefaultMPT to borrower
    mint_to_holder(
        client,
        default_issuer_wallet,
        borrower_address,
        amount=principal + interest,
        issuance_id=default_mpt_id
    )
```

**Testnet Demo Checklist**:
- [ ] Create lender wallet and fund with test XRP
- [ ] Create RLUSD trust line for lender
- [ ] Create PoolMPT on-chain with visible metadata
- [ ] Create borrower wallet and DID
- [ ] Create ApplicationMPT on-chain linking to PoolMPT
- [ ] Approve application → creates LoanMPT on-chain
- [ ] Verify all MPT transactions in XRPL explorer
- [ ] Trigger default → creates DefaultMPT on-chain
- [ ] Query all MPT balances and metadata from ledger

---

## 3. DEFAULT INTERFACE

### Specification
```
Default Interface:
- On triggering of 'Default' event, DefaultMPT tokens sent to borrower
  with amount = principal + interest
- If loan MPT state=='DEFAULTED', paying off the loan should be disabled
```

### Current Implementation
- ❌ No default mechanism exists
- ❌ No DefaultMPT concept
- ❌ No loan state tracking on-chain
- ❌ No payment blocking logic

### Gap Analysis
**Status**: 🔴 NOT IMPLEMENTED

**Required Changes**:

1. **DefaultMPT Issuance Setup**
```python
# Global DefaultMPT issuance (one per system)
DEFAULT_MPT_ID = create_issuance(
    client,
    system_wallet,
    ticker="DEFAULT",
    name="LendX Default Token",
    flags=lsfMPTNonTransferable  # Only issuer can transfer
)
```

2. **Default Trigger Logic**
```python
def check_and_trigger_defaults():
    """Cron job to check expired loans"""
    current_time = time.time()

    for loan_id, loan in active_loans.items():
        # Get on-chain LoanMPT metadata
        loan_mpt = get_mpt_metadata(client, loan_id)

        if current_time > loan_mpt.endDate and loan_mpt.state == "ONGOING":
            # Mint DefaultMPT to borrower
            default_amount = loan_mpt.principal + loan_mpt.interest
            mint_to_holder(
                client,
                system_wallet,
                loan_mpt.borrowerAddress,
                default_amount,
                DEFAULT_MPT_ID
            )

            # Update LoanMPT state to DEFAULTED
            update_mpt_metadata(client, loan_id, {"state": "DEFAULTED"})
```

3. **Payment Blocking**
```python
@app.post("/loans/{loan_id}/pay")
async def make_loan_payment(loan_id: str, payment: PaymentRequest):
    # Get on-chain loan state
    loan_mpt = get_mpt_metadata(client, loan_id)

    if loan_mpt.state == "DEFAULTED":
        raise HTTPException(
            status_code=403,
            detail="Cannot make payment on defaulted loan. Loan is permanently closed."
        )

    # Process payment...
```

4. **DefaultMPT Balance Display**
```python
@app.get("/api/verify")
async def get_user_metadata(address: str):
    # Query DefaultMPT balance from ledger
    default_balance = get_mpt_balance(client, address, DEFAULT_MPT_ID)

    return {
        "did": get_did_document(client, address),
        "defaultMPTBalance": default_balance
    }
```

---

## 4. MPT DATA STRUCTURES

### Specification

The spec defines **4 MPT types** with specific metadata fields:

#### LoanMPT
```
PoolAddr
BorrowerAddr
LenderAddr
StartDate
EndDate
Principal
Interest
State: Enum{ONGOING, PAID, DEFAULTED}
```

#### ApplicationMPT
```
BorrowerAddr
PoolAddr
ApplicationDate
DissolutionDate
State: Enum{APPROVED, REJECTED, EXPIRED}
Principal
Interest
```

#### PoolMPT
```
IssuerAddr
TotalBalance
CurrentBalance
MinimumLoan
Duration
InterestRate
```

#### DefaultMPT
```
borrowerAddr
```

### Current Implementation

**MPT Storage on XRPL**:
- ✅ MPT metadata can store arbitrary JSON (up to ~256KB)
- ❌ None of these MPT types exist in current code
- ❌ No metadata schema defined
- ❌ No on-chain storage of lending data

**Current Data Storage**:
```python
# backend/api/main.py - IN-MEMORY ONLY
lending_pools: Dict[str, dict] = {}      # Should be PoolMPT
loan_applications: Dict[str, dict] = {}  # Should be ApplicationMPT
active_loans: Dict[str, dict] = {}       # Should be LoanMPT
```

### Gap Analysis
**Status**: 🔴 ARCHITECTURE MISMATCH

**Current**: Off-chain data in Python dictionaries
**Required**: On-chain data in MPT metadata

**Migration Path**:

1. **Define MPT Metadata Schemas**
```python
# backend/models/mpt_schemas.py
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class LoanState(str, Enum):
    ONGOING = "ONGOING"
    PAID = "PAID"
    DEFAULTED = "DEFAULTED"

class ApplicationState(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class LoanMPTMetadata(BaseModel):
    poolAddr: str
    borrowerAddr: str
    lenderAddr: str
    startDate: datetime
    endDate: datetime
    principal: float
    interest: float
    state: LoanState

class ApplicationMPTMetadata(BaseModel):
    borrowerAddr: str
    poolAddr: str
    applicationDate: datetime
    dissolutionDate: datetime
    state: ApplicationState
    principal: float
    interest: float

class PoolMPTMetadata(BaseModel):
    issuerAddr: str
    totalBalance: float
    currentBalance: float
    minimumLoan: float
    duration: int  # days
    interestRate: float  # percentage
```

2. **Implement MPT CRUD Operations**
```python
# backend/services/mpt_service.py
def create_pool_mpt(issuer_wallet, metadata: PoolMPTMetadata) -> str:
    """Create PoolMPT and return MPT ID"""
    mpt_id = create_issuance(
        client,
        issuer_wallet,
        ticker="POOL",
        metadata=metadata.dict()
    )
    return mpt_id

def get_pool_mpt(mpt_id: str) -> PoolMPTMetadata:
    """Read PoolMPT metadata from ledger"""
    ledger_data = get_mpt_metadata(client, mpt_id)
    return PoolMPTMetadata(**ledger_data)

def update_pool_mpt(mpt_id: str, updates: dict):
    """Update PoolMPT metadata (requires re-issue or memo)"""
    # Note: MPT metadata is immutable after creation!
    # Need to use NFTs or another mechanism for mutable state
    # OR create new version and burn old one
```

**CRITICAL ISSUE**: MPT metadata is **immutable** after issuance creation!

**Solutions**:
1. **Use NFTs instead**: NFTs have mutable URIs that can point to updated metadata
2. **Versioning**: Create new MPT issuance when state changes, burn old one
3. **Hybrid**: Store immutable data in MPT, mutable state in database
4. **XRPL Memos**: Store state updates as transaction memos

**Recommended Approach**:
- **Immutable data in MPT metadata**: poolAddr, borrowerAddr, principal, startDate
- **Mutable state in memo transactions**: loan state, current balance, payments
- **Index memos**: Backend indexes memos to reconstruct current state

---

## 5. DATABASE STRUCTURES

### Specification
```
Database structs:
User(userAddress, pool[], application[], loan[], defaultMPTBalance)
Pool(poolAddress, application[], loan[])
Application(borrowerAddress, poolAddress, applicationDate, dissolutionDate, state, principal, interest)
Loan(poolAddress, borrowerAddress, lenderAddress, startDate, endDate, principal, interest, state)
```

### Current Implementation
- ❌ **NO DATABASE**
- ✅ In-memory dictionaries with similar structure
- ❌ No persistence across restarts
- ❌ No relationships/foreign keys
- ❌ No indexing

### Gap Analysis
**Status**: 🔴 CRITICAL - No persistence layer

**Required Changes**:

1. **Choose Database**: PostgreSQL recommended (relational data, good JSON support)

2. **Schema Definition**
```sql
-- users table
CREATE TABLE users (
    address VARCHAR(34) PRIMARY KEY,  -- XRP address
    did VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- pools table (indexes PoolMPT data)
CREATE TABLE pools (
    pool_address VARCHAR(66) PRIMARY KEY,  -- MPT ID
    issuer_address VARCHAR(34) REFERENCES users(address),
    total_balance DECIMAL(20,6),
    current_balance DECIMAL(20,6),
    minimum_loan DECIMAL(20,6),
    duration_days INTEGER,
    interest_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    tx_hash VARCHAR(64)  -- XRPL transaction hash
);

-- applications table (indexes ApplicationMPT data)
CREATE TABLE applications (
    application_address VARCHAR(66) PRIMARY KEY,  -- MPT ID
    borrower_address VARCHAR(34) REFERENCES users(address),
    pool_address VARCHAR(66) REFERENCES pools(pool_address),
    application_date TIMESTAMP,
    dissolution_date TIMESTAMP,
    state VARCHAR(20),  -- APPROVED, REJECTED, EXPIRED
    principal DECIMAL(20,6),
    interest DECIMAL(20,6),
    tx_hash VARCHAR(64)
);

-- loans table (indexes LoanMPT data)
CREATE TABLE loans (
    loan_address VARCHAR(66) PRIMARY KEY,  -- MPT ID
    pool_address VARCHAR(66) REFERENCES pools(pool_address),
    borrower_address VARCHAR(34) REFERENCES users(address),
    lender_address VARCHAR(34) REFERENCES users(address),
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    principal DECIMAL(20,6),
    interest DECIMAL(20,6),
    state VARCHAR(20),  -- ONGOING, PAID, DEFAULTED
    tx_hash VARCHAR(64)
);

-- user_mpt_balances (cache of on-chain balances)
CREATE TABLE user_mpt_balances (
    user_address VARCHAR(34) REFERENCES users(address),
    mpt_id VARCHAR(66),
    balance DECIMAL(20,6),
    last_synced TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_address, mpt_id)
);

-- indexes for common queries
CREATE INDEX idx_pools_issuer ON pools(issuer_address);
CREATE INDEX idx_applications_borrower ON applications(borrower_address);
CREATE INDEX idx_applications_pool ON applications(pool_address);
CREATE INDEX idx_loans_borrower ON loans(borrower_address);
CREATE INDEX idx_loans_lender ON loans(lender_address);
CREATE INDEX idx_loans_pool ON loans(pool_address);
```

3. **ORM Setup** (using SQLAlchemy)
```python
# backend/models/database.py
from sqlalchemy import create_engine, Column, String, Numeric, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    address = Column(String(34), primary_key=True)
    did = Column(String(255), unique=True)
    created_at = Column(DateTime)

    pools = relationship("Pool", back_populates="issuer")
    applications = relationship("Application", back_populates="borrower")
    loans_as_borrower = relationship("Loan", foreign_keys="Loan.borrower_address")
    loans_as_lender = relationship("Loan", foreign_keys="Loan.lender_address")

class Pool(Base):
    __tablename__ = 'pools'
    pool_address = Column(String(66), primary_key=True)
    issuer_address = Column(String(34), ForeignKey('users.address'))
    # ... other fields

    issuer = relationship("User", back_populates="pools")
    applications = relationship("Application", back_populates="pool")
    loans = relationship("Loan", back_populates="pool")
```

4. **Sync Strategy**: Database as index/cache of on-chain data
   - When MPT created → insert into database
   - When MPT updated → update database
   - On startup → sync database from XRPL ledger
   - Periodic sync job to catch missed updates

---

## 6. API ROUTES ALIGNMENT

### User Level Routes

| Route | Spec | Current | Status | Notes |
|-------|------|---------|--------|-------|
| GET /api/loans?mode={borrower\|lender} | ✅ Required | ❌ Missing | 🔴 | Need to implement |
| GET /api/pools | ✅ Required | ✅ Exists | 🟡 | Missing user filter |
| GET /api/applications?mode={borrower\|lender} | ✅ Required | ⚠️ Partial | 🟡 | Exists but wrong structure |
| GET /api/verify?address={} | ✅ Required | ❌ Missing | 🔴 | Need DID integration |

### Global Level Routes

| Route | Spec | Current | Status | Notes |
|-------|------|---------|--------|-------|
| GET /api/pools | ✅ Required | ✅ Exists | ✅ | Working |
| GET /api/pool?poolAddress={} | ✅ Required | ✅ Exists | 🟡 | Missing applications/loans |
| POST /api/pool | ✅ Required | ✅ Exists | 🔴 | Not creating MPT |
| POST /api/application?poolAddress={} | ✅ Required | ⚠️ Partial | 🔴 | Not creating MPT |
| PUT /api/application?poolAddress={} | ✅ Required | ❌ Missing | 🔴 | Need to implement |
| POST /api/loan?poolAddress={} | ✅ Required | ❌ Missing | 🔴 | Need to implement |
| PUT /api/loan?poolAddress={} | ✅ Required | ❌ Missing | 🔴 | Need to implement |

### Required Implementation

```python
# backend/api/main.py - Add missing routes

@app.get("/api/loans")
async def get_loans(
    mode: Literal["borrower", "lender"],
    user_address: str = Depends(get_current_user)  # Add auth
):
    """Get all loans for user as borrower or lender"""
    if mode == "borrower":
        loans = db.query(Loan).filter(Loan.borrower_address == user_address).all()
    else:
        loans = db.query(Loan).filter(Loan.lender_address == user_address).all()

    return {"loans": [loan.to_dict() for loan in loans]}

@app.get("/api/verify")
async def verify_user(address: str):
    """Retrieve user metadata including DID and default balance"""
    # Query DID from XRPL
    did_document = get_did_document(client, address)

    # Query DefaultMPT balance
    default_balance = get_mpt_balance(client, address, DEFAULT_MPT_ID)

    return {
        "did": did_document,
        "defaultMPTBalance": default_balance
    }

@app.put("/api/application")
async def update_application(
    application_id: str,
    updates: ApplicationUpdate,
    user_wallet: Wallet = Depends(get_user_wallet)
):
    """Update application (approve/reject)"""
    # Get ApplicationMPT from ledger
    app_mpt = get_mpt_metadata(client, application_id)

    if updates.state == "APPROVED":
        # Create LoanMPT
        loan_id = create_loan_from_application(user_wallet, application_id)
        return {"message": "Application approved", "loan_id": loan_id}

    elif updates.state == "REJECTED":
        # Update ApplicationMPT state (via memo or new issuance)
        update_application_state(client, user_wallet, application_id, "REJECTED")
        return {"message": "Application rejected"}
```

### Authentication Required

**All @protected routes need**:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> str:
    """Verify JWT or wallet signature and return user address"""
    # Verify token signature
    # Extract wallet address
    # Return address or raise HTTPException
    pass

async def get_user_wallet(user_address: str = Depends(get_current_user)) -> Wallet:
    """Get wallet for authenticated user"""
    # Load wallet from secure storage
    # Or use Xumm signing request
    pass
```

---

## 7. LENDER & BORROWER INTERFACES

### Specification

#### Lender Interface
```
createPool()
approveApplication(ApplicationMPT)
rejectApplication(ApplicationMPT)
```

#### Borrower Interface
```
createApplication(input details)
submitApplication() - maybe automatically triggered instead???
```

#### Internal App Interface
```
createLoan(ApplicationMPT) -> LoanMPT (triggered when approved)
Add assert to check it actually got approved
```

### Current Implementation

**Frontend Components**:
- ✅ `lender-view.tsx` has UI for all lender operations
- ✅ `borrower-view.tsx` has UI for borrower operations
- ❌ All operations are UI-only, no backend integration
- ❌ Missing `@/lib/xrpl` integration layer

**Backend API**:
- ✅ `POST /pools` for createPool
- ✅ `POST /loans/{id}/approve` for approveApplication
- ❌ No explicit rejectApplication endpoint
- ✅ `POST /loans/apply` for createApplication
- ❌ createLoan happens in approve endpoint but doesn't create MPT

### Gap Analysis
**Status**: 🟡 UI COMPLETE, BACKEND PARTIAL, INTEGRATION MISSING

**Required Implementation**:

#### 1. Lender Interface - Backend
```python
# backend/api/lender.py
from fastapi import APIRouter, Depends
from backend.services.mpt_service import create_pool_mpt, create_loan_mpt

router = APIRouter(prefix="/api/lender", tags=["lender"])

@router.post("/pool")
async def create_pool(
    pool_data: PoolCreate,
    lender_wallet: Wallet = Depends(get_user_wallet)
):
    """Create PoolMPT on-chain"""
    # 1. Create PoolMPT issuance
    pool_mpt_id = create_pool_mpt(lender_wallet, PoolMPTMetadata(
        issuerAddr=lender_wallet.address,
        totalBalance=pool_data.amount,
        currentBalance=pool_data.amount,
        minimumLoan=pool_data.min_loan,
        duration=pool_data.duration_days,
        interestRate=pool_data.interest_rate
    ))

    # 2. Store in database
    db_pool = Pool(
        pool_address=pool_mpt_id,
        issuer_address=lender_wallet.address,
        total_balance=pool_data.amount,
        current_balance=pool_data.amount,
        # ... other fields
    )
    db.add(db_pool)
    db.commit()

    return {"pool_address": pool_mpt_id, "tx_hash": "..."}

@router.post("/application/{app_id}/approve")
async def approve_application(
    app_id: str,
    lender_wallet: Wallet = Depends(get_user_wallet)
):
    """Approve application and create LoanMPT"""
    # 1. Get ApplicationMPT from ledger
    app_mpt = get_application_mpt(app_id)

    # Assert: Application must be in PENDING state
    assert app_mpt.state == "PENDING", "Application not in PENDING state"

    # 2. Create LoanMPT
    loan_mpt_id = create_loan_mpt(lender_wallet, LoanMPTMetadata(
        poolAddr=app_mpt.poolAddr,
        borrowerAddr=app_mpt.borrowerAddr,
        lenderAddr=lender_wallet.address,
        startDate=datetime.now(),
        endDate=datetime.now() + timedelta(days=duration),
        principal=app_mpt.principal,
        interest=app_mpt.interest,
        state="ONGOING"
    ))

    # 3. Update ApplicationMPT state to APPROVED
    update_application_state(client, lender_wallet, app_id, "APPROVED")

    # 4. Disburse RLUSD from pool to borrower
    disburse_loan_funds(lender_wallet, app_mpt.borrowerAddr, app_mpt.principal)

    # 5. Update pool current balance
    update_pool_balance(app_mpt.poolAddr, -app_mpt.principal)

    return {"loan_address": loan_mpt_id}

@router.post("/application/{app_id}/reject")
async def reject_application(
    app_id: str,
    reason: str,
    lender_wallet: Wallet = Depends(get_user_wallet)
):
    """Reject application"""
    # Update ApplicationMPT state to REJECTED
    update_application_state(client, lender_wallet, app_id, "REJECTED", memo=reason)
    return {"message": "Application rejected"}
```

#### 2. Borrower Interface - Backend
```python
# backend/api/borrower.py
router = APIRouter(prefix="/api/borrower", tags=["borrower"])

@router.post("/application")
async def create_application(
    pool_address: str,
    app_data: ApplicationCreate,
    borrower_wallet: Wallet = Depends(get_user_wallet)
):
    """Create and submit ApplicationMPT on-chain"""
    # 1. Validate pool exists and has sufficient funds
    pool_mpt = get_pool_mpt(pool_address)
    assert pool_mpt.currentBalance >= app_data.principal, "Insufficient pool funds"
    assert app_data.principal >= pool_mpt.minimumLoan, "Below minimum loan amount"

    # 2. Create ApplicationMPT
    app_mpt_id = create_application_mpt(borrower_wallet, ApplicationMPTMetadata(
        borrowerAddr=borrower_wallet.address,
        poolAddr=pool_address,
        applicationDate=datetime.now(),
        dissolutionDate=datetime.now() + timedelta(days=30),  # 30 days to decide
        state="PENDING",
        principal=app_data.principal,
        interest=app_data.principal * pool_mpt.interestRate / 100
    ))

    # 3. Store in database
    db_app = Application(
        application_address=app_mpt_id,
        borrower_address=borrower_wallet.address,
        pool_address=pool_address,
        # ... other fields
    )
    db.add(db_app)
    db.commit()

    # 4. Notify lender (via webhook or notification service)
    notify_lender(pool_mpt.issuerAddr, app_mpt_id)

    return {"application_address": app_mpt_id}

@router.post("/loan/{loan_id}/pay")
async def make_loan_payment(
    loan_id: str,
    amount: Decimal,
    borrower_wallet: Wallet = Depends(get_user_wallet)
):
    """Make payment on active loan"""
    # 1. Get LoanMPT from ledger
    loan_mpt = get_loan_mpt(loan_id)

    # Assert: Loan not defaulted
    assert loan_mpt.state != "DEFAULTED", "Cannot pay defaulted loan"

    # 2. Transfer RLUSD from borrower to lender
    tx_hash = transfer_rlusd(
        client,
        borrower_wallet,
        loan_mpt.lenderAddr,
        amount
    )

    # 3. Update loan balance (via memo or state update)
    remaining = loan_mpt.principal + loan_mpt.interest - amount

    if remaining <= 0:
        # Loan fully paid
        update_loan_state(client, loan_id, "PAID")
        # Burn LoanMPT tokens from borrower
        burn_loan_tokens(client, borrower_wallet.address, loan_id)

    return {"tx_hash": tx_hash, "remaining": max(0, remaining)}
```

#### 3. Frontend Integration Layer
```typescript
// frontend/lib/xrpl/index.ts
import { Client, Wallet } from 'xrpl'
import { XummSdk } from 'xumm-sdk'

const xumm = new XummSdk(
  process.env.NEXT_PUBLIC_XUMM_API_KEY!,
  process.env.NEXT_PUBLIC_XUMM_API_SECRET!
)

export function useWallet() {
  const [connected, setConnected] = useState(false)
  const [address, setAddress] = useState<string>()

  const signTransaction = async (tx: any) => {
    // Use Xumm to sign transaction
    const request = await xumm.payload.create({
      txjson: tx
    })

    // Show QR code or deep link
    window.open(request.next.always)

    // Wait for signature
    const result = await xumm.payload.subscribe(request.uuid)
    return result.payload.signed
  }

  return { connected, address, signTransaction }
}

export async function createLendingPool(poolData: PoolData) {
  // Call backend API
  const response = await fetch('/api/lender/pool', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(poolData)
  })
  return response.json()
}
```

---

## 8. VERIFIABLE CREDENTIALS & DID

### Specification
```
From Borrow Address:
Need to create some interface to access:
- Verifiable credentials
- DID
```

### Current Implementation
- ❌ No DID creation
- ❌ No VC issuance
- ❌ No VC verification
- ⚠️ Placeholder in signup flow

### XRPL DID Capabilities (from research)
- ✅ W3C DID v1.0 compliant (activated Oct 30, 2024)
- ✅ DIDCreate, DIDUpdate, DIDDelete transactions
- ✅ On-chain DID document storage
- ✅ XRPL Credentials amendment (activated Sept 4, 2025)
- ✅ W3C Verifiable Credentials 2.0 compatible

### Gap Analysis
**Status**: 🔴 NOT IMPLEMENTED (but XRPL fully supports it!)

**Required Implementation**:

#### 1. DID Creation (Signup Flow)
```python
# backend/services/did_service.py
from xrpl.models import DIDSet

def create_did_for_user(user_wallet: Wallet) -> str:
    """Create on-chain DID for user"""
    did_tx = DIDSet(
        account=user_wallet.address,
        uri="https://lendx.example.com/did/" + user_wallet.address,
        data="",  # Optional DID document
        did_document={
            "@context": ["https://www.w3.org/ns/did/v1"],
            "id": f"did:xrpl:1:{user_wallet.address}",
            "verificationMethod": [{
                "id": f"did:xrpl:1:{user_wallet.address}#keys-1",
                "type": "Ed25519VerificationKey2020",
                "controller": f"did:xrpl:1:{user_wallet.address}",
                "publicKeyMultibase": user_wallet.public_key
            }]
        }
    )

    result = submit_and_wait(client, did_tx, user_wallet)
    return f"did:xrpl:1:{user_wallet.address}"

def get_did_document(address: str) -> dict:
    """Retrieve DID document from XRPL"""
    response = client.request({
        "command": "account_info",
        "account": address,
        "ledger_index": "validated"
    })
    # Extract DID document from account data
    return response.result.get("did_document", {})
```

#### 2. Verifiable Credential Issuance
```python
# backend/services/credential_service.py
from xrpl.models import CredentialCreate

def issue_kyc_credential(
    issuer_wallet: Wallet,
    subject_address: str,
    kyc_data: dict
) -> str:
    """Issue KYC verifiable credential"""
    credential_tx = CredentialCreate(
        account=issuer_wallet.address,
        subject=subject_address,
        credential_type="KYCVerification",
        uri="https://lendx.example.com/credentials/kyc",
        # Privacy-preserving: No PII on-chain
        # Actual data stored off-chain, only hash on-chain
    )

    result = submit_and_wait(client, credential_tx, issuer_wallet)
    return result.meta.credential_id

def verify_credential(credential_id: str) -> bool:
    """Verify credential is valid and not revoked"""
    response = client.request({
        "command": "credential_info",
        "credential_id": credential_id
    })
    return response.result.credential.status == "active"
```

#### 3. Frontend Integration
```typescript
// frontend/lib/credentials.ts
export class CredentialManager {
  async createDID(wallet: Wallet): Promise<string> {
    const response = await fetch('/api/did/create', {
      method: 'POST',
      body: JSON.stringify({ address: wallet.address })
    })
    const { did } = await response.json()
    return did
  }

  async requestCredential(type: string): Promise<void> {
    // Request credential from issuer
    await fetch('/api/credentials/request', {
      method: 'POST',
      body: JSON.stringify({ type })
    })
  }

  async getCredentials(address: string): Promise<Credential[]> {
    const response = await fetch(`/api/credentials/${address}`)
    return response.json()
  }
}
```

#### 4. Credit Score Credential
```python
def issue_credit_score_credential(
    issuer_wallet: Wallet,
    borrower_address: str,
    credit_score: int,
    default_history: list
) -> str:
    """Issue credit score based on DefaultMPT balance and history"""
    # Calculate credit score
    default_balance = get_mpt_balance(client, borrower_address, DEFAULT_MPT_ID)

    credit_score = 850  # Perfect score
    credit_score -= min(default_balance * 10, 300)  # Deduct for defaults

    # Issue credential
    credential_id = issue_credential(
        issuer_wallet,
        borrower_address,
        credential_type="CreditScore",
        claims={
            "score": credit_score,
            "defaultCount": len(default_history),
            "issuedAt": datetime.now().isoformat()
        }
    )

    return credential_id
```

---

## 9. CRITICAL ARCHITECTURAL ISSUES

### Issue #1: MPT Metadata Immutability

**Problem**: MPT metadata is set at creation and **cannot be updated**.

**Impact**:
- Cannot change `state` field (ONGOING → PAID → DEFAULTED)
- Cannot update `currentBalance` of pools
- Cannot modify any ApplicationMPT or LoanMPT fields

**Solutions**:

1. **Transaction Memos** (Recommended)
```python
# Store state changes as memos on payment transactions
def update_loan_state(loan_id: str, new_state: str):
    # Send 1 drop payment to self with memo
    tx = Payment(
        account=system_wallet.address,
        destination=system_wallet.address,
        amount="1",
        memos=[{
            "Memo": {
                "MemoType": "4C6F616E5374617465",  # "LoanState" in hex
                "MemoData": encode_memo({
                    "loanId": loan_id,
                    "state": new_state,
                    "timestamp": time.time()
                })
            }
        }]
    )
    submit_and_wait(client, tx, system_wallet)
```

2. **NFT Metadata** (Alternative)
```python
# Use NFTs instead of MPTs for mutable data
# NFTs have URIs that can point to updated JSON
def create_loan_nft(loan_data):
    nft_id = mint_nft(
        client,
        lender_wallet,
        uri="https://lendx.example.com/loans/" + loan_id,
        flags=tfTransferable
    )
    # Update URI endpoint returns current loan state
```

3. **Hybrid Approach** (Practical)
```python
# Immutable data in MPT, mutable state in database + memo log
class LoanState:
    # On-chain immutable
    loan_mpt_id: str  # MPT ID
    pool_addr: str
    borrower_addr: str
    principal: Decimal
    interest: Decimal
    start_date: datetime

    # Off-chain mutable (synced via memos)
    current_state: str  # ONGOING, PAID, DEFAULTED
    payments: List[Payment]
    last_payment_date: datetime
```

### Issue #2: RLUSD vs XRP

**Spec says**: "Amount in wallet is just RLUSD?"

**Current implementation**: Uses XRP only

**Required**:
- Set up RLUSD trust lines for all wallets
- Use RLUSD for all loan transactions
- Display RLUSD balances instead of XRP
- Handle trust line limits

**RLUSD Setup**:
```python
from xrpl.models import TrustSet

RLUSD_ISSUER = "rsoLo2S1kiGeCcn6hCUXVrCpGMWLrRrLZz"  # Example

def setup_rlusd_trustline(user_wallet: Wallet, limit: str = "1000000"):
    """Create trust line to RLUSD issuer"""
    trust_tx = TrustSet(
        account=user_wallet.address,
        limit_amount={
            "currency": "RLUSD",
            "issuer": RLUSD_ISSUER,
            "value": limit
        }
    )
    result = submit_and_wait(client, trust_tx, user_wallet)
    return result.meta.TransactionResult == "tesSUCCESS"

def transfer_rlusd(from_wallet: Wallet, to_address: str, amount: Decimal):
    """Transfer RLUSD tokens"""
    payment_tx = Payment(
        account=from_wallet.address,
        destination=to_address,
        amount={
            "currency": "RLUSD",
            "issuer": RLUSD_ISSUER,
            "value": str(amount)
        }
    )
    return submit_and_wait(client, payment_tx, from_wallet)
```

### Issue #3: Scalability & Gas Costs

**Problem**: Creating MPT for every loan/application is expensive

**Gas Cost Estimate** (XRPL testnet):
- Create MPT issuance: 10 XRP reserve + 0.00001 XRP fee
- Authorize holder: 0.00001 XRP fee
- Each state update (if using new MPT): 10 XRP reserve

**For 1000 loans**: ~30,000 XRP in reserves (~$90,000 at $3/XRP)

**Solutions**:

1. **Single MPT with Amounts** (Recommended)
```python
# One LoanMPT issuance, amounts represent individual loans
LOAN_MPT_ID = create_issuance(...)  # Created once

def create_loan(borrower_addr, loan_amount):
    # Mint loan_amount tokens to borrower
    mint_to_holder(client, lender_wallet, borrower_addr, loan_amount, LOAN_MPT_ID)
    # Token balance = outstanding debt

def pay_loan(borrower_wallet, payment_amount):
    # Burn tokens when paid
    burn_from_holder(client, lender_wallet, borrower_wallet.address, payment_amount, LOAN_MPT_ID)
```

2. **NFT for Loan Agreements** (Alternative)
```python
# Use NFTs for unique loan contracts
# Cheaper than MPT issuance (2 XRP reserve vs 10 XRP)
def create_loan_nft(loan_data):
    nft_id = mint_nft(
        client,
        lender_wallet,
        uri="ipfs://" + upload_to_ipfs(loan_data),
        flags=tfTransferable | tfBurnable
    )
```

### Issue #4: Missing Frontend Library

**Current**: All XRPL integration code missing from frontend

**Required**: Create `/frontend/lib/` directory with:
- `xrpl/index.ts` - Wallet connection and transaction signing
- `xrpl/transactions.ts` - Transaction builders
- `xrpl/hooks.ts` - React hooks for XRPL state
- `demo-context.tsx` - Demo state management
- `utils.ts` - Utility functions
- `api.ts` - Backend API client

**Priority**: 🔴 CRITICAL - Nothing works without this

---

## 10. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Week 1-2)
- [ ] Set up PostgreSQL database
- [ ] Implement database schema and ORM models
- [ ] Create `/frontend/lib/` directory structure
- [ ] Implement wallet connection (Xumm integration)
- [ ] Add RLUSD trust line setup

### Phase 2: MPT Core (Week 3-4)
- [ ] Implement PoolMPT creation with metadata
- [ ] Implement ApplicationMPT creation
- [ ] Implement LoanMPT creation on approval
- [ ] Implement DefaultMPT system
- [ ] Add memo-based state tracking

### Phase 3: API Completion (Week 5)
- [ ] Implement all missing API routes
- [ ] Add JWT authentication
- [ ] Connect frontend to backend APIs
- [ ] Add error handling and validation

### Phase 4: DID & Credentials (Week 6)
- [ ] Implement DID creation in signup
- [ ] Add credential issuance system
- [ ] Create credit score credential
- [ ] Add credential verification

### Phase 5: Testing & Demo (Week 7-8)
- [ ] End-to-end testing on testnet
- [ ] Create demo accounts and data
- [ ] Verify all on-chain events
- [ ] Document testnet transactions
- [ ] Performance testing

---

## 11. SUMMARY & RECOMMENDATIONS

### Current State
- **Architecture**: 70% correct structure, wrong implementation
- **Backend**: 50% complete (MPT client done, lending logic missing)
- **Frontend**: 90% UI, 0% integration
- **Overall**: 20% aligned with spec

### Critical Gaps
1. 🔴 **No MPT usage in lending flow** - Spec's core requirement
2. 🔴 **No database** - All data in-memory
3. 🔴 **No frontend-backend integration** - Missing lib layer
4. 🔴 **No DID/VC implementation** - Spec requirement
5. 🔴 **No RLUSD support** - Using wrong currency

### Recommended Approach

**Option A: Full Rewrite** (8 weeks)
- Align with spec completely
- Use MPTs as primary data layer
- Implement all on-chain events
- Production-ready system

**Option B: Hybrid Approach** (4 weeks)
- Use database as primary storage
- Create MPTs for key events only
- Sync database ↔ XRPL via memos
- Demo-ready, scalable to production

**Option C: Minimal Viable Demo** (2 weeks)
- Keep current structure
- Add single MPT creation per pool/loan
- Implement basic DID
- Show on-chain transactions in explorer
- Not scalable, demo-only

### Recommendation: **Option B** (Hybrid Approach)

**Rationale**:
- Balances spec requirements with practicality
- On-chain proof for demo while remaining scalable
- Avoids 30,000 XRP in reserves for 1000 loans
- Easier to implement and maintain
- Can evolve to full on-chain later

**Implementation**:
- PoolMPT: One per pool (on-chain)
- ApplicationMPT: One per application (on-chain)
- LoanMPT: One per loan (on-chain)
- DefaultMPT: Global (on-chain)
- State updates: Database + transaction memos
- DID: On-chain at signup
- Credentials: On-chain

This gives full on-chain audit trail while using database for query efficiency.

---

## Contact & Questions

For implementation questions or clarifications on this analysis, refer to:
- XRPL Documentation: https://xrpl.org/docs
- MPT Reference: https://xrpl.org/docs/concepts/tokens/fungible-tokens/multi-purpose-tokens
- DID Standard: https://xrpl.org/docs/concepts/decentralized-storage/decentralized-identifiers
- Current codebase: `/backend` and `/frontend` directories
