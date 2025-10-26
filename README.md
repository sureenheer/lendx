# LendX

A decentralized lending marketplace built on XRPL (XRP Ledger) with Auth0 authentication, XRPL wallet integration, and a modern React-based interface focused on emerging market lending.

## Features

- **Decentralized Lending**: Create lending pools and apply for loans through peer-to-peer transactions
- **Dual Role Interface**: Seamlessly switch between lender and borrower dashboard views
- **XRPL Integration**: Native XRP Ledger blockchain integration with direct transaction support
- **Auth0 Authentication**: Google SSO integration with secure authentication flows
- **XRPL Wallet Management**: Direct wallet generation and connection (replacing Xumm SDK)
- **Verifiable Credentials**: DID-based identity and trust system for borrower verification
- **Professional Dashboard**: Modern React interface with dark theme and responsive design
- **Multi-signature Support**: Enterprise-grade security features for institutional use

## Project Structure

```
lendx/
├── frontend/                # Next.js 14 LendX application
│   ├── app/                # App router pages
│   │   ├── (auth)/         # Authentication pages (signup)
│   │   ├── (dashboard)/    # Main dashboard with lender/borrower views
│   │   ├── layout.tsx     # Root layout with theme provider
│   │   └── page.tsx       # Landing page
│   ├── components/         # React UI components
│   │   ├── lendx/         # Core lending components (lender-view, borrower-view)
│   │   ├── ui/            # Shadcn/ui base components
│   │   ├── dashboard/     # Dashboard-specific components
│   │   ├── chat/          # Chat interface components
│   │   └── icons/         # Custom icon components
│   ├── lib/               # Utility libraries
│   │   ├── xrpl/         # XRPL integration (client, wallet, transactions, credentials)
│   │   ├── auth0.ts      # Auth0 configuration
│   │   └── utils.ts      # General utilities
│   └── package.json      # Frontend dependencies
├── backend/               # Python FastAPI services
│   ├── xrpl_client/      # XRPL client library
│   │   ├── client.py     # Connection and transaction handling
│   │   ├── mpt.py        # Multi-Purpose Token operations
│   │   ├── escrow.py     # Escrow transaction handling
│   │   ├── multisig.py   # Multi-signature account management
│   │   └── exceptions.py # Custom XRPL exceptions
│   ├── api/              # FastAPI application
│   └── tests/            # Python test suite
├── pyproject.toml        # Python dependencies and configuration
└── README.md
```

## Installation

### Frontend (Next.js Application)

```bash
# Clone the repository
git clone https://github.com/sureenheer/lendx.git
cd lendx

# Navigate to frontend
cd frontend

# Install dependencies (legacy peer deps required for some XRPL packages)
npm install --legacy-peer-deps

# Create environment file
cp .env.example .env.local
# Add your Auth0 and XRPL configuration

# Start development server
npm run dev
```

### Backend (Python Services)

```bash
# From project root
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run tests
pytest

# Start FastAPI server (when implemented)
uvicorn backend.api.main:app --reload
```

## Usage

### Frontend Application

The LendX frontend provides two main interfaces:

1. **Landing Page** (`/`): Welcome page with Auth0 login/signup
2. **Dashboard** (`/dashboard`): Main application with dual-role interface

#### Lender Dashboard Features
- Create lending pools with custom rates and terms
- View pool statistics and available liquidity
- Approve/reject loan requests from borrowers
- Withdraw funds from pools

#### Borrower Dashboard Features
- Browse available lending pools
- Apply for loans with purpose descriptions
- Track loan status and repayment schedules
- Make loan payments

### Python XRPL Client Library

#### Basic Connection and Transactions

```python
from backend.xrpl_client import connect, submit_and_wait
from xrpl.wallet import Wallet

# Connect to XRPL network
client = connect('testnet')  # or 'mainnet'

# Create a wallet
wallet = Wallet.create()

# Submit a payment transaction
tx = {
    "TransactionType": "Payment",
    "Account": wallet.address,
    "Destination": "rDestinationAddress",
    "Amount": "1000000"  # 1 XRP in drops
}
result = submit_and_wait(client, tx, wallet)
```

#### Multi-Purpose Token (MPT) Operations

```python
from backend.xrpl_client import create_issuance, mint_to_holder, get_mpt_balance

# Create MPT issuance for loan representation
issuance_id = create_issuance(client, issuer_wallet, "LOAN", "LendX Loan Token")

# Mint tokens to represent loan amount
tx_hash = mint_to_holder(client, issuer_wallet, borrower_address, 100.0, issuance_id)

# Check token balance
balance = get_mpt_balance(client, borrower_address, issuance_id)
```

#### Escrow Operations for Loan Security

```python
from backend.xrpl_client import create_deposit_escrow, finish_escrow

# Create escrow for loan collateral
sequence = create_deposit_escrow(client, borrower_wallet, 1000000, lender_address)

# Release escrow when loan is repaid
tx_hash = finish_escrow(client, lender_wallet, borrower_address, sequence)
```

#### Multi-Signature Account Management

```python
from backend.xrpl_client import setup_multisig_account, create_multisig_tx

# Setup multisig account for institutional lending
signers = ["rAddress1", "rAddress2", "rAddress3"]
tx_hash = setup_multisig_account(client, master_wallet, signers, threshold=2)

# Create multi-signed transaction
multisig_blob = create_multisig_tx(tx_json, [wallet1, wallet2])
```

## Configuration

### Environment Variables

Create a `.env.local` file in the frontend directory:

```env
# Auth0 Configuration
AUTH0_SECRET='use [openssl rand -hex 32] to generate a 32 bytes value'
AUTH0_BASE_URL='http://localhost:3000'
AUTH0_ISSUER_BASE_URL='https://your-tenant.auth0.com'
AUTH0_CLIENT_ID='your_auth0_client_id'
AUTH0_CLIENT_SECRET='your_auth0_client_secret'

# XRPL Configuration
NEXT_PUBLIC_XRPL_NETWORK=testnet  # or mainnet
NEXT_PUBLIC_XRPL_WEBSOCKET=wss://s.altnet.rippletest.net:51233

# Optional: Xumm Wallet Integration (legacy)
NEXT_PUBLIC_XAMAN_API_KEY=your_xaman_key
NEXT_PUBLIC_XAMAN_API_SECRET=your_xaman_secret
```

## Testing

```bash
# Run Python backend tests
pytest

# Run frontend linting
cd frontend
npm run lint

# Build frontend for production
npm run build
```

## Tech Stack

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript development
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/ui**: Modern component library
- **Auth0**: Authentication and user management
- **Framer Motion**: Animation library
- **XRPL.js**: Direct XRPL blockchain integration
- **Zustand**: State management

### Backend
- **Python 3.11+**: Core backend language
- **FastAPI**: Modern Python web framework
- **xrpl-py**: Official Python XRPL library
- **Pydantic**: Data validation and settings management
- **pytest**: Testing framework

## Key Implementation Details

### XRPL Integration
- Direct wallet generation replacing Xumm SDK dependency
- Multi-Purpose Token (MPT) support for loan representation
- Escrow transactions for secure loan handling
- Multi-signature account support for institutional use
- WebSocket subscriptions for real-time updates

### Authentication Flow
- Auth0 Google SSO integration
- XRPL wallet connection and DID generation
- Verifiable credential management for borrower verification

### Frontend Architecture
- Dual-role dashboard with seamless switching
- Real-time transaction status updates
- Responsive design with dark theme
- Professional financial interface components

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [XRPL Documentation](https://xrpl.org/) for comprehensive ledger documentation
- [Auth0](https://auth0.com/) for authentication services
- CalHacks 2025 organizers and participants

Built for CalHacks 2025
