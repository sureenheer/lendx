<div align="center">

# 🏆 Cal Hacks 2025 - First Place Winner 🏆

### Ripple: Best Use of XRP Ledger

[![Cal Hacks 2025](https://img.shields.io/badge/Cal%20Hacks%202025-1st%20Place-gold?style=for-the-badge)](https://cal-hacks-2025.devpost.com/)
[![Ripple Award](https://img.shields.io/badge/Ripple-Best%20Use%20of%20XRPL-blue?style=for-the-badge)](https://xrpl.org/)

</div>

---

# LendX

**Democratizing Access to Credit Through Decentralized Finance**

A decentralized lending marketplace built on XRPL (XRP Ledger) that empowers peer-to-peer lending with verifiable credentials, multi-signature support, and automated settlement - focused on bringing financial inclusion to emerging markets.

<div align="center">

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-lendxrp.vercel.app-brightgreen?style=for-the-badge)](https://lendxrp.vercel.app)
[![Demo Video](https://img.shields.io/badge/🎥%20Demo%20Video-YouTube-red?style=for-the-badge)](https://www.youtube.com/watch?v=6GD9fiZIC9I)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688)](https://fastapi.tiangolo.com/)
[![XRPL](https://img.shields.io/badge/XRPL-Blockchain-0052FF)](https://xrpl.org/)

</div>

---

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [Inspiration](#-inspiration)
- [Key Features](#-key-features)
- [Demo Video](#-demo-video)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [What We Learned](#-what-we-learned)
- [Accomplishments](#-accomplishments)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 🌟 About the Project

LendX is a revolutionary decentralized lending platform that leverages the XRP Ledger to create a trustless, efficient, and accessible marketplace for peer-to-peer lending. By combining blockchain technology with modern UX design, we're making financial services accessible to billions of underserved people in emerging markets.

Unlike traditional banking systems that exclude billions due to lack of credit history, high fees, and geographical barriers, LendX enables:

- **Zero-friction lending** with transaction fees of fractions of a cent
- **Trustless loan agreements** secured by blockchain smart contracts
- **Native wallet integration** for seamless user experience
- **Verifiable credentials** for identity and reputation without traditional credit scores
- **Real-time settlement** with instant transaction confirmation

### 🖼️ Screenshots

> 📸 **Coming Soon**: Screenshots showcasing the lender dashboard, borrower interface, loan application flow, and real-time transaction monitoring.

---

## 💡 Inspiration

Financial inclusion remains one of the world's greatest challenges, particularly in emerging markets where traditional banking systems fail to serve billions of people. We were inspired by the potential of decentralized finance (DeFi) to democratize access to credit, especially for small business owners and entrepreneurs in regions like Southeast Asia, Africa, and Latin America.

**The Problem:**
- 1.7 billion adults globally remain unbanked
- Traditional credit scoring excludes individuals without formal financial history
- High banking fees make microlending economically unviable
- Cross-border lending is prohibitively expensive and slow

**Our Solution:**
LendX leverages XRPL's incredibly low transaction costs (fractions of a cent) and fast settlement times (3-5 seconds) to make microlending economically viable at scale. By building a native blockchain application with verifiable credentials, we're creating a new paradigm for trust and credit access.

---

## ✨ Key Features

### For Borrowers
- 🔍 **Browse Lending Pools**: Discover lending opportunities with transparent rates and terms
- 📝 **Apply for Loans**: Submit loan applications with purpose descriptions and verifiable credentials
- 💳 **Track Loan Status**: Monitor application progress, approval status, and repayment schedules in real-time
- 💰 **Make Payments**: Seamless loan repayment with instant on-chain settlement
- 🎯 **Credit Building**: Build on-chain reputation through successful loan repayments

### For Lenders
- 🏦 **Create Lending Pools**: Deploy custom lending pools with configurable interest rates, terms, and minimum amounts
- 📊 **Pool Analytics**: View detailed statistics on pool performance, available liquidity, and historical returns
- ✅ **Approve Loans**: Review and approve loan applications with borrower credential verification
- 💸 **Manage Funds**: Withdraw earnings and adjust pool parameters dynamically
- 🔐 **Multi-signature Support**: Enterprise-grade security for institutional lenders

### Core Technology
- ⚡ **Native XRPL Integration**: Direct blockchain integration without external wallet dependencies
- 🎫 **Multi-Purpose Tokens (MPT)**: Tokenized debt instruments representing loans on-chain
- 🔒 **Escrow Transactions**: Trustless loan security with conditional fund release
- 🌐 **Verifiable Credentials**: DID-based identity system for borrower trust
- 📱 **Real-time Updates**: WebSocket subscriptions for instant transaction feedback
- 🎨 **Professional UI/UX**: Modern, responsive interface rivaling traditional fintech apps

---

## 🎥 Demo Video

<div align="center">

[![LendX Demo Video](https://img.youtube.com/vi/6GD9fiZIC9I/maxresdefault.jpg)](https://www.youtube.com/watch?v=6GD9fiZIC9I)

**[Watch the Full Demo on YouTube](https://www.youtube.com/watch?v=6GD9fiZIC9I)**

</div>

---

## 📁 Project Structure

```
lendx/
├── frontend/                # Next.js 14 LendX application (PRIMARY UI)
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

---

## 🚀 Getting Started

Ready to run LendX locally? Follow these steps to get your development environment up and running.

### Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js** 18+ and npm
- **Python** 3.11+
- **Git**

### Frontend (Next.js Application)

```bash
# Clone the repository
git clone https://github.com/sureenheer/lendx.git
cd calhacks

# Navigate to frontend
cd frontend

# Install dependencies (legacy peer deps required for some XRPL packages)
npm install --legacy-peer-deps

# Create environment file
cp .env.example .env.local
# Add your Auth0 and XRPL configuration

# Start development server
npm run dev
# Frontend runs on http://localhost:3000
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

**Python Backend** (`backend/.env`):
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

## 🛠️ Tech Stack

### Frontend
- ![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js) **Next.js 14**: React framework with App Router
- ![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript) **TypeScript**: Type-safe JavaScript development
- ![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.0-38B2AC?logo=tailwind-css) **Tailwind CSS**: Utility-first CSS framework
- ![Shadcn/ui](https://img.shields.io/badge/Shadcn%2Fui-Latest-black) **Shadcn/ui**: Modern component library built on Radix UI
- ![Auth0](https://img.shields.io/badge/Auth0-Latest-EB5424?logo=auth0) **Auth0**: Authentication and user management with Google SSO
- ![Framer Motion](https://img.shields.io/badge/Framer%20Motion-11.0-0055FF?logo=framer) **Framer Motion**: Production-ready animation library
- ![XRPL.js](https://img.shields.io/badge/XRPL.js-4.4.2-0052FF) **XRPL.js**: Direct XRPL blockchain integration
- ![Zustand](https://img.shields.io/badge/Zustand-4.5-brown) **Zustand**: Lightweight state management

### Backend
- ![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python) **Python 3.11+**: Core backend language
- ![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi) **FastAPI**: Modern, high-performance web framework
- ![xrpl-py](https://img.shields.io/badge/xrpl--py-3.1-0052FF) **xrpl-py**: Official Python XRPL library
- ![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase) **Supabase**: PostgreSQL database with real-time capabilities
- ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00) **SQLAlchemy**: ORM for database operations
- ![Pydantic](https://img.shields.io/badge/Pydantic-2.0-E92063) **Pydantic**: Data validation and settings management
- ![pytest](https://img.shields.io/badge/pytest-8.0-0A9EDC?logo=pytest) **pytest**: Comprehensive testing framework

### Blockchain
- ![XRPL](https://img.shields.io/badge/XRPL-Testnet%20%26%20Mainnet-0052FF) **XRP Ledger**: Layer-1 blockchain with native DeFi features
- **Multi-Purpose Tokens (MPT)**: XRPL native token standard for loan representation
- **Escrow**: Built-in escrow functionality for trustless transactions
- **Multi-signature**: Native multi-sig support for institutional security

### DevOps
- ![Vercel](https://img.shields.io/badge/Vercel-Deployment-black?logo=vercel) **Vercel**: Frontend deployment platform
- ![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?logo=github-actions) **GitHub Actions**: Continuous integration and deployment

---

## 🎓 What We Learned

Building LendX from concept to production taught us invaluable lessons about blockchain development, user experience, and financial technology:

### Technical Insights
- **XRPL's Economic Advantage**: The power of XRPL's incredibly low transaction fees (fractions of a cent) makes microlending economically viable at scale - something impossible with Ethereum's gas fees or Bitcoin's transaction costs
- **Multi-Purpose Tokens (MPT)**: XRPL's native MPT feature provides an elegant, gas-efficient solution for representing complex financial instruments on-chain without requiring smart contracts
- **Native Integration > External Wallets**: Building native blockchain integration significantly improves user experience compared to external wallet dependencies like MetaMask or Xumm
- **Identity Layer**: Verifiable credentials (DIDs) combined with traditional OAuth create a powerful identity verification system that bridges Web2 and Web3

### Design & UX Lessons
- **Real-time Feedback is Critical**: Financial applications require immediate transaction feedback - users need to see their actions reflected instantly
- **Progressive Disclosure**: Breaking complex lending workflows into simple, guided steps dramatically improves user confidence
- **Dark Mode for Financial Apps**: Professional dark themes reduce eye strain during extended financial management sessions

### Development Best Practices
- **Test-Driven Development**: Writing comprehensive test suites for database models and XRPL operations caught edge cases early
- **Separation of Concerns**: Clean architecture with distinct layers (API, services, blockchain client) made the codebase maintainable
- **Type Safety Everywhere**: TypeScript on frontend + Pydantic on backend eliminated entire classes of bugs

---

## 🏅 Accomplishments

We're incredibly proud of what we achieved in 36 hours:

### Technical Achievements
- ✅ **Complete End-to-End Flow**: Full lending lifecycle from pool creation → loan application → approval → disbursement → repayment working on XRPL testnet
- ✅ **Production-Grade UI/UX**: Professional interface that rivals traditional fintech applications like LendingClub or Prosper
- ✅ **Native XRPL Integration**: Direct blockchain integration without external wallet dependencies, providing seamless user experience
- ✅ **Comprehensive Python XRPL Library**: Robust, well-tested Python library for XRPL operations with full MPT, escrow, and multi-sig support
- ✅ **Real-time Transaction Monitoring**: WebSocket-based real-time updates providing immediate feedback for all blockchain operations
- ✅ **Database-Backed Application State**: Full PostgreSQL integration with SQLAlchemy ORM for indexing on-chain data

### Business Impact
- 🌍 **Addressing Real-World Problems**: Tackling financial exclusion affecting 1.7 billion people globally
- 💰 **Economic Viability**: Demonstrated that microlending can be profitable with XRPL's low transaction costs
- 🏦 **Institutional-Ready**: Multi-signature support makes the platform suitable for institutional lenders and DeFi protocols
- 📈 **Scalable Architecture**: Built to support both individual peer-to-peer lending and large-scale lending pools

---

## 🚀 Roadmap / What's Next

LendX is just getting started. Here's our vision for the future:

### Phase 1: Mainnet Launch (Q1 2026)
- [ ] Mainnet deployment on XRPL production network
- [ ] Integrated fiat on/off ramps via payment providers (Stripe, PayPal, local payment networks)
- [ ] Enhanced security audits and smart contract verification
- [ ] Multi-currency support for local currency lending pools (USD, EUR, NGN, INR, BRL)

### Phase 2: Credit Scoring & Risk Management (Q2 2026)
- [ ] On-chain credit scoring algorithm using XRPL transaction history
- [ ] Machine learning models for default prediction and risk assessment
- [ ] Borrower reputation system with verifiable credentials
- [ ] Automated interest rate adjustment based on borrower credit score

### Phase 3: Insurance & Risk Mitigation (Q3 2026)
- [ ] Insurance pools to protect lenders against default risk
- [ ] Parametric insurance using on-chain oracles
- [ ] Yield optimization for lenders through automated pool allocation
- [ ] Default recovery mechanisms and liquidation protocols

### Phase 4: Mobile-First Expansion (Q4 2026)
- [ ] Progressive Web App (PWA) optimized for smartphone usage in emerging markets
- [ ] SMS-based notifications for loan status updates
- [ ] Offline-first architecture for low-connectivity regions
- [ ] Native mobile apps for iOS and Android

### Phase 5: Ecosystem Growth (2027+)
- [ ] Integration with decentralized identity protocols (Self-Sovereign Identity)
- [ ] Cross-chain lending support (Ethereum, Polygon, Solana)
- [ ] Institutional lending products for banks and financial institutions
- [ ] Developer API and SDK for third-party integrations
- [ ] Decentralized governance through DAO structure

---

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help makes LendX better for everyone.

### How to Contribute

1. **Fork the repository**
   ```bash
   git clone https://github.com/sureenheer/lendx.git
   cd calhacks
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

- Follow the existing code style and conventions
- Write tests for new features (we use pytest for backend, Jest for frontend)
- Update documentation for API changes
- Ensure all tests pass before submitting PR

For detailed contributing guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

You are free to use, modify, and distribute this software for any purpose, including commercial use, as long as you include the original copyright and license notice.

---

## 🙏 Acknowledgments

We couldn't have built LendX without the support of:

### Awards & Recognition
- **Cal Hacks 2025** - First Place Winner
- **Ripple** - Best Use of XRP Ledger Award

### Technology Partners
- **[XRPL Foundation](https://xrpl.org/)** - For comprehensive XRP Ledger documentation and developer resources
- **[Ripple](https://ripple.com/)** - For pioneering enterprise blockchain solutions and supporting the XRPL ecosystem
- **[Auth0](https://auth0.com/)** - For providing robust authentication and identity management services
- **[Vercel](https://vercel.com/)** - For seamless frontend deployment and hosting
- **[Supabase](https://supabase.com/)** - For PostgreSQL database infrastructure

### Community & Support
- **Cal Hacks 2025 Organizers** - For creating an amazing hackathon experience
- **XRPL Developer Community** - For invaluable support and technical guidance
- **All Cal Hacks 2025 Participants** - For the inspiring collaboration and innovation

### Special Thanks
To everyone who believed in the vision of democratizing access to credit through decentralized finance.

---

<div align="center">

**Built with ❤️ at Cal Hacks 2025**

[![Cal Hacks](https://img.shields.io/badge/Cal%20Hacks-2025-gold?style=for-the-badge)](https://calhacks.io/)
[![XRPL](https://img.shields.io/badge/Powered%20by-XRPL-0052FF?style=for-the-badge)](https://xrpl.org/)

**[Live Demo](https://lendxrp.vercel.app)** • **[Watch Demo Video](https://www.youtube.com/watch?v=6GD9fiZIC9I)** • **[Report Bug](https://github.com/sureenheer/lendx/issues)** • **[Request Feature](https://github.com/sureenheer/lendx/issues)**

---

### ⭐ If you found LendX helpful, please consider giving us a star on GitHub! ⭐

---

Made by the LendX Team | © 2025 | [MIT License](LICENSE)

</div>
