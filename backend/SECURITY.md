# LendX Database Security Advisory

**Generated**: 2025-10-26
**Status**: Development - RLS Disabled

---

## Current Security Status

### ⚠️ Security Advisories (5 Issues)

Supabase security linter has identified the following issues:

1. **RLS Disabled on `users` table** - [ERROR]
   - **Risk**: Table is publicly accessible without row-level security
   - **Remediation**: https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public

2. **RLS Disabled on `pools` table** - [ERROR]
   - **Risk**: Table is publicly accessible without row-level security
   - **Remediation**: https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public

3. **RLS Disabled on `applications` table** - [ERROR]
   - **Risk**: Table is publicly accessible without row-level security
   - **Remediation**: https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public

4. **RLS Disabled on `loans` table** - [ERROR]
   - **Risk**: Table is publicly accessible without row-level security
   - **Remediation**: https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public

5. **RLS Disabled on `user_mpt_balances` table** - [ERROR]
   - **Risk**: Table is publicly accessible without row-level security
   - **Remediation**: https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public

---

## Understanding Row-Level Security (RLS)

**What is RLS?**
Row-Level Security allows you to control which rows users can access in database tables based on their authentication credentials.

**Why is it important?**
- Prevents unauthorized access to sensitive data
- Ensures users can only see/modify their own data
- Adds defense-in-depth security layer
- Required for production Supabase applications

**Current Risk**:
Without RLS, any authenticated user with the `anon` or `service_role` key can:
- Read all users' data
- Access all pools, applications, and loans
- Modify or delete any records

---

## Enabling RLS (Production Requirement)

### Step 1: Enable RLS on All Tables

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pools ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_mpt_balances ENABLE ROW LEVEL SECURITY;
```

### Step 2: Create RLS Policies

#### Users Table Policies

```sql
-- Users can read their own record
CREATE POLICY "Users can view own record"
ON users FOR SELECT
USING (auth.uid()::text = address);

-- Users can update their own record
CREATE POLICY "Users can update own record"
ON users FOR UPDATE
USING (auth.uid()::text = address);

-- Service role can do everything (backend operations)
CREATE POLICY "Service role full access"
ON users FOR ALL
USING (auth.role() = 'service_role');
```

#### Pools Table Policies

```sql
-- Anyone can view pools (public marketplace)
CREATE POLICY "Pools are publicly viewable"
ON pools FOR SELECT
TO authenticated
USING (true);

-- Only pool issuer can create/update their pools
CREATE POLICY "Issuers can manage own pools"
ON pools FOR ALL
USING (auth.uid()::text = issuer_address);

-- Service role full access
CREATE POLICY "Service role full access"
ON pools FOR ALL
USING (auth.role() = 'service_role');
```

#### Applications Table Policies

```sql
-- Borrowers can view their own applications
CREATE POLICY "Borrowers view own applications"
ON applications FOR SELECT
USING (auth.uid()::text = borrower_address);

-- Pool issuers can view applications to their pools
CREATE POLICY "Lenders view pool applications"
ON applications FOR SELECT
USING (
  auth.uid()::text IN (
    SELECT issuer_address FROM pools WHERE pool_address = applications.pool_address
  )
);

-- Borrowers can create applications
CREATE POLICY "Borrowers create applications"
ON applications FOR INSERT
WITH CHECK (auth.uid()::text = borrower_address);

-- Pool issuers can update application state (approve/reject)
CREATE POLICY "Lenders update applications"
ON applications FOR UPDATE
USING (
  auth.uid()::text IN (
    SELECT issuer_address FROM pools WHERE pool_address = applications.pool_address
  )
);

-- Service role full access
CREATE POLICY "Service role full access"
ON applications FOR ALL
USING (auth.role() = 'service_role');
```

#### Loans Table Policies

```sql
-- Borrowers can view their loans
CREATE POLICY "Borrowers view own loans"
ON loans FOR SELECT
USING (auth.uid()::text = borrower_address);

-- Lenders can view their loans
CREATE POLICY "Lenders view own loans"
ON loans FOR SELECT
USING (auth.uid()::text = lender_address);

-- Only service role can create loans (from approved applications)
CREATE POLICY "Service role creates loans"
ON loans FOR INSERT
WITH CHECK (auth.role() = 'service_role');

-- Borrowers and lenders can update loan state (payments)
CREATE POLICY "Participants update loans"
ON loans FOR UPDATE
USING (
  auth.uid()::text = borrower_address OR
  auth.uid()::text = lender_address
);

-- Service role full access
CREATE POLICY "Service role full access"
ON loans FOR ALL
USING (auth.role() = 'service_role');
```

#### User MPT Balances Table Policies

```sql
-- Users can view their own balances
CREATE POLICY "Users view own balances"
ON user_mpt_balances FOR SELECT
USING (auth.uid()::text = user_address);

-- Service role manages balance cache
CREATE POLICY "Service role manages balances"
ON user_mpt_balances FOR ALL
USING (auth.role() = 'service_role');
```

### Step 3: Apply Policies

Create a migration file `002_enable_rls.sql` with the above SQL and apply it:

```bash
# Using Supabase MCP tool
mcp__supabase__apply_migration(
  name="enable_rls",
  query="<SQL from above>"
)
```

---

## Authentication Strategy

### Option 1: JWT Authentication (Recommended)

Use Supabase Auth with JWT tokens:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from supabase import create_client

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    """Verify JWT token and return user address"""
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    try:
        user = supabase.auth.get_user(token.credentials)
        return user.user.id  # This would be the wallet address
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")
```

### Option 2: Service Role (Backend Only)

For backend operations, use service role key:

```python
from backend.config.database import get_db_session

# Service role bypasses RLS
session = get_db_session()  # Uses service role key
users = session.query(User).all()  # Can see all users
```

---

## Security Checklist for Production

### Before Going Live

- [ ] Enable RLS on all tables
- [ ] Create and test RLS policies
- [ ] Implement JWT authentication
- [ ] Rotate all API keys (anon, service_role)
- [ ] Enable Supabase Auth
- [ ] Configure allowed authentication providers
- [ ] Set up email verification
- [ ] Enable MFA (multi-factor authentication)
- [ ] Configure CORS properly
- [ ] Enable audit logging
- [ ] Set up automated backups
- [ ] Test RLS policies thoroughly
- [ ] Document all policies
- [ ] Review security advisor regularly

### Ongoing Security

- [ ] Rotate credentials quarterly
- [ ] Review access logs monthly
- [ ] Monitor for suspicious activity
- [ ] Keep dependencies updated
- [ ] Run security audits
- [ ] Test disaster recovery
- [ ] Review and update policies as features change

---

## Development vs Production

### Development (Current Setup)

- ✅ RLS disabled for easier testing
- ✅ Backend uses service role key directly
- ✅ No authentication required
- ⚠️ **DO NOT use this in production**

### Production (Required Setup)

- ✅ RLS enabled on all tables
- ✅ Policies enforcing data access rules
- ✅ JWT authentication for all API calls
- ✅ Service role key only used server-side
- ✅ Regular security audits
- ✅ Monitoring and alerting

---

## Testing RLS Policies

```sql
-- Test as anonymous user
SET ROLE anon;
SET request.jwt.claims TO '{"sub": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"}';

-- Try to query users (should only see own record)
SELECT * FROM users;

-- Try to query another user's data (should fail)
SELECT * FROM users WHERE address != 'rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx';

-- Reset
RESET ROLE;
```

---

## Additional Security Measures

### 1. Input Validation

```python
from pydantic import BaseModel, validator

class CreatePoolRequest(BaseModel):
    amount: Decimal
    interest_rate: Decimal

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
```

### 2. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/pools")
@limiter.limit("5/minute")
async def create_pool(...):
    ...
```

### 3. SQL Injection Prevention

✅ **Already Protected**: SQLAlchemy ORM uses parameterized queries automatically

```python
# Safe - parameterized
session.query(User).filter(User.address == user_input).first()

# Dangerous - string interpolation (DON'T DO THIS)
session.execute(f"SELECT * FROM users WHERE address = '{user_input}'")
```

### 4. Secrets Management

```python
# Good - from environment
import os
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Bad - hardcoded
SECRET_KEY = "my-secret-key-123"  # NEVER DO THIS
```

---

## Incident Response Plan

If a security breach occurs:

1. **Immediate**: Rotate all API keys and secrets
2. **Assess**: Determine scope of breach (what data was accessed)
3. **Contain**: Disable affected accounts/services
4. **Notify**: Inform affected users (if PII was exposed)
5. **Remediate**: Fix the vulnerability
6. **Review**: Conduct post-mortem and update policies

---

## Resources

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/security.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Supabase Database Linter](https://supabase.com/docs/guides/database/database-linter)

---

**IMPORTANT**: This document should be reviewed and updated before deploying to production. RLS must be enabled for any production deployment.

*Last Updated: 2025-10-26*
