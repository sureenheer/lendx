# ADR-002: RLS vs Application-Level Authorization

**Status**: Accepted
**Date**: 2025-10-26
**Deciders**: System Architect
**Technical Story**: Determine authorization enforcement strategy

---

## Context

LendX needs to enforce authorization rules to ensure:
- Users can only access their own data
- Pool owners can manage their pools
- Lenders can approve applications to their pools
- Borrowers can only see their own loans

There are two primary places to enforce these rules:

1. **Database Layer (RLS)**: PostgreSQL Row-Level Security policies
2. **Application Layer**: Python code in FastAPI endpoints

The question is: **Which layer should enforce authorization, and how much should each layer do?**

### Authorization Requirements

From the database schema analysis:

**Users Table**:
- Users should read their own record
- Users should update only their own DID
- Public user discovery not required (privacy)

**Pools Table**:
- Anyone can view pools (public marketplace)
- Only pool issuer can create/update their pools
- Service role can manage pools (admin operations)

**Applications Table**:
- Borrowers can view their own applications
- Pool owners can view applications to their pools
- Borrowers can create applications
- Pool owners can update applications (approve/reject)
- Nobody can delete applications (audit trail)

**Loans Table**:
- Borrowers can view their own loans
- Lenders can view loans they issued
- Both parties can update loan state (payments)
- Service role creates loans (from approved applications)

**User MPT Balances**:
- Users can view only their own balances
- Service role updates balances (cache sync from XRPL)

---

## Options Considered

### Option 1: Application-Level Authorization Only

**Approach**: Disable RLS, implement all authorization in FastAPI code.

```python
@app.get("/applications/{application_id}")
async def get_application(application_id: str, current_user: str = Depends(get_current_user)):
    """Get application details."""
    application = db.query(Application).filter(Application.application_address == application_id).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Authorization in application layer
    pool = db.query(Pool).filter(Pool.pool_address == application.pool_address).first()
    if current_user != application.borrower_address and current_user != pool.issuer_address:
        raise HTTPException(status_code=403, detail="Access denied")

    return application.to_dict()
```

**Pros**:
- ✅ Simple mental model (all logic in one place)
- ✅ Easier to debug (Python code vs SQL)
- ✅ More flexible (complex authorization logic)
- ✅ Faster development initially

**Cons**:
- ❌ **Security risk**: Easy to forget authorization checks
- ❌ **No defense in depth**: One forgotten check = vulnerability
- ❌ **Code duplication**: Authorization repeated across endpoints
- ❌ **Testing burden**: Must test every endpoint for authorization
- ❌ **Database queries bypass protection**: Direct SQL queries bypass app logic
- ❌ **Service role has unlimited access**: No guardrails at database level

**Verdict**: ❌ **Rejected** - Too risky, single point of failure

---

### Option 2: RLS Only (Database-Level Authorization)

**Approach**: Enable RLS, implement all authorization in PostgreSQL policies.

```sql
-- Users can view own applications
CREATE POLICY "users_view_own_applications"
ON applications FOR SELECT
USING (auth.uid() = borrower_address);

-- Pool owners can view applications to their pools
CREATE POLICY "pool_owners_view_applications"
ON applications FOR SELECT
USING (
  auth.uid() IN (
    SELECT issuer_address
    FROM pools
    WHERE pool_address = applications.pool_address
  )
);
```

**Pros**:
- ✅ **Defense in depth**: Enforced at database level
- ✅ **Can't be bypassed**: Works for all queries (ORM, raw SQL)
- ✅ **Consistent**: Same rules apply everywhere
- ✅ **Separation of concerns**: Security separate from business logic
- ✅ **Audit-friendly**: Policies are versioned in migrations
- ✅ **Performance**: Postgres optimizes policies efficiently

**Cons**:
- ⚠️ **Complex SQL**: Harder to read than Python
- ⚠️ **Debugging**: PostgreSQL error messages can be cryptic
- ⚠️ **Limited flexibility**: Some authorization logic hard to express in SQL
- ⚠️ **Service role bypasses**: Need separate mechanism for admin operations

**Verdict**: ✅ **Strong candidate** - Excellent security but needs app-level supplement

---

### Option 3: Layered Authorization (RLS + Application Checks) - RECOMMENDED

**Approach**: Use RLS as the security foundation, add application-level checks for complex logic and better UX.

**Database Layer (RLS)**: Enforce fundamental access control
```sql
-- RLS ensures users can ONLY see allowed data
-- These policies are the security boundary
CREATE POLICY "users_view_own_applications"
ON applications FOR SELECT
USING (
  auth.uid() = borrower_address OR
  auth.uid() IN (SELECT issuer_address FROM pools WHERE pool_address = applications.pool_address)
);
```

**Application Layer**: Add business logic and UX improvements
```python
@app.get("/applications/{application_id}")
async def get_application(
    application_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get application details."""
    # RLS automatically filters this query
    # User will get 404 if they don't have access (not 403)
    application = db.query(Application).filter(
        Application.application_address == application_id
    ).first()

    if not application:
        # Could be "doesn't exist" or "no access"
        # RLS prevents information leakage
        raise HTTPException(status_code=404, detail="Application not found")

    # Optional: Add explicit check for better error messages
    # This is redundant with RLS but improves UX
    is_borrower = current_user == application.borrower_address
    pool = db.query(Pool).filter(Pool.pool_address == application.pool_address).first()
    is_pool_owner = current_user == pool.issuer_address if pool else False

    if not (is_borrower or is_pool_owner):
        # This should never happen due to RLS, but provides clear error
        raise HTTPException(status_code=403, detail="Access denied")

    # Add computed fields based on user role
    response = application.to_dict()
    response['user_role'] = 'borrower' if is_borrower else 'lender'
    response['can_approve'] = is_pool_owner and application.state == 'PENDING'

    return response
```

**Pros**:
- ✅ **Defense in depth**: RLS prevents unauthorized access
- ✅ **Better UX**: Application layer provides clear error messages
- ✅ **Fail-safe**: Even if app check is removed, RLS protects data
- ✅ **Flexibility**: Complex logic in Python, security in SQL
- ✅ **Best of both worlds**: Security + developer experience

**Cons**:
- ⚠️ **More code**: Policies + application checks (acceptable trade-off)
- ⚠️ **Potential redundancy**: Some checks in both layers
- ⚠️ **Learning curve**: Developers must understand both layers

**Verdict**: ✅ **SELECTED** - Best balance of security and maintainability

---

## Decision

**We will implement layered authorization with RLS as the security foundation and application-level checks for UX and complex logic.**

### Principles

1. **RLS is the Security Boundary**
   - All tables have RLS enabled in production
   - Policies enforce fundamental access control
   - Cannot be bypassed (except by service role)
   - Policies tested with automated tests

2. **Application Layer Enhances UX**
   - Provides clear error messages (403 vs 404)
   - Implements complex business logic
   - Adds computed fields based on user context
   - Handles multi-step authorization workflows

3. **Defense in Depth**
   - Even if application check is buggy, RLS prevents data leakage
   - Code review must verify RLS policies before production
   - Regular security audits of both layers

4. **Service Role for Admin Operations**
   - Backend uses service role to bypass RLS when needed
   - Carefully scoped (e.g., creating loans from approved applications)
   - Logged and monitored

### Authorization Matrix

| Resource | Action | Who | RLS Policy | App-Level Check |
|----------|--------|-----|------------|----------------|
| Users | SELECT | Self | `auth.uid() = address` | Return 404 if not found |
| Users | UPDATE | Self | `auth.uid() = address` | Validate DID format |
| Pools | SELECT | Anyone | `true` (public) | Add user-specific fields |
| Pools | INSERT | Owner | `auth.uid() = issuer_address` | Validate pool parameters |
| Pools | UPDATE | Owner | `auth.uid() = issuer_address` | Only allow balance updates |
| Applications | SELECT | Borrower OR Lender | `auth.uid() = borrower OR issuer` | Add role context |
| Applications | INSERT | Borrower | `auth.uid() = borrower_address` | Validate pool exists, amount OK |
| Applications | UPDATE | Lender | `auth.uid() = pool.issuer` | Only allow state transitions |
| Loans | SELECT | Borrower OR Lender | `auth.uid() IN (borrower, lender)` | Add payment status |
| Loans | INSERT | Service Role | Service role only | Create from approved application |
| Loans | UPDATE | Borrower OR Lender | `auth.uid() IN (borrower, lender)` | Validate state transitions |
| MPT Balances | SELECT | Self | `auth.uid() = user_address` | Check if stale, trigger refresh |
| MPT Balances | UPDATE | Service Role | Service role only | Sync from XRPL |

---

## Implementation Strategy

### Phase 1: Enable RLS with Basic Policies (Week 1)

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pools ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_mpt_balances ENABLE ROW LEVEL SECURITY;

-- Create basic policies (see RLS_POLICIES.md for full SQL)
-- Start with most restrictive policies, relax as needed
```

### Phase 2: Add Application-Level Checks (Week 1)

```python
# Create authorization utilities
from backend.auth.authorization import (
    require_pool_owner,
    require_application_access,
    require_loan_access,
)

@app.put("/pools/{pool_id}")
async def update_pool(
    pool_id: str,
    current_user: str = Depends(get_current_user),
    pool_owner: bool = Depends(require_pool_owner(pool_id))
):
    # pool_owner dependency does the check
    # If user doesn't own pool, 403 is raised
    ...
```

### Phase 3: Testing Both Layers (Week 2)

```python
# Test RLS policies directly
def test_application_rls_borrower_access():
    """Verify RLS allows borrower to see own application."""
    # Set JWT claims to borrower address
    set_jwt_claims({"sub": "rBORROWER123"})

    # Query should return borrower's applications only
    apps = db.query(Application).all()
    assert all(app.borrower_address == "rBORROWER123" for app in apps)

def test_application_rls_lender_access():
    """Verify RLS allows lender to see applications to their pools."""
    set_jwt_claims({"sub": "rLENDER456"})

    # Should see applications to pools they own
    apps = db.query(Application).all()
    for app in apps:
        pool = db.query(Pool).filter(Pool.pool_address == app.pool_address).first()
        assert pool.issuer_address == "rLENDER456"

def test_application_endpoint_authorization():
    """Verify API endpoint enforces authorization."""
    # Borrower can access their application
    response = client.get("/applications/app123", headers=borrower_auth_header)
    assert response.status_code == 200

    # Different borrower gets 404 (not 403 to prevent info leakage)
    response = client.get("/applications/app123", headers=other_borrower_auth_header)
    assert response.status_code == 404
```

---

## Consequences

### Positive

✅ **Maximum Security**: RLS provides bulletproof access control

✅ **Defense in Depth**: Two layers of protection

✅ **Better UX**: Clear error messages from application layer

✅ **Maintainable**: Complex logic in Python (easier than SQL)

✅ **Audit Trail**: RLS policies versioned in migrations

✅ **Fail-Safe**: Removing app check doesn't create vulnerability

### Negative

⚠️ **More Code**: Must maintain both RLS policies and app checks

⚠️ **Learning Curve**: Developers must understand RLS

⚠️ **Debugging**: Need to check both layers when access issues occur

### Migration Strategy

**Development Environment** (current state):
- RLS disabled for easier development
- Application-level checks optional
- Use service role key for all operations

**Staging Environment**:
- RLS enabled with permissive policies
- Application-level checks enforced
- Test all user flows thoroughly

**Production Environment**:
- RLS enabled with restrictive policies
- Application-level checks enforced
- Regular security audits
- Monitoring for authorization failures

---

## Related ADRs

- **ADR-001**: Authentication Method Selection (provides `auth.uid()`)
- **ADR-003**: Wallet Key Management (service role key handling)
- **ADR-004**: Session Management (token claims structure)

---

## References

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL RLS Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Defense in Depth Security](https://en.wikipedia.org/wiki/Defense_in_depth_(computing))
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)

---

**Last Updated**: 2025-10-26
**Status**: Accepted ✅
**Implemented**: No (RLS currently disabled for development)
