# LendX

A decentralized lending marketplace built on XRPL (XRP Ledger) with verifiable credentials, multi-signature support, and automated settlement.

## 🚀 Features

- **Decentralized Lending**: Create lending pools and apply for loans
- **Dual Role Interface**: Switch between lender and borrower views
- **XRPL Integration**: Native XRP Ledger blockchain integration
- **Verifiable Credentials**: DID-based identity and trust system
- **Xumm Wallet Support**: Secure wallet connection and transaction signing
- **Real-time Dashboard**: Professional financial interface with dark theme
- **Escrow Automation**: Smart contract-like escrow for loan security
- **Multi-signature Support**: Enterprise-grade security features

## 📁 Project Structure

```
lendx/
├── frontend/                # Next.js 14 LendX application
│   ├── app/                # App router pages
│   │   ├── (auth)/         # Authentication flow
│   │   └── (dashboard)/    # Main dashboard
│   ├── components/         # UI components
│   │   ├── lendx/         # Core LendX components
│   │   ├── ui/            # Shadcn/ui components
│   │   └── dashboard/     # Dashboard widgets
│   ├── lib/               # Utilities
│   │   └── xrpl/         # XRPL integration layer
│   └── package.json
├── backend/               # Python FastAPI services
│   ├── xrpl_client/      # XRPL client library
│   ├── graph/           # Settlement algorithms
│   └── services/        # Business logic
├── pyproject.toml        # Python dependencies
└── README.md
```

## 🛠️ Installation

### Frontend (LendX App)

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
# Add your Xumm API credentials

# Start development server
npm run dev
```

### Backend (Python)

```bash
# From project root
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Start FastAPI server (when implemented)
uvicorn backend.api.main:app --reload
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

Create a `.env` file in the root directory:

```env
# XRPL Network
XRPL_NETWORK=testnet  # or mainnet

# Xaman Wallet (for frontend)
VITE_XAMAN_API_KEY=your_api_key
VITE_XAMAN_API_SECRET=your_api_secret
```

## 🧪 Testing

```bash
# Run Python tests
pytest

# Run frontend tests
cd client
npm test

# Lint code
cd client && npm run lint
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
