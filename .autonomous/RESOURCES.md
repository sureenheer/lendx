# LendX MVP Development Resources

**Last Updated**: 2025-10-26
**Purpose**: Quick reference for engineers building the local MVP demo

---

## 🎯 MVP Goal

Demonstrate **end-to-end lending flow** with **on-chain MPT creation** on XRPL testnet:
1. Lender creates pool → **PoolMPT on XRPL**
2. Borrower applies → **ApplicationMPT on XRPL**
3. Lender approves → **LoanMPT on XRPL**
4. All visible in XRPL explorer

**Skip for MVP**: Production security, RLS, JWT auth, RLUSD, payment tracking

---

## 📚 XRPL Documentation

### Multi-Purpose Tokens (MPT)

**Official Docs**:
- **Core Concept**: https://xrpl.org/docs/concepts/tokens/fungible-tokens/multi-purpose-tokens
- **Tutorial**: https://xrpl.org/docs/use-cases/tokenization/creating-an-asset-backed-multi-purpose-token
- **XLS-33 Spec**: https://github.com/XRPLF/XRPL-Standards/discussions/231

**Key Info** (from search results):
- MPT amendment activated in XRPL 2.3.0 (November 2024)
- Status: Live on testnet/devnet, performance tested in January 2025
- Features: On-chain metadata, compact storage, fungible tokens
- Our usage: Store pool/loan/application metadata on-chain

**Blog Posts**:
- https://blog.multichainmedia.xyz/index.php/2024/07/18/multi-purpose-tokens-mpt-on-xrpl/
- https://dev.to/ripplexdev/multi-purpose-tokens-mpt-chronology-and-how-to-test-on-devnet-19nj

### Decentralized Identifiers (DID)

**Official Docs**:
- **Core Concept**: https://xrpl.org/docs/concepts/decentralized-storage/decentralized-identifiers
- **W3C DID Spec**: https://www.w3.org/TR/did-core/

**Key Info** (from search results):
- DID amendment (XLS-40) activated October 30, 2024
- W3C DID v1.0 compliant
- Three storage options:
  1. URI reference to IPFS/STORJ
  2. Minimal DID document on-chain (256 char limit)
  3. Implicit DID from public key
- Our implementation: Uses option 2 (minimal on-chain)

**Implementation**:
- Transaction type: `DIDSet`
- Our code: `backend/services/did_service.py`
- Tested: ✅ Working on testnet

**Medium Article**:
- https://medium.com/@LachlanTodd/building-the-future-of-finance-new-identity-credentialing-tools-on-the-xrp-ledger-37c2d4617077

---

## 🔧 Backend Development

### FastAPI + SQLAlchemy + PostgreSQL

**Best Practices (2024)**:
1. **Async SQLAlchemy 2.0** - Modern approach (Sept 2024)
   - https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/
   - Covers: Async sessions, Alembic migrations, Docker

2. **CRUD Operations** - Comprehensive guide (Jan 2025)
   - https://medium.com/@stanker801/creating-a-crud-api-with-fastapi-sqlalchemy-postgresql-postman-pydantic-1ba6b9de9f23
   - Includes: Pydantic models, Postman testing

3. **Official FastAPI Docs**:
   - https://fastapi.tiangolo.com/tutorial/sql-databases/
   - Project generator with PostgreSQL

**Our Stack**:
- SQLAlchemy (declarative base, not async for simplicity)
- Session management: `backend/config/database.py`
- Models: `backend/models/database.py`

### XRPL Python Library

**Library**: `xrpl-py`
- Install: `pip install xrpl-py`
- Docs: https://xrpl-py.readthedocs.io/

**Our Wrappers**:
- Client: `backend/xrpl_client/client.py`
- MPT operations: `backend/xrpl_client/mpt.py`
- Service layer: `backend/services/mpt_service.py`

---

## 🎨 Frontend Development

### Next.js 14 + XRPL + Wallet Integration

**Wallet Connection Templates**:
1. **XRPL Wallet Connect** (supports Xumm/Xaman, Gem, Crossmark)
   - https://github.com/Aaditya-T/xrpl-wallet-connect
   - Next.js template with JWT auth
   - Get Xumm API keys from: https://xumm.app/

2. **Official Browser Wallet Tutorial**:
   - https://xrpl.org/docs/tutorials/javascript/build-apps/build-a-browser-wallet-in-javascript

3. **XRPL Wallet Library**:
   - https://github.com/tequdev/xrpl-wallet
   - NPM: https://www.npmjs.com/package/xrpl-wallet
   - Supports multiple wallet adapters

**XRPL.js**:
- Install: `npm install xrpl`
- Docs: https://js.xrpl.org/
- Examples: https://github.com/XRPLF/xrpl.js/blob/main/APPLICATIONS.md

**Xumm SDK**:
- Install: `npm install xumm-sdk`
- Docs: https://xumm.readme.io/
- Used for: Transaction signing, wallet connection

**Our Implementation**:
- Will create: `frontend/lib/xrpl/` for wallet integration
- Components: `lender-view.tsx`, `borrower-view.tsx` (already have UI)

---

## 🧪 Testing & Development

### XRPL Testnet

**Faucets** (get free test XRP):
- **Official**: https://xrpl.org/resources/dev-tools/xrp-faucets
- **Bithomp**: https://test.bithomp.com/faucet/
- **DataWallet Guide**: https://www.datawallet.com/crypto/get-xrp-testnet-tokens

**Limits** (2024):
- Default: 100 XRP per request
- Maximum: 1,000 XRP per request
- Daily limits may apply

**Explorer**:
- https://testnet.xrpl.org/
- Use to verify MPT transactions

**Network URL**:
- Testnet: `wss://s.altnet.rippletest.net:51233`
- Our config: `backend/xrpl_client/config.py`

### Local Development

**Backend**:
```bash
# Start API server
cd /home/users/duynguy/proj/calhacks
source venv/bin/activate
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
PYTHONPATH=$(pwd) pytest backend/tests/ -v
```

**Frontend**:
```bash
cd frontend
npm run dev  # Starts on localhost:3000
```

**Database**:
- Supabase dashboard: https://app.supabase.com/project/sspwpkhajtooztzisioo
- Connection managed via `backend/config/database.py`

---

## 📋 Implementation Checklist

### MVP Phase 1: API Integration

**Backend Engineer #1**:
- [ ] Update `backend/api/main.py` to use database ORM
- [ ] Replace in-memory dicts with DB queries
- [ ] Add `get_db()` dependency to routes
- [ ] Test all existing endpoints

**Reference**:
- Current endpoints: `backend/api/main.py`
- Database session: `from backend.config.database import get_db_session`

### MVP Phase 2: MPT Integration

**Backend Engineer #2**:
- [ ] Import MPT service: `from backend.services.mpt_service import create_pool_mpt`
- [ ] Update `POST /pools` to call `create_pool_mpt()`
- [ ] Update `POST /applications` to call `create_application_mpt()`
- [ ] Update approval endpoint to call `create_loan_mpt()`
- [ ] Store MPT IDs in database

**Reference**:
- Service layer: `backend/services/mpt_service.py`
- Schemas: `backend/models/mpt_schemas.py`

### MVP Phase 3: Frontend Integration

**Frontend Engineer #1**:
- [ ] Create `frontend/lib/xrpl/index.ts` with wallet connection
- [ ] Add Xumm SDK integration
- [ ] Create API client: `frontend/lib/api.ts`
- [ ] Connect components to backend
- [ ] Add transaction signing flow

**Reference**:
- Template: https://github.com/Aaditya-T/xrpl-wallet-connect
- Components: `frontend/components/lendx/lender-view.tsx`

### MVP Phase 4: DID Integration

**Backend Engineer #3**:
- [ ] Add DID creation to signup endpoint
- [ ] Update `POST /signup` to call `create_did_for_user()`
- [ ] Store DID in `users.did` field

**Reference**:
- DID service: `backend/services/did_service.py`

---

## 🚀 Demo Script

### Preparation
1. Get testnet XRP: https://test.bithomp.com/faucet/
2. Create 2 test wallets (lender + borrower)
3. Fund both wallets with 1000 XRP each

### Demo Flow
1. **Lender**: Create pool
   - POST /api/pool
   - Verify PoolMPT in explorer
2. **Borrower**: Create DID
   - POST /signup
   - Verify DID in explorer
3. **Borrower**: Apply for loan
   - POST /api/application
   - Verify ApplicationMPT in explorer
4. **Lender**: Approve application
   - PUT /api/application/{id}/approve
   - Verify LoanMPT in explorer
5. **Show**: All MPTs visible at testnet.xrpl.org

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| XRPL Docs | https://xrpl.org/docs |
| MPT Guide | https://xrpl.org/docs/concepts/tokens/fungible-tokens/multi-purpose-tokens |
| DID Guide | https://xrpl.org/docs/concepts/decentralized-storage/decentralized-identifiers |
| Testnet Faucet | https://test.bithomp.com/faucet/ |
| Testnet Explorer | https://testnet.xrpl.org/ |
| FastAPI + SQLAlchemy | https://fastapi.tiangolo.com/tutorial/sql-databases/ |
| XRPL.js Docs | https://js.xrpl.org/ |
| Xumm SDK | https://xumm.readme.io/ |
| Wallet Template | https://github.com/Aaditya-T/xrpl-wallet-connect |

---

## 📞 Support

- XRPL Discord: https://discord.gg/xrpl
- FastAPI Discord: https://discord.gg/VQjSZaeJmf
- Project Spec: `docs/SPEC_ALIGNMENT.md`
- Database Docs: `DATABASE_SETUP_SUMMARY.md`

**Last Updated**: 2025-10-26
