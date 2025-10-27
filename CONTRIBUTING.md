# Contributing to LendX

Welcome to LendX! We're thrilled that you're interested in contributing to our decentralized lending marketplace on XRPL. This project won first place at Cal Hacks 2025, and we're excited to continue building with the community.

LendX enables peer-to-peer lending with verifiable credentials, multi-signature support, and automated settlement through XRPL integration. Whether you're fixing bugs, adding features, improving documentation, or suggesting new ideas, your contributions are valued and appreciated.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Improving Documentation](#improving-documentation)
  - [Contributing Code](#contributing-code)
- [Development Setup](#development-setup)
  - [Prerequisites](#prerequisites)
  - [Frontend Setup](#frontend-setup)
  - [Backend Setup](#backend-setup)
  - [Environment Configuration](#environment-configuration)
- [Development Workflow](#development-workflow)
  - [Branch Naming Conventions](#branch-naming-conventions)
  - [Commit Message Guidelines](#commit-message-guidelines)
  - [Pull Request Process](#pull-request-process)
- [Code Style Guidelines](#code-style-guidelines)
  - [Frontend Standards](#frontend-standards)
  - [Backend Standards](#backend-standards)
- [Testing Requirements](#testing-requirements)
  - [Frontend Testing](#frontend-testing)
  - [Backend Testing](#backend-testing)
- [Documentation Standards](#documentation-standards)
- [Review Process](#review-process)
- [Community Guidelines](#community-guidelines)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. We are committed to providing a welcoming and inclusive environment for everyone, regardless of background or identity.

**Our Standards:**

- Be respectful and considerate in your communication
- Welcome diverse perspectives and experiences
- Accept constructive criticism gracefully
- Focus on what's best for the community and project
- Show empathy towards other community members

Unacceptable behavior includes harassment, trolling, personal attacks, or any conduct that makes others feel unwelcome. Project maintainers have the right to remove contributions or ban contributors who violate these standards.

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report, please:

1. **Check existing issues** to avoid duplicates
2. **Verify the bug** exists in the latest version
3. **Collect information** about your environment

When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs. actual behavior
- **Environment details** (OS, Node.js version, Python version, browser)
- **Screenshots or logs** if applicable
- **Additional context** that might help

**Example:**
```
Title: "MPT balance query returns incorrect value after escrow completion"

Steps to reproduce:
1. Create a lending pool with 1000 XRP
2. Approve a loan for 100 XRP
3. Complete the escrow transaction
4. Query MPT balance via GET /api/balances/mpt/{address}

Expected: Balance should be 900 XRP
Actual: Balance shows 1000 XRP

Environment:
- OS: Ubuntu 22.04
- Python: 3.11
- Node.js: 20.x
- XRPL Network: Testnet
```

### Suggesting Features

We welcome feature suggestions! Before submitting:

1. **Check if it aligns** with the project's goals (decentralized lending on XRPL)
2. **Search existing issues** to see if it's been discussed
3. **Consider the scope** - is it feasible to implement?

When suggesting a feature, include:

- **Clear description** of the feature
- **Use case** - what problem does it solve?
- **Proposed solution** - how would it work?
- **Alternatives considered** - other ways to solve the problem
- **Impact** - how would this benefit users?

### Improving Documentation

Documentation improvements are always welcome! Areas that need help:

- **API documentation** - document FastAPI endpoints
- **User guides** - how to use LendX features
- **Code comments** - explain complex logic
- **Architecture diagrams** - visualize system components
- **Deployment guides** - production deployment instructions

### Contributing Code

Ready to write code? Great! Please:

1. **Start with good first issues** if you're new to the project
2. **Discuss large changes** before implementing (open an issue first)
3. **Follow our development workflow** (see below)
4. **Write tests** for your changes
5. **Update documentation** as needed

## Development Setup

### Prerequisites

Ensure you have the following installed:

- **Node.js**: v18.x or later (v20.x recommended)
- **Python**: 3.9 or later (3.11+ recommended)
- **PostgreSQL**: Managed by Supabase (cloud-hosted)
- **Git**: For version control
- **Code editor**: VS Code recommended with ESLint and Python extensions

### Frontend Setup

The frontend is a Next.js 14 application with TypeScript and Tailwind CSS.

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
# Note: --legacy-peer-deps is required due to React 19 compatibility
npm install --legacy-peer-deps

# Start development server
npm run dev

# Frontend will be available at http://localhost:3000
```

**Frontend Commands:**
```bash
npm run dev      # Start dev server with hot reload
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Backend Setup

The backend is a Python FastAPI application with XRPL integration.

```bash
# Navigate to project root
cd /path/to/calhacks

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies in editable mode
pip install -e .

# Install development dependencies (recommended)
pip install pytest black isort mypy flake8

# Start API server
uvicorn backend.api.main:app --reload

# API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Backend Commands:**
```bash
uvicorn backend.api.main:app --reload  # Start dev server
pytest backend/tests/ -v               # Run tests
black backend/                         # Format code
isort backend/                         # Sort imports
mypy backend/                          # Type checking
flake8 backend/                        # Lint code
```

### Environment Configuration

#### 1. Backend Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
# Supabase (required)
SUPABASE_URL=https://sspwpkhajtooztzisioo.supabase.co
SUPABASE_DB_PASSWORD=your_database_password
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# XUMM Wallet (required for frontend)
NEXT_PUBLIC_XUMM_API_KEY=your_xumm_api_key
NEXT_PUBLIC_XUMM_API_SECRET=your_xumm_api_secret

# Application Settings
ENVIRONMENT=development
JWT_SECRET_KEY=your_secret_key  # Generate with: openssl rand -hex 32
```

**Get Supabase credentials:**
- URL and Keys: https://app.supabase.com/project/_/settings/api
- Database Password: https://app.supabase.com/project/_/settings/database

**Get XUMM credentials:**
- Register at: https://apps.xumm.dev/

#### 2. Frontend Environment Variables

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_XUMM_API_KEY=your_xumm_api_key
NEXT_PUBLIC_XUMM_API_SECRET=your_xumm_api_secret
```

#### 3. Database Setup

The database schema is already applied via migration. To verify connection:

```bash
# Set database password
export SUPABASE_DB_PASSWORD="your_password"

# Run database tests
pytest backend/tests/test_database.py -v
```

## Development Workflow

### Branch Naming Conventions

Use descriptive branch names with the following prefixes:

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `style/` - Code style changes (formatting, no logic change)
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks (dependencies, build config)

**Examples:**
```
feat/mpt-balance-caching
fix/escrow-timeout-handling
docs/contributing-guide
refactor/xrpl-client-error-handling
test/loan-state-transitions
```

### Commit Message Guidelines

Write clear, concise commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) specification.

**Format:**
```
<type>(<scope>): <subject>

<body (optional)>

<footer (optional)>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples:**

```
feat(api): add MPT balance caching endpoint

Implement GET /api/balances/mpt/{address} endpoint that queries
cached balances from user_mpt_balances table before falling back
to on-chain queries. Reduces XRPL API calls by ~80%.

Closes #123
```

```
fix(escrow): handle timeout errors gracefully

Previously, escrow finalization would crash if the hold period
expired. Now catches MaxLedgerExceeded exception and returns
appropriate error response to client.

Fixes #456
```

```
docs: add CONTRIBUTING.md with development guidelines
```

**Commit Message Rules:**

- Use imperative mood ("add feature" not "added feature")
- First line <= 72 characters
- Separate subject from body with blank line
- Reference issue numbers in footer
- Explain *what* and *why*, not *how*

### Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes** following our code style guidelines

3. **Write or update tests** for your changes

4. **Run tests locally** to ensure they pass:
   ```bash
   # Backend
   pytest backend/tests/ -v

   # Frontend (when configured)
   npm test
   ```

5. **Run linters** and fix any issues:
   ```bash
   # Backend
   black backend/
   isort backend/
   flake8 backend/

   # Frontend
   cd frontend && npm run lint
   ```

6. **Commit your changes** with descriptive commit messages

7. **Push to your fork**:
   ```bash
   git push origin feat/your-feature-name
   ```

8. **Open a Pull Request** with:
   - **Clear title** describing the change
   - **Description** explaining what and why
   - **Screenshots** for UI changes
   - **Testing notes** - how to test your changes
   - **Checklist** (see template below)

**Pull Request Template:**

```markdown
## Description
Brief description of what this PR does.

## Motivation
Why is this change needed? What problem does it solve?

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
How to test these changes:
1. Step 1
2. Step 2
3. Expected result

## Screenshots (if applicable)
Add screenshots for UI changes.

## Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow conventions
- [ ] No breaking changes (or documented)
- [ ] Self-review completed
```

9. **Address review feedback** promptly and professionally

10. **Ensure CI passes** before requesting final review

## Code Style Guidelines

### Frontend Standards

The frontend uses TypeScript, React 19, Next.js 14, and Tailwind CSS.

**TypeScript:**
- Use strict mode (enabled in `tsconfig.json`)
- Avoid `any` types - use proper type annotations
- Define interfaces for component props
- Use type inference where obvious

**React Patterns:**
```typescript
// Good: Typed props interface
interface UserProfileProps {
  user: User;
  onEdit: () => void;
}

export function UserProfile({ user, onEdit }: UserProfileProps) {
  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-2xl font-bold">{user.name}</h2>
      <button onClick={onEdit}>Edit Profile</button>
    </div>
  );
}

// Bad: Untyped props
export function UserProfile({ user, onEdit }) {
  // ...
}
```

**Component Structure:**
```
src/components/
  feature-name/
    feature-component.tsx      # Main component
    feature-component.test.tsx # Tests (when configured)
    index.ts                   # Exports
```

**Styling with Tailwind:**
- Use utility classes, not custom CSS
- Follow mobile-first responsive design
- Use design system tokens from `tailwind.config`
- Group utilities logically (layout, spacing, colors, typography)

**ESLint & Prettier:**
```bash
# Run linter
npm run lint

# Auto-fix issues
npm run lint -- --fix
```

**Import Order:**
```typescript
// 1. External dependencies
import React from 'react';
import { useRouter } from 'next/navigation';

// 2. Internal components
import { Button } from '@/components/ui/button';
import { UserProfile } from '@/components/user/user-profile';

// 3. Utils and types
import { formatCurrency } from '@/lib/utils';
import type { User } from '@/types';

// 4. Styles (if any)
import './styles.css';
```

### Backend Standards

The backend uses Python 3.9+, FastAPI, SQLAlchemy, and XRPL integration.

**Code Formatting:**

Use **Black** (line length: 88) and **isort** for consistent formatting:

```bash
# Format code
black backend/

# Sort imports
isort backend/

# Check formatting without changes
black --check backend/
isort --check backend/
```

**Type Hints:**

Use type hints for all function signatures:

```python
# Good: Type hints for parameters and return value
def create_lending_pool(
    issuer_address: str,
    total_balance: Decimal,
    interest_rate: Decimal,
    db: Session
) -> Pool:
    """Create a new lending pool."""
    pool = Pool(
        issuer_address=issuer_address,
        total_balance=total_balance,
        interest_rate=interest_rate
    )
    db.add(pool)
    db.commit()
    return pool

# Bad: No type hints
def create_lending_pool(issuer_address, total_balance, interest_rate, db):
    # ...
```

**Run type checker:**
```bash
mypy backend/
```

**Linting:**

Use **flake8** for linting:

```bash
flake8 backend/

# Configuration in .flake8 or setup.cfg
```

**Docstrings:**

Use Google-style docstrings for all public functions:

```python
def mint_to_holder(
    client: Client,
    mpt_id: str,
    issuer_wallet: Wallet,
    holder_address: str,
    amount: str
) -> str:
    """Mint MPT tokens to a holder address.

    Args:
        client: Connected XRPL client
        mpt_id: MPT ID (hexadecimal string)
        issuer_wallet: Issuer wallet with signing capability
        holder_address: Recipient XRP Ledger address
        amount: Amount to mint (as string to preserve precision)

    Returns:
        Transaction hash (hexadecimal string)

    Raises:
        InsufficientXRP: If issuer doesn't have enough XRP for fees
        PermissionDenied: If issuer doesn't have minting permission
        ConnectionError: If unable to submit transaction
    """
    # Implementation...
```

**Import Order:**
```python
# 1. Standard library
import os
from typing import List, Optional
from decimal import Decimal

# 2. Third-party packages
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from xrpl.clients import JsonRpcClient

# 3. Local imports
from backend.config.database import get_db
from backend.models.database import Pool, Loan
from backend.xrpl_client import create_escrow, submit_and_wait
```

**Error Handling:**

Use custom exceptions and proper error handling:

```python
from backend.xrpl_client.exceptions import wrap_xrpl_exception

@wrap_xrpl_exception
def submit_transaction(client: Client, tx: Transaction) -> str:
    """Submit transaction with automatic error handling."""
    response = submit_and_wait(tx, client)
    return response.result['hash']
```

## Testing Requirements

### Frontend Testing

Frontend testing is **not yet configured**. We welcome contributions to set up testing infrastructure!

**Recommended Setup:**
- **Jest** or **Vitest** for unit/component tests
- **React Testing Library** for component testing
- **Playwright** for E2E tests
- **MSW** for API mocking

**When configured, test coverage should include:**
- Component rendering and interactions
- Form validation
- API integration
- Accessibility (using `@axe-core/react`)
- Responsive behavior (critical flows)

### Backend Testing

Backend uses **pytest** with comprehensive test coverage. Tests are **required** for all new features and bug fixes.

**Running Tests:**

```bash
# Set database password
export SUPABASE_DB_PASSWORD="your_password"

# Run all tests
PYTHONPATH=$(pwd) pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/test_users.py -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

**Test Structure:**

```
backend/tests/
  conftest.py              # Shared fixtures
  test_database.py         # Database connection tests
  test_users.py            # User model tests
  test_pools.py            # Pool model tests
  test_applications.py     # Application model tests
  test_loans.py            # Loan model tests
```

**Writing Tests:**

Use **pytest** with fixtures from `conftest.py`:

```python
def test_create_lending_pool(db_session, create_test_user):
    """Test creating a lending pool."""
    # Arrange
    user = create_test_user("rN7n7otQDd6FczFgLdlqtyMVrn3WnFBBEx")

    # Act
    pool = Pool(
        pool_address="00000A4E5C15B67B6C5F7A2D3E2F4A5B6C7D8E9F",
        issuer_address=user.address,
        total_balance=Decimal("1000.00"),
        current_balance=Decimal("1000.00"),
        minimum_loan=Decimal("10.00"),
        duration_days=30,
        interest_rate=Decimal("5.50")
    )
    db_session.add(pool)
    db_session.commit()

    # Assert
    assert pool.pool_address is not None
    assert pool.total_balance == Decimal("1000.00")
    assert pool.interest_rate == Decimal("5.50")
```

**Test Coverage Requirements:**

- **Minimum coverage**: 80% for new code
- **Critical paths**: 100% coverage (authentication, transactions, escrow)
- **All models**: CRUD operations tested
- **Edge cases**: Error handling, boundary conditions
- **Integration**: API endpoints with database

**Test Naming:**
```python
def test_<function_name>_<scenario>_<expected_result>():
    """Test description."""
    pass

# Examples:
def test_create_user_with_valid_address_succeeds():
    """Test that creating a user with valid address succeeds."""
    pass

def test_create_loan_without_approved_application_fails():
    """Test that creating a loan without approved application raises error."""
    pass
```

## Documentation Standards

Good documentation helps everyone understand and contribute to the project.

**Code Documentation:**

- **Docstrings**: Required for all public functions, classes, and modules
- **Inline comments**: For complex logic or non-obvious decisions
- **Type hints**: For all function parameters and return values

**Project Documentation:**

- **README.md**: Project overview, quick start, features
- **docs/DEVELOPMENT.md**: Technical details for AI assistants and developers
- **CONTRIBUTING.md**: This file - contribution guidelines
- **API documentation**: Auto-generated from FastAPI (available at `/docs`)

**Update documentation when:**

- Adding new features
- Changing API endpoints
- Modifying configuration options
- Updating dependencies
- Changing development workflow

**Documentation Style:**

- Write in clear, concise English
- Use active voice ("Create a pool" not "A pool should be created")
- Include code examples where helpful
- Add links to external resources
- Keep it up-to-date with code changes

## Review Process

All contributions go through code review to maintain quality and consistency.

**Review Timeline:**

- **Initial response**: Within 2 business days
- **Full review**: Within 1 week
- **Follow-up**: Ongoing until merged or closed

**What Reviewers Look For:**

1. **Correctness**: Does the code work as intended?
2. **Tests**: Are there adequate tests? Do they pass?
3. **Style**: Does it follow our code style guidelines?
4. **Documentation**: Is it properly documented?
5. **Performance**: Are there any performance concerns?
6. **Security**: Are there any security vulnerabilities?
7. **Maintainability**: Is the code easy to understand and modify?

**Review Process:**

1. **Automated checks**: CI runs tests and linters
2. **Code review**: Maintainer reviews code and leaves feedback
3. **Discussion**: Contributor and reviewer discuss changes
4. **Revisions**: Contributor makes requested changes
5. **Approval**: Maintainer approves PR
6. **Merge**: PR merged to main branch

**How to Respond to Feedback:**

- Be open to suggestions and criticism
- Ask questions if feedback is unclear
- Make requested changes promptly
- Explain your reasoning if you disagree
- Thank reviewers for their time

**As a Reviewer:**

- Be respectful and constructive
- Focus on the code, not the person
- Explain *why* something should change
- Suggest alternatives when possible
- Approve quickly when appropriate

## Community Guidelines

LendX is built by a welcoming, inclusive community. Here's how we work together:

**Communication Channels:**

- **GitHub Issues**: Bug reports, feature requests, discussions
- **Pull Requests**: Code contributions and reviews
- **Discussions**: General questions and community chat

**Best Practices:**

- **Be patient**: Contributors have different experience levels
- **Be helpful**: Share knowledge and assist others
- **Be professional**: Treat everyone with respect
- **Be collaborative**: Work together towards common goals
- **Be transparent**: Communicate clearly about plans and decisions

**Getting Help:**

- **Technical questions**: Open a GitHub Discussion
- **Bug reports**: Create an issue with details
- **Feature ideas**: Open an issue for discussion first
- **Code questions**: Comment on the relevant PR or file

**Recognition:**

We recognize all contributors:
- Contributors listed in GitHub insights
- Significant contributions acknowledged in release notes
- Community members highlighted in project updates

**Decision Making:**

- **Minor changes**: Reviewed and merged by any maintainer
- **Major changes**: Discussed with core team before implementation
- **Breaking changes**: Require consensus and careful planning

## Thank You!

Thank you for contributing to LendX! Your efforts help build a better decentralized lending platform for everyone. Whether you're fixing a typo or implementing a major feature, every contribution matters.

If you have questions or need help getting started, don't hesitate to reach out. We're here to help!

Happy coding!

---

**Project Links:**
- [Repository](https://github.com/sureenheer/lendx)
- [Documentation](https://github.com/sureenheer/lendx/tree/main/docs)
- [Issue Tracker](https://github.com/sureenheer/lendx/issues)
- [XRPL Documentation](https://xrpl.org/docs.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
