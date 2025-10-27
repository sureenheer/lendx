<div align="center">

# 🏆 Cal Hacks 2025 - First Place Winner 🏆

### Ripple: Best Use of XRP Ledger

[![Cal Hacks 2025](https://img.shields.io/badge/Cal%20Hacks%202025-1st%20Place-gold?style=for-the-badge)](https://cal-hacks-2025.devpost.com/)
[![Ripple Award](https://img.shields.io/badge/Ripple-Best%20Use%20of%20XRPL-blue?style=for-the-badge)](https://xrpl.org/)

</div>

---

# LendX

**Democratizing Access to Credit Through Decentralized Finance**

A decentralized lending marketplace built on XRPL (XRP Ledger) that enables peer-to-peer lending with verifiable credentials, multi-signature support, and automated settlement.

<div align="center">

[![Live Demo](https://img.shields.io/badge/Live%20Demo-lendxrp.vercel.app-brightgreen?style=for-the-badge)](https://lendxrp.vercel.app)
[![Demo Video](https://img.shields.io/badge/Demo%20Video-YouTube-red?style=for-the-badge)](https://www.youtube.com/watch?v=6GD9fiZIC9I)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688)](https://fastapi.tiangolo.com/)
[![XRPL](https://img.shields.io/badge/XRPL-Blockchain-0052FF)](https://xrpl.org/)

</div>

---

## Table of Contents

- [About the Project](#about-the-project)
- [Inspiration](#inspiration)
- [Key Features](#key-features)
- [Demo Video](#demo-video)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [What We Learned](#what-we-learned)
- [Accomplishments](#accomplishments)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## About the Project

LendX is a decentralized lending platform that leverages the XRP Ledger to create a trustless, efficient marketplace for peer-to-peer lending. By combining blockchain technology with modern UX design, we're making financial services accessible to underserved populations in emerging markets.

**Key Benefits:**

- Transaction fees of fractions of a cent
- Trustless loan agreements secured by blockchain
- Native wallet integration for seamless user experience
- Verifiable credentials for identity and reputation
- Real-time settlement with instant confirmation

---

## Inspiration

Financial inclusion remains one of the world's greatest challenges. Traditional banking systems fail to serve billions of people, particularly in emerging markets. We were inspired by the potential of decentralized finance (DeFi) to democratize access to credit for small business owners and entrepreneurs in regions like Southeast Asia, Africa, and Latin America.

**The Problem:**
- 1.7 billion adults globally remain unbanked
- Traditional credit scoring excludes individuals without formal financial history
- High banking fees make microlending economically unviable
- Cross-border lending is prohibitively expensive and slow

**Our Solution:**

LendX leverages XRPL's low transaction costs (fractions of a cent) and fast settlement times (3-5 seconds) to make microlending economically viable at scale.

---

## Key Features

### For Borrowers
- Browse lending pools with transparent rates and terms
- Submit loan applications with purpose descriptions
- Track application progress and repayment schedules in real-time
- Make loan payments with instant on-chain settlement
- Build on-chain reputation through successful repayments

### For Lenders
- Create lending pools with configurable interest rates, terms, and minimum amounts
- View pool analytics and historical returns
- Review and approve loan applications
- Manage funds and adjust pool parameters
- Multi-signature support for institutional lenders

### Core Technology
- Native XRPL integration without external wallet dependencies
- Multi-Purpose Tokens (MPT) representing loans on-chain
- Escrow transactions for trustless loan security
- DID-based verifiable credentials
- Real-time WebSocket updates for instant transaction feedback

---

## Demo Video

<div align="center">

[![LendX Demo Video](https://img.youtube.com/vi/6GD9fiZIC9I/maxresdefault.jpg)](https://www.youtube.com/watch?v=6GD9fiZIC9I)

**[Watch the Full Demo on YouTube](https://www.youtube.com/watch?v=6GD9fiZIC9I)**

</div>

---

## Project Structure

```
lendx/
├── frontend/                # Next.js 14 application
│   ├── app/                # App router pages
│   │   ├── (auth)/         # Authentication pages
│   │   └── (dashboard)/    # Main dashboard
│   ├── components/         # React UI components
│   │   ├── lendx/         # Core lending components
│   │   ├── ui/            # Shadcn/ui base components
│   │   └── dashboard/     # Dashboard components
│   └── lib/               # Utility libraries
│       └── xrpl/          # XRPL integration
├── backend/               # Python FastAPI services
│   ├── xrpl_client/      # XRPL client library
│   │   ├── client.py     # Connection and transactions
│   │   ├── mpt.py        # Multi-Purpose Token operations
│   │   ├── escrow.py     # Escrow transactions
│   │   └── multisig.py   # Multi-signature accounts
│   ├── api/              # FastAPI application
│   └── tests/            # Test suite
└── README.md
```

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Git

### Frontend Setup

```bash
# Clone the repository
git clone https://github.com/sureenheer/lendx.git
cd lendx

# Navigate to frontend
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Create environment file
cp .env.example .env.local
# Add your Auth0 and XRPL configuration

# Start development server
npm run dev
# Frontend runs on http://localhost:3000
```

### Backend Setup

```bash
# From project root
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run tests
pytest

# Start FastAPI server
uvicorn backend.api.main:app --reload
```

## Usage

### Frontend Application

The LendX frontend provides two main interfaces:

1. **Landing Page** (`/`): Welcome page with Auth0 login/signup
2. **Dashboard** (`/dashboard`): Main application with dual-role interface

**Lender Dashboard:**
- Create lending pools with custom rates and terms
- View pool statistics and available liquidity
- Approve/reject loan requests
- Withdraw funds from pools

**Borrower Dashboard:**
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

---

## Tech Stack

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript development
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/ui**: Component library built on Radix UI
- **Auth0**: Authentication with Google SSO
- **Framer Motion**: Animation library
- **XRPL.js**: Direct XRPL blockchain integration
- **Zustand**: State management

### Backend
- **Python 3.11+**: Core backend language
- **FastAPI**: High-performance web framework
- **xrpl-py**: Official Python XRPL library
- **Supabase**: PostgreSQL database
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation
- **pytest**: Testing framework

### Blockchain
- **XRP Ledger**: Layer-1 blockchain with native DeFi features
- **Multi-Purpose Tokens (MPT)**: Native token standard for loan representation
- **Escrow**: Built-in escrow functionality
- **Multi-signature**: Native multi-sig support

### DevOps
- **Vercel**: Frontend deployment platform
- **GitHub Actions**: CI/CD

---

## What We Learned

### Technical Insights
- XRPL's low transaction fees (fractions of a cent) make microlending economically viable at scale
- Multi-Purpose Tokens (MPT) provide an efficient solution for representing complex financial instruments on-chain
- Native blockchain integration significantly improves user experience compared to external wallet dependencies
- Verifiable credentials (DIDs) combined with OAuth create a powerful identity verification system

### Design & UX Lessons
- Real-time feedback is critical for financial applications
- Progressive disclosure improves user confidence in complex workflows
- Professional dark themes reduce eye strain during extended sessions

### Development Best Practices
- Test-driven development catches edge cases early
- Clean architecture with distinct layers improves maintainability
- Type safety (TypeScript + Pydantic) eliminates entire classes of bugs

---

## Accomplishments

### Technical Achievements
- Complete end-to-end lending flow working on XRPL testnet
- Production-grade UI/UX rivaling traditional fintech applications
- Native XRPL integration without external wallet dependencies
- Comprehensive Python XRPL library with MPT, escrow, and multi-sig support
- Real-time transaction monitoring with WebSocket updates
- PostgreSQL integration with SQLAlchemy ORM

### Business Impact
- Addressing financial exclusion affecting 1.7 billion people globally
- Demonstrated economic viability of microlending with XRPL's low costs
- Multi-signature support suitable for institutional lenders
- Scalable architecture for individual and large-scale lending

---

## Roadmap

### Phase 1: Mainnet Launch (Q1 2026)
- [ ] Mainnet deployment on XRPL production network
- [ ] Integrated fiat on/off ramps
- [ ] Security audits and smart contract verification
- [ ] Multi-currency support (USD, EUR, NGN, INR, BRL)

### Phase 2: Credit Scoring & Risk Management (Q2 2026)
- [ ] On-chain credit scoring algorithm
- [ ] Machine learning models for default prediction
- [ ] Borrower reputation system with verifiable credentials
- [ ] Automated interest rate adjustment

### Phase 3: Insurance & Risk Mitigation (Q3 2026)
- [ ] Insurance pools to protect lenders
- [ ] Parametric insurance using on-chain oracles
- [ ] Yield optimization for lenders
- [ ] Default recovery mechanisms

### Phase 4: Mobile-First Expansion (Q4 2026)
- [ ] Progressive Web App (PWA) for emerging markets
- [ ] SMS-based notifications
- [ ] Offline-first architecture for low-connectivity regions
- [ ] Native mobile apps for iOS and Android

### Phase 5: Ecosystem Growth (2027+)
- [ ] Self-sovereign identity integration
- [ ] Cross-chain lending support
- [ ] Institutional lending products
- [ ] Developer API and SDK
- [ ] Decentralized governance (DAO)

---

## Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help makes LendX better.

### How to Contribute

1. **Fork the repository**
   ```bash
   git clone https://github.com/sureenheer/lendx.git
   cd lendx
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes and commit**
   ```bash
   git commit -m 'feat: add amazing feature'
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

5. **Open a Pull Request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Include screenshots for UI changes

### Development Guidelines

- Follow existing code style and conventions
- Write tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting PR

For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

### Awards & Recognition
- **Cal Hacks 2025** - First Place Winner
- **Ripple** - Best Use of XRP Ledger Award

### Technology Partners
- **[XRPL Foundation](https://xrpl.org/)** - XRP Ledger documentation and developer resources
- **[Ripple](https://ripple.com/)** - Enterprise blockchain solutions and XRPL ecosystem support
- **[Auth0](https://auth0.com/)** - Authentication and identity management
- **[Vercel](https://vercel.com/)** - Frontend deployment and hosting
- **[Supabase](https://supabase.com/)** - PostgreSQL database infrastructure

### Community & Support
- **Cal Hacks 2025 Organizers**
- **XRPL Developer Community**
- **All Cal Hacks 2025 Participants**

---

<div align="center">

**Built at Cal Hacks 2025**

[![Cal Hacks](https://img.shields.io/badge/Cal%20Hacks-2025-gold?style=for-the-badge)](https://calhacks.io/)
[![XRPL](https://img.shields.io/badge/Powered%20by-XRPL-0052FF?style=for-the-badge)](https://xrpl.org/)

**[Live Demo](https://lendxrp.vercel.app)** • **[Watch Demo Video](https://www.youtube.com/watch?v=6GD9fiZIC9I)** • **[Report Bug](https://github.com/sureenheer/lendx/issues)** • **[Request Feature](https://github.com/sureenheer/lendx/issues)**

---

Made by the LendX Team | © 2025 | [MIT License](LICENSE)

</div>
