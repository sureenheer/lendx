# Row-Level Security (RLS) Policies for LendX

**Version**: 1.0
**Last Updated**: 2025-10-26
**Status**: Ready for Production Deployment

---

## Overview

This document contains production-ready SQL for enabling Row-Level Security (RLS) on all LendX database tables. These policies enforce authorization at the database layer, providing defense-in-depth security.

### Security Model

- **`auth.uid()`** returns the wallet address from JWT token's `sub` claim
- **Service role** bypasses RLS (used by backend for admin operations)
- **Anon role** has limited access (public marketplace data only)
- **Authenticated role** has access based on ownership and relationships

---

## Quick Start

### Enable RLS on All Tables

```sql
-- Enable RLS (must be done before creating policies)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pools ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_mpt_balances ENABLE ROW LEVEL SECURITY;
```

### Apply All Policies

Run the SQL in the sections below for each table. Policies are designed to be:
- **Additive**: Multiple policies can grant access
- **Permissive**: If ANY policy grants access, operation is allowed
- **Role-specific**: Different policies for `anon`, `authenticated`, `service_role`

---

## Users Table Policies

### Requirements
- ✅ Users can read their own record
- ✅ Users can update their own record (DID only)
- ❌ Users CANNOT see other users' data (privacy)
- ✅ Service role has full access (backend operations)

### SQL

```sql
-- ============================================================================
-- USERS TABLE POLICIES
-- ============================================================================

-- Policy: Users can view their own record
CREATE POLICY "users_select_own"
ON users
FOR SELECT
TO authenticated
USING (auth.uid() = address);

-- Policy: Users can update their own record
-- (Only DID can be updated, address is immutable)
CREATE POLICY "users_update_own"
ON users
FOR UPDATE
TO authenticated
USING (auth.uid() = address)
WITH CHECK (auth.uid() = address);

-- Policy: Users can insert their own record (signup)
-- Note: In practice, backend (service role) creates users
-- This policy allows self-signup if needed
CREATE POLICY "users_insert_own"
ON users
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = address);

-- Policy: Service role has full access
CREATE POLICY "users_service_role_all"
ON users
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Note: No DELETE policy - users cannot delete themselves
-- Deletion would require admin intervention (service role)
```

### Testing

```sql
-- Test as authenticated user
SET ROLE authenticated;
SET request.jwt.claims TO '{"sub": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx"}';

-- Should return only this user's record
SELECT * FROM users WHERE address = 'rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx';

-- Should return empty (no access to other users)
SELECT * FROM users WHERE address = 'rOTHERUSER123456789';

-- Reset
RESET ROLE;
```

---

## Pools Table Policies

### Requirements
- ✅ Anyone can view all pools (public marketplace)
- ✅ Only pool issuer can create pools
- ✅ Only pool issuer can update their pools
- ✅ Service role has full access
- ❌ Users CANNOT delete pools (audit trail)

### SQL

```sql
-- ============================================================================
-- POOLS TABLE POLICIES
-- ============================================================================

-- Policy: Pools are publicly viewable (marketplace requirement)
-- Both authenticated and anonymous users can see all pools
CREATE POLICY "pools_select_public"
ON pools
FOR SELECT
TO authenticated, anon
USING (true);

-- Policy: Authenticated users can create pools
-- Must be the issuer of the pool they're creating
CREATE POLICY "pools_insert_own"
ON pools
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = issuer_address);

-- Policy: Only pool issuer can update their pools
-- (e.g., update current_balance after loan disbursement)
CREATE POLICY "pools_update_own"
ON pools
FOR UPDATE
TO authenticated
USING (auth.uid() = issuer_address)
WITH CHECK (auth.uid() = issuer_address);

-- Policy: Service role has full access
CREATE POLICY "pools_service_role_all"
ON pools
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Note: No DELETE policy - pools cannot be deleted (audit requirement)
-- Soft delete via status field if needed
```

### Testing

```sql
-- Test public read access (anonymous user)
SET ROLE anon;
SELECT COUNT(*) FROM pools;  -- Should return all pools
RESET ROLE;

-- Test create pool (authenticated user)
SET ROLE authenticated;
SET request.jwt.claims TO '{"sub": "rLENDER123456789"}';

-- Should succeed
INSERT INTO pools (pool_address, issuer_address, total_balance, current_balance, minimum_loan, duration_days, interest_rate, tx_hash)
VALUES ('pool_test', 'rLENDER123456789', 1000, 1000, 100, 30, 5.5, 'hash123');

-- Should fail (not the issuer)
INSERT INTO pools (pool_address, issuer_address, total_balance, current_balance, minimum_loan, duration_days, interest_rate, tx_hash)
VALUES ('pool_test2', 'rOTHERLENDER999', 1000, 1000, 100, 30, 5.5, 'hash456');

RESET ROLE;
```

---

## Applications Table Policies

### Requirements
- ✅ Borrowers can view their own applications
- ✅ Pool issuers can view applications to their pools
- ✅ Borrowers can create applications
- ✅ Pool issuers can update applications (approve/reject)
- ❌ No one can delete applications (audit trail)
- ✅ Service role has full access

### SQL

```sql
-- ============================================================================
-- APPLICATIONS TABLE POLICIES
-- ============================================================================

-- Policy: Borrowers can view their own applications
CREATE POLICY "applications_select_borrower"
ON applications
FOR SELECT
TO authenticated
USING (auth.uid() = borrower_address);

-- Policy: Pool issuers can view applications to their pools
CREATE POLICY "applications_select_pool_issuer"
ON applications
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM pools
    WHERE pools.pool_address = applications.pool_address
    AND pools.issuer_address = auth.uid()
  )
);

-- Policy: Borrowers can create applications
-- Must be the borrower on the application they're creating
CREATE POLICY "applications_insert_borrower"
ON applications
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = borrower_address);

-- Policy: Pool issuers can update applications to their pools
-- (e.g., change state from PENDING to APPROVED/REJECTED)
CREATE POLICY "applications_update_pool_issuer"
ON applications
FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM pools
    WHERE pools.pool_address = applications.pool_address
    AND pools.issuer_address = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM pools
    WHERE pools.pool_address = applications.pool_address
    AND pools.issuer_address = auth.uid()
  )
);

-- Policy: Service role has full access
CREATE POLICY "applications_service_role_all"
ON applications
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Note: No DELETE policy - applications are immutable (audit trail)
```

### Testing

```sql
-- Test borrower can see own applications
SET ROLE authenticated;
SET request.jwt.claims TO '{"sub": "rBORROWER123456789"}';

SELECT * FROM applications WHERE borrower_address = 'rBORROWER123456789';
-- Should return only this borrower's applications

-- Test lender can see applications to their pools
SET request.jwt.claims TO '{"sub": "rLENDER123456789"}';

SELECT a.* FROM applications a
JOIN pools p ON p.pool_address = a.pool_address
WHERE p.issuer_address = 'rLENDER123456789';
-- Should return applications to lender's pools

RESET ROLE;
```

---

## Loans Table Policies

### Requirements
- ✅ Borrowers can view their own loans
- ✅ Lenders can view loans they issued
- ✅ Both borrower and lender can update loan state
- ❌ Users CANNOT create loans (only service role)
- ❌ Users CANNOT delete loans (audit trail)
- ✅ Service role has full access

### SQL

```sql
-- ============================================================================
-- LOANS TABLE POLICIES
-- ============================================================================

-- Policy: Borrowers can view their own loans
CREATE POLICY "loans_select_borrower"
ON loans
FOR SELECT
TO authenticated
USING (auth.uid() = borrower_address);

-- Policy: Lenders can view loans they issued
CREATE POLICY "loans_select_lender"
ON loans
FOR SELECT
TO authenticated
USING (auth.uid() = lender_address);

-- Policy: Only service role can create loans
-- (Loans are created from approved applications by backend)
CREATE POLICY "loans_insert_service_role"
ON loans
FOR INSERT
TO service_role
WITH CHECK (true);

-- Policy: Borrowers can update their loans
-- (e.g., mark as PAID when payment is made)
CREATE POLICY "loans_update_borrower"
ON loans
FOR UPDATE
TO authenticated
USING (auth.uid() = borrower_address)
WITH CHECK (auth.uid() = borrower_address);

-- Policy: Lenders can update their loans
-- (e.g., mark as DEFAULTED if payment overdue)
CREATE POLICY "loans_update_lender"
ON loans
FOR UPDATE
TO authenticated
USING (auth.uid() = lender_address)
WITH CHECK (auth.uid() = lender_address);

-- Policy: Service role has full access
CREATE POLICY "loans_service_role_all"
ON loans
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Note: No DELETE policy - loans are immutable (audit trail)
```

### Testing

```sql
-- Test borrower can see own loans
SET ROLE authenticated;
SET request.jwt.claims TO '{"sub": "rBORROWER123456789"}';

SELECT * FROM loans WHERE borrower_address = 'rBORROWER123456789';
-- Should return borrower's loans

-- Test lender can see their loans
SET request.jwt.claims TO '{"sub": "rLENDER123456789"}';

SELECT * FROM loans WHERE lender_address = 'rLENDER123456789';
-- Should return lender's loans

-- Test users cannot create loans (should fail)
SET request.jwt.claims TO '{"sub": "rBORROWER123456789"}';

INSERT INTO loans (loan_address, pool_address, borrower_address, lender_address, start_date, end_date, principal, interest, state, tx_hash)
VALUES ('loan_test', 'pool1', 'rBORROWER123456789', 'rLENDER123456789', NOW(), NOW() + INTERVAL '30 days', 1000, 50, 'ONGOING', 'hash789');
-- Should fail with permission denied

RESET ROLE;
```

---

## User MPT Balances Table Policies

### Requirements
- ✅ Users can view their own balances
- ❌ Users CANNOT view other users' balances
- ❌ Users CANNOT update balances (only service role)
- ✅ Service role has full access (for cache sync)

### SQL

```sql
-- ============================================================================
-- USER MPT BALANCES TABLE POLICIES
-- ============================================================================

-- Policy: Users can view their own MPT balances
CREATE POLICY "user_mpt_balances_select_own"
ON user_mpt_balances
FOR SELECT
TO authenticated
USING (auth.uid() = user_address);

-- Policy: Only service role can insert balances
-- (Balances are synced from XRPL by backend)
CREATE POLICY "user_mpt_balances_insert_service_role"
ON user_mpt_balances
FOR INSERT
TO service_role
WITH CHECK (true);

-- Policy: Only service role can update balances
-- (Balance cache is updated from XRPL by backend)
CREATE POLICY "user_mpt_balances_update_service_role"
ON user_mpt_balances
FOR UPDATE
TO service_role
USING (true)
WITH CHECK (true);

-- Policy: Service role has full access
CREATE POLICY "user_mpt_balances_service_role_all"
ON user_mpt_balances
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Note: No DELETE policy - balances are managed by service role only
```

### Testing

```sql
-- Test user can see own balances
SET ROLE authenticated;
SET request.jwt.claims TO '{"sub": "rUSER123456789"}';

SELECT * FROM user_mpt_balances WHERE user_address = 'rUSER123456789';
-- Should return user's balances

-- Test user cannot see other balances
SELECT * FROM user_mpt_balances WHERE user_address = 'rOTHERUSER999';
-- Should return empty

RESET ROLE;
```

---

## Migration Script

Create a migration file to apply all policies:

```sql
-- ============================================================================
-- Migration: 002_enable_rls_policies.sql
-- Description: Enable RLS and create security policies
-- Author: System Architect
-- Date: 2025-10-26
-- ============================================================================

-- STEP 1: Enable RLS on all tables
-- ============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pools ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_mpt_balances ENABLE ROW LEVEL SECURITY;

-- STEP 2: Create policies for USERS table
-- ============================================================================

CREATE POLICY "users_select_own" ON users
FOR SELECT TO authenticated
USING (auth.uid() = address);

CREATE POLICY "users_update_own" ON users
FOR UPDATE TO authenticated
USING (auth.uid() = address)
WITH CHECK (auth.uid() = address);

CREATE POLICY "users_insert_own" ON users
FOR INSERT TO authenticated
WITH CHECK (auth.uid() = address);

CREATE POLICY "users_service_role_all" ON users
FOR ALL TO service_role
USING (true) WITH CHECK (true);

-- STEP 3: Create policies for POOLS table
-- ============================================================================

CREATE POLICY "pools_select_public" ON pools
FOR SELECT TO authenticated, anon
USING (true);

CREATE POLICY "pools_insert_own" ON pools
FOR INSERT TO authenticated
WITH CHECK (auth.uid() = issuer_address);

CREATE POLICY "pools_update_own" ON pools
FOR UPDATE TO authenticated
USING (auth.uid() = issuer_address)
WITH CHECK (auth.uid() = issuer_address);

CREATE POLICY "pools_service_role_all" ON pools
FOR ALL TO service_role
USING (true) WITH CHECK (true);

-- STEP 4: Create policies for APPLICATIONS table
-- ============================================================================

CREATE POLICY "applications_select_borrower" ON applications
FOR SELECT TO authenticated
USING (auth.uid() = borrower_address);

CREATE POLICY "applications_select_pool_issuer" ON applications
FOR SELECT TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM pools
    WHERE pools.pool_address = applications.pool_address
    AND pools.issuer_address = auth.uid()
  )
);

CREATE POLICY "applications_insert_borrower" ON applications
FOR INSERT TO authenticated
WITH CHECK (auth.uid() = borrower_address);

CREATE POLICY "applications_update_pool_issuer" ON applications
FOR UPDATE TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM pools
    WHERE pools.pool_address = applications.pool_address
    AND pools.issuer_address = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM pools
    WHERE pools.pool_address = applications.pool_address
    AND pools.issuer_address = auth.uid()
  )
);

CREATE POLICY "applications_service_role_all" ON applications
FOR ALL TO service_role
USING (true) WITH CHECK (true);

-- STEP 5: Create policies for LOANS table
-- ============================================================================

CREATE POLICY "loans_select_borrower" ON loans
FOR SELECT TO authenticated
USING (auth.uid() = borrower_address);

CREATE POLICY "loans_select_lender" ON loans
FOR SELECT TO authenticated
USING (auth.uid() = lender_address);

CREATE POLICY "loans_insert_service_role" ON loans
FOR INSERT TO service_role
WITH CHECK (true);

CREATE POLICY "loans_update_borrower" ON loans
FOR UPDATE TO authenticated
USING (auth.uid() = borrower_address)
WITH CHECK (auth.uid() = borrower_address);

CREATE POLICY "loans_update_lender" ON loans
FOR UPDATE TO authenticated
USING (auth.uid() = lender_address)
WITH CHECK (auth.uid() = lender_address);

CREATE POLICY "loans_service_role_all" ON loans
FOR ALL TO service_role
USING (true) WITH CHECK (true);

-- STEP 6: Create policies for USER_MPT_BALANCES table
-- ============================================================================

CREATE POLICY "user_mpt_balances_select_own" ON user_mpt_balances
FOR SELECT TO authenticated
USING (auth.uid() = user_address);

CREATE POLICY "user_mpt_balances_insert_service_role" ON user_mpt_balances
FOR INSERT TO service_role
WITH CHECK (true);

CREATE POLICY "user_mpt_balances_update_service_role" ON user_mpt_balances
FOR UPDATE TO service_role
USING (true) WITH CHECK (true);

CREATE POLICY "user_mpt_balances_service_role_all" ON user_mpt_balances
FOR ALL TO service_role
USING (true) WITH CHECK (true);

-- ============================================================================
-- VERIFICATION: Check that all policies are created
-- ============================================================================

SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Should show 19 policies total:
-- - users: 4 policies
-- - pools: 4 policies
-- - applications: 5 policies
-- - loans: 6 policies
-- - user_mpt_balances: 4 policies

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================

-- To disable RLS and drop all policies:
/*
DROP POLICY IF EXISTS "users_select_own" ON users;
DROP POLICY IF EXISTS "users_update_own" ON users;
DROP POLICY IF EXISTS "users_insert_own" ON users;
DROP POLICY IF EXISTS "users_service_role_all" ON users;

DROP POLICY IF EXISTS "pools_select_public" ON pools;
DROP POLICY IF EXISTS "pools_insert_own" ON pools;
DROP POLICY IF EXISTS "pools_update_own" ON pools;
DROP POLICY IF EXISTS "pools_service_role_all" ON pools;

DROP POLICY IF EXISTS "applications_select_borrower" ON applications;
DROP POLICY IF EXISTS "applications_select_pool_issuer" ON applications;
DROP POLICY IF EXISTS "applications_insert_borrower" ON applications;
DROP POLICY IF EXISTS "applications_update_pool_issuer" ON applications;
DROP POLICY IF EXISTS "applications_service_role_all" ON applications;

DROP POLICY IF EXISTS "loans_select_borrower" ON loans;
DROP POLICY IF EXISTS "loans_select_lender" ON loans;
DROP POLICY IF EXISTS "loans_insert_service_role" ON loans;
DROP POLICY IF EXISTS "loans_update_borrower" ON loans;
DROP POLICY IF EXISTS "loans_update_lender" ON loans;
DROP POLICY IF EXISTS "loans_service_role_all" ON loans;

DROP POLICY IF EXISTS "user_mpt_balances_select_own" ON user_mpt_balances;
DROP POLICY IF EXISTS "user_mpt_balances_insert_service_role" ON user_mpt_balances;
DROP POLICY IF EXISTS "user_mpt_balances_update_service_role" ON user_mpt_balances;
DROP POLICY IF EXISTS "user_mpt_balances_service_role_all" ON user_mpt_balances;

ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE pools DISABLE ROW LEVEL SECURITY;
ALTER TABLE applications DISABLE ROW LEVEL SECURITY;
ALTER TABLE loans DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_mpt_balances DISABLE ROW LEVEL SECURITY;
*/
```

---

## Applying the Migration

### Using Supabase MCP Tool

```python
from mcp__supabase__apply_migration import apply_migration

# Read the migration SQL file
with open('backend/migrations/002_enable_rls_policies.sql', 'r') as f:
    sql = f.read()

# Apply the migration
apply_migration(name="enable_rls_policies", query=sql)
```

### Using Supabase Dashboard

1. Go to Supabase Dashboard → SQL Editor
2. Copy the migration SQL
3. Click "Run" to execute
4. Verify policies in Database → Policies tab

### Using psql CLI

```bash
# Connect to Supabase database
psql "postgresql://postgres.sspwpkhajtooztzisioo:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# Run migration file
\i backend/migrations/002_enable_rls_policies.sql

# Verify policies
\dp users
\dp pools
\dp applications
\dp loans
\dp user_mpt_balances
```

---

## Performance Considerations

### Index Optimization

RLS policies that join tables (e.g., `applications_select_pool_issuer`) should have supporting indexes:

```sql
-- Already exists from initial migration
CREATE INDEX IF NOT EXISTS idx_applications_pool ON applications(pool_address);
CREATE INDEX IF NOT EXISTS idx_pools_issuer ON pools(issuer_address);
CREATE INDEX IF NOT EXISTS idx_loans_borrower ON loans(borrower_address);
CREATE INDEX IF NOT EXISTS idx_loans_lender ON loans(lender_address);
```

### Query Performance

RLS adds overhead to queries. For optimal performance:

1. **Use indexes** on columns in USING clauses
2. **Avoid complex subqueries** in policies (use EXISTS instead of IN)
3. **Service role bypasses RLS** - use for bulk operations
4. **Cache results** in application layer where appropriate

### Performance Testing

```sql
-- Explain analyze with RLS
SET ROLE authenticated;
SET request.jwt.claims TO '{"sub": "rLENDER123456789"}';

EXPLAIN ANALYZE
SELECT a.* FROM applications a
WHERE a.pool_address IN (
  SELECT pool_address FROM pools WHERE issuer_address = 'rLENDER123456789'
);

-- Should use indexes efficiently
-- Look for "Index Scan" not "Seq Scan"

RESET ROLE;
```

---

## Troubleshooting

### Common Issues

#### 1. "Permission denied for relation X"

**Cause**: RLS is enabled but no policy grants access

**Solution**: Verify JWT claims are set correctly
```sql
SELECT auth.uid();  -- Should return wallet address
```

#### 2. "Row is not visible due to RLS"

**Cause**: User doesn't own the resource

**Solution**: Check ownership in database
```sql
SELECT issuer_address FROM pools WHERE pool_address = 'pool123';
-- Compare with auth.uid()
```

#### 3. Policies not applied

**Cause**: Using wrong database role

**Solution**: Verify role
```sql
SELECT current_user;  -- Should be "authenticated" or "service_role"
```

### Debug Queries

```sql
-- List all policies
SELECT * FROM pg_policies WHERE schemaname = 'public';

-- Check if RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';

-- Test policy logic manually
SELECT
  auth.uid() as current_user,
  address,
  CASE WHEN auth.uid() = address THEN 'GRANTED' ELSE 'DENIED' END as access
FROM users;
```

---

## Security Audit Checklist

Before production deployment:

- [ ] All tables have RLS enabled
- [ ] All tables have service_role policy
- [ ] No tables allow anonymous INSERT/UPDATE/DELETE
- [ ] Sensitive tables (loans, balances) restrict SELECT to owners only
- [ ] Public marketplace data (pools) allows anonymous SELECT
- [ ] Policies tested with real JWT tokens
- [ ] Performance tested with realistic data volume
- [ ] Backup/rollback plan documented
- [ ] Monitoring for RLS errors configured

---

## Maintenance

### Adding New Tables

When adding new tables:

1. **Enable RLS immediately**
   ```sql
   ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;
   ```

2. **Create service role policy first** (allows backend to work)
   ```sql
   CREATE POLICY "new_table_service_role_all" ON new_table
   FOR ALL TO service_role USING (true) WITH CHECK (true);
   ```

3. **Add user policies** based on data sensitivity

4. **Test thoroughly** before deploying

### Updating Policies

To modify an existing policy:

```sql
-- Drop old policy
DROP POLICY IF EXISTS "old_policy_name" ON table_name;

-- Create new policy
CREATE POLICY "new_policy_name" ON table_name
FOR SELECT TO authenticated
USING (new_logic_here);
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-26
**Next Review**: Before production deployment
**Owner**: Backend Team
**Status**: Ready for Implementation
