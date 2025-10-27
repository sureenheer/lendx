# LendX Production Deployment Guide

**CRITICAL: This guide contains security-sensitive information. Handle with care.**

> **Warning**: Do not deploy to mainnet without completing security audit and compliance review.

---

## Table of Contents

1. [Pre-Deployment Checklist](#1-pre-deployment-checklist)
2. [Frontend Deployment (Vercel)](#2-frontend-deployment-vercel)
3. [Backend Deployment](#3-backend-deployment)
4. [Database Setup (Supabase)](#4-database-setup-supabase)
5. [XRPL Configuration](#5-xrpl-configuration)
6. [Security Checklist](#6-security-checklist)
7. [Monitoring & Logging](#7-monitoring--logging)
8. [CI/CD Pipeline](#8-cicd-pipeline)
9. [Rollback Procedure](#9-rollback-procedure)
10. [Mainnet Considerations](#10-mainnet-considerations)

---

## 1. Pre-Deployment Checklist

### Security Audit Requirements

- [ ] **Code Security Review**
  - [ ] All SQL queries use parameterized statements (SQLAlchemy ORM)
  - [ ] Input validation on all API endpoints (Pydantic models)
  - [ ] Authentication/authorization implemented and tested
  - [ ] XRPL wallet private keys never stored in database
  - [ ] Rate limiting configured for all public endpoints
  - [ ] CORS configured for production domains only
  - [ ] Error messages don't leak sensitive information

- [ ] **Dependency Security**
  ```bash
  # Backend (Python)
  pip install safety
  safety check

  # Frontend (Node.js)
  cd frontend
  npm audit
  npm audit fix --force  # Only if safe
  ```

- [ ] **Environment Variables Audit**
  - [ ] All `.env.example` variables documented
  - [ ] No secrets committed to git
  - [ ] Production secrets stored in secure vault (e.g., 1Password, AWS Secrets Manager)
  - [ ] Different credentials for dev/staging/production
  - [ ] JWT_SECRET_KEY generated using: `openssl rand -hex 32`

- [ ] **Database Migrations Status**
  ```bash
  # Verify current migration state
  psql $DATABASE_URL -c "SELECT * FROM migrations ORDER BY version DESC LIMIT 5;"

  # Check for unapplied migrations
  ls backend/migrations/*.sql
  ```

- [ ] **XRPL Network Selection**
  - [ ] Testnet for staging environment
  - [ ] Mainnet only after full testing and security audit
  - [ ] Network configured in environment variable: `XRPL_NETWORK=testnet|mainnet`

- [ ] **Test Coverage**
  ```bash
  # Run full backend test suite
  export SUPABASE_DB_PASSWORD="test_password"
  PYTHONPATH=$(pwd) pytest backend/tests/ -v --cov=backend --cov-report=html

  # Minimum coverage: 80%
  # Current coverage areas:
  # ✅ Database models (users, pools, applications, loans)
  # ✅ XRPL client operations
  # ⚠️  API endpoints (add integration tests)
  # ⚠️  Frontend components (add unit tests)
  ```

---

## 2. Frontend Deployment (Vercel)

### Current Status
- **Live URL**: https://lendxrp.vercel.app
- **Platform**: Vercel
- **Framework**: Next.js 14 with App Router

### Environment Variables

Configure these in Vercel Dashboard → Project Settings → Environment Variables:

```env
# XUMM Wallet Integration
NEXT_PUBLIC_XUMM_API_KEY=your_production_xumm_api_key
NEXT_PUBLIC_XUMM_API_SECRET=your_production_xumm_api_secret

# Backend API
NEXT_PUBLIC_API_URL=https://api.lendxrp.com  # Your backend URL

# XRPL Network
NEXT_PUBLIC_XRPL_NETWORK=testnet  # Change to 'mainnet' for production

# Analytics (optional)
NEXT_PUBLIC_VERCEL_ANALYTICS_ID=your_analytics_id
```

### Build Configuration

**vercel.json** (create if doesn't exist):
```json
{
  "buildCommand": "cd frontend && npm install --legacy-peer-deps && npm run build",
  "outputDirectory": "frontend/.next",
  "devCommand": "cd frontend && npm run dev",
  "installCommand": "cd frontend && npm install --legacy-peer-deps",
  "framework": "nextjs",
  "regions": ["iad1"],
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 10
    }
  }
}
```

**Important**: Next.js 14 with React 19 requires `--legacy-peer-deps` flag.

### Custom Domain Setup

1. **Add Domain in Vercel**
   - Go to Project Settings → Domains
   - Add your custom domain (e.g., `app.lendxrp.com`)
   - Configure DNS records as instructed by Vercel

2. **DNS Configuration**
   ```
   Type: CNAME
   Name: app (or @)
   Value: cname.vercel-dns.com
   ```

3. **SSL Certificate**
   - Vercel automatically provisions SSL certificates
   - Verify HTTPS enforcement in Settings → Security

### Deployment Steps

#### Manual Deployment
```bash
cd frontend
npm install --legacy-peer-deps
npm run build
npm run lint

# Verify build success
ls -la .next/

# Deploy via Vercel CLI
vercel --prod
```

#### Continuous Deployment (Recommended)
Vercel automatically deploys on git push to main branch:
```bash
git add .
git commit -m "feat: production-ready deployment"
git push origin main
```

### Post-Deployment Verification

```bash
# Check build status
curl https://lendxrp.vercel.app/

# Verify API connectivity
curl https://lendxrp.vercel.app/api/health

# Check browser console for errors
# Open https://lendxrp.vercel.app in browser
# Open DevTools → Console → Network tab
```

---

## 3. Backend Deployment

### Deployment Platform Options

#### Option A: Railway (Recommended for MVP)
**Pros**: Simple setup, auto-scaling, built-in PostgreSQL support
**Cons**: More expensive than VPS

**Setup Steps**:
1. Create Railway account: https://railway.app
2. Create new project → Deploy from GitHub repo
3. Add environment variables (see below)
4. Configure start command: `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`

#### Option B: AWS (Recommended for Production)
**Pros**: Full control, enterprise-grade, scalable
**Cons**: Complex setup, higher DevOps overhead

**Services**:
- **AWS ECS/Fargate**: Container orchestration
- **AWS RDS**: Managed PostgreSQL (alternative to Supabase)
- **AWS Secrets Manager**: Secure credential storage
- **AWS CloudWatch**: Logging and monitoring
- **AWS CloudFront**: CDN for API caching

#### Option C: Google Cloud Run (Serverless)
**Pros**: Pay-per-use, auto-scaling, zero maintenance
**Cons**: Cold start latency

#### Option D: Render
**Pros**: Simple deployment, competitive pricing
**Cons**: Limited to US/EU regions

### Environment Variables (Production)

```env
# ============================================================================
# SUPABASE CONFIGURATION
# ============================================================================
SUPABASE_URL=https://sspwpkhajtooztzisioo.supabase.co
SUPABASE_DB_PASSWORD=REPLACE_WITH_PRODUCTION_PASSWORD
SUPABASE_ANON_KEY=REPLACE_WITH_PRODUCTION_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=REPLACE_WITH_PRODUCTION_SERVICE_ROLE_KEY

# ============================================================================
# DATABASE CONNECTION POOL
# ============================================================================
DB_POOL_SIZE=10  # Increase for production load
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_ECHO_SQL=false  # MUST be false in production

# ============================================================================
# XRPL CONFIGURATION
# ============================================================================
XRPL_NETWORK=testnet  # Change to 'mainnet' after testing
XRPL_TESTNET_URL=https://s.altnet.rippletest.net:51234/
XRPL_MAINNET_URL=https://s1.ripple.com:51234/

# ============================================================================
# RLUSD CONFIGURATION
# ============================================================================
# Testnet issuer
RLUSD_ISSUER=rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV
RLUSD_CURRENCY=RLUSD

# Mainnet issuer (uncomment for production)
# RLUSD_ISSUER=rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================
ENVIRONMENT=production
API_BASE_URL=https://api.lendxrp.com
FRONTEND_URL=https://lendxrp.vercel.app

# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=REPLACE_WITH_PRODUCTION_JWT_SECRET

# ============================================================================
# LOGGING
# ============================================================================
LOG_LEVEL=INFO  # DEBUG only for troubleshooting
LOG_FORMAT=json

# ============================================================================
# SECURITY
# ============================================================================
# CORS allowed origins (comma-separated)
CORS_ORIGINS=https://lendxrp.vercel.app,https://app.lendxrp.com

# Rate limiting (requests per minute)
RATE_LIMIT_PER_MINUTE=60
```

### Dockerfile

Create `/home/users/duynguy/proj/calhacks/Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY backend ./backend

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user for security
RUN useradd -m -u 1000 lendx && chown -R lendx:lendx /app
USER lendx

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Start application
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Build and Deploy

```bash
# Build Docker image
docker build -t lendx-backend:latest .

# Test locally
docker run -p 8000:8000 --env-file .env lendx-backend:latest

# Tag for registry (example: AWS ECR)
docker tag lendx-backend:latest 123456789.dkr.ecr.us-west-1.amazonaws.com/lendx-backend:latest

# Push to registry
docker push 123456789.dkr.ecr.us-west-1.amazonaws.com/lendx-backend:latest
```

### Process Management (Non-Docker Deployment)

**systemd service** (`/etc/systemd/system/lendx-backend.service`):

```ini
[Unit]
Description=LendX FastAPI Backend
After=network.target

[Service]
Type=notify
User=lendx
Group=lendx
WorkingDirectory=/opt/lendx
Environment="PATH=/opt/lendx/venv/bin"
EnvironmentFile=/opt/lendx/.env
ExecStart=/opt/lendx/venv/bin/uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/lendx/logs

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable lendx-backend
sudo systemctl start lendx-backend
sudo systemctl status lendx-backend
```

### Nginx Reverse Proxy

**`/etc/nginx/sites-available/lendx-api`**:

```nginx
upstream lendx_backend {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name api.lendxrp.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.lendxrp.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.lendxrp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.lendxrp.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
    limit_req zone=api_limit burst=20 nodelay;

    # Proxy settings
    location / {
        proxy_pass http://lendx_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (bypass rate limiting)
    location /health {
        proxy_pass http://lendx_backend;
        access_log off;
    }
}
```

Enable and reload:
```bash
sudo ln -s /etc/nginx/sites-available/lendx-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Scaling Considerations

**Horizontal Scaling**:
- Use load balancer (AWS ALB, Nginx, HAProxy)
- Multiple backend instances behind load balancer
- Session state must be stateless (JWT tokens, not server sessions)

**Vertical Scaling**:
- Increase Uvicorn workers: `--workers 4` (rule: 2 * CPU cores + 1)
- Monitor CPU/memory usage
- Upgrade instance size when CPU >70% sustained

**Database Scaling**:
- Enable connection pooling (already configured: 5 connections, 10 overflow)
- Add read replicas for read-heavy queries
- Implement caching layer (Redis) for frequently accessed data

---

## 4. Database Setup (Supabase)

### Production Database Configuration

1. **Create Production Project**
   - Go to https://app.supabase.com
   - Create new project (separate from development)
   - Choose region closest to backend deployment
   - Enable **Point-in-Time Recovery (PITR)** for production

2. **Database Credentials**
   ```bash
   # Get from Supabase Dashboard → Settings → Database
   SUPABASE_URL=https://your-prod-project.supabase.co
   SUPABASE_DB_PASSWORD=your_secure_production_password
   ```

3. **Connection Pooling**
   - Supabase provides connection pooler at port `6543`
   - Use pooler URL for application connections:
     ```
     postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
     ```
   - Direct connection port `5432` for migrations only

### Running Migrations

**Option 1: Manual SQL Execution**
```bash
# Connect to production database
psql "postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?sslmode=require"

# Run migration
\i backend/migrations/001_initial_schema.sql

# Verify tables
\dt

# Check indexes
\di
```

**Option 2: Migration Script**

Create `/home/users/duynguy/proj/calhacks/scripts/run_migrations.py`:

```python
"""Run database migrations."""
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from backend.config.database import DatabaseConfig

def run_migrations():
    """Execute all SQL migration files in order."""
    config = DatabaseConfig()
    engine = create_engine(config.DATABASE_URL)

    migrations_dir = Path(__file__).parent.parent / "backend" / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))

    print(f"Found {len(migration_files)} migration files")

    with engine.connect() as conn:
        for migration_file in migration_files:
            print(f"Running {migration_file.name}...")
            sql = migration_file.read_text()
            conn.execute(text(sql))
            conn.commit()
            print(f"✓ {migration_file.name} completed")

    print("All migrations completed successfully")

if __name__ == "__main__":
    run_migrations()
```

Run:
```bash
export SUPABASE_DB_PASSWORD="production_password"
python scripts/run_migrations.py
```

### Row-Level Security (RLS)

**CRITICAL: Enable RLS for production**

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pools ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_mpt_balances ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own data
CREATE POLICY "Users can view own data" ON users
    FOR SELECT
    USING (auth.uid() = address);

-- Policy: Users can view pools they created or applied to
CREATE POLICY "Users can view relevant pools" ON pools
    FOR SELECT
    USING (
        issuer_address = auth.uid() OR
        pool_address IN (
            SELECT pool_address FROM applications WHERE borrower_address = auth.uid()
        )
    );

-- Policy: Users can view their own applications
CREATE POLICY "Users can view own applications" ON applications
    FOR SELECT
    USING (borrower_address = auth.uid());

-- Policy: Users can view loans they're involved in
CREATE POLICY "Users can view own loans" ON loans
    FOR SELECT
    USING (
        borrower_address = auth.uid() OR
        lender_address = auth.uid()
    );
```

### Backup Strategy

**Automated Backups (Supabase)**:
- Daily automated backups (retained for 7 days on Pro plan)
- Point-in-Time Recovery (PITR) available on Pro/Enterprise plans
- Configure in Dashboard → Database → Backups

**Manual Backup**:
```bash
# Full database dump
pg_dump "postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require" > backup_$(date +%Y%m%d).sql

# Restore from backup
psql "postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require" < backup_20250126.sql
```

**Backup Schedule**:
- **Daily**: Automated full backup
- **Weekly**: Manual verification backup
- **Before major deployments**: Manual snapshot

### Database Monitoring

**Enable in Supabase Dashboard**:
1. Navigate to Database → Monitoring
2. Watch for:
   - Connection count (should be < pool size * instances)
   - Query performance (slow queries >1s)
   - Database size growth
   - Index usage

**Alert Thresholds**:
- Database size >80% of plan limit
- Connection pool exhaustion
- Replication lag >10 seconds (if using read replicas)

---

## 5. XRPL Configuration

### Testnet vs Mainnet Decision Matrix

| Criteria | Testnet | Mainnet |
|----------|---------|---------|
| **Purpose** | Development, staging, demos | Production with real funds |
| **XRP Cost** | Free (faucet) | Real money required |
| **Transaction Fees** | Free | ~0.00001 XRP per transaction |
| **Reliability** | May be reset periodically | Production-grade uptime |
| **Risk** | Zero financial risk | Financial risk, regulatory compliance |
| **Data Persistence** | Not guaranteed | Permanent |

**Recommendation**:
- Use **Testnet** for initial launch and beta testing
- Migrate to **Mainnet** only after:
  - Security audit completed
  - Compliance review finished
  - Insurance/guarantor mechanisms in place
  - User agreement and terms finalized

### Network Configuration

**Backend**: `backend/xrpl_client/config.py`
```python
# Current configuration
TESTNET_URL = "https://s.altnet.rippletest.net:51234/"
MAINNET_URL = "https://s1.ripple.com:51234/"
```

**Environment Variable Override**:
```env
# Use testnet
XRPL_NETWORK=testnet

# Use mainnet (only after approval)
XRPL_NETWORK=mainnet
```

### Wallet Management (CRITICAL SECURITY)

**WARNING: Current implementation generates wallets in backend (line 141, 251, 363 in main.py)**

**Current (INSECURE for production)**:
```python
# backend/api/main.py
lender_wallet = Wallet.create()  # ⚠️ Backend-generated wallet
logger.info(f"Wallet seed: {lender_wallet.seed}")  # ⚠️ Logged to server
```

**Production Requirements**:

1. **NEVER generate or store private keys on backend server**
2. **NEVER log wallet seeds**
3. **Use client-side signing only**

**Secure Implementation Pattern**:

```python
# Client sends SIGNED transaction (not wallet credentials)
@app.post("/pools")
async def create_lending_pool(
    pool_data: LendingPoolCreate,
    signed_tx: str,  # Client-signed transaction
    db: Session = Depends(get_db)
):
    # Verify signature
    # Submit to XRPL
    # Store result in database
```

**Wallet Security Options**:

| Method | Security | Complexity | Cost |
|--------|----------|------------|------|
| **XUMM SDK** (Current) | Good | Low | Free |
| **Hardware Wallet** (Ledger) | Excellent | Medium | $50-200 per device |
| **AWS KMS** | Excellent | High | ~$1/key/month |
| **Azure Key Vault** | Excellent | High | ~$0.03/10k ops |
| **Google Cloud KMS** | Excellent | High | ~$0.03/key/month |

**Recommended for Production**: XUMM SDK for user wallets + AWS KMS for operational wallets (settlement, fees)

### Transaction Fee Considerations

**XRPL Base Fees** (as of 2025):
- Standard transaction: **0.00001 XRP** (~$0.000025 at $2.50/XRP)
- High-load periods: Fees may increase dynamically
- Reserve requirement: **10 XRP** base + **2 XRP** per object

**LendX Operations**:
- Create Pool (MPT issuance): **0.00001 XRP**
- Submit Application: **0.00001 XRP**
- Approve Loan: **0.00001 XRP**
- Escrow deposit: **0.00001 XRP**
- Escrow finish: **0.00001 XRP**

**Estimated Monthly Costs** (1000 loans/month):
- Transaction fees: 5,000 transactions × 0.00001 XRP = **0.05 XRP** (~$0.125)
- Reserve requirements: Negligible after initial setup

**Fee Strategy**:
- Pass transaction fees to users (transparently)
- Maintain operational wallet with 100 XRP buffer
- Monitor fee escalation during high-load periods

### Rate Limiting

**XRPL Public Nodes**:
- Rate limit: ~200 requests/second
- Use WebSocket connections for better performance
- Consider running own node for high-volume production

**Run Your Own Node** (recommended for mainnet):
```bash
# Install rippled (XRPL node software)
# See: https://xrpl.org/install-rippled.html

# Requires:
# - 8 CPU cores
# - 32 GB RAM
# - 2 TB NVMe SSD
# - 10 Gbps network

# Cost: ~$200-400/month on AWS/GCP
```

**Alternative**: Use Ripple's Clio server (optimized for read operations)

---

## 6. Security Checklist

### Critical Security Items

#### Rotate All API Keys

**Before production deployment**:

- [ ] **Generate new Supabase credentials**
  ```bash
  # Do NOT reuse development credentials
  # Create new production project with fresh keys
  ```

- [ ] **Rotate JWT secret**
  ```bash
  openssl rand -hex 32
  # Update JWT_SECRET_KEY in production environment
  ```

- [ ] **Generate new XUMM API keys**
  - Create production app at https://apps.xumm.dev/
  - Use different keys than development

- [ ] **Update CORS origins**
  ```python
  # backend/api/main.py
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "https://lendxrp.vercel.app",
          "https://app.lendxrp.com"
      ],  # ⚠️ Remove localhost origins
      allow_credentials=True,
      allow_methods=["GET", "POST", "PUT", "DELETE"],
      allow_headers=["*"],
  )
  ```

#### Enable HTTPS Only

- [ ] **Enforce SSL in database connections** (already configured)
  ```python
  connect_args={"sslmode": "require"}
  ```

- [ ] **Set HSTS headers** (configured in Nginx)
  ```nginx
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
  ```

- [ ] **Redirect HTTP to HTTPS** (configured in Nginx)

#### Secure Wallet Private Keys

**CRITICAL**: Fix current implementation before production

**Current Issues** (in `backend/api/main.py`):
```python
# Line 141, 251, 363 - INSECURE
lender_wallet = Wallet.create()
return {"wallet_seed": lender_wallet.seed}  # ⚠️ NEVER expose seeds
```

**Required Changes**:

1. **Remove backend wallet generation**
2. **Implement client-side signing**
3. **Use Hardware Security Modules (HSM) for operational wallets**

**Action Items**:
- [ ] Refactor pool creation to accept signed transactions
- [ ] Remove wallet seed exposure from API responses
- [ ] Remove wallet seed logging
- [ ] Implement XUMM signing flow
- [ ] Set up AWS KMS/Azure Key Vault for operational wallets

#### Rate Limiting

**API Rate Limiting** (implement in `backend/api/main.py`):

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/pools")
@limiter.limit("5/minute")  # 5 pool creations per minute
async def create_lending_pool(...):
    pass

@app.post("/loans/apply")
@limiter.limit("10/minute")  # 10 applications per minute
async def apply_for_loan(...):
    pass
```

**Install dependency**:
```bash
pip install slowapi
```

**Configuration**:
- Public endpoints: 60 requests/minute
- Authenticated endpoints: 120 requests/minute
- Pool creation: 5 requests/minute
- Loan application: 10 requests/minute

#### DDoS Protection

**Infrastructure Level**:
- [ ] Use Cloudflare (free plan includes basic DDoS protection)
- [ ] Enable AWS Shield Standard (free with AWS)
- [ ] Configure rate limiting in Nginx/load balancer

**Application Level**:
- [ ] Implement request validation (Pydantic already in place)
- [ ] Add connection pooling limits
- [ ] Set up health check endpoints for monitoring
- [ ] Configure circuit breakers for external API calls

#### Input Validation

**Current State**: ✅ Already implemented with Pydantic

```python
class LendingPoolCreate(BaseModel):
    name: str
    amount: float
    interest_rate: float
    max_term_days: int
    min_loan_amount: float
    lender_address: str
```

**Additional Validations Needed**:

```python
from pydantic import BaseModel, Field, validator

class LendingPoolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0, le=1000000)  # Max 1M
    interest_rate: float = Field(..., ge=0, le=100)  # 0-100%
    max_term_days: int = Field(..., ge=1, le=365)  # Max 1 year
    min_loan_amount: float = Field(..., gt=0)
    lender_address: str = Field(..., regex=r'^r[1-9A-HJ-NP-Za-km-z]{25,34}$')

    @validator('lender_address')
    def validate_xrpl_address(cls, v):
        # Additional XRPL address validation
        if not v.startswith('r'):
            raise ValueError('Invalid XRPL address')
        return v
```

#### Database Security

- [ ] **Enable Row-Level Security (RLS)** - See Section 4
- [ ] **Create read-only database user for analytics**
  ```sql
  CREATE USER analytics_readonly WITH PASSWORD 'secure_password';
  GRANT CONNECT ON DATABASE postgres TO analytics_readonly;
  GRANT USAGE ON SCHEMA public TO analytics_readonly;
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;
  ```

- [ ] **Audit database permissions**
  ```sql
  -- List all roles and permissions
  SELECT * FROM information_schema.role_table_grants
  WHERE grantee = 'postgres';
  ```

- [ ] **Enable connection encryption** (already configured via `sslmode=require`)

- [ ] **Regular security updates**
  ```bash
  # Monitor Supabase dashboard for security patches
  # Apply migrations during maintenance windows
  ```

### Security Testing

**Run before production launch**:

```bash
# 1. SQL Injection Testing
# Verify all queries use parameterized statements
grep -r "execute.*%" backend/  # Should return nothing

# 2. Dependency Vulnerability Scan
pip install safety
safety check

# 3. Static Code Analysis
pip install bandit
bandit -r backend/ -f json -o security_report.json

# 4. OWASP ZAP Scan (optional)
# Run against staging environment
docker run -t owasp/zap2docker-stable zap-baseline.py -t https://staging-api.lendxrp.com

# 5. SSL/TLS Configuration Test
testssl.sh https://api.lendxrp.com
```

---

## 7. Monitoring & Logging

### Application Logs

**Structured Logging** (implement in `backend/api/main.py`):

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Usage in endpoints
@app.post("/pools")
async def create_lending_pool(...):
    logger.info("Pool creation requested", extra={
        "lender_address": pool_data.lender_address,
        "amount": pool_data.amount
    })
```

**Log to File** (for non-containerized deployments):

```python
handler = logging.FileHandler('/var/log/lendx/api.log')
logger.addHandler(handler)

# Log rotation
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler(
    '/var/log/lendx/api.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
```

### XRPL Transaction Monitoring

**Track All Transactions**:

```python
# Add to all XRPL operations
logger.info("XRPL transaction submitted", extra={
    "tx_type": "MPTCreate",
    "tx_hash": tx_hash,
    "account": wallet.classic_address,
    "network": "testnet"
})

# Monitor transaction results
logger.info("XRPL transaction confirmed", extra={
    "tx_hash": tx_hash,
    "result": "tesSUCCESS",
    "ledger_index": result.ledger_index
})
```

**Failed Transaction Alerts**:

```python
if result.meta.get("TransactionResult") != "tesSUCCESS":
    logger.error("XRPL transaction failed", extra={
        "tx_hash": tx_hash,
        "error_code": result.meta.get("TransactionResult"),
        "error_message": get_error_message(result)
    })
    # Send alert to monitoring service
```

### Database Performance Monitoring

**Slow Query Logging**:

```sql
-- Enable in PostgreSQL (Supabase dashboard)
ALTER DATABASE postgres SET log_min_duration_statement = 1000;  -- Log queries >1s

-- Monitor slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;
```

**Connection Pool Monitoring**:

```python
# Add health check endpoint
@app.get("/metrics/db")
async def database_metrics():
    engine = get_db().bind
    pool = engine.pool

    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow()
    }
```

### Error Tracking (Sentry)

**Install Sentry**:

```bash
pip install sentry-sdk[fastapi]
```

**Configure** (in `backend/api/main.py`):

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project-id",
    environment=os.getenv("ENVIRONMENT", "production"),
    traces_sample_rate=0.1,  # 10% of transactions
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
)

# Add user context to errors
@app.middleware("http")
async def add_sentry_context(request: Request, call_next):
    if user_address := request.headers.get("X-User-Address"):
        sentry_sdk.set_user({"id": user_address})
    response = await call_next(request)
    return response
```

### Uptime Monitoring

**Tools**:
- **UptimeRobot** (free plan: 50 monitors, 5-min checks)
- **Pingdom** (paid: more features, faster checks)
- **StatusCake** (free tier available)

**Endpoints to Monitor**:
- Frontend: `https://lendxrp.vercel.app/` (expect: 200)
- Backend: `https://api.lendxrp.com/health` (expect: 200, JSON response)
- Database: Health check included in `/health` endpoint

**Alert Channels**:
- Email
- Slack webhook
- PagerDuty (for on-call rotation)
- SMS (critical alerts only)

### Dashboards

**Recommended Stack**:

1. **Application Metrics**: Grafana + Prometheus
2. **Error Tracking**: Sentry
3. **Uptime**: UptimeRobot
4. **XRPL Explorer**: https://livenet.xrpl.org/ (mainnet) or https://testnet.xrpl.org/ (testnet)

**Key Metrics to Track**:
- API response time (p50, p95, p99)
- Request rate (requests/second)
- Error rate (%)
- Database query time
- XRPL transaction success rate
- Active loan count
- Total value locked (TVL)

---

## 8. CI/CD Pipeline

### GitHub Actions Workflow

Create `/.github/workflows/deploy.yml`:

```yaml
name: Deploy LendX

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}

    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-cov safety

    - name: Security scan
      run: safety check

    - name: Run tests
      env:
        SUPABASE_DB_PASSWORD: test_password
        DATABASE_URL: postgresql://postgres:test_password@localhost:5432/test_db
      run: |
        pytest backend/tests/ -v --cov=backend --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  test-frontend:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json

    - name: Install dependencies
      working-directory: ./frontend
      run: npm ci --legacy-peer-deps

    - name: Lint
      working-directory: ./frontend
      run: npm run lint

    - name: Build
      working-directory: ./frontend
      run: npm run build
      env:
        NEXT_PUBLIC_API_URL: https://api.lendxrp.com

  deploy-backend:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-1

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1

    - name: Build and push Docker image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: lendx-backend
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

    - name: Deploy to ECS
      run: |
        aws ecs update-service \
          --cluster lendx-cluster \
          --service lendx-backend-service \
          --force-new-deployment

  deploy-frontend:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v25
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        vercel-args: '--prod'
        working-directory: ./frontend
```

### GitHub Secrets

**Required Secrets** (Settings → Secrets and variables → Actions):

```
# AWS (for backend deployment)
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY

# Vercel (for frontend deployment)
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID

# Supabase (for integration tests)
SUPABASE_URL
SUPABASE_DB_PASSWORD
SUPABASE_SERVICE_ROLE_KEY

# Optional: Sentry (error tracking)
SENTRY_DSN
```

### Deployment Stages

**Multi-Environment Strategy**:

```yaml
# .github/workflows/deploy-staging.yml (on merge to develop branch)
# .github/workflows/deploy-production.yml (on merge to main branch)

deploy-staging:
  environment:
    name: staging
    url: https://staging.lendxrp.com

  steps:
    # Same as production but different environment variables

deploy-production:
  environment:
    name: production
    url: https://lendxrp.vercel.app

  # Require manual approval
  needs: [test-backend, test-frontend]
  # Only deploy on main branch
  if: github.ref == 'refs/heads/main'
```

---

## 9. Rollback Procedure

### Database Rollback

**Before Running Migration**:

```bash
# 1. Create backup
pg_dump $DATABASE_URL > backup_pre_migration_$(date +%Y%m%d_%H%M%S).sql

# 2. Run migration
psql $DATABASE_URL < backend/migrations/002_new_feature.sql

# 3. If migration fails or has issues, restore
psql $DATABASE_URL < backup_pre_migration_20250126_143000.sql
```

**Migration Rollback Scripts**:

Create down migrations for each up migration:

```
backend/migrations/
  001_initial_schema.sql          (up)
  001_initial_schema_down.sql     (down)
  002_add_credit_scores.sql       (up)
  002_add_credit_scores_down.sql  (down)
```

**Example down migration**:

```sql
-- backend/migrations/002_add_credit_scores_down.sql
BEGIN;

ALTER TABLE users DROP COLUMN IF EXISTS credit_score;
ALTER TABLE users DROP COLUMN IF EXISTS verification_level;

COMMIT;
```

### Application Rollback

**Docker/ECS Deployment**:

```bash
# List recent deployments
aws ecs describe-services \
  --cluster lendx-cluster \
  --services lendx-backend-service \
  --query 'services[0].deployments'

# Rollback to previous task definition
aws ecs update-service \
  --cluster lendx-cluster \
  --service lendx-backend-service \
  --task-definition lendx-backend:42  # Previous version
```

**Vercel Rollback**:

```bash
# Via Vercel dashboard: Deployments → Click previous deployment → "Promote to Production"

# Or via CLI
vercel rollback https://lendxrp-abc123.vercel.app
```

**Git-based Rollback**:

```bash
# Identify commit to rollback to
git log --oneline -10

# Revert to previous commit
git revert HEAD
git push origin main

# Or hard reset (if safe and coordinated with team)
git reset --hard abc1234
git push origin main --force
```

### Emergency Procedures

**Critical Bug in Production**:

1. **Immediate**: Disable affected endpoint
   ```python
   # Add to backend/api/main.py
   @app.post("/pools")
   async def create_lending_pool(...):
       raise HTTPException(status_code=503, detail="Temporarily unavailable for maintenance")
   ```

2. **Deploy hotfix branch**:
   ```bash
   git checkout -b hotfix/critical-bug
   # Fix the bug
   git commit -m "fix: critical security vulnerability"
   git push origin hotfix/critical-bug
   # Deploy directly to production (bypass normal CI/CD)
   ```

3. **Notify users**: Update status page, send notifications

4. **Post-mortem**: Document what happened, why, and how to prevent

**Database Corruption**:

1. **Immediately stop writes**:
   ```sql
   REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM PUBLIC;
   ```

2. **Restore from backup** (see Database Rollback section)

3. **Investigate root cause** before re-enabling writes

**XRPL Network Issues**:

1. **Switch to backup XRPL node**:
   ```python
   # Add fallback URLs in backend/xrpl_client/config.py
   TESTNET_URLS = [
       "https://s.altnet.rippletest.net:51234/",
       "https://testnet.xrpl-labs.com/",
   ]
   ```

2. **Enable maintenance mode** if XRPL unavailable

3. **Queue transactions** for later submission when network recovers

---

## 10. Mainnet Considerations

### Pre-Mainnet Requirements

**Legal & Compliance**:

- [ ] **Legal Entity Formation**
  - LLC or Corporation registration
  - Business licenses in operating jurisdictions
  - Tax ID (EIN) obtained

- [ ] **Terms of Service**
  - User agreement drafted and reviewed by lawyer
  - Privacy policy (GDPR, CCPA compliant if applicable)
  - Risk disclosures for lenders and borrowers

- [ ] **Regulatory Compliance**
  - Money Transmitter License (if required in your jurisdiction)
  - AML/KYC requirements analysis
  - Securities law compliance (Howey test analysis)
  - Consult with crypto/fintech lawyer

- [ ] **Insurance**
  - Cyber liability insurance
  - Errors & Omissions (E&O) insurance
  - Smart contract insurance (if available)
  - Business interruption insurance

**Technical Readiness**:

- [ ] **Security Audit**
  - Smart contract audit (if using custom XRPL hooks)
  - Backend security audit
  - Penetration testing
  - Bug bounty program consideration

- [ ] **Load Testing**
  - Simulate 10x expected traffic
  - Database query optimization
  - XRPL rate limiting handled
  - CDN caching configured

- [ ] **Disaster Recovery Plan**
  - RTO (Recovery Time Objective): < 1 hour
  - RPO (Recovery Point Objective): < 5 minutes
  - Runbook for common failures
  - On-call rotation established

### Fiat On/Off Ramps

**Integration Options**:

1. **Wyre** (Acquired by Bolt)
   - Credit card to crypto
   - US and international support
   - API integration available

2. **Ramp Network**
   - 170+ countries
   - 90+ fiat currencies
   - Widget integration

3. **Transak**
   - KYC/AML compliant
   - 100+ countries
   - NFT checkout support

4. **MoonPay**
   - Popular in crypto space
   - Good UX
   - Higher fees

**Implementation**:

```javascript
// Frontend: components/deposit/fiat-onramp.tsx
import { RampInstantSDK } from '@ramp-network/ramp-instant-sdk';

const depositFiat = () => {
  new RampInstantSDK({
    hostAppName: 'LendX',
    hostLogoUrl: 'https://lendxrp.com/logo.png',
    swapAsset: 'XRP',
    userAddress: userWalletAddress,
    fiatCurrency: 'USD',
    fiatValue: '100',
  }).show();
};
```

**Compliance Considerations**:
- Most on-ramps handle KYC/AML
- You may still need to log transactions
- Monitor for suspicious activity
- Report CTRs (Currency Transaction Reports) if required

### KYC/AML Implementation

**KYC Providers**:

1. **Sumsub**
   - Document verification
   - Liveness detection
   - AML screening

2. **Onfido**
   - Global coverage
   - Good fraud detection
   - API-first

3. **Jumio**
   - Enterprise-grade
   - High accuracy
   - More expensive

**Implementation Tiers**:

| Tier | Requirements | Limits |
|------|-------------|--------|
| **Anonymous** | None | $100/transaction, $500/month |
| **Basic** | Email + phone | $1,000/transaction, $10k/month |
| **Verified** | ID verification | $10k/transaction, $100k/month |
| **Enhanced** | ID + proof of address | Unlimited |

**Backend Integration**:

```python
# backend/api/kyc.py
from sumsub_sdk import SumsubClient

@app.post("/api/kyc/verify")
async def initiate_kyc_verification(user_address: str):
    # Generate applicant token
    token = sumsub_client.create_applicant_token(
        user_id=user_address,
        level_name="basic-kyc-level"
    )

    return {
        "verification_url": f"https://sumsub.com/verify?token={token}",
        "token": token
    }

@app.get("/api/kyc/status/{user_address}")
async def get_kyc_status(user_address: str):
    status = sumsub_client.get_applicant_status(user_address)

    # Update user record
    db.query(User).filter_by(address=user_address).update({
        "kyc_status": status,
        "kyc_verified_at": datetime.now() if status == "approved" else None
    })

    return {"status": status}
```

### Credit Scoring System

**Data Sources**:

1. **On-chain History**
   - Previous loan repayment history on LendX
   - XRPL transaction history
   - Wallet age and activity

2. **Off-chain Verification**
   - Bank account connection (Plaid, Teller)
   - Employment verification
   - Traditional credit score (Experian, Equifax)

3. **DeFi Credit Scores**
   - Arcx (DeFi credit score)
   - Spectral Finance
   - Credora

**Score Calculation**:

```python
# backend/services/credit_scoring.py
from decimal import Decimal

def calculate_credit_score(user_address: str) -> int:
    """
    Calculate credit score (300-850, like FICO).

    Factors:
    - Payment history (35%)
    - Amounts owed (30%)
    - Length of credit history (15%)
    - New credit (10%)
    - Credit mix (10%)
    """
    db = get_db_session()

    # Payment history
    loans = db.query(Loan).filter_by(borrower_address=user_address).all()
    total_loans = len(loans)
    paid_on_time = sum(1 for loan in loans if loan.state == "PAID" and loan.paid_date <= loan.end_date)
    payment_score = (paid_on_time / total_loans * 350) if total_loans > 0 else 250

    # Amounts owed (debt-to-credit ratio)
    active_debt = sum(loan.principal for loan in loans if loan.state == "ONGOING")
    total_credit_limit = Decimal("10000")  # Could be dynamic
    utilization_ratio = active_debt / total_credit_limit if total_credit_limit > 0 else 1
    amounts_owed_score = max(0, 300 - (utilization_ratio * 300))

    # Length of history
    if total_loans > 0:
        first_loan_date = min(loan.start_date for loan in loans)
        days_active = (datetime.now() - first_loan_date).days
        history_score = min(150, days_active / 365 * 150)
    else:
        history_score = 0

    # Simplified scoring
    total_score = int(payment_score * 0.35 + amounts_owed_score * 0.30 + history_score * 0.15 + 150)

    return min(850, max(300, total_score))
```

### Liquidation & Default Handling

**Escrow-based Protection**:

Current implementation uses XRPL escrow (1 hour hold time). For production:

```python
# Extend escrow duration for loan term
ESCROW_HOLD_SECONDS = loan_term_days * 24 * 3600

# Add finish conditions
escrow_tx = create_deposit_escrow(
    client=client,
    sender_wallet=borrower_wallet,
    recipient=lender_address,
    amount_xrp=loan_amount,
    hold_seconds=ESCROW_HOLD_SECONDS,
    condition=payment_condition,  # Crypto condition for cryptographic proof
    cancel_after=finish_time + grace_period
)
```

**Grace Period**:
- 7-day grace period after loan end date
- Automatic email/SMS reminders
- Penalty interest accrual during grace period

**Default Process**:
1. Loan marked as DEFAULTED after grace period
2. Escrow funds released to lender
3. Credit score impact (-200 points)
4. Report to credit bureaus (if integrated)
5. Collections process initiated (if applicable)

**Partial Repayment**:

```python
@app.post("/api/loans/{loan_id}/partial-payment")
async def make_partial_payment(
    loan_id: str,
    amount: Decimal,
    tx_hash: str,  # XRPL payment transaction
    db: Session = Depends(get_db)
):
    loan = db.query(Loan).filter_by(loan_address=loan_id).first()

    # Track payment
    payment = LoanPayment(
        loan_address=loan_id,
        amount=amount,
        tx_hash=tx_hash,
        payment_date=datetime.now()
    )
    db.add(payment)

    # Update remaining balance
    total_paid = db.query(func.sum(LoanPayment.amount)).filter_by(loan_address=loan_id).scalar()
    remaining = loan.principal + loan.interest - total_paid

    if remaining <= 0:
        loan.state = "PAID"
        loan.paid_date = datetime.now()

    db.commit()

    return {
        "remaining_balance": float(remaining),
        "paid_to_date": float(total_paid),
        "status": loan.state
    }
```

### Guarantor System

**Multi-Signature Guarantors**:

```python
# Borrower + Guarantor both sign loan application
# Guarantor's funds locked in escrow as collateral

@app.post("/api/loans/apply-with-guarantor")
async def apply_with_guarantor(
    application: LoanApplication,
    guarantor_address: str,
    guarantor_collateral: Decimal,
    db: Session = Depends(get_db)
):
    # Create multi-sig account
    multisig_address = setup_multisig_account(
        client=client,
        signers=[application.borrower_address, guarantor_address],
        required_signatures=2
    )

    # Lock guarantor collateral in escrow
    escrow_tx = create_deposit_escrow(
        client=client,
        sender_wallet=guarantor_wallet,
        recipient=lender_address,
        amount_xrp=guarantor_collateral,
        hold_seconds=loan_term_seconds,
        condition="default_condition"  # Released only if borrower defaults
    )

    # Create application with guarantor
    app = Application(
        # ... standard fields
        guarantor_address=guarantor_address,
        guarantor_collateral=guarantor_collateral,
        guarantor_escrow_sequence=escrow_tx.sequence
    )
    db.add(app)
    db.commit()
```

**Guarantor Risk Tiers**:
- Tier 1: 25% collateral (high trust borrower)
- Tier 2: 50% collateral (medium trust)
- Tier 3: 100% collateral (low trust/new borrower)

### Production Support

**Support Channels**:
- [ ] Email support (support@lendxrp.com)
- [ ] In-app chat (Intercom, Crisp)
- [ ] Discord/Telegram community
- [ ] FAQ/Knowledge base
- [ ] Status page (https://status.lendxrp.com)

**On-Call Rotation**:
- 24/7 coverage for P0 incidents (platform down, security breach)
- Business hours for P1/P2 (bugs, performance issues)
- Use PagerDuty or OpsGenie for alerting

**SLA Targets**:
- **Uptime**: 99.9% (43 minutes downtime/month)
- **API Response Time**: p95 < 500ms
- **Support Response**: < 2 hours (business hours)
- **Critical Bug Fix**: < 4 hours

---

## Appendix

### Useful Commands Reference

```bash
# Backend
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --workers 4
PYTHONPATH=$(pwd) pytest backend/tests/ -v
pip install safety && safety check

# Frontend
cd frontend
npm install --legacy-peer-deps
npm run build
npm run lint

# Database
psql $DATABASE_URL
pg_dump $DATABASE_URL > backup.sql
psql $DATABASE_URL < backup.sql

# Docker
docker build -t lendx-backend:latest .
docker run -p 8000:8000 --env-file .env lendx-backend:latest
docker logs -f container_id

# Monitoring
curl https://api.lendxrp.com/health
curl https://api.lendxrp.com/metrics/db
tail -f /var/log/lendx/api.log
```

### Environment Variables Cheatsheet

| Variable | Dev | Staging | Prod | Secret? |
|----------|-----|---------|------|---------|
| `SUPABASE_URL` | ✓ | ✓ | ✓ | No |
| `SUPABASE_DB_PASSWORD` | ✓ | ✓ | ✓ | **YES** |
| `SUPABASE_SERVICE_ROLE_KEY` | ✓ | ✓ | ✓ | **YES** |
| `JWT_SECRET_KEY` | ✓ | ✓ | ✓ | **YES** |
| `XRPL_NETWORK` | testnet | testnet | mainnet | No |
| `ENVIRONMENT` | development | staging | production | No |
| `LOG_LEVEL` | DEBUG | INFO | INFO | No |
| `DB_ECHO_SQL` | true | false | false | No |

### Support Contacts

- **XRPL Support**: https://xrpl.org/community.html
- **Supabase Support**: https://supabase.com/support
- **Vercel Support**: https://vercel.com/support
- **Security Issues**: security@lendxrp.com (create this!)

### Additional Resources

- [XRPL Documentation](https://xrpl.org/)
- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [OWASP Security Guidelines](https://owasp.org/)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-26
**Owner**: Backend Engineering Team
**Review Frequency**: Quarterly or before major releases

**IMPORTANT**: This deployment guide contains security-sensitive information. Restrict access to authorized personnel only. Never commit production secrets to version control.
