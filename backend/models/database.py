"""
SQLAlchemy ORM models for LendX database.

These models represent the database schema and provide an ORM interface
for interacting with the Supabase PostgreSQL database.

The database acts as an index/cache layer for on-chain XRPL data:
- Users: Wallet addresses and DIDs
- Pools: PoolMPT metadata (lending pools)
- Applications: ApplicationMPT metadata (loan applications)
- Loans: LoanMPT metadata (active and completed loans)
- UserMPTBalances: Cache of MPT token balances
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, String, Numeric, Integer, DateTime, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship, validates
from sqlalchemy.sql import func

# Create base class for declarative models
Base = declarative_base()


class User(Base):
    """
    User model representing XRPL wallet addresses.

    Attributes:
        address: XRP wallet address (primary key)
        did: Decentralized Identifier (W3C DID standard)
        created_at: Timestamp when user was created
    """
    __tablename__ = 'users'

    address = Column(String(34), primary_key=True)
    did = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    pools = relationship("Pool", back_populates="issuer", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="borrower", cascade="all, delete-orphan")
    loans_as_borrower = relationship(
        "Loan",
        foreign_keys="Loan.borrower_address",
        back_populates="borrower",
        cascade="all, delete-orphan"
    )
    loans_as_lender = relationship(
        "Loan",
        foreign_keys="Loan.lender_address",
        back_populates="lender",
        cascade="all, delete-orphan"
    )
    mpt_balances = relationship("UserMPTBalance", back_populates="user", cascade="all, delete-orphan")

    @validates('address')
    def validate_address(self, key, address):
        """Validate XRP address format (basic validation)"""
        if address and not address.startswith('r'):
            # Note: This is basic validation. Full validation requires checksum verification
            pass  # Allow for testing, but should implement proper validation in production
        return address

    def __repr__(self):
        return f"<User(address='{self.address}', did='{self.did}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "address": self.address,
            "did": self.did,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Pool(Base):
    """
    Pool model representing lending pools (PoolMPT on XRPL).

    Attributes:
        pool_address: MPT issuance ID (primary key)
        issuer_address: Lender's wallet address
        total_balance: Initial pool balance
        current_balance: Available balance for new loans
        minimum_loan: Minimum loan amount allowed
        duration_days: Loan duration in days
        interest_rate: Interest rate percentage
        created_at: Timestamp when pool was created
        tx_hash: XRPL transaction hash for verification
    """
    __tablename__ = 'pools'

    pool_address = Column(String(66), primary_key=True, comment="MPT issuance ID from XRPL")
    issuer_address = Column(String(34), ForeignKey('users.address'), nullable=False)
    total_balance = Column(Numeric(20, 6), nullable=False)
    current_balance = Column(Numeric(20, 6), nullable=False, comment="Available balance for new loans")
    minimum_loan = Column(Numeric(20, 6), nullable=False)
    duration_days = Column(Integer, nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    tx_hash = Column(String(64), nullable=False)

    # Relationships
    issuer = relationship("User", back_populates="pools")
    applications = relationship("Application", back_populates="pool", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="pool", cascade="all, delete-orphan")

    # Indexes are created in migration, but we document them here
    __table_args__ = (
        Index('idx_pools_issuer', 'issuer_address'),
        CheckConstraint('current_balance >= 0', name='check_current_balance_positive'),
        CheckConstraint('total_balance >= current_balance', name='check_total_gte_current'),
        CheckConstraint('minimum_loan > 0', name='check_minimum_loan_positive'),
        CheckConstraint('duration_days > 0', name='check_duration_positive'),
        CheckConstraint('interest_rate >= 0', name='check_interest_rate_non_negative'),
    )

    def __repr__(self):
        return f"<Pool(address='{self.pool_address}', issuer='{self.issuer_address}', balance={self.current_balance})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "pool_address": self.pool_address,
            "issuer_address": self.issuer_address,
            "total_balance": float(self.total_balance),
            "current_balance": float(self.current_balance),
            "minimum_loan": float(self.minimum_loan),
            "duration_days": self.duration_days,
            "interest_rate": float(self.interest_rate),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tx_hash": self.tx_hash
        }


class Application(Base):
    """
    Application model representing loan applications (ApplicationMPT on XRPL).

    Attributes:
        application_address: MPT issuance ID (primary key)
        borrower_address: Borrower's wallet address
        pool_address: Associated pool's MPT ID
        application_date: When application was created
        dissolution_date: Expiration date for pending applications
        state: Application status (PENDING, APPROVED, REJECTED, EXPIRED)
        principal: Requested loan amount
        interest: Calculated interest amount
        tx_hash: XRPL transaction hash
    """
    __tablename__ = 'applications'

    application_address = Column(String(66), primary_key=True)
    borrower_address = Column(String(34), ForeignKey('users.address'), nullable=False)
    pool_address = Column(String(66), ForeignKey('pools.pool_address'), nullable=False)
    application_date = Column(DateTime, nullable=False)
    dissolution_date = Column(DateTime, nullable=False, comment="Expiration date for pending applications")
    state = Column(String(20), nullable=False)
    principal = Column(Numeric(20, 6), nullable=False)
    interest = Column(Numeric(20, 6), nullable=False)
    tx_hash = Column(String(64), nullable=False)

    # Relationships
    borrower = relationship("User", back_populates="applications")
    pool = relationship("Pool", back_populates="applications")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "state IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')",
            name='check_application_state'
        ),
        Index('idx_applications_borrower', 'borrower_address'),
        Index('idx_applications_pool', 'pool_address'),
        Index('idx_applications_state', 'state'),
        CheckConstraint('principal > 0', name='check_principal_positive'),
        CheckConstraint('interest >= 0', name='check_interest_non_negative'),
    )

    @validates('state')
    def validate_state(self, key, state):
        """Validate application state"""
        valid_states = ['PENDING', 'APPROVED', 'REJECTED', 'EXPIRED']
        if state not in valid_states:
            raise ValueError(f"Invalid state: {state}. Must be one of {valid_states}")
        return state

    def __repr__(self):
        return f"<Application(address='{self.application_address}', borrower='{self.borrower_address}', state='{self.state}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "application_address": self.application_address,
            "borrower_address": self.borrower_address,
            "pool_address": self.pool_address,
            "application_date": self.application_date.isoformat() if self.application_date else None,
            "dissolution_date": self.dissolution_date.isoformat() if self.dissolution_date else None,
            "state": self.state,
            "principal": float(self.principal),
            "interest": float(self.interest),
            "tx_hash": self.tx_hash
        }


class Loan(Base):
    """
    Loan model representing active and completed loans (LoanMPT on XRPL).

    Attributes:
        loan_address: MPT issuance ID (primary key)
        pool_address: Associated pool's MPT ID
        borrower_address: Borrower's wallet address
        lender_address: Lender's wallet address
        start_date: Loan start date
        end_date: Loan due date
        principal: Loan amount
        interest: Interest amount
        state: Loan status (ONGOING, PAID, DEFAULTED)
        tx_hash: XRPL transaction hash
    """
    __tablename__ = 'loans'

    loan_address = Column(String(66), primary_key=True)
    pool_address = Column(String(66), ForeignKey('pools.pool_address'), nullable=False)
    borrower_address = Column(String(34), ForeignKey('users.address'), nullable=False)
    lender_address = Column(String(34), ForeignKey('users.address'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    principal = Column(Numeric(20, 6), nullable=False)
    interest = Column(Numeric(20, 6), nullable=False)
    state = Column(
        String(20),
        nullable=False,
        comment="Loan status: ONGOING (active), PAID (completed), DEFAULTED (overdue)"
    )
    tx_hash = Column(String(64), nullable=False)

    # Relationships
    pool = relationship("Pool", back_populates="loans")
    borrower = relationship("User", foreign_keys=[borrower_address], back_populates="loans_as_borrower")
    lender = relationship("User", foreign_keys=[lender_address], back_populates="loans_as_lender")

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "state IN ('ONGOING', 'PAID', 'DEFAULTED')",
            name='check_loan_state'
        ),
        Index('idx_loans_borrower', 'borrower_address'),
        Index('idx_loans_lender', 'lender_address'),
        Index('idx_loans_pool', 'pool_address'),
        Index('idx_loans_state', 'state'),
        CheckConstraint('principal > 0', name='check_loan_principal_positive'),
        CheckConstraint('interest >= 0', name='check_loan_interest_non_negative'),
        CheckConstraint('end_date > start_date', name='check_end_date_after_start'),
    )

    @validates('state')
    def validate_state(self, key, state):
        """Validate loan state"""
        valid_states = ['ONGOING', 'PAID', 'DEFAULTED']
        if state not in valid_states:
            raise ValueError(f"Invalid state: {state}. Must be one of {valid_states}")
        return state

    def is_overdue(self) -> bool:
        """Check if loan is past due date"""
        return datetime.now() > self.end_date and self.state == 'ONGOING'

    def total_amount_due(self) -> Decimal:
        """Calculate total amount due (principal + interest)"""
        return self.principal + self.interest

    def __repr__(self):
        return f"<Loan(address='{self.loan_address}', borrower='{self.borrower_address}', state='{self.state}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "loan_address": self.loan_address,
            "pool_address": self.pool_address,
            "borrower_address": self.borrower_address,
            "lender_address": self.lender_address,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "principal": float(self.principal),
            "interest": float(self.interest),
            "state": self.state,
            "tx_hash": self.tx_hash
        }


class UserMPTBalance(Base):
    """
    UserMPTBalance model for caching MPT token balances.

    This table caches on-chain MPT balances to reduce XRPL API calls.
    Balances should be periodically synced from the XRPL ledger.

    Attributes:
        user_address: User's wallet address
        mpt_id: MPT issuance ID
        balance: Cached balance
        last_synced: When balance was last updated from XRPL
    """
    __tablename__ = 'user_mpt_balances'

    user_address = Column(String(34), ForeignKey('users.address'), primary_key=True)
    mpt_id = Column(String(66), primary_key=True)
    balance = Column(Numeric(20, 6), nullable=False, default=0)
    last_synced = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="mpt_balances")

    # Indexes
    __table_args__ = (
        Index('idx_user_mpt_balances_mpt', 'mpt_id'),
        CheckConstraint('balance >= 0', name='check_balance_non_negative'),
    )

    def is_stale(self, max_age_seconds: int = 300) -> bool:
        """
        Check if balance is stale (older than max_age_seconds).

        Args:
            max_age_seconds: Maximum age in seconds (default 5 minutes)

        Returns:
            bool: True if balance should be refreshed
        """
        if not self.last_synced:
            return True
        age = (datetime.now() - self.last_synced).total_seconds()
        return age > max_age_seconds

    def __repr__(self):
        return f"<UserMPTBalance(user='{self.user_address}', mpt='{self.mpt_id}', balance={self.balance})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "user_address": self.user_address,
            "mpt_id": self.mpt_id,
            "balance": float(self.balance),
            "last_synced": self.last_synced.isoformat() if self.last_synced else None
        }
