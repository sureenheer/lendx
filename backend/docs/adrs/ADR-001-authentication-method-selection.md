# ADR-001: Authentication Method Selection

**Status**: Accepted
**Date**: 2025-10-26
**Deciders**: System Architect
**Technical Story**: Implement authentication for LendX lending marketplace

---

## Context

LendX requires authentication to protect user data and enforce authorization rules. The application has unique requirements:

1. **Wallet-based identity**: Users are identified by XRPL wallet addresses (not email/password)
2. **Decentralized nature**: Users authenticate via cryptographic signatures, not passwords
3. **Dual client types**: Web application (Xumm wallet) and potential direct wallet connections
4. **Existing infrastructure**: Supabase PostgreSQL database with built-in authentication capabilities
5. **Session requirements**: Need persistent sessions for better UX, not just per-transaction signatures

### Options Considered

#### Option 1: Pure Wallet Signature Authentication (No Sessions)
**Approach**: Each API request includes a fresh signature proving wallet ownership.

**How it works**:
- Client signs a message containing (timestamp, endpoint, request body hash)
- Server verifies signature matches wallet address
- No sessions or tokens stored

**Pros**:
- Truly decentralized, no server-side session state
- Maximum security (every request authenticated)
- Simple backend implementation
- No token expiration issues

**Cons**:
- Poor UX (user must sign every API request via Xumm)
- High friction for read operations
- Xumm overhead (mobile app popups for each request)
- Cannot use Supabase RLS effectively (requires auth.uid())
- Performance overhead (signature verification on every request)

**Verdict**: ❌ **Rejected** - UX is unacceptable for a lending marketplace

---

#### Option 2: JWT with Wallet Signature for Login
**Approach**: User signs a challenge message once to get a JWT token, then uses JWT for subsequent requests.

**How it works**:
1. **Login Flow**:
   - Client requests challenge nonce from server
   - Client signs nonce with wallet (via Xumm)
   - Server verifies signature, issues JWT containing wallet address
2. **Subsequent Requests**:
   - Client includes JWT in Authorization header
   - Server validates JWT to extract wallet address
   - Backend uses wallet address for authorization logic

**Pros**:
- Good UX (sign once, use token for duration)
- Works with Supabase RLS (custom JWT claims)
- Industry standard approach (RFC 7519)
- Can set reasonable expiration (e.g., 24 hours)
- Supports both web and mobile clients
- Can include additional claims (DID, roles)

**Cons**:
- Server must manage JWT secret securely
- Need token refresh mechanism
- More complex than pure signature auth
- Requires session revocation mechanism for logout

**Verdict**: ✅ **Partially Suitable** - Good baseline but missing Supabase integration

---

#### Option 3: Supabase Auth with Custom Provider (RECOMMENDED)
**Approach**: Use Supabase Auth with a custom authentication provider for wallet signatures.

**How it works**:
1. **Custom Auth Handler**:
   - FastAPI endpoint receives signed challenge
   - Verifies signature against wallet address
   - Calls Supabase Admin API to create/update user
   - Issues Supabase JWT token with wallet address as user ID
2. **Supabase Session**:
   - Token conforms to Supabase JWT format
   - Works seamlessly with RLS policies
   - Supabase handles token refresh, expiration
3. **Authorization**:
   - RLS policies use `auth.uid()` which returns wallet address
   - Application-level checks use wallet address from JWT

**Pros**:
- ✅ Full integration with Supabase RLS
- ✅ Leverages Supabase's battle-tested auth infrastructure
- ✅ Built-in token refresh mechanism
- ✅ Admin API for user management
- ✅ Audit logging capabilities
- ✅ Can extend with additional auth methods later
- ✅ Supports service role for backend operations
- ✅ Good UX (sign once per session)

**Cons**:
- Requires Supabase dependency (already committed)
- More setup complexity initially
- Need to understand Supabase JWT format
- Custom provider implementation needed

**Verdict**: ✅ **SELECTED** - Best balance of security, UX, and integration

---

## Decision

**We will implement Supabase Auth with a custom wallet signature provider.**

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. User clicks "Connect Wallet"                      │  │
│  │  2. Xumm SDK creates SignIn payload                   │  │
│  │  3. User approves in Xumm app                         │  │
│  │  4. Frontend receives signature + wallet address      │  │
│  └───────────────────┬───────────────────────────────────┘  │
└────────────────────────┼───────────────────────────────────┘
                         │
                         │ POST /auth/wallet/login
                         │ { address, signature, message }
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. Verify signature matches address                  │  │
│  │  2. Check if user exists in DB (users table)          │  │
│  │  3. Create user if first-time                         │  │
│  │  4. Generate Supabase JWT with custom claims:         │  │
│  │     - sub: wallet_address                             │  │
│  │     - role: authenticated                             │  │
│  │     - exp: 24 hours from now                          │  │
│  │  5. Return JWT + user data                            │  │
│  └───────────────────┬───────────────────────────────────┘  │
└────────────────────────┼───────────────────────────────────┘
                         │
                         │ JWT Token
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. Store JWT in localStorage/cookie                  │  │
│  │  2. Include in Authorization header:                  │  │
│  │     Authorization: Bearer <jwt>                       │  │
│  │  3. Refresh before expiration                         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ Authenticated API Requests
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   SUPABASE DATABASE                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  RLS Policies:                                        │  │
│  │  - auth.uid() extracts wallet address from JWT        │  │
│  │  - Policies enforce access control                    │  │
│  │  - Example: WHERE auth.uid() = user_address           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### JWT Claims Structure

```json
{
  "iss": "https://sspwpkhajtooztzisioo.supabase.co/auth/v1",
  "sub": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "aud": "authenticated",
  "role": "authenticated",
  "wallet_address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "did": "did:xrpl:testnet:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "iat": 1729900800,
  "exp": 1729987200
}
```

### Key Technical Decisions

1. **User ID = Wallet Address**
   - `auth.uid()` returns the wallet address directly
   - Simplifies RLS policies (no lookup needed)
   - Consistent with XRPL identity model

2. **Session Duration**: 24 hours
   - Balance between security and UX
   - Requires re-authentication daily
   - Automatic refresh at 23 hours if user active

3. **Signature Challenge Format**:
   ```
   LendX Authentication
   Timestamp: 1729900800
   Nonce: a1b2c3d4e5f6...
   Chain: testnet

   By signing this message, you authorize access to your LendX account.
   This signature will not trigger any blockchain transaction.
   ```

4. **Backend Uses Service Role**
   - FastAPI connects with service_role key
   - Bypasses RLS for administrative operations
   - User context passed via JWT to RLS layer

---

## Consequences

### Positive

✅ **Seamless Supabase Integration**: RLS policies work out of the box with `auth.uid()`

✅ **Good UX**: Users sign once, not on every request

✅ **Scalable**: Supabase handles session management, token refresh, storage

✅ **Secure**: Leverages industry-standard JWT with cryptographic wallet signatures

✅ **Future-Proof**: Can add OAuth, email auth later without changing architecture

✅ **Audit Trail**: Supabase auth logs provide compliance audit trail

### Negative

⚠️ **Complexity**: Custom auth provider requires careful implementation

⚠️ **Supabase Dependency**: Locked into Supabase ecosystem (acceptable given database choice)

⚠️ **Initial Setup**: More work upfront than simple JWT implementation

### Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| JWT secret compromise | Rotate regularly, store in secure vault, use long random secret |
| Replay attacks | Include timestamp in signature challenge, reject old signatures (>5min) |
| Session hijacking | Use HTTPS only, secure cookie flags, short expiration |
| User confusion (signing challenge) | Clear UX messaging explaining it's not a transaction |

---

## Implementation Notes

### Phase 1: Basic Authentication (Week 1)

1. Create `/auth/wallet/challenge` endpoint (generates nonce)
2. Create `/auth/wallet/login` endpoint (verifies signature, issues JWT)
3. Add FastAPI dependency `get_current_user()` for protected endpoints
4. Frontend integration with Xumm wallet
5. Basic JWT validation middleware

### Phase 2: Supabase Integration (Week 1-2)

1. Configure Supabase JWT secret in backend
2. Issue Supabase-compatible JWTs from login endpoint
3. Test RLS policies with real JWTs
4. Implement token refresh endpoint
5. Add logout functionality (token revocation)

### Phase 3: Polish (Week 2)

1. Add rate limiting to auth endpoints
2. Implement session management UI
3. Add "remember me" option (longer-lived tokens)
4. Security logging and monitoring
5. Penetration testing

---

## Alternatives Considered (Detailed Analysis)

### Why Not OAuth/OIDC?
- Users don't have email addresses (wallet-based identity)
- OAuth designed for password-based systems
- Adds unnecessary complexity for blockchain auth
- Could be added later for hybrid auth (wallet + email)

### Why Not API Keys?
- Poor UX (users managing long strings)
- Difficult to rotate securely
- No standard expiration mechanism
- Can't leverage Supabase RLS

### Why Not Session Cookies?
- Harder for mobile apps to manage
- CORS complications with SameSite
- JWT more flexible for API-first architecture
- Supabase Auth uses JWT internally anyway

---

## Related ADRs

- **ADR-002**: RLS vs Application-Level Authorization (depends on this)
- **ADR-003**: Wallet Key Management Strategy (signing mechanism)
- **ADR-004**: Session Management Approach (token refresh, expiration)

---

## References

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [JWT Best Practices (RFC 8725)](https://datatracker.ietf.org/doc/html/rfc8725)
- [XRPL Signing Guide](https://xrpl.org/transaction-signing.html)
- [Xumm SDK Documentation](https://xumm.readme.io/)
- [Wallet-based Authentication Patterns](https://eips.ethereum.org/EIPS/eip-4361)

---

**Last Updated**: 2025-10-26
**Status**: Accepted ✅
**Implemented**: No (Ready for implementation)
