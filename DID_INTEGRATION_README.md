# XRPL DID Integration with Auth0 + Google Sign-In

This document describes the complete integration of XRPL Decentralized Identifiers (DIDs) with Auth0 authentication and Google Sign-In for the LendX platform.

## Overview

Every user who signs up automatically receives:
- ✅ **XRPL Wallet**: Initialized with public/private key pair
- ✅ **DID Document**: Created and stored on-chain
- ✅ **Verifiable Credentials**: Associated with their identity
- ✅ **Auth0 Integration**: Seamless login with Google

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   TypeScript    │    │   XRPL Ledger   │
│   (Next.js)     │◄──►│   Backend       │◄──►│   (Testnet)     │
│                 │    │   (Express)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│     Auth0       │    │   DID Registry  │
│   (Google SSO)  │    │   (In-Memory)   │
└─────────────────┘    └─────────────────┘
```

## Project Structure

```
calhacks/
├── frontend/                     # Next.js 14 application
│   ├── app/
│   │   ├── api/auth/[...auth0]/  # Auth0 API routes
│   │   └── (auth)/signup/        # Enhanced signup page
│   ├── lib/
│   │   ├── auth0.ts             # Auth0 configuration
│   │   └── api.ts               # API client for backend
│   └── .env.local               # Frontend environment variables
├── @backend/                     # TypeScript backend
│   ├── src/
│   │   ├── auth/                # Auth0 service
│   │   ├── did/                 # XRPL DID service
│   │   ├── services/            # User management
│   │   ├── routes/              # API endpoints
│   │   └── types/               # TypeScript interfaces
│   ├── package.json
│   └── .env                     # Backend environment variables
└── DID_INTEGRATION_README.md    # This file
```

## Setup Instructions

### 1. Auth0 Configuration

1. Create an Auth0 account and application
2. Configure Google Social Connection
3. Set up API in Auth0 Dashboard
4. Update environment variables

#### Frontend (.env.local)
```env
# Auth0 Configuration
AUTH0_SECRET='your-32-byte-secret-here'
AUTH0_BASE_URL='http://localhost:3000'
AUTH0_ISSUER_BASE_URL='https://your-domain.auth0.com'
AUTH0_CLIENT_ID='your-client-id'
AUTH0_CLIENT_SECRET='your-client-secret'
AUTH0_AUDIENCE='your-api-audience'

# Backend API
NEXT_PUBLIC_API_URL='http://localhost:3001'
```

#### Backend (.env)
```env
# Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_AUDIENCE=your-api-audience

# XRPL Configuration
XRPL_NETWORK=testnet
XRPL_ISSUER_WALLET_SEED=your-issuer-seed

# Server
PORT=3001
FRONTEND_URL=http://localhost:3000
```

### 2. Generate Auth0 Secret

```bash
openssl rand -hex 32
```

### 3. Create XRPL Issuer Wallet

```bash
# Using XRPL CLI or create manually
# Save the seed securely for XRPL_ISSUER_WALLET_SEED
```

### 4. Start the Applications

#### Backend
```bash
cd @backend
npm install
npm run dev
```

#### Frontend
```bash
cd frontend
npm run dev
```

## API Endpoints

### Authentication Endpoints (`/api/auth`)

- `GET /api/auth/me` - Get current user profile
- `POST /api/auth/register` - Register new user with DID creation
- `POST /api/auth/create-did` - Create DID for existing user
- `GET /api/auth/status` - Check authentication and DID status

### DID Endpoints (`/api/did`)

- `GET /api/did/document/:did?` - Get DID document
- `POST /api/did/credentials/issue` - Issue verifiable credential
- `POST /api/did/credentials/verify` - Verify credential
- `GET /api/did/credentials` - Get user's credentials
- `POST /api/did/credentials/business` - Issue business credential
- `POST /api/did/credentials/income` - Issue income credential
- `DELETE /api/did/deactivate` - Deactivate DID

## User Registration Flow

1. **User clicks "Sign In with Google"**
   - Redirects to Auth0 → Google OAuth
   - User grants permissions
   - Returns to application with JWT token

2. **Frontend calls `/api/auth/register`**
   - Backend creates XRPL wallet (address + keys)
   - Creates DID document with verification methods
   - Stores DID document on XRPL ledger
   - Issues initial "VerifiedUser" credential
   - Associates DID with Auth0 user metadata

3. **User receives complete identity package**
   - XRPL wallet address
   - DID identifier (`did:xrpl:address`)
   - DID document with verification methods
   - Initial verifiable credential

## DID Document Structure

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1"
  ],
  "id": "did:xrpl:rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "controller": "did:xrpl:rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "verificationMethod": [{
    "id": "did:xrpl:rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#key-1",
    "type": "Ed25519VerificationKey2020",
    "controller": "did:xrpl:rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "publicKeyBase58": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  }],
  "authentication": ["did:xrpl:rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#key-1"],
  "service": [{
    "id": "did:xrpl:rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#lendx-profile",
    "type": "LendXProfile",
    "serviceEndpoint": "https://api.lendx.finance/profile/rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  }],
  "created": "2024-01-01T00:00:00.000Z"
}
```

## Verifiable Credentials

### Basic User Credential
```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://lendx.finance/credentials/v1"
  ],
  "id": "https://api.lendx.finance/credentials/uuid",
  "type": ["VerifiableCredential", "VerifiedUser"],
  "issuer": {
    "id": "did:xrpl:issuer-address",
    "name": "LendX Platform"
  },
  "issuanceDate": "2024-01-01T00:00:00.000Z",
  "credentialSubject": {
    "id": "did:xrpl:user-address",
    "email": "user@example.com",
    "verificationLevel": "basic",
    "platform": "LendX"
  }
}
```

### Business Credential
- Business name and type
- Registration number
- Verification documents
- Enhanced trust level

### Income Credential
- Monthly income amount
- Currency and source
- Verification documents
- Credit assessment data

## Security Features

1. **JWT Token Validation**: All API endpoints protected with Auth0 JWT
2. **DID Ownership Verification**: Users can only access their own DID data
3. **Credential Integrity**: Verifiable credentials with issuer signatures
4. **XRPL Integration**: DID documents stored on decentralized ledger
5. **Secure Key Management**: Private keys never stored on backend

## Error Handling

- **Authentication Errors**: 401 with clear error messages
- **DID Creation Failures**: Detailed error responses with retry guidance
- **XRPL Connection Issues**: Graceful fallback and status reporting
- **Validation Errors**: 400 responses with validation details

## Testing

### Health Check
```bash
curl http://localhost:3001/health
```

### User Registration (with JWT)
```bash
curl -X POST http://localhost:3001/api/auth/register \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Get DID Document
```bash
curl http://localhost:3001/api/did/document \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Production Considerations

1. **Database Integration**: Replace in-memory storage with PostgreSQL/MongoDB
2. **Redis Caching**: Cache DID documents and credentials
3. **Key Management**: Use AWS KMS or similar for issuer key security
4. **Rate Limiting**: Implement API rate limiting
5. **Monitoring**: Add comprehensive logging and metrics
6. **Backup**: Regular backup of DID registry and user data
7. **HTTPS**: Enable SSL/TLS for all communications
8. **Secret Management**: Use environment-specific secret management

## Troubleshooting

### Common Issues

1. **Auth0 Configuration**
   - Verify domain, client ID, and secret
   - Check callback URLs in Auth0 dashboard
   - Ensure API audience is correct

2. **XRPL Connection**
   - Verify network selection (testnet/mainnet)
   - Check issuer wallet seed validity
   - Monitor XRPL network status

3. **JWT Token Issues**
   - Verify token expiration
   - Check audience and issuer claims
   - Ensure proper scopes

4. **DID Creation Failures**
   - Check XRPL wallet balance for fees
   - Verify network connectivity
   - Monitor transaction status

## Next Steps

1. **Enhanced UI**: Improve signup flow with better error handling
2. **Credential Management**: Add UI for viewing and managing credentials
3. **Trust Scores**: Implement reputation system based on credentials
4. **Multi-chain Support**: Extend to other blockchain networks
5. **Advanced Verification**: Integrate with external verification services
6. **Mobile Support**: Create mobile app with DID wallet functionality

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review XRPL documentation: https://xrpl.org/docs
3. Check Auth0 documentation: https://auth0.com/docs
4. Create an issue in the project repository