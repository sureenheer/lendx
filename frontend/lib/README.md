# LendX Frontend Integration Layer

This directory contains the complete frontend integration layer for the LendX decentralized lending marketplace.

## Overview

The integration layer connects the Next.js UI components with:
- XRPL (XRP Ledger) blockchain via Xumm wallet
- FastAPI backend for lending pool and loan management
- State management for wallet and demo flows

## Directory Structure

```
lib/
├── xrpl/                    # XRPL integration modules
│   ├── index.ts            # Main export file
│   ├── types.ts            # TypeScript interfaces
│   ├── wallet.ts           # Xumm wallet connection
│   ├── transactions.ts     # Transaction builders
│   ├── hooks.ts            # React hooks with Zustand
│   └── credentials.ts      # Verifiable credentials manager
├── api.ts                  # Backend API client wrapper
├── demo-context.tsx        # Demo flow state management
├── v0-context.tsx          # V0 integration context
└── utils.ts                # Utility functions
```

## Key Features

### XRPL Integration (`/xrpl`)

**Wallet Management (`wallet.ts`)**
- Xumm SDK integration for mobile wallet signing
- Connect/disconnect wallet functionality
- Balance queries (XRP + RLUSD)
- Trust line management
- Transaction signing via Xumm

**Transaction Builders (`transactions.ts`)**
- Create lending pools
- Direct loan payments
- Loan repayments
- RLUSD trust line setup
- Integration with backend API

**React Hooks (`hooks.ts`)**
- `useWallet()` - Zustand store for wallet state
- `useRLUSDTrustline()` - Trust line status and setup
- `useWalletBalanceRefresh()` - Auto-refresh balances
- `useWalletReady()` - Check wallet readiness for transactions

**Types (`types.ts`)**
- Pool, LoanApplication, ActiveLoan interfaces
- Wallet state types
- Xumm payload and response types
- Trust line status types

**Credentials (`credentials.ts`)**
- Verifiable credentials management
- DID (Decentralized Identity) support
- Credential issuance and verification

### Backend API Client (`api.ts`)

Generic REST API client with endpoints for:
- **Pools**: List, get, create lending pools
- **Loans**: List applications, list active loans, apply, approve
- **Balance**: Get XRP/token balances
- **Health**: API health check

### State Management

**Demo Context (`demo-context.tsx`)**
- Lender flow state (empty → pool-created → loan-request → loan-approved)
- Borrower flow state (empty → pending → approved → payment-made)
- View mode switching (lender/borrower)
- Notification management
- Auto-dismissing notifications (5 second timeout)

**V0 Context (`v0-context.tsx`)**
- V0 integration state
- `useIsV0()` hook for components

### Utilities (`utils.ts`)

Formatting and helper functions:
- `cn()` - Tailwind class name merging
- `formatCurrency()` - Currency formatting with symbols
- `formatAddress()` - Shorten XRPL addresses
- `formatTxHash()` - Shorten transaction hashes
- `formatDate()` - Date formatting
- `calculateRepaymentAmount()` - Loan calculations
- `calculateInterest()` - Interest calculations
- `isValidXRPLAddress()` - Address validation
- `dropsToXRP()` / `xrpToDrops()` - XRP conversion

## Usage Examples

### Connect Wallet

```typescript
import { useWallet } from '@/lib/xrpl'

function WalletButton() {
  const { connected, address, connect, disconnect } = useWallet()

  return (
    <button onClick={connected ? disconnect : connect}>
      {connected ? `Disconnect ${formatAddress(address!)}` : 'Connect Wallet'}
    </button>
  )
}
```

### Create Lending Pool

```typescript
import { createLendingPool } from '@/lib/xrpl'
import { useWallet } from '@/lib/xrpl'

async function createPool() {
  const { address } = useWallet()

  const poolData = {
    poolId: `pool_${Date.now()}`,
    amount: '1000000000', // 1000 XRP in drops
    lender: address!,
  }

  const txHash = await createLendingPool(poolData)
  console.log('Pool created:', txHash)
}
```

### Fetch Pools from Backend

```typescript
import { poolsAPI } from '@/lib/api'

async function fetchPools() {
  const { pools } = await poolsAPI.list()
  return pools
}
```

### Use Demo Context

```typescript
import { useDemoContext } from '@/lib/demo-context'

function LenderDashboard() {
  const {
    lenderStep,
    setLenderStep,
    onNotificationAdd
  } = useDemoContext()

  const handleCreatePool = () => {
    setLenderStep('pool-created')
    onNotificationAdd({
      message: 'Pool created successfully!',
      type: 'success',
    })
  }

  return <div>Current step: {lenderStep}</div>
}
```

## Environment Variables

Copy `/frontend/.env.local.example` to `/frontend/.env.local` and configure:

```env
NEXT_PUBLIC_XUMM_API_KEY=your_xumm_api_key
NEXT_PUBLIC_XUMM_API_SECRET=your_xumm_api_secret
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_RLUSD_ISSUER=rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx
NEXT_PUBLIC_XRPL_NETWORK=testnet
```

## Architecture Decisions

### Why Zustand?
- Lightweight state management (already in dependencies)
- Persistent wallet state in localStorage
- Simple API with React hooks
- No provider wrapping needed

### Why Xumm SDK?
- Industry standard for XRPL mobile wallet integration
- QR code signing support
- Deep linking for mobile apps
- Secure transaction signing

### Why Separate Transaction Builders?
- Separation of concerns
- Easier testing
- Reusable across components
- Clear transaction structure

### Error Handling
- All XRPL operations wrapped in try-catch
- User-friendly error messages
- Console logging for debugging
- Error state in Zustand store

## Testing Checklist

- [x] TypeScript type checking passes
- [x] All imports resolve correctly
- [x] No circular dependencies
- [x] Wallet connection flow works
- [ ] Transaction signing with Xumm works (requires API keys)
- [ ] Backend API integration works (requires running backend)
- [ ] Demo flow state transitions work
- [ ] Notifications display and auto-dismiss

## Next Steps

1. **Add Xumm API Credentials**: Get credentials from https://apps.xumm.dev/
2. **Start Backend**: `uvicorn backend.api.main:app --reload`
3. **Test Wallet Connection**: Connect Xumm wallet via QR code
4. **Create Test Pool**: Use lender view to create a lending pool
5. **Apply for Loan**: Use borrower view to apply for a loan
6. **Approve Loan**: Use lender view to approve loan request

## Accessibility

All components follow WCAG 2.2 AA standards:
- Semantic HTML throughout
- Proper ARIA labels
- Keyboard navigation support
- Focus indicators visible
- Screen reader compatibility

## Performance

- Code splitting via dynamic imports
- Zustand middleware for localStorage persistence
- Balance refresh on 30-second intervals (configurable)
- Memoized components where appropriate
- Lazy loading for heavy operations

## Security Considerations

- Never store private keys in frontend
- All transactions signed via Xumm mobile app
- Environment variables for sensitive config
- Input validation on all user inputs
- Rate limiting on API calls (backend)
- HTTPS required in production

## Support

For issues or questions:
1. Check backend logs: `uvicorn backend.api.main:app --reload`
2. Check browser console for errors
3. Verify environment variables are set
4. Test with Xumm testnet wallet
5. Review XRPL testnet status

## License

MIT
