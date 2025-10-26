# LendX

A decentralized lending marketplace built on XRPL (XRP Ledger) with verifiable credentials, multi-signature support, and automated settlement.

## 🚀 Features

- **Decentralized Lending**: Create lending pools and apply for loans
- **Dual Role Interface**: Switch between lender and borrower views
- **XRPL Integration**: Native XRP Ledger blockchain integration with MPT (Multi-Purpose Token) support
- **Verifiable Credentials**: DID-based identity and trust system
- **Xumm Wallet Support**: Secure wallet connection and transaction signing with JWT OAuth
- **Auth0 Integration**: Enterprise-grade authentication and authorization
- **Real-time Dashboard**: Professional financial interface with dark theme (Next.js 14 + React 19)
- **Escrow Automation**: Smart contract-like escrow for loan security
- **Multi-signature Support**: Enterprise-grade security features
- **Dual Backend Architecture**: Python FastAPI for blockchain operations + Express.js for authentication

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 14 with React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4 + PostCSS
- **UI Components**: Shadcn/ui with Radix UI
- **State Management**: Zustand
- **Form Handling**: React Hook Form + Zod validation
- **Authentication**: Auth0 (@auth0/nextjs-auth0)
- **XRPL Integration**: xrpl SDK + Xumm SDK

### Backend
- **Python FastAPI**: Primary backend for lending logic and XRPL operations
  - Database: SQLAlchemy ORM + PostgreSQL (Supabase)
  - XRPL Client: xrpl-py library
  - Services: DID, MPT, Xumm integration
- **Express.js**: Authentication and identity management
  - Auth0 JWT authentication
  - DID operations
  - Port: 3001

## 📁 Project Structure

```
lendx/
├── frontend/                # Next.js 14 LendX application (PRIMARY UI)
│   ├── app/                # App router pages
│   │   ├── (auth)/         # Authentication flow
│   │   └── (dashboard)/    # Main dashboard
│   ├── components/         # UI components
│   │   ├── lendx/         # Core LendX components
│   │   ├── ui/            # Shadcn/ui components
│   │   └── dashboard/     # Dashboard widgets
│   ├── lib/               # Utilities
│   │   └── xrpl/         # XRPL integration layer
│   ├── hooks/             # React hooks
│   └── package.json       # Next.js dependencies
├── @backend/              # Express.js Node backend
│   └── src/
│       ├── index.ts       # Express server (port 3001)
│       ├── auth/          # Auth0 JWT authentication
│       ├── routes/        # API routes (auth, DID)
│       └── services/      # Business logic
├── backend/               # Python FastAPI services (PRIMARY BACKEND)
│   ├── api/              # FastAPI endpoints
│   │   ├── main.py       # Main application
│   │   ├── auth.py       # Authentication
│   │   └── xumm.py       # Xumm wallet integration
│   ├── xrpl_client/      # XRPL client library
│   ├── services/         # Business logic
│   │   ├── did_service.py    # Decentralized identity
│   │   ├── mpt_service.py    # Multi-Purpose Token
│   │   └── xumm_service.py   # Xumm integration
│   ├── models/           # Database models
│   ├── config/           # Configuration & database
│   ├── migrations/       # Database migrations
│   └── tests/            # Test suite
├── client/                # Vite app (experimental/untracked)
├── pyproject.toml        # Python dependencies
└── README.md
```

## 🛠️ Installation

### Frontend (LendX App)

```bash
# Clone the repository
git clone https://github.com/sureenheer/calhacks.git
cd calhacks

# Navigate to frontend
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Create environment file
cp .env.local.example .env.local
# Add your Xumm API credentials and Auth0 configuration

# Start development server
npm run dev
# Frontend runs on http://localhost:3000
```

### Backend (Python FastAPI)

```bash
# From project root
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Configure database (create .env in backend/)
# Add DATABASE_URL, SUPABASE_URL, SUPABASE_KEY

# Start FastAPI server
uvicorn backend.api.main:app --reload --port 8000
```

### Backend (Express.js)

```bash
# Navigate to @backend directory
cd @backend

# Install dependencies
npm install

# Configure Auth0 (create .env)
# Add AUTH0_DOMAIN, AUTH0_AUDIENCE, etc.

# Start Express server
npm run dev  # Runs on port 3001
```

## 📖 Usage

### XRPL Client

```python
from src.xrpl_client import connect, submit_and_wait
from xrpl.wallet import Wallet

# Connect to XRPL
client = connect('testnet')

# Create a wallet
wallet = Wallet.create()

# Submit a transaction
tx = {
    "TransactionType": "Payment",
    "Account": wallet.address,
    "Destination": "rDestinationAddress",
    "Amount": "1000000"  # 1 XRP in drops
}
result = submit_and_wait(client, tx, wallet)
```

### Multi-Signature Accounts

```python
from src.xrpl_client import setup_multisig_account, create_multisig_tx

# Setup multisig account
signers = ["rAddress1", "rAddress2", "rAddress3"]
tx_hash = setup_multisig_account(client, master_wallet, signers, threshold=2)

# Create multisigned transaction
multisig_blob = create_multisig_tx(tx_json, [wallet1, wallet2])
```

### MPT Operations

```python
from src.xrpl_client import create_issuance, mint_to_holder, get_mpt_balance

# Create MPT issuance
issuance_id = create_issuance(client, issuer_wallet, "TOKEN", "My Token")

# Mint tokens to holder
tx_hash = mint_to_holder(client, issuer_wallet, holder_address, 100.0, issuance_id)

# Check balance
balance = get_mpt_balance(client, holder_address, issuance_id)
```

### Escrow Transactions

```python
from src.xrpl_client import create_deposit_escrow, finish_escrow

# Create deposit escrow
sequence = create_deposit_escrow(client, member_wallet, 1000000, dest_address)

# Finish escrow (when conditions are met)
tx_hash = finish_escrow(client, wallet, owner_address, sequence)
```

## 🔧 Configuration

### Environment Variables

**Frontend** (`frontend/.env.local`):
```env
# Auth0 Configuration
AUTH0_SECRET=your_auth0_secret
AUTH0_BASE_URL=http://localhost:3000
AUTH0_ISSUER_BASE_URL=https://your-domain.auth0.com
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret

# Xumm Wallet
NEXT_PUBLIC_XUMM_API_KEY=your_xumm_api_key

# Backend URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTH_API_URL=http://localhost:3001
```

**Python Backend** (`backend/.env`):
```env
# Database (Supabase/PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key

# XRPL Network
XRPL_NETWORK=testnet  # or mainnet

# Xumm Integration
XUMM_API_KEY=your_xumm_api_key
XUMM_API_SECRET=your_xumm_api_secret
```

**Express Backend** (`@backend/.env`):
```env
# Auth0 Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_AUDIENCE=your_api_audience
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret

# Server
PORT=3001
NODE_ENV=development
```

## 🧪 Testing

```bash
# Run Python tests
pytest

# Run frontend tests
cd frontend
npm test

# Lint code
cd frontend && npm run lint
```

## 📚 Documentation

- [CalHacks 2025 Notion](https://www.notion.so/CalHacks-2025-29853e49b0ab80b48a7af9dbcd6f10eb?source=copy_link)
- [API Documentation](docs/api.md) (coming soon)
- [Architecture Overview](docs/architecture.md) (coming soon)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [XRPL Documentation](https://xrpl.org/) for comprehensive ledger documentation
- [Xaman Wallet](https://xaman.app/) for wallet integration
- CalHacks 2025 organizers and participants

## 📞 Support

If you have any questions or need support:

- Open an [Issue](https://github.com/sureenheer/calhacks/issues)
- Join our [Discussions](https://github.com/sureenheer/calhacks/discussions)
- Check our [Notion](https://www.notion.so/CalHacks-2025-29853e49b0ab80b48a7af9dbcd6f10eb?source=copy_link) documentation

---

**Built with ❤️ for CalHacks 2025**
