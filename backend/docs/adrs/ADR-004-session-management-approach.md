# ADR-004: Session Management Approach

**Status**: Accepted
**Date**: 2025-10-26
**Deciders**: System Architect
**Technical Story**: Define session lifecycle and token management strategy

---

## Context

After deciding on JWT-based authentication (ADR-001), we need to define how sessions are managed throughout their lifecycle:

1. **Session Creation**: When user connects wallet and signs challenge
2. **Session Duration**: How long should sessions last?
3. **Token Refresh**: How to maintain sessions without repeated wallet signatures
4. **Session Revocation**: How to logout or invalidate compromised tokens
5. **Multi-Device**: Should users be able to have concurrent sessions?
6. **Session Storage**: Where to store session state (if any)?

### User Experience Requirements

- ✅ Sign wallet once per session (not on every request)
- ✅ Sessions persist across browser refreshes
- ✅ Clear logout functionality
- ✅ Automatic re-authentication when session expires
- ✅ Support multiple devices/browsers (desktop + mobile)

### Security Requirements

- ✅ Limited session lifetime (minimize compromise window)
- ✅ Token revocation capability (logout, suspicious activity)
- ✅ Detection of stolen/leaked tokens
- ✅ Prevention of token replay attacks
- ✅ Secure token storage (client-side)

---

## Options Considered

### Option 1: Short-Lived Tokens (1 hour) with No Refresh

**Approach**: JWT expires in 1 hour. User must re-authenticate via wallet signature.

```javascript
// Login
const { token } = await api.login(walletAddress, signature)
localStorage.setItem('auth_token', token)

// After 1 hour
// Token expires, user must connect wallet again
```

**Pros**:
- ✅ **Simple implementation** (no refresh mechanism)
- ✅ **High security** (short-lived tokens)
- ✅ **Stateless** (no refresh token storage)
- ✅ **Self-cleaning** (tokens auto-expire)

**Cons**:
- ❌ **Poor UX** (re-auth every hour)
- ❌ **Friction** (Xumm app popup hourly)
- ❌ **User frustration** (mid-transaction expiration)

**Verdict**: ❌ **Rejected** - UX is unacceptable for lending marketplace

---

### Option 2: Long-Lived Tokens (30 days) with No Refresh

**Approach**: JWT expires in 30 days. User stays logged in for a month.

```javascript
const { token } = await api.login(walletAddress, signature)
// Token valid for 30 days
localStorage.setItem('auth_token', token)
```

**Pros**:
- ✅ **Excellent UX** (login once per month)
- ✅ **Simple implementation** (no refresh logic)
- ✅ **Stateless** (no server-side session state)

**Cons**:
- ❌ **Security risk** (30-day window if token stolen)
- ❌ **Cannot revoke** (JWT is stateless)
- ❌ **No logout** (token still valid after "logout")
- ❌ **Compromised token** has long lifetime

**Verdict**: ❌ **Rejected** - Security risk too high

---

### Option 3: Access Token + Refresh Token Pattern

**Approach**: Short-lived access token (15min) + long-lived refresh token (30 days).

```
Login Flow:
1. User signs wallet challenge
2. Backend issues:
   - Access Token (JWT, 15min expiration)
   - Refresh Token (secure random string, 30 days)
3. Store refresh token in database (users.refresh_token)

Request Flow:
1. Client sends access token with each request
2. If access token expired (401), use refresh token to get new access token
3. Refresh token endpoint validates and issues new access+refresh tokens

Logout Flow:
1. Client calls /logout endpoint
2. Backend deletes refresh token from database
3. Access token becomes useless after 15min (can't refresh)
```

**Pros**:
- ✅ **Best security** (short access token lifetime)
- ✅ **Good UX** (transparent token refresh)
- ✅ **Revocable** (delete refresh token from DB)
- ✅ **Industry standard** (OAuth 2.0 pattern)
- ✅ **Detect theft** (refresh token used from new IP)

**Cons**:
- ⚠️ **Stateful** (refresh tokens in database)
- ⚠️ **Complexity** (refresh logic in frontend + backend)
- ⚠️ **Database overhead** (refresh token storage + queries)

**Verdict**: ✅ **Strong candidate** - Best security/UX trade-off

---

### Option 4: Sliding Session with Single Token (RECOMMENDED)

**Approach**: Medium-lived JWT (24 hours) with sliding expiration.

```
Login Flow:
1. User signs wallet challenge
2. Backend issues JWT with 24-hour expiration
3. JWT includes:
   - iat (issued at): timestamp
   - exp (expires): iat + 24 hours
   - wallet_address: user's address

Request Flow:
1. Client sends JWT with each request
2. Backend checks expiration
3. If token < 1 hour from expiration AND user active:
   - Issue new token with fresh 24-hour expiration
   - Return in response header: X-New-Token
4. Frontend detects X-New-Token header, updates localStorage

Logout Flow:
1. Client calls /logout
2. Backend adds token to blocklist (Redis/DB) with TTL = remaining time
3. Client deletes token from localStorage

Token Blocklist Check:
- On each request, check if token JTI in blocklist
- If blocklisted, reject with 401
- Blocklist entries expire automatically (TTL = token exp - now)
```

**Pros**:
- ✅ **Good UX** (stay logged in for 24h+, auto-extends if active)
- ✅ **Reasonable security** (tokens expire within 24h)
- ✅ **Logout works** (blocklist prevents use)
- ✅ **Simpler than refresh tokens** (single token flow)
- ✅ **Automatic cleanup** (Redis TTL expires blocklist entries)

**Cons**:
- ⚠️ **Requires Redis** (or in-memory cache for blocklist)
- ⚠️ **Slightly stateful** (blocklist storage)
- ⚠️ **Header management** (frontend must handle X-New-Token)

**Verdict**: ✅ **SELECTED** - Best balance for LendX use case

---

## Decision

**We will implement sliding sessions with a 24-hour JWT and token blocklist for revocation.**

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      SESSION LIFECYCLE                        │
└──────────────────────────────────────────────────────────────┘

1. LOGIN (User Connects Wallet)
   ┌──────────────┐
   │   Frontend   │
   └──────┬───────┘
          │ Xumm Sign-In
          │ (user approves in Xumm app)
          ▼
   ┌──────────────┐
   │   Backend    │ Verify signature
   │              │ Generate JWT:
   │              │  - exp: now + 24h
   │              │  - jti: unique ID
   │              │  - sub: wallet_address
   └──────┬───────┘
          │ JWT token
          ▼
   ┌──────────────┐
   │   Frontend   │ Store in localStorage
   └──────────────┘

2. AUTHENTICATED REQUEST
   ┌──────────────┐
   │   Frontend   │ Authorization: Bearer <JWT>
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   Backend    │ 1. Verify JWT signature
   │              │ 2. Check if expired
   │              │ 3. Check if in blocklist
   │              │ 4. Extract wallet_address from sub
   │              │ 5. If < 1h until expiry: issue new token
   └──────┬───────┘
          │ Response + X-New-Token (if refreshed)
          ▼
   ┌──────────────┐
   │   Frontend   │ If X-New-Token present, update localStorage
   └──────────────┘

3. LOGOUT
   ┌──────────────┐
   │   Frontend   │ POST /auth/logout + JWT
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   Backend    │ Add JWT.jti to Redis blocklist
   │              │ TTL = exp - now
   └──────┬───────┘
          │ 200 OK
          ▼
   ┌──────────────┐
   │   Frontend   │ Clear localStorage
   └──────────────┘

4. TOKEN EXPIRATION (after 24h of inactivity)
   ┌──────────────┐
   │   Frontend   │ Request with expired token
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   Backend    │ 401 Unauthorized
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │   Frontend   │ Redirect to wallet connect
   └──────────────┘
```

### JWT Structure

```json
{
  "iss": "lendx-api",
  "sub": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "aud": "lendx-frontend",
  "jti": "550e8400-e29b-41d4-a716-446655440000",
  "iat": 1729900800,
  "exp": 1729987200,
  "wallet_address": "rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "did": "did:xrpl:testnet:rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx",
  "network": "testnet"
}
```

**Field Descriptions**:
- `jti` (JWT ID): Unique identifier for revocation (UUID v4)
- `sub` (Subject): User's wallet address (used by RLS policies)
- `iat` (Issued At): Token creation timestamp
- `exp` (Expires): Expiration timestamp (iat + 24 hours)
- `wallet_address`: Redundant with `sub` for clarity
- `did`: User's DID (if available)
- `network`: XRPL network (testnet/mainnet) for validation

### Session Duration Configuration

| Session State | Duration | Action |
|---------------|----------|--------|
| **Initial Login** | 24 hours | User signs wallet challenge |
| **Active Session** | 24h (sliding) | Auto-refresh if < 1h to expiry |
| **Inactive Session** | 24h (expires) | Must re-authenticate |
| **Logout** | Immediate | Token blocklisted |
| **Security Revocation** | Immediate | Admin adds all user's tokens to blocklist |

### Token Refresh Logic

```python
# backend/auth/middleware.py
from datetime import datetime, timedelta

def check_token_refresh(token: dict) -> Optional[str]:
    """Check if token should be refreshed (< 1 hour to expiry)."""
    exp = datetime.fromtimestamp(token['exp'])
    now = datetime.now()
    time_to_expiry = (exp - now).total_seconds()

    # Refresh if less than 1 hour remaining
    if time_to_expiry < 3600:
        # Generate new token with same claims but fresh expiration
        new_token = generate_jwt(
            wallet_address=token['wallet_address'],
            did=token.get('did'),
            network=token['network']
        )
        return new_token

    return None
```

```javascript
// frontend/lib/api/client.ts
async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('auth_token')

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: token ? `Bearer ${token}` : '',
    },
  })

  // Check for refreshed token in response headers
  const newToken = response.headers.get('X-New-Token')
  if (newToken) {
    localStorage.setItem('auth_token', newToken)
    console.log('Token refreshed automatically')
  }

  if (response.status === 401) {
    // Token expired or invalid, redirect to login
    localStorage.removeItem('auth_token')
    window.location.href = '/auth/connect'
  }

  return response
}
```

### Token Blocklist (Redis)

```python
# backend/auth/blocklist.py
import redis
from datetime import datetime

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def blocklist_token(jti: str, exp: int):
    """Add token to blocklist until it expires."""
    now = int(datetime.now().timestamp())
    ttl = max(exp - now, 0)  # Remaining time until expiration

    if ttl > 0:
        redis_client.setex(f"blocklist:{jti}", ttl, "1")

def is_token_blocklisted(jti: str) -> bool:
    """Check if token is blocklisted."""
    return redis_client.exists(f"blocklist:{jti}") > 0

def blocklist_all_user_tokens(wallet_address: str):
    """Blocklist all tokens for a user (security incident)."""
    # This requires tracking all active tokens per user
    # Implementation depends on whether we store active sessions
    # For now, user can still use tokens until they expire (max 24h)
    # Future: maintain active_tokens set in Redis
    pass
```

---

## Multi-Device Support

Users can have **concurrent sessions** on multiple devices:

- Each device gets its own JWT (unique `jti`)
- Logging out on one device doesn't affect others
- All devices auto-refresh their tokens independently

**Optional: Session Management UI** (future enhancement):
```
Active Sessions:
- Chrome on MacBook (current)          [Revoke]
- Safari on iPhone (last active 2h ago) [Revoke]
- Firefox on Windows (last active 1d ago) [Revoke]

[Revoke All Other Sessions]
```

Implementation:
1. Store active sessions in database (users.active_sessions JSON array)
2. Track device info (user agent, IP, last active time)
3. Allow user to revoke individual sessions (blocklist those JTIs)

---

## Security Considerations

### Token Theft Protection

| Attack Vector | Mitigation |
|---------------|------------|
| **XSS** (token stolen from localStorage) | CSP headers, sanitize inputs, use `httpOnly` cookies (future) |
| **Token replay** | Short expiration (24h), HTTPS only, detect unusual IP changes |
| **Man-in-the-middle** | HTTPS enforced, HSTS headers, certificate pinning (mobile) |
| **Token leaked in logs** | Never log full tokens, only last 4 chars of JTI |
| **Session fixation** | Generate new JTI on each refresh, invalidate old token |

### Suspicious Activity Detection

Monitor for:
- ✅ **Rapid IP changes** (token used from US then China within 1 minute)
- ✅ **Concurrent requests from different IPs** (shared token)
- ✅ **Unusual user agent changes** (device fingerprint mismatch)
- ✅ **High request rate** (automated abuse)

Action on suspicious activity:
1. Blocklist token immediately
2. Notify user via email/notification
3. Require wallet re-authentication

### Token Rotation on Security Events

Force all users to re-authenticate by:
1. Rotating JWT secret key
2. All existing tokens become invalid (signature verification fails)
3. Users must reconnect wallet to get new tokens

**Use sparingly** (major security breach only):
```python
# backend/auth/jwt.py
import os
from datetime import datetime

def rotate_jwt_secret():
    """Emergency JWT secret rotation."""
    # 1. Generate new secret
    new_secret = os.urandom(32).hex()

    # 2. Update environment variable (requires deployment)
    # or update in secrets manager (KMS/Vault)

    # 3. Log rotation event
    print(f"JWT secret rotated at {datetime.now()}")

    # 4. All existing tokens are now invalid
    # 5. Users will get 401 and must re-authenticate
```

---

## Implementation Checklist

### Phase 1: Basic JWT Sessions (Week 1)
- [ ] Generate JWT secret key (store in .env / KMS)
- [ ] Implement `generate_jwt()` function
- [ ] Implement `verify_jwt()` function
- [ ] Create `/auth/wallet/login` endpoint (issues JWT)
- [ ] Create `get_current_user()` FastAPI dependency
- [ ] Frontend: store JWT in localStorage
- [ ] Frontend: include JWT in Authorization header

### Phase 2: Token Refresh (Week 1)
- [ ] Implement `check_token_refresh()` logic
- [ ] Add X-New-Token header to responses
- [ ] Frontend: detect and update token from header
- [ ] Test sliding expiration (active user stays logged in)

### Phase 3: Token Revocation (Week 2)
- [ ] Set up Redis instance (local dev + production)
- [ ] Implement `blocklist_token()` function
- [ ] Implement `is_token_blocklisted()` check in JWT verification
- [ ] Create `/auth/logout` endpoint
- [ ] Frontend: logout button clears token
- [ ] Test logout prevents further API access

### Phase 4: Security Hardening (Week 2-3)
- [ ] Add HTTPS-only enforcement
- [ ] Add security headers (CSP, HSTS)
- [ ] Implement rate limiting on auth endpoints
- [ ] Add logging for auth events (login, logout, failed attempts)
- [ ] Add monitoring for suspicious activity
- [ ] Test token theft scenarios

---

## Consequences

### Positive

✅ **Good UX**: Users stay logged in for 24h+, auto-refresh extends session

✅ **Good Security**: 24h max lifetime, revocable via blocklist

✅ **Simple Frontend**: Single token to manage, automatic refresh

✅ **Multi-Device**: Users can login on phone + desktop simultaneously

✅ **Observable**: Can track active sessions, detect abuse

### Negative

⚠️ **Redis Dependency**: Requires Redis for blocklist (adds infrastructure)

⚠️ **Stateful Revocation**: Not truly stateless due to blocklist

⚠️ **Token Storage**: localStorage vulnerable to XSS (future: httpOnly cookies)

### Trade-offs Made

| Decision | Trade-off |
|----------|-----------|
| 24h expiration | Security vs UX (balanced) |
| Sliding refresh | Complexity vs UX (worth it) |
| Redis blocklist | Statefulness vs revocation capability (necessary) |
| localStorage | XSS risk vs mobile app compatibility (acceptable with CSP) |

---

## Future Enhancements

### Phase 5+: Advanced Features

1. **Remember Me** (optional 30-day sessions)
   - Checkbox on login
   - Longer expiration but requires periodic re-auth for sensitive operations

2. **HttpOnly Cookies** (XSS protection)
   - Move token from localStorage to httpOnly cookie
   - Requires SameSite=Strict configuration
   - Better security but complicates mobile app

3. **Active Session Management UI**
   - Show all active devices
   - Revoke individual sessions
   - "Revoke all other sessions" button

4. **Device Fingerprinting**
   - Track device characteristics (user agent, screen size, timezone)
   - Alert on fingerprint mismatch

5. **Two-Factor Authentication** (for high-value operations)
   - Optional 2FA for loan approvals > $10k
   - Email or authenticator app

---

## Related ADRs

- **ADR-001**: Authentication Method Selection (JWT chosen)
- **ADR-002**: RLS Authorization (JWT.sub used in policies)
- **ADR-003**: Wallet Key Management (signing challenge messages)

---

## References

- [JWT Best Practices (RFC 8725)](https://datatracker.ietf.org/doc/html/rfc8725)
- [OAuth 2.0 Token Revocation](https://tools.ietf.org/html/rfc7009)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [Redis TTL Documentation](https://redis.io/commands/expire)
- [JWT.io](https://jwt.io/)

---

**Last Updated**: 2025-10-26
**Status**: Accepted ✅
**Implemented**: No (Ready for implementation)
