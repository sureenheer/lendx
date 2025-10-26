"""
Pydantic models for MPT (Multi-Purpose Token) metadata schemas.

These schemas define the structure of metadata stored in XRPL MPT tokens.
MPT metadata is immutable after creation, so mutable state (like application/loan status)
is tracked in the database with transaction memos for updates.

The 4 MPT types represent the core data layer of LendX:
1. PoolMPT: Lending pool configurations
2. ApplicationMPT: Loan application records
3. LoanMPT: Active and completed loan records
4. DefaultMPT: Borrower default tracking (global, system-owned)
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ApplicationState(str, Enum):
    """Application status enum."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class LoanState(str, Enum):
    """Loan status enum."""
    ONGOING = "ONGOING"
    PAID = "PAID"
    DEFAULTED = "DEFAULTED"


class PoolMPTMetadata(BaseModel):
    """
    Metadata for PoolMPT tokens representing lending pools.

    Attributes:
        issuer_addr: Lender's XRP wallet address
        total_balance: Initial pool balance in XRP
        current_balance: Available balance for new loans in XRP
        minimum_loan: Minimum loan amount allowed in XRP
        duration: Loan duration in days
        interest_rate: Interest rate as percentage (e.g., 5.5 for 5.5%)
    """
    issuer_addr: str = Field(..., min_length=25, max_length=35, description="Lender's XRP address")
    total_balance: Decimal = Field(..., gt=0, description="Initial pool balance")
    current_balance: Decimal = Field(..., ge=0, description="Available balance for loans")
    minimum_loan: Decimal = Field(..., gt=0, description="Minimum loan amount")
    duration: int = Field(..., gt=0, description="Loan duration in days")
    interest_rate: Decimal = Field(..., ge=0, le=100, description="Interest rate percentage")

    @field_validator('issuer_addr')
    @classmethod
    def validate_xrp_address(cls, v: str) -> str:
        """Validate XRP address format."""
        if not v.startswith('r'):
            raise ValueError("XRP address must start with 'r'")
        if len(v) < 25 or len(v) > 35:
            raise ValueError("XRP address must be between 25-35 characters")
        return v

    @model_validator(mode='after')
    def validate_balances(self):
        """Validate that total_balance >= current_balance."""
        if self.total_balance < self.current_balance:
            raise ValueError("total_balance must be >= current_balance")
        return self

    def to_json_dict(self) -> dict:
        """
        Convert to JSON-serializable dictionary for XRPL metadata.
        Decimal values are converted to float for JSON compatibility.
        """
        return {
            "issuer_addr": self.issuer_addr,
            "total_balance": float(self.total_balance),
            "current_balance": float(self.current_balance),
            "minimum_loan": float(self.minimum_loan),
            "duration": self.duration,
            "interest_rate": float(self.interest_rate)
        }

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "issuer_addr": "rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",
                "total_balance": "10000.0",
                "current_balance": "10000.0",
                "minimum_loan": "100.0",
                "duration": 30,
                "interest_rate": "5.5"
            }
        }


class ApplicationMPTMetadata(BaseModel):
    """
    Metadata for ApplicationMPT tokens representing loan applications.

    Attributes:
        borrower_addr: Borrower's XRP wallet address
        pool_addr: Associated pool's MPT issuance ID
        application_date: When application was created
        dissolution_date: Expiration date for pending applications
        state: Application status (PENDING/APPROVED/REJECTED/EXPIRED)
        principal: Requested loan amount in XRP
        interest: Calculated interest amount in XRP
    """
    borrower_addr: str = Field(..., min_length=25, max_length=35, description="Borrower's XRP address")
    pool_addr: str = Field(..., min_length=64, max_length=68, description="Pool MPT issuance ID")
    application_date: datetime = Field(..., description="Application creation timestamp")
    dissolution_date: datetime = Field(..., description="Application expiration timestamp")
    state: ApplicationState = Field(..., description="Application status")
    principal: Decimal = Field(..., gt=0, description="Requested loan amount")
    interest: Decimal = Field(..., ge=0, description="Calculated interest amount")

    @field_validator('borrower_addr')
    @classmethod
    def validate_borrower_address(cls, v: str) -> str:
        """Validate borrower XRP address format."""
        if not v.startswith('r'):
            raise ValueError("XRP address must start with 'r'")
        if len(v) < 25 or len(v) > 35:
            raise ValueError("XRP address must be between 25-35 characters")
        return v

    @field_validator('pool_addr')
    @classmethod
    def validate_pool_address(cls, v: str) -> str:
        """Validate pool MPT ID format (64 hex chars)."""
        if len(v) < 64 or len(v) > 68:
            raise ValueError("Pool address must be 64-68 characters (MPT issuance ID)")
        return v

    @model_validator(mode='after')
    def validate_dates(self):
        """Validate that dissolution_date is after application_date."""
        if self.dissolution_date <= self.application_date:
            raise ValueError("dissolution_date must be after application_date")
        return self

    def to_json_dict(self) -> dict:
        """
        Convert to JSON-serializable dictionary for XRPL metadata.
        Datetime and Decimal values are converted for JSON compatibility.
        """
        return {
            "borrower_addr": self.borrower_addr,
            "pool_addr": self.pool_addr,
            "application_date": self.application_date.isoformat(),
            "dissolution_date": self.dissolution_date.isoformat(),
            "state": self.state.value,
            "principal": float(self.principal),
            "interest": float(self.interest)
        }

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "borrower_addr": "rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
                "pool_addr": "0000000092C5C1F67F6F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F",
                "application_date": "2025-10-26T00:00:00Z",
                "dissolution_date": "2025-11-26T00:00:00Z",
                "state": "PENDING",
                "principal": "1000.0",
                "interest": "55.0"
            }
        }


class LoanMPTMetadata(BaseModel):
    """
    Metadata for LoanMPT tokens representing active and completed loans.

    Attributes:
        pool_addr: Associated pool's MPT issuance ID
        borrower_addr: Borrower's XRP wallet address
        lender_addr: Lender's XRP wallet address
        start_date: Loan start date
        end_date: Loan due date
        principal: Loan amount in XRP
        interest: Interest amount in XRP
        state: Loan status (ONGOING/PAID/DEFAULTED)
    """
    pool_addr: str = Field(..., min_length=64, max_length=68, description="Pool MPT issuance ID")
    borrower_addr: str = Field(..., min_length=25, max_length=35, description="Borrower's XRP address")
    lender_addr: str = Field(..., min_length=25, max_length=35, description="Lender's XRP address")
    start_date: datetime = Field(..., description="Loan start timestamp")
    end_date: datetime = Field(..., description="Loan due timestamp")
    principal: Decimal = Field(..., gt=0, description="Loan principal amount")
    interest: Decimal = Field(..., ge=0, description="Interest amount")
    state: LoanState = Field(..., description="Loan status")

    @field_validator('borrower_addr', 'lender_addr')
    @classmethod
    def validate_xrp_address(cls, v: str) -> str:
        """Validate XRP address format."""
        if not v.startswith('r'):
            raise ValueError("XRP address must start with 'r'")
        if len(v) < 25 or len(v) > 35:
            raise ValueError("XRP address must be between 25-35 characters")
        return v

    @field_validator('pool_addr')
    @classmethod
    def validate_pool_address(cls, v: str) -> str:
        """Validate pool MPT ID format."""
        if len(v) < 64 or len(v) > 68:
            raise ValueError("Pool address must be 64-68 characters (MPT issuance ID)")
        return v

    @model_validator(mode='after')
    def validate_dates(self):
        """Validate that end_date is after start_date."""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

    @model_validator(mode='after')
    def validate_parties(self):
        """Validate that borrower and lender are different addresses."""
        if self.borrower_addr == self.lender_addr:
            raise ValueError("borrower_addr and lender_addr must be different")
        return self

    def to_json_dict(self) -> dict:
        """
        Convert to JSON-serializable dictionary for XRPL metadata.
        Datetime and Decimal values are converted for JSON compatibility.
        """
        return {
            "pool_addr": self.pool_addr,
            "borrower_addr": self.borrower_addr,
            "lender_addr": self.lender_addr,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "principal": float(self.principal),
            "interest": float(self.interest),
            "state": self.state.value
        }

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "pool_addr": "0000000092C5C1F67F6F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F",
                "borrower_addr": "rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
                "lender_addr": "rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",
                "start_date": "2025-10-26T00:00:00Z",
                "end_date": "2025-11-25T00:00:00Z",
                "principal": "1000.0",
                "interest": "55.0",
                "state": "ONGOING"
            }
        }


class DefaultMPTMetadata(BaseModel):
    """
    Metadata for DefaultMPT tokens tracking borrower defaults.

    This is a global, system-owned MPT where each borrower's default amount
    is tracked as their token balance. Higher balance = more defaults.

    Attributes:
        borrower_addr: Borrower's XRP wallet address
        default_amount: Total default amount in XRP
    """
    borrower_addr: str = Field(..., min_length=25, max_length=35, description="Borrower's XRP address")
    default_amount: Decimal = Field(..., ge=0, description="Total default amount")

    @field_validator('borrower_addr')
    @classmethod
    def validate_xrp_address(cls, v: str) -> str:
        """Validate XRP address format."""
        if not v.startswith('r'):
            raise ValueError("XRP address must start with 'r'")
        if len(v) < 25 or len(v) > 35:
            raise ValueError("XRP address must be between 25-35 characters")
        return v

    def to_json_dict(self) -> dict:
        """
        Convert to JSON-serializable dictionary for XRPL metadata.
        Decimal values are converted to float for JSON compatibility.
        """
        return {
            "borrower_addr": self.borrower_addr,
            "default_amount": float(self.default_amount)
        }

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "borrower_addr": "rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
                "default_amount": "500.0"
            }
        }
