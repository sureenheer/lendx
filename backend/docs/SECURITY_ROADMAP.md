# LendX Security Implementation Roadmap

**Version**: 1.0
**Last Updated**: 2025-10-26
**Timeline**: 3 weeks to production-ready security

---

## Executive Summary

This roadmap outlines the implementation plan for securing the LendX lending marketplace. The plan is divided into 3 phases over 3 weeks, with each phase building on the previous one to achieve production-ready security.

### Current State (Week 0)

- ✅ Database schema implemented (5 tables)
- ✅ Basic XRPL integration (MPT, escrow, multi-sig)
- ✅ Frontend wallet connection (Xumm)
- ⚠️ **RLS disabled** (development mode)
- ❌ **No authentication** (all endpoints public)
- ❌ **No authorization** (anyone can access all data)

### Target State (Week 3)

- ✅ **JWT authentication** with wallet signatures
- ✅ **RLS enabled** with comprehensive policies
- ✅ **Token revocation** via Redis blocklist
- ✅ **Rate limiting** on auth endpoints
- ✅ **Security headers** (CSP, HSTS, etc.)
- ✅ **Audit logging** for security events
- ✅ **Automated tests** for auth and RLS

---

## Phase 1: Basic Authentication (Week 1)

**Goal**: Implement wallet-based authentication and JWT session management

### Week 1, Day 1-2: Backend Authentication Core

#### Tasks

1. **Set up JWT infrastructure**
   ```bash
   pip install pyjwt python-jose[cryptography]
   ```
   - [ ] Generate JWT secret key (store in `.env`)
   - [ ] Create `backend/auth/jwt.py` module
   - [ ] Implement `generate_jwt(wallet_address)` function
   - [ ] Implement `verify_jwt(token)` function
   - [ ] Add JWT secret to environment variables

2. **Set up Redis for challenges**
   ```bash
   pip install redis
   docker run -d -p 6379:6379 redis:alpine
   ```
   - [ ] Create `backend/config/redis.py` connection module
   - [ ] Implement `store_challenge(address, nonce, message)` function
   - [ ] Implement `get_challenge(address, nonce)` function
   - [ ] Add Redis URL to environment variables

3. **Implement challenge generation**
   - [ ] Create `backend/auth/challenge.py` module
   - [ ] Implement `generate_challenge(address)` function
   - [ ] Challenge format: "LendX Authentication\\nTimestamp: ...\\nNonce: ..."
   - [ ] Store challenges in Redis with 5-minute TTL

4. **Implement signature verification**
   - [ ] Create `backend/auth/signature.py` module
   - [ ] Implement `verify_xrpl_signature(message, signature, address)` function
   - [ ] Use `xrpl` library for signature verification
   - [ ] Handle invalid signatures gracefully

**Deliverables**:
- ✅ JWT generation and verification working
- ✅ Redis connection established
- ✅ Challenge generation and storage working
- ✅ Signature verification working

---

### Week 1, Day 3-4: Authentication Endpoints

#### Tasks

1. **Create auth endpoints**
   - [ ] Create `backend/api/auth.py` module
   - [ ] Implement `POST /auth/wallet/challenge` endpoint
   - [ ] Implement `POST /auth/wallet/login` endpoint
   - [ ] Implement `POST /auth/logout` endpoint (basic, no blocklist yet)
   - [ ] Implement `GET /auth/me` endpoint

2. **Create FastAPI dependencies**
   - [ ] Create `backend/auth/dependencies.py` module
   - [ ] Implement `get_current_user()` dependency
   - [ ] Implement `require_auth()` dependency
   - [ ] Implement `optional_auth()` dependency

3. **Add authentication to existing endpoints**
   - [ ] Update `POST /pools` to require authentication
   - [ ] Update `POST /loans/apply` to require authentication
   - [ ] Update `POST /loans/{id}/approve` to require authentication
   - [ ] Keep `GET /pools` public (marketplace requirement)

4. **Error handling**
   - [ ] Add proper HTTP status codes (401, 403, 400)
   - [ ] Add detailed error messages
   - [ ] Add error logging

**Deliverables**:
- ✅ All auth endpoints functional
- ✅ Protected endpoints require valid JWT
- ✅ Error handling in place

**Testing**:
```bash
# Test challenge generation
curl -X POST http://localhost:8000/auth/wallet/challenge \
  -H "Content-Type: application/json" \
  -d '{"address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx", "network": "testnet"}'

# Test login (with mock signature)
curl -X POST http://localhost:8000/auth/wallet/login \
  -H "Content-Type: application/json" \
  -d '{"address": "rN7n7...", "signature": "...", "nonce": "..."}'

# Test protected endpoint
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### Week 1, Day 5: Frontend Integration

#### Tasks

1. **Create auth store**
   - [ ] Create `frontend/lib/auth/store.ts` (Zustand store)
   - [ ] Implement `login()` action
   - [ ] Implement `logout()` action
   - [ ] Implement `refreshToken()` action
   - [ ] Persist token in localStorage

2. **Create wallet connection flow**
   - [ ] Update `frontend/lib/auth/wallet.ts`
   - [ ] Integrate challenge request
   - [ ] Integrate Xumm signing
   - [ ] Integrate login API call

3. **Create API client**
   - [ ] Create `frontend/lib/api/client.ts`
   - [ ] Add `Authorization` header automatically
   - [ ] Handle 401 errors (redirect to login)
   - [ ] Handle token refresh (X-New-Token header)

4. **Create auth components**
   - [ ] Create `ConnectWallet` component
   - [ ] Create `ProtectedRoute` component
   - [ ] Create logout button in dashboard

**Deliverables**:
- ✅ End-to-end wallet connection working
- ✅ Users can login and access protected routes
- ✅ Logout clears token and redirects

**Testing**:
- [ ] User can connect Xumm wallet
- [ ] User can sign challenge
- [ ] User receives JWT token
- [ ] Token is stored in localStorage
- [ ] Protected pages require authentication
- [ ] Logout works correctly

---

### Week 1 Checkpoint

**Success Criteria**:
- ✅ Users can authenticate via wallet signature
- ✅ JWT tokens are issued and verified
- ✅ Protected endpoints require authentication
- ✅ Frontend integrates with auth system
- ✅ Basic error handling in place

**Risks**:
- ⚠️ Xumm signature format may need adjustment
- ⚠️ Token expiration not yet implemented (sliding sessions)
- ⚠️ No token revocation yet (blocklist)

---

## Phase 2: Authorization & Security Hardening (Week 2)

**Goal**: Enable RLS, implement token revocation, add security features

### Week 2, Day 1-2: Row-Level Security

#### Tasks

1. **Create RLS migration**
   - [ ] Copy SQL from `RLS_POLICIES.md`
   - [ ] Create `backend/migrations/002_enable_rls_policies.sql`
   - [ ] Test migration in local database
   - [ ] Apply migration to staging database

2. **Configure Supabase JWT**
   - [ ] Get JWT secret from Supabase dashboard
   - [ ] Configure backend to issue Supabase-compatible JWTs
   - [ ] Ensure `sub` claim contains wallet address
   - [ ] Test `auth.uid()` returns correct value

3. **Test RLS policies**
   - [ ] Create test users with different wallet addresses
   - [ ] Verify users can only see their own data
   - [ ] Verify pool owners can see applications
   - [ ] Verify lenders can see their loans
   - [ ] Verify service role bypasses RLS

4. **Update backend to use RLS**
   - [ ] Ensure database queries use JWT context
   - [ ] Remove redundant authorization checks (RLS handles it)
   - [ ] Keep application-level checks for better UX

**Deliverables**:
- ✅ RLS enabled on all tables
- ✅ Policies enforced correctly
- ✅ Backend works with RLS

**Testing**:
```python
# Test RLS enforcement
def test_rls_users_cannot_see_others():
    # Login as user A
    token_a = login("rUSERA...")

    # Try to query user B's data
    response = client.get("/users/rUSERB...", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 404  # Not 403 (prevents info leakage)

def test_rls_pool_owner_sees_applications():
    # Login as pool owner
    token = login("rOWNER...")

    # Query applications to their pool
    response = client.get("/applications?pool_id=pool123", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()["applications"]) > 0
```

---

### Week 2, Day 3: Token Revocation (Blocklist)

#### Tasks

1. **Implement blocklist**
   - [ ] Create `backend/auth/blocklist.py` module
   - [ ] Implement `blocklist_token(jti, exp)` function
   - [ ] Implement `is_token_blocklisted(jti)` function
   - [ ] Store blocklisted tokens in Redis with TTL

2. **Update JWT verification**
   - [ ] Add `jti` claim to generated JWTs (UUID)
   - [ ] Check blocklist in `verify_jwt()` function
   - [ ] Raise exception if token blocklisted

3. **Update logout endpoint**
   - [ ] Extract `jti` from JWT
   - [ ] Add token to blocklist
   - [ ] Set TTL = remaining time until expiration

4. **Add token refresh logic**
   - [ ] Implement `refresh_jwt()` function (sliding sessions)
   - [ ] Check if token < 1 hour from expiry
   - [ ] Issue new token with fresh expiration
   - [ ] Add `X-New-Token` header to response

**Deliverables**:
- ✅ Logout properly revokes tokens
- ✅ Revoked tokens cannot be used
- ✅ Tokens auto-refresh (sliding sessions)

**Testing**:
```python
def test_logout_revokes_token():
    token = login("rUSER...")

    # Logout
    client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})

    # Try to use token again
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401

def test_token_refresh():
    # Login with token expiring in 30 minutes
    token = login("rUSER...")

    # Make request
    response = client.get("/pools", headers={"Authorization": f"Bearer {token}"})

    # Should receive new token in header
    new_token = response.headers.get("X-New-Token")
    assert new_token is not None
```

---

### Week 2, Day 4-5: Security Hardening

#### Tasks

1. **Add rate limiting**
   ```bash
   pip install slowapi
   ```
   - [ ] Add rate limiter to FastAPI app
   - [ ] Limit `/auth/wallet/challenge` to 5 req/min per IP
   - [ ] Limit `/auth/wallet/login` to 10 req/min per IP
   - [ ] Return 429 status code when rate limited

2. **Add security headers**
   - [ ] Add middleware for security headers
   - [ ] Add `Strict-Transport-Security` (HSTS)
   - [ ] Add `X-Content-Type-Options: nosniff`
   - [ ] Add `X-Frame-Options: DENY`
   - [ ] Add `Content-Security-Policy`

3. **Add audit logging**
   - [ ] Install `structlog`
   - [ ] Log successful logins (wallet address, IP, timestamp)
   - [ ] Log failed logins (IP, reason, timestamp)
   - [ ] Log logout events
   - [ ] Log suspicious activity (rapid IP changes)

4. **Secrets management**
   - [ ] Move JWT secret to Supabase Vault (staging)
   - [ ] Document KMS migration (production)
   - [ ] Add secret rotation procedure
   - [ ] Never log secrets

**Deliverables**:
- ✅ Rate limiting prevents brute force
- ✅ Security headers in place
- ✅ Comprehensive audit logging
- ✅ Secrets properly managed

---

### Week 2 Checkpoint

**Success Criteria**:
- ✅ RLS enforces authorization at database level
- ✅ Logout properly revokes tokens
- ✅ Tokens auto-refresh (good UX)
- ✅ Rate limiting prevents abuse
- ✅ Security headers in place
- ✅ Audit logging working

**Risks**:
- ⚠️ Redis single point of failure (needs replication for production)
- ⚠️ Rate limiting by IP may affect users behind NAT

---

## Phase 3: Testing & Production Readiness (Week 3)

**Goal**: Comprehensive testing, monitoring, documentation

### Week 3, Day 1-2: Automated Testing

#### Tasks

1. **Auth unit tests**
   - [ ] Test JWT generation and verification
   - [ ] Test challenge generation and verification
   - [ ] Test signature verification
   - [ ] Test token blocklist
   - [ ] Test token refresh

2. **Auth integration tests**
   - [ ] Test complete login flow
   - [ ] Test logout flow
   - [ ] Test protected endpoint access
   - [ ] Test expired token handling
   - [ ] Test invalid token handling

3. **RLS tests**
   - [ ] Test users can only see own data
   - [ ] Test pool owners see applications
   - [ ] Test lenders see loans
   - [ ] Test service role bypasses RLS
   - [ ] Test cross-user access is denied

4. **Security tests**
   - [ ] Test signature replay attack prevention
   - [ ] Test rate limiting
   - [ ] Test XSS prevention (CSP headers)
   - [ ] Test CSRF prevention (CORS)
   - [ ] Test SQL injection (SQLAlchemy protects)

**Deliverables**:
- ✅ 90%+ test coverage for auth module
- ✅ All security scenarios tested
- ✅ CI/CD runs tests automatically

**Test Command**:
```bash
# Run all tests
PYTHONPATH=$(pwd) pytest backend/tests/ -v --cov=backend/auth

# Run security tests only
pytest backend/tests/test_security.py -v

# Run RLS tests only
pytest backend/tests/test_rls.py -v
```

---

### Week 3, Day 3: Monitoring & Observability

#### Tasks

1. **Set up metrics**
   - [ ] Track login success/failure rate
   - [ ] Track active sessions count
   - [ ] Track token refresh rate
   - [ ] Track rate limit hits
   - [ ] Track RLS policy violations

2. **Set up alerts**
   - [ ] Alert on high login failure rate (potential attack)
   - [ ] Alert on rate limit threshold (> 100/hour)
   - [ ] Alert on suspicious activity (IP hopping)
   - [ ] Alert on Redis downtime

3. **Set up dashboards**
   - [ ] Authentication metrics dashboard
   - [ ] Security events dashboard
   - [ ] User activity dashboard

4. **Log aggregation**
   - [ ] Centralize logs (CloudWatch, Datadog, etc.)
   - [ ] Add structured logging
   - [ ] Add request tracing

**Deliverables**:
- ✅ Metrics tracked and visualized
- ✅ Alerts configured
- ✅ Logs aggregated

---

### Week 3, Day 4: Documentation & Knowledge Transfer

#### Tasks

1. **Update documentation**
   - [ ] Update docs/DEVELOPMENT.md with auth information
   - [ ] Update API documentation (Swagger/OpenAPI)
   - [ ] Create deployment guide
   - [ ] Create incident response playbook

2. **Create runbooks**
   - [ ] "How to rotate JWT secret"
   - [ ] "How to revoke all user tokens"
   - [ ] "How to handle security incident"
   - [ ] "How to debug RLS issues"

3. **Team training**
   - [ ] Walkthrough of auth system
   - [ ] Explain RLS policies
   - [ ] Explain token management
   - [ ] Explain monitoring and alerts

**Deliverables**:
- ✅ Comprehensive documentation
- ✅ Runbooks for common tasks
- ✅ Team trained on security

---

### Week 3, Day 5: Production Deployment

#### Tasks

1. **Pre-deployment checklist**
   - [ ] All tests passing
   - [ ] RLS policies reviewed and approved
   - [ ] JWT secret rotated (production secret)
   - [ ] Redis production instance set up
   - [ ] Environment variables configured
   - [ ] Monitoring and alerts enabled
   - [ ] Backup and rollback plan ready

2. **Staging deployment**
   - [ ] Deploy to staging environment
   - [ ] Run smoke tests
   - [ ] Test end-to-end user flows
   - [ ] Load test authentication endpoints
   - [ ] Verify RLS policies work
   - [ ] Verify monitoring works

3. **Production deployment**
   - [ ] Deploy during low-traffic window
   - [ ] Enable RLS gradually (table by table)
   - [ ] Monitor error rates
   - [ ] Monitor auth success rate
   - [ ] Monitor performance metrics

4. **Post-deployment verification**
   - [ ] Run smoke tests in production
   - [ ] Verify users can login
   - [ ] Verify protected endpoints work
   - [ ] Verify RLS policies enforced
   - [ ] Verify monitoring working

**Deliverables**:
- ✅ Production deployment successful
- ✅ All systems operational
- ✅ No regressions

---

### Week 3 Checkpoint

**Success Criteria**:
- ✅ Comprehensive test suite (90%+ coverage)
- ✅ Monitoring and alerts operational
- ✅ Documentation complete
- ✅ Production deployment successful
- ✅ Zero security vulnerabilities

---

## Post-Launch (Week 4+)

### Week 4: Stabilization & Optimization

- [ ] Monitor metrics closely
- [ ] Fix any bugs discovered in production
- [ ] Optimize slow queries (RLS overhead)
- [ ] User feedback collection

### Month 2: Advanced Features

- [ ] Active session management UI
- [ ] Remember me (30-day sessions)
- [ ] Device fingerprinting
- [ ] Suspicious activity auto-detection

### Month 3: Security Audit

- [ ] External security audit
- [ ] Penetration testing
- [ ] Compliance review (if needed)
- [ ] Address findings

---

## Risk Management

### Critical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| **RLS breaks existing functionality** | Medium | High | Thorough testing in staging first |
| **Token theft (XSS)** | Low | High | CSP headers, input sanitization |
| **Redis downtime** | Low | High | Redis replication, graceful degradation |
| **JWT secret leak** | Low | Critical | Use KMS, rotate immediately if suspected |
| **Performance degradation (RLS)** | Medium | Medium | Index optimization, caching |

### Mitigation Strategies

1. **Gradual rollout**: Enable RLS table by table, monitor each
2. **Feature flags**: Ability to disable auth/RLS if critical issue
3. **Rollback plan**: Script to disable RLS and revert to previous state
4. **Monitoring**: Alert on auth failures, RLS errors, performance degradation

---

## Success Metrics

### Week 1 (Authentication)
- ✅ 100% of users can login via wallet
- ✅ < 2% login failure rate
- ✅ < 500ms average login time

### Week 2 (Authorization)
- ✅ Zero unauthorized data access
- ✅ < 100ms RLS overhead on queries
- ✅ > 99.9% auth endpoint uptime

### Week 3 (Production)
- ✅ Zero security incidents
- ✅ > 95% user satisfaction (auth UX)
- ✅ 90%+ test coverage
- ✅ < 1% false positive rate (legitimate users blocked)

---

## Resource Requirements

### Team

- **Backend Engineer** (1.0 FTE) - Auth implementation, RLS policies
- **Frontend Engineer** (0.5 FTE) - Wallet integration, auth UI
- **DevOps Engineer** (0.25 FTE) - Redis setup, monitoring, deployment
- **QA Engineer** (0.5 FTE) - Security testing, RLS testing
- **Security Reviewer** (0.1 FTE) - Code review, policy review

### Infrastructure

- **Redis** - $10-30/month (managed service)
- **Monitoring** - $20-50/month (Datadog/CloudWatch)
- **KMS** (production) - $1/month per key
- **Load testing** - $50 (one-time, temporary instances)

**Total**: ~$100-150/month ongoing

---

## Rollback Plan

If critical issues arise during deployment:

### Immediate Rollback (< 5 minutes)

```sql
-- Disable RLS on all tables
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE pools DISABLE ROW LEVEL SECURITY;
ALTER TABLE applications DISABLE ROW LEVEL SECURITY;
ALTER TABLE loans DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_mpt_balances DISABLE ROW LEVEL SECURITY;
```

### Full Rollback (< 30 minutes)

1. Revert code deployment (previous version)
2. Disable RLS (SQL above)
3. Clear Redis (blocklist)
4. Notify users of temporary maintenance
5. Investigate issue in staging

---

## Communication Plan

### Week 1
- **Daily standup**: Progress updates, blockers
- **End-of-week demo**: Show login flow to stakeholders

### Week 2
- **Mid-week review**: RLS policies approval
- **Security review**: External review of implementation

### Week 3
- **Pre-launch review**: Final go/no-go decision
- **Launch announcement**: Notify users of new security features

---

## Appendix: Checklists

### Development Checklist

- [ ] JWT generation and verification
- [ ] Challenge generation and storage
- [ ] Signature verification (XRPL)
- [ ] Auth endpoints (challenge, login, logout, me)
- [ ] FastAPI dependencies (get_current_user)
- [ ] Frontend auth store (Zustand)
- [ ] Frontend wallet integration
- [ ] Frontend API client (auto token refresh)
- [ ] RLS migration SQL
- [ ] RLS policies for all tables
- [ ] Token blocklist (Redis)
- [ ] Token refresh (sliding sessions)
- [ ] Rate limiting
- [ ] Security headers
- [ ] Audit logging
- [ ] Unit tests
- [ ] Integration tests
- [ ] Security tests
- [ ] RLS tests
- [ ] Monitoring and alerts
- [ ] Documentation

### Deployment Checklist

- [ ] Generate production JWT secret
- [ ] Store secret in KMS/Vault
- [ ] Set up production Redis (with replication)
- [ ] Configure CORS for production domain
- [ ] Enable HTTPS (enforce with HSTS)
- [ ] Deploy to staging
- [ ] Run smoke tests in staging
- [ ] Load test authentication
- [ ] Security review (internal)
- [ ] Security review (external, optional)
- [ ] Deploy to production (gradual rollout)
- [ ] Monitor error rates
- [ ] Monitor auth success rate
- [ ] Verify RLS policies enforced
- [ ] Verify monitoring working
- [ ] User communication (new login flow)

---

**Roadmap Version**: 1.0
**Last Updated**: 2025-10-26
**Next Review**: End of Week 1
**Owner**: Backend Team Lead
**Status**: Ready for Execution
