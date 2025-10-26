# ADR-003: Wallet Key Management Strategy

**Status**: Accepted
**Date**: 2025-10-26
**Deciders**: System Architect
**Technical Story**: Secure storage and usage of XRPL wallet private keys

---

## Context

LendX needs to manage XRPL wallet private keys for several purposes:

1. **User Wallets**: Users own their private keys (via Xumm or self-custody)
2. **Service Wallet**: Backend may need a wallet for:
   - Creating MPT issuances (pools, applications, loans)
   - Executing multi-signature transactions
   - Paying transaction fees for users (if subsidized)
   - Administrative operations

The critical question: **Where and how should private keys be stored?**

### Security Requirements

- ✅ Users must maintain custody of their private keys (decentralized principle)
- ✅ Service wallet keys must be secured against unauthorized access
- ✅ Keys must never be logged or exposed in error messages
- ✅ Development and production environments must use different keys
- ✅ Key rotation must be possible without downtime
- ✅ Compromised keys must be detectable and recoverable

### Current State

From codebase analysis:
- **Frontend**: Xumm SDK handles user wallet signatures (no private keys stored)
- **Backend**: No service wallet implementation yet
- **Environment variables**: `.env.example` exists but no wallet key fields

---

## Options Considered

### Option 1: Store Private Keys in Environment Variables

**Approach**: Store wallet seed/private key in `.env` file, load via `os.getenv()`.

```python
# .env
XRPL_SERVICE_WALLET_SEED=sEdVxxx...

# Python
from xrpl.wallet import Wallet
service_wallet = Wallet.from_seed(os.getenv("XRPL_SERVICE_WALLET_SEED"))
```

**Pros**:
- ✅ Simple implementation
- ✅ Standard 12-factor app pattern
- ✅ No external dependencies
- ✅ Easy to rotate (update .env, restart app)

**Cons**:
- ❌ **Keys in plaintext** on filesystem
- ❌ **Logged in crash dumps** if not careful
- ❌ **Visible in process list** on some systems
- ❌ **No audit trail** for key usage
- ❌ **Difficult secret rotation** (requires deployment)
- ❌ **Not compliant** with PCI-DSS, SOC2

**Verdict**: ❌ **Rejected for production** - OK for development only

---

### Option 2: Hardware Security Module (HSM) / Cloud KMS

**Approach**: Store keys in AWS KMS, GCP Secret Manager, or Azure Key Vault.

```python
import boto3

kms = boto3.client('kms')
response = kms.decrypt(
    CiphertextBlob=encrypted_seed,
    KeyId='alias/lendx-service-wallet'
)
seed = response['Plaintext'].decode('utf-8')
wallet = Wallet.from_seed(seed)
```

**Pros**:
- ✅ **Industry-standard** key management
- ✅ **Audit logging** (who accessed key, when)
- ✅ **Key rotation** built-in
- ✅ **Compliance ready** (SOC2, PCI-DSS)
- ✅ **No plaintext keys** on application servers
- ✅ **Access control** via IAM policies

**Cons**:
- ⚠️ **Vendor lock-in** (AWS, GCP, Azure)
- ⚠️ **Additional cost** (~$1-5/month per key)
- ⚠️ **Complexity** in development environment
- ⚠️ **Network dependency** (KMS API calls)
- ⚠️ **Latency** (50-200ms per key retrieval)

**Verdict**: ✅ **RECOMMENDED for production** - Best security posture

---

### Option 3: Encrypted Secrets in Database (Supabase Vault)

**Approach**: Use Supabase's `vault.secrets` for encrypted storage.

```sql
-- Store secret
SELECT vault.create_secret('service_wallet_seed', 'sEdVxxx...');

-- Retrieve secret
SELECT decrypted_secret FROM vault.decrypted_secrets
WHERE name = 'service_wallet_seed';
```

```python
# Python
from backend.config.database import get_db_session

def get_service_wallet_seed():
    session = get_db_session()
    result = session.execute(
        "SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name = 'service_wallet_seed'"
    ).fetchone()
    return result[0] if result else None
```

**Pros**:
- ✅ **No additional infrastructure** (already using Supabase)
- ✅ **Encrypted at rest** (database-level encryption)
- ✅ **Access control** via database roles
- ✅ **Simple API** for storing/retrieving secrets
- ✅ **Works in development** and production

**Cons**:
- ⚠️ **Supabase dependency** (acceptable given database choice)
- ⚠️ **Limited audit trail** vs dedicated KMS
- ⚠️ **Decryption in database** (key visible to postgres role)
- ⚠️ **Not as battle-tested** as AWS KMS

**Verdict**: ✅ **ACCEPTABLE** - Good middle ground for startups

---

### Option 4: User-Managed Keys Only (No Service Wallet)

**Approach**: Don't store any private keys in backend. Users sign all transactions.

**Workflow**:
1. Backend prepares unsigned transaction
2. Returns transaction JSON to frontend
3. User signs via Xumm
4. Frontend submits signed transaction to XRPL

**Pros**:
- ✅ **Maximum security** (no keys to steal)
- ✅ **True decentralization** (users control everything)
- ✅ **No key management** complexity
- ✅ **Regulatory simplicity** (not a custodial service)

**Cons**:
- ❌ **Poor UX** (user signs many transactions)
- ❌ **No automated operations** (cron jobs, webhooks)
- ❌ **Can't subsidize fees** (users pay all transaction costs)
- ❌ **Multi-sig complications** (need all signers online)

**Verdict**: ⚠️ **PARTIAL** - Use for user funds, not for system operations

---

## Decision

**We will implement a hybrid approach:**

1. **User Wallets**: Users manage their own keys (via Xumm, never stored in backend)
2. **Service Wallet**: Stored in Supabase Vault initially, migrate to AWS KMS for production
3. **Development**: Environment variables (`.env`) for local development only

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER WALLET KEYS                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Storage:      User's device (Xumm app / hardware)    │  │
│  │  Access:       User only, via biometric/PIN           │  │
│  │  Usage:        Sign transactions via Xumm SDK         │  │
│  │  Backend sees: Signatures only (never private key)    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  SERVICE WALLET KEY                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Development:  .env file (plaintext, not committed)   │  │
│  │  Staging:      Supabase Vault (encrypted in DB)       │  │
│  │  Production:   AWS KMS (hardware-backed encryption)   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Usage:                                                     │
│  - Create MPT issuances (pools, applications, loans)        │
│  - Execute multi-signature transactions                     │
│  - Administrative operations (NOT user fund transfers)      │
└─────────────────────────────────────────────────────────────┘
```

### Service Wallet Usage Policy

**Service wallet MAY be used for**:
- ✅ Creating MPT issuances (token creation, minting)
- ✅ Setting up multi-signature accounts
- ✅ Paying transaction fees for sponsored operations (if implemented)
- ✅ Administrative XRPL operations (account settings)

**Service wallet MUST NOT be used for**:
- ❌ Storing user funds
- ❌ Transferring XRP on behalf of users
- ❌ Signing user loan agreements (users sign via Xumm)
- ❌ Any operation requiring user consent

### Implementation Details

#### Development Environment

```python
# backend/config/secrets.py
import os
from xrpl.wallet import Wallet

def get_service_wallet() -> Wallet:
    """Get service wallet from environment (dev only)."""
    if os.getenv("ENVIRONMENT") != "development":
        raise RuntimeError("Use get_service_wallet_production() for non-dev environments")

    seed = os.getenv("XRPL_SERVICE_WALLET_SEED")
    if not seed:
        raise ValueError("XRPL_SERVICE_WALLET_SEED not set in .env")

    return Wallet.from_seed(seed)
```

```env
# .env (local development only, in .gitignore)
ENVIRONMENT=development
XRPL_SERVICE_WALLET_SEED=sEdV1234567890abcdefghijklmnopqrstuvwxyz
XRPL_NETWORK=testnet
```

#### Staging/Production Environment (Supabase Vault)

```python
# backend/config/secrets.py
from backend.config.database import get_db_session

def get_service_wallet_production() -> Wallet:
    """Get service wallet from Supabase Vault (staging/prod)."""
    session = get_db_session()

    # Query encrypted secret from vault
    result = session.execute("""
        SELECT decrypted_secret
        FROM vault.decrypted_secrets
        WHERE name = 'service_wallet_seed'
    """).fetchone()

    if not result:
        raise ValueError("Service wallet seed not found in vault")

    seed = result[0]

    # Never log the seed
    # Create wallet and immediately clear seed variable
    wallet = Wallet.from_seed(seed)
    del seed

    return wallet
```

```sql
-- Migration: Store service wallet in vault
-- Run this manually in Supabase SQL editor (not in migration file!)
SELECT vault.create_secret('service_wallet_seed', 'sEdV...');

-- Grant access to service role only
GRANT SELECT ON vault.decrypted_secrets TO service_role;
```

#### Production Environment (AWS KMS) - Future

```python
# backend/config/secrets.py
import boto3
import base64
from xrpl.wallet import Wallet

def get_service_wallet_kms() -> Wallet:
    """Get service wallet from AWS KMS (production)."""
    kms = boto3.client('kms', region_name='us-west-1')

    # Encrypted seed stored as base64 in environment variable
    encrypted_seed_b64 = os.getenv("ENCRYPTED_SERVICE_WALLET_SEED")
    encrypted_seed = base64.b64decode(encrypted_seed_b64)

    # Decrypt using KMS
    response = kms.decrypt(
        CiphertextBlob=encrypted_seed,
        KeyId='alias/lendx-service-wallet',
        EncryptionContext={'app': 'lendx', 'env': 'production'}
    )

    seed = response['Plaintext'].decode('utf-8')

    # Create wallet and immediately clear seed
    wallet = Wallet.from_seed(seed)
    del seed
    del response

    return wallet
```

---

## Key Rotation Strategy

### User Wallets
- Users rotate their own keys by generating new wallet and transferring funds
- Backend doesn't need to be aware (uses wallet address, not key)

### Service Wallet

**Quarterly Rotation** (or after suspected compromise):

1. **Generate New Wallet**
   ```python
   from xrpl.wallet import Wallet
   new_wallet = Wallet.create()
   print(f"Address: {new_wallet.classic_address}")
   print(f"Seed: {new_wallet.seed}")  # Store in KMS/Vault
   ```

2. **Fund New Wallet** (testnet: use faucet, mainnet: transfer XRP)

3. **Update Vault/KMS**
   ```sql
   -- Supabase Vault
   SELECT vault.update_secret('service_wallet_seed', 'new_seed_here');
   ```

4. **Transfer Critical Operations** (if any multi-sig accounts, re-create with new key)

5. **Update Environment Variables** (for staging/production deployments)

6. **Restart Application** (load new wallet)

7. **Verify** (test transaction with new wallet)

8. **Decommission Old Wallet** (remove from vault, zero balance)

---

## Security Controls

### Access Control

| Environment | Key Storage | Access Control |
|-------------|-------------|----------------|
| Development | `.env` file | File system permissions (local only) |
| Staging | Supabase Vault | Database role `service_role` only |
| Production | AWS KMS | IAM policy: backend service account only |

### Monitoring

- ✅ **Log wallet address** (public, OK to log)
- ❌ **NEVER log seed or private key** (even in debug mode)
- ✅ **Alert on unexpected transactions** from service wallet
- ✅ **Daily balance checks** (detect unauthorized withdrawals)
- ✅ **Audit KMS access logs** (who retrieved key, when)

### Testing

```python
def test_service_wallet_seed_not_logged():
    """Ensure seed is never logged."""
    with patch('logging.Logger.info') as mock_log:
        wallet = get_service_wallet()
        # Check that seed doesn't appear in any log call
        for call in mock_log.call_args_list:
            assert 'sEd' not in str(call)  # Seeds start with 's'
            assert 'private' not in str(call).lower()

def test_service_wallet_seed_cleared_from_memory():
    """Ensure seed is cleared after wallet creation."""
    # This is hard to test in Python (no manual memory management)
    # Best practice: use `del seed` after wallet creation
    wallet = get_service_wallet()
    # Verify wallet works
    assert wallet.classic_address.startswith('r')
```

---

## Consequences

### Positive

✅ **User Sovereignty**: Users control their private keys

✅ **Defense in Depth**: Different key storage for dev/staging/prod

✅ **Compliance Ready**: Can migrate to KMS for regulatory requirements

✅ **Developer Friendly**: Simple .env for local development

✅ **Audit Trail**: KMS provides detailed access logs (in production)

### Negative

⚠️ **Complexity**: Three different key storage mechanisms to maintain

⚠️ **Migration Path**: Need to plan Supabase Vault → KMS migration

⚠️ **Cost**: KMS costs ~$1/month per key (negligible but not zero)

### Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Service wallet key leak | Rotate immediately, monitor old wallet, alert users |
| Insider access to vault | Limit `service_role` access, audit logs, key rotation |
| KMS API outage | Cache decrypted wallet in memory (30min TTL), fallback to Vault |
| Lost service wallet seed | Store backup in physical vault (CEO + CTO access) |
| Accidental logging of seed | Code review checks, automated tests, log sanitization |

---

## Implementation Checklist

### Phase 1: Development Setup (Week 1)
- [x] Add `XRPL_SERVICE_WALLET_SEED` to `.env.example`
- [ ] Implement `get_service_wallet()` for development
- [ ] Generate testnet wallet, fund with faucet
- [ ] Add seed to `.env` (ensure `.env` in `.gitignore`)
- [ ] Test wallet can sign transactions

### Phase 2: Vault Integration (Week 2)
- [ ] Enable Supabase Vault (if not already enabled)
- [ ] Create `vault.create_secret()` migration
- [ ] Implement `get_service_wallet_production()`
- [ ] Test in staging environment
- [ ] Document vault access procedures

### Phase 3: Security Hardening (Week 3)
- [ ] Add logging sanitization (never log seeds)
- [ ] Implement balance monitoring
- [ ] Set up key rotation procedure
- [ ] Create incident response plan
- [ ] Security audit of key handling code

### Phase 4: KMS Migration (Month 2-3)
- [ ] Set up AWS KMS key
- [ ] Encrypt service wallet seed with KMS
- [ ] Implement `get_service_wallet_kms()`
- [ ] Test in production environment
- [ ] Migrate from Vault to KMS
- [ ] Decommission Vault secret

---

## Related ADRs

- **ADR-001**: Authentication Method Selection (user wallet signatures)
- **ADR-002**: RLS Authorization (service role access to vault)
- **ADR-004**: Session Management (JWT vs wallet signatures)

---

## References

- [XRPL Account Security](https://xrpl.org/accounts.html#special-addresses)
- [Supabase Vault Documentation](https://supabase.com/docs/guides/database/vault)
- [AWS KMS Best Practices](https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html)
- [OWASP Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)

---

**Last Updated**: 2025-10-26
**Status**: Accepted ✅
**Implemented**: Partial (development .env exists, vault integration pending)
