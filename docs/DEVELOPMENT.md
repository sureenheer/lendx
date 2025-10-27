# LendX Development Guide

This file provides comprehensive technical documentation for developers working with the LendX codebase. It was originally created to guide Claude Code (claude.ai/code) and serves as a detailed reference for all contributors.

## Project Overview

LendX is a decentralized lending marketplace built on XRPL (XRP Ledger) with a Next.js 14 frontend and Python FastAPI backend. The application enables peer-to-peer lending with verifiable credentials, multi-signature support, and automated settlement through XRPL integration.

## Development Commands

### Frontend (Next.js)
```bash
cd frontend
npm install --legacy-peer-deps  # Required due to peer dependency conflicts
npm run dev                      # Start dev server (http://localhost:3000)
npm run build                    # Build for production
npm run lint                     # Lint code with ESLint
npm start                        # Start production server
```

### Backend (Python FastAPI)
```bash
# From project root
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -e .                 # Install in editable mode

# Set up database credentials
cp .env.example .env
# Edit .env and add your SUPABASE_DB_PASSWORD

# Run the API server
uvicorn backend.api.main:app --reload  # Start API server (http://localhost:8000)

# Run tests
export SUPABASE_DB_PASSWORD="your_password"
PYTHONPATH=$(pwd) pytest backend/tests/ -v
```

## Architecture

### Backend Structure (`/backend`)

The Python backend is organized into specialized modules:

**`xrpl_client/`** - XRPL blockchain integration layer
- `client.py`: Connection handling and transaction submission
- `mpt.py`: Multi-Purpose Token (MPT) operations (create issuance, mint, burn)
- `escrow.py`: Escrow transaction creation and finalization
- `multisig.py`: Multi-signature account setup and transaction signing
- `exceptions.py`: Custom XRPL error handling with `@wrap_xrpl_exception` decorator
- `config.py`: Network URLs and XRPL constants (testnet/mainnet)

**`graph/`** - Settlement algorithm implementation
- `reduce.py`: Cycle reduction algorithm to minimize debt transfers
- `cycles.py`: Debt cycle detection in transaction graphs
- `nets.py`: Net balance computation
- `types.py`: Graph data structures (Edge, Graph)

**`services/`** - Business logic layer
- `settlement.py`: Settlement proposal creation and escrow instruction generation
- `iou.py`: IOU tracking and group balance management with cycle reduction
- `balance_sync.py`: Balance synchronization between XRPL and application state

**`api/`** - FastAPI REST endpoints
- `main.py`: API server with CORS configuration for localhost:3000/3001
  - Lending pool CRUD operations
  - Loan application and approval workflow
  - Balance queries (XRP and MPT tokens)

**`models/`** - Database ORM models
- `database.py`: SQLAlchemy models for all database tables
  - User: Wallet addresses and DIDs
  - Pool: Lending pools (indexes PoolMPT data)
  - Application: Loan applications (indexes ApplicationMPT data)
  - Loan: Active and completed loans (indexes LoanMPT data)
  - UserMPTBalance: Cache of on-chain MPT balances

**`config/`** - Configuration modules
- `database.py`: Supabase PostgreSQL connection and session management
  - Connection pooling (5 connections, 10 overflow)
  - SSL enforcement
  - Automatic timezone setting (UTC)
  - Health check utilities

**`migrations/`** - Database schema migrations
- `001_initial_schema.sql`: Initial database schema with all tables and indexes

**`tests/`** - Test suite (TDD approach)
- `test_database.py`: Connection and basic operations
- `test_users.py`: User model tests
- `test_pools.py`: Pool model tests
- `test_applications.py`: Application model tests
- `test_loans.py`: Loan model tests
- `conftest.py`: Shared test fixtures and configuration

### Frontend Structure (`/frontend`)

Next.js 14 application using App Router with TypeScript:

**App Router** (`/app`)
- `(auth)/`: Authentication flow (signup)
- `(dashboard)/`: Main dashboard with layout and page
- Route groups isolate layouts for different sections

**Components** (`/components`)
- `lendx/`: Core application components
  - `lender-view.tsx`: Lending pool creation and loan approval interface
  - `borrower-view.tsx`: Loan application and management interface
- `dashboard/`: Dashboard widgets, sidebar, notifications, mobile header
- `chat/`: Chat interface components
- `ui/`: Shadcn/ui component library (Radix UI primitives)
- `icons/`: Icon components

**Data Flow**
- Mock data from `mock.json` provides initial dashboard state
- XRPL integration through `@/lib/xrpl` (imports found but implementation may be incomplete)
- State management via `@/lib/demo-context` DemoProvider
- Wallet connection using `xumm-sdk` and native `xrpl` library

**Key Dependencies**
- UI: Radix UI primitives, Tailwind CSS, Framer Motion
- XRPL: `xrpl` v4.4.2, `xumm-sdk` v1.11.2
- Forms: React Hook Form with Zod validation
- State: Zustand for client state management
- Charts: Recharts for data visualization

## XRPL Integration Patterns

### Python Client Usage
```python
from backend.xrpl_client import connect, submit_and_wait

# Connect to network
client = connect('testnet')  # or 'mainnet'

# All XRPL operations use exception wrapper
# Exceptions: ConnectionError, InsufficientXRP, PermissionDenied, MaxLedgerExceeded
```

### Multi-Purpose Tokens (MPT)
The application uses XRPL's MPT feature for tokenized debt instruments:
- `create_issuance()`: Create new token type
- `mint_to_holder()`: Issue tokens to holder address
- `get_mpt_balance()`: Query token balance
- `burn_from_holder()`: Destroy tokens

### Escrow Transactions
Escrow provides trustless loan security:
- `create_deposit_escrow()`: Lock funds with conditions
- `finish_escrow()`: Release funds when conditions met
- Default hold time: 1 hour (`ESCROW_HOLD_SECONDS = 3600`)

### Settlement Algorithm
The graph-based settlement system minimizes transaction count:
1. IOUs tracked as directed graph edges (debtor → creditor)
2. Cycle detection identifies circular debt
3. Cycle reduction eliminates offsetting debts
4. Net balances computed for final settlement
5. Escrow instructions generated for remaining transfers

## Configuration

### Database Setup (Supabase PostgreSQL)

LendX uses Supabase PostgreSQL as the persistence layer for indexing on-chain XRPL data.

**Initial Setup**:
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Add your Supabase credentials to .env
# Get these from: https://app.supabase.com/project/_/settings/database
SUPABASE_URL=https://sspwpkhajtooztzisioo.supabase.co
SUPABASE_DB_PASSWORD=your_database_password
```

**Database Schema**:
The schema is already applied via migration `001_initial_schema.sql`:

- **users**: Wallet addresses and DIDs
  - Primary key: `address` (VARCHAR(34))
  - Unique: `did` (VARCHAR(255))

- **pools**: Lending pools (indexes PoolMPT)
  - Primary key: `pool_address` (VARCHAR(66) - MPT ID)
  - Foreign key: `issuer_address` → users.address
  - Tracks: total_balance, current_balance, minimum_loan, duration_days, interest_rate

- **applications**: Loan applications (indexes ApplicationMPT)
  - Primary key: `application_address` (VARCHAR(66) - MPT ID)
  - Foreign keys: `borrower_address` → users.address, `pool_address` → pools
  - States: PENDING, APPROVED, REJECTED, EXPIRED

- **loans**: Active/completed loans (indexes LoanMPT)
  - Primary key: `loan_address` (VARCHAR(66) - MPT ID)
  - Foreign keys: `pool_address`, `borrower_address`, `lender_address`
  - States: ONGOING, PAID, DEFAULTED

- **user_mpt_balances**: MPT balance cache
  - Composite key: (user_address, mpt_id)
  - Reduces XRPL API calls for balance queries

**Connection Details**:
- Connection pooling: 5 connections, max 10 overflow
- SSL required (enforced by Supabase)
- Timezone: UTC (auto-set on connect)
- Health check: `check_db_connection()` function available

**Using the Database in Code**:
```python
from backend.config.database import get_db_session
from backend.models.database import User, Pool, Loan

# Create a session
session = get_db_session()

# Query users
users = session.query(User).all()

# Create a new user
user = User(
    address="rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
    did="did:xrpl:1:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"
)
session.add(user)
session.commit()

# Always close the session
session.close()
```

**FastAPI Dependency Injection**:
```python
from fastapi import Depends
from backend.config.database import get_db
from sqlalchemy.orm import Session

@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

### Frontend Environment Variables
Create `frontend/.env.local`:
```env
NEXT_PUBLIC_XUMM_API_KEY=your_api_key
NEXT_PUBLIC_XUMM_API_SECRET=your_api_secret
```

### Backend Environment Variables
Create `.env` in project root (see `.env.example` for full template):
```env
# Supabase
SUPABASE_URL=https://sspwpkhajtooztzisioo.supabase.co
SUPABASE_DB_PASSWORD=your_password
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Database Connection Pool
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_ECHO_SQL=false

# Application
ENVIRONMENT=development
JWT_SECRET_KEY=your_secret_key
```

### XRPL Network Selection
Backend uses `TESTNET_URL` and `MAINNET_URL` from `backend/xrpl_client/config.py`
- Testnet for development
- Mainnet for production

## Important Notes

- **Legacy Peer Deps**: Frontend requires `--legacy-peer-deps` flag due to React 19 and package conflicts
- **Path Aliases**: Frontend uses `@/*` alias mapping to root directory (see `tsconfig.json`)
- **XRPL Constants**: 1 XRP = 1,000,000 drops (`DROPS_PER_UNIT`)
- **Database**: Supabase PostgreSQL with SQLAlchemy ORM (connection pooling, SSL enforced)
- **CORS**: Backend configured for localhost:3000 and localhost:3001 during development
- **Multi-sig**: Settlement proposals require 2 signatures (`REQUIRED_SIGNATURES = 2`)
- **Error Handling**: All XRPL client functions wrapped with `@wrap_xrpl_exception` decorator
- **TDD**: All database models have comprehensive test coverage

## Testing

### Backend Tests

Test suite uses **Test-Driven Development (TDD)** methodology with pytest.

**Running Tests**:
```bash
# Set database password
export SUPABASE_DB_PASSWORD="your_password"

# Run all tests
PYTHONPATH=$(pwd) pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/test_users.py -v

# Run single test
pytest backend/tests/test_users.py::TestUserModel::test_create_user -v
```

**Test Coverage**:
- ✅ Database connection and initialization
- ✅ User CRUD operations (create, read, update, delete)
- ✅ Pool operations with decimal precision
- ✅ Application state management (PENDING, APPROVED, REJECTED, EXPIRED)
- ✅ Loan state management (ONGOING, PAID, DEFAULTED)
- ✅ Foreign key constraints
- ✅ Unique constraints (DID uniqueness)
- ✅ Check constraints (state validation)

**Test Files**:
- `test_database.py`: Connection and basic operations
- `test_users.py`: User model tests
- `test_pools.py`: Pool model tests
- `test_applications.py`: Application model tests
- `test_loans.py`: Loan model tests
- `conftest.py`: Shared fixtures (db_session, create_test_user, etc.)

See `backend/tests/README.md` for detailed testing documentation.

### Frontend Tests

Frontend testing not yet configured. Recommended setup:
- Jest or Vitest for component testing
- React Testing Library for UI testing
- Playwright for E2E tests
