# LendX Backend Documentation

This directory contains comprehensive architecture and security documentation for the LendX lending marketplace backend.

## Quick Navigation

### Architecture Decision Records (ADRs)

Detailed justifications for key architectural decisions:

- **[ADR-001: Authentication Method Selection](adrs/ADR-001-authentication-method-selection.md)**
  - Decision: JWT with wallet signature authentication
  - Rationale: Best balance of security, UX, and Supabase integration
  - Status: Accepted, ready for implementation

- **[ADR-002: RLS vs Application-Level Authorization](adrs/ADR-002-rls-vs-application-level-authorization.md)**
  - Decision: Layered authorization (RLS + application checks)
  - Rationale: Defense in depth with good developer experience
  - Status: Accepted, RLS currently disabled for development

- **[ADR-003: Wallet Key Management Strategy](adrs/ADR-003-wallet-key-management-strategy.md)**
  - Decision: Users control keys, service wallet in Vault/KMS
  - Rationale: User sovereignty + secure backend operations
  - Status: Accepted, development uses .env

- **[ADR-004: Session Management Approach](adrs/ADR-004-session-management-approach.md)**
  - Decision: 24-hour sliding sessions with token blocklist
  - Rationale: Good UX with strong security (revocable sessions)
  - Status: Accepted, ready for implementation

### Implementation Guides

Comprehensive guides for implementing the architecture:

- **[AUTHENTICATION_DESIGN.md](AUTHENTICATION_DESIGN.md)** (40KB)
  - Complete authentication architecture specification
  - Detailed flow diagrams for login, requests, logout
  - Backend and frontend component specifications
  - API endpoint specifications
  - Security model and threat mitigation
  - Testing strategy and examples
  - Deployment guide and monitoring setup

- **[RLS_POLICIES.md](RLS_POLICIES.md)** (24KB)
  - Production-ready SQL for all RLS policies
  - Table-by-table policy specifications
  - Complete migration script
  - Testing queries for each policy
  - Performance optimization guidance
  - Troubleshooting common issues
  - Security audit checklist

- **[SECURITY_ROADMAP.md](SECURITY_ROADMAP.md)** (21KB)
  - 3-week implementation plan
  - Phase 1: Basic Authentication (Week 1)
  - Phase 2: Authorization & Security Hardening (Week 2)
  - Phase 3: Testing & Production Readiness (Week 3)
  - Detailed tasks, deliverables, and success criteria
  - Risk management and rollback plans
  - Resource requirements and timelines

### Existing Documentation

- **[SECURITY.md](../SECURITY.md)** (11KB)
  - Security advisory (RLS currently disabled)
  - Quick-start RLS policies (draft)
  - Security checklist
  - Generated: 2025-10-26

---

## Document Overview

### For Product Managers

Start here:
1. Read **SECURITY_ROADMAP.md** to understand the 3-week plan
2. Review success metrics and timelines
3. Understand risks and mitigation strategies

Key takeaways:
- Week 1: Users can login with wallet signatures
- Week 2: Data is protected with Row-Level Security
- Week 3: Production-ready with monitoring and tests
- Cost: ~$100-150/month for infrastructure
- Team: 2.35 FTE for 3 weeks

### For Engineers (Backend)

Start here:
1. Read **ADR-001** to understand why JWT authentication
2. Read **AUTHENTICATION_DESIGN.md** for complete implementation details
3. Read **RLS_POLICIES.md** for database security
4. Follow **SECURITY_ROADMAP.md** Phase 1 tasks (Week 1)

Key files to implement:
```
backend/
├── auth/
│   ├── jwt.py              # JWT generation/verification
│   ├── challenge.py        # Challenge generation
│   ├── signature.py        # XRPL signature verification
│   ├── blocklist.py        # Token revocation
│   ├── middleware.py       # FastAPI middleware
│   └── dependencies.py     # FastAPI dependencies
├── api/
│   └── auth.py            # Auth endpoints
└── config/
    ├── redis.py           # Redis connection
    └── secrets.py         # Secret management
```

### For Engineers (Frontend)

Start here:
1. Read **ADR-001** sections on frontend integration
2. Read **AUTHENTICATION_DESIGN.md** section "Frontend Integration"
3. Follow **SECURITY_ROADMAP.md** Phase 1, Day 5 tasks

Key files to implement:
```
frontend/
├── lib/
│   ├── auth/
│   │   ├── store.ts       # Zustand auth store
│   │   ├── wallet.ts      # Wallet connection (update existing)
│   │   └── api.ts         # Auth API calls
│   └── api/
│       └── client.ts      # API client with auto-refresh
└── components/
    ├── auth/
    │   ├── ConnectWallet.tsx
    │   └── ProtectedRoute.tsx
    └── dashboard/
        └── LogoutButton.tsx
```

### For QA Engineers

Start here:
1. Read **AUTHENTICATION_DESIGN.md** section "Testing Strategy"
2. Read **SECURITY_ROADMAP.md** Phase 3, Day 1-2 (Testing)
3. Review test examples in AUTHENTICATION_DESIGN.md

Focus areas:
- End-to-end wallet connection flow
- Token expiration and refresh
- RLS policy enforcement
- Security tests (signature replay, rate limiting, etc.)
- Load testing authentication endpoints

### For DevOps/SRE

Start here:
1. Read **ADR-003** for secrets management
2. Read **ADR-004** for session infrastructure (Redis)
3. Read **AUTHENTICATION_DESIGN.md** section "Deployment Guide"
4. Read **SECURITY_ROADMAP.md** section "Infrastructure Requirements"

Infrastructure to set up:
- Redis instance (challenges + token blocklist)
- Secrets management (Supabase Vault initially, AWS KMS for production)
- Monitoring (auth metrics, error rates, security events)
- Alerts (failed auth, rate limits, suspicious activity)
- Load balancer (HTTPS, HSTS, security headers)

---

## Architecture Summary

### Authentication Flow

```
User → Xumm Wallet (Sign Challenge) → Backend (Verify Signature) → JWT Token
         ↓
  Token stored in localStorage
         ↓
  Subsequent requests include: Authorization: Bearer <token>
         ↓
  Backend verifies JWT → Extracts wallet address → Applies RLS
```

### Authorization Layers

1. **Database (RLS)**: PostgreSQL policies enforce access at row level
   - Users can only SELECT their own data
   - Pool owners can SELECT applications to their pools
   - Service role bypasses RLS for admin operations

2. **Application (FastAPI)**: Additional checks for UX and complex logic
   - Better error messages (403 vs 404)
   - Complex business rules
   - Computed fields based on user context

3. **Frontend (React)**: UI-level protection
   - Hide actions user can't perform
   - Client-side route protection
   - Not a security boundary (server enforces)

### Security Model

```
┌─────────────────────────────────────────────────────┐
│  FRONTEND                                            │
│  - localStorage (JWT token)                          │
│  - CSP headers prevent XSS                           │
│  - CORS prevents unauthorized origins                │
└───────────────────┬─────────────────────────────────┘
                    │ HTTPS (TLS 1.3)
                    │ HSTS enforced
                    ▼
┌─────────────────────────────────────────────────────┐
│  FASTAPI BACKEND                                     │
│  - Rate limiting (prevent brute force)               │
│  - JWT verification (signature + expiration)         │
│  - Token blocklist check (Redis)                     │
│  - Extract wallet_address from token                 │
│  - Security headers (CSP, X-Frame-Options, etc.)     │
└───────────────────┬─────────────────────────────────┘
                    │ Connection pooling
                    │ SSL enforced
                    ▼
┌─────────────────────────────────────────────────────┐
│  POSTGRESQL (Supabase)                               │
│  - RLS policies (row-level security)                 │
│  - auth.uid() = wallet_address from JWT             │
│  - Service role bypasses RLS                         │
│  - Encrypted at rest                                 │
│  - Automated backups                                 │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Basic Authentication (Week 1)

Focus: Users can login via wallet signatures and receive JWT tokens

Deliverables:
- JWT generation and verification
- Challenge generation and storage (Redis)
- XRPL signature verification
- Auth endpoints (challenge, login, logout, me)
- Frontend wallet connection integration
- Protected endpoints require authentication

Success criteria:
- Users can connect Xumm wallet
- Users receive JWT token after signing challenge
- Protected endpoints return 401 without valid token
- Basic error handling in place

### Phase 2: Authorization & Security (Week 2)

Focus: Enable RLS, add token revocation, security hardening

Deliverables:
- RLS enabled on all tables
- RLS policies enforced
- Token blocklist (logout revokes tokens)
- Sliding sessions (auto token refresh)
- Rate limiting on auth endpoints
- Security headers (CSP, HSTS, etc.)
- Audit logging

Success criteria:
- Users can only access their own data
- Logout prevents further token use
- Tokens auto-refresh (stay logged in if active)
- Rate limiting prevents brute force
- All security headers present

### Phase 3: Testing & Production (Week 3)

Focus: Comprehensive testing, monitoring, production deployment

Deliverables:
- Automated tests (unit, integration, security)
- RLS policy tests
- Monitoring and alerts
- Documentation complete
- Production deployment
- Post-deployment verification

Success criteria:
- 90%+ test coverage
- Zero security vulnerabilities
- Monitoring operational
- Successful production deployment
- No regressions

---

## Key Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Authentication Method** | JWT with wallet signatures | Best UX + security for blockchain apps |
| **Authorization Strategy** | RLS + application checks | Defense in depth |
| **Session Duration** | 24 hours (sliding) | Balance security vs UX |
| **Token Revocation** | Redis blocklist | Enables logout, reasonable overhead |
| **Secrets Storage** | Vault (staging) → KMS (prod) | Secure + compliant |
| **User Keys** | Never stored in backend | User sovereignty (Xumm manages) |
| **Service Keys** | Vault/KMS | Secure, auditable, rotatable |
| **Public Data** | Pools viewable by all | Marketplace requirement |
| **Private Data** | Users, Loans, Balances | RLS enforces privacy |

---

## Success Metrics

### Security Metrics

- **Zero** unauthorized data access incidents
- **< 1%** false positive rate (legit users blocked)
- **> 99.9%** auth endpoint uptime
- **90%+** test coverage on auth module

### UX Metrics

- **< 30s** average time to login (including Xumm)
- **< 2%** login failure rate (signature issues)
- **> 95%** user satisfaction with login flow

### Performance Metrics

- **< 100ms** RLS overhead on typical queries
- **< 500ms** average JWT verification time
- **< 200ms** Redis blocklist check time

---

## Next Steps

### For Immediate Implementation

1. **Set up development environment**
   ```bash
   # Install dependencies
   pip install pyjwt python-jose redis slowapi

   # Start Redis
   docker run -d -p 6379:6379 redis:alpine

   # Generate JWT secret
   openssl rand -hex 32 > .jwt_secret
   ```

2. **Create initial auth files**
   ```bash
   mkdir -p backend/auth
   touch backend/auth/__init__.py
   touch backend/auth/jwt.py
   touch backend/auth/challenge.py
   touch backend/auth/signature.py
   ```

3. **Follow Week 1 tasks** from SECURITY_ROADMAP.md

### For Team Coordination

1. **Schedule kickoff meeting** to review architecture
2. **Assign tasks** from SECURITY_ROADMAP.md Phase 1
3. **Set up daily standups** during implementation
4. **Schedule security review** at end of Week 2

---

## Questions?

For clarification on architecture decisions:
- Review relevant ADR in `adrs/` directory
- Check "References" section at end of each ADR
- Consult AUTHENTICATION_DESIGN.md for implementation details

For implementation guidance:
- Follow SECURITY_ROADMAP.md phase-by-phase
- Use code examples in AUTHENTICATION_DESIGN.md
- Reference RLS_POLICIES.md for SQL queries

---

**Last Updated**: 2025-10-26
**Documentation Version**: 1.0
**Status**: Complete, ready for implementation
