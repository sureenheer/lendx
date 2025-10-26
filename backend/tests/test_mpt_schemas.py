"""
Tests for MPT schema models and JSON serialization.

These tests verify that all MPT schemas:
1. Validate input correctly
2. Serialize to JSON-compatible dictionaries
3. Handle edge cases and validation errors
"""

import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal

from backend.models.mpt_schemas import (
    PoolMPTMetadata,
    ApplicationMPTMetadata,
    LoanMPTMetadata,
    DefaultMPTMetadata,
    ApplicationState,
    LoanState
)


class TestPoolMPTMetadata:
    """Test suite for PoolMPTMetadata schema."""

    def test_valid_pool_creation(self):
        """Test creating a valid pool metadata object."""
        pool = PoolMPTMetadata(
            issuer_addr="rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",
            total_balance=Decimal("10000.0"),
            current_balance=Decimal("10000.0"),
            minimum_loan=Decimal("100.0"),
            duration=30,
            interest_rate=Decimal("5.5")
        )

        assert pool.issuer_addr == "rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x"
        assert pool.total_balance == Decimal("10000.0")
        assert pool.current_balance == Decimal("10000.0")
        assert pool.minimum_loan == Decimal("100.0")
        assert pool.duration == 30
        assert pool.interest_rate == Decimal("5.5")

    def test_pool_json_serialization(self):
        """Test that pool metadata serializes to valid JSON."""
        pool = PoolMPTMetadata(
            issuer_addr="rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",
            total_balance=Decimal("10000.0"),
            current_balance=Decimal("8500.0"),
            minimum_loan=Decimal("100.0"),
            duration=30,
            interest_rate=Decimal("5.5")
        )

        json_dict = pool.to_json_dict()

        # Verify it's JSON-serializable
        json_str = json.dumps(json_dict)
        assert json_str is not None

        # Verify structure
        assert json_dict["issuer_addr"] == "rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x"
        assert json_dict["total_balance"] == 10000.0
        assert json_dict["current_balance"] == 8500.0
        assert json_dict["minimum_loan"] == 100.0
        assert json_dict["duration"] == 30
        assert json_dict["interest_rate"] == 5.5

        # Verify all values are JSON-compatible types
        assert isinstance(json_dict["issuer_addr"], str)
        assert isinstance(json_dict["total_balance"], float)
        assert isinstance(json_dict["current_balance"], float)
        assert isinstance(json_dict["minimum_loan"], float)
        assert isinstance(json_dict["duration"], int)
        assert isinstance(json_dict["interest_rate"], float)

    def test_pool_invalid_address(self):
        """Test that invalid XRP address raises validation error."""
        with pytest.raises(ValueError, match="XRP address must start with 'r'"):
            PoolMPTMetadata(
                issuer_addr="xN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",  # Should start with 'r'
                total_balance=Decimal("10000.0"),
                current_balance=Decimal("10000.0"),
                minimum_loan=Decimal("100.0"),
                duration=30,
                interest_rate=Decimal("5.5")
            )

    def test_pool_invalid_balances(self):
        """Test that total_balance < current_balance raises validation error."""
        with pytest.raises(ValueError, match="total_balance must be >= current_balance"):
            PoolMPTMetadata(
                issuer_addr="rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",
                total_balance=Decimal("5000.0"),
                current_balance=Decimal("10000.0"),  # Current > Total (invalid)
                minimum_loan=Decimal("100.0"),
                duration=30,
                interest_rate=Decimal("5.5")
            )

    def test_pool_negative_values(self):
        """Test that negative values raise validation errors."""
        with pytest.raises(ValueError):
            PoolMPTMetadata(
                issuer_addr="rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",
                total_balance=Decimal("-1000.0"),  # Negative (invalid)
                current_balance=Decimal("10000.0"),
                minimum_loan=Decimal("100.0"),
                duration=30,
                interest_rate=Decimal("5.5")
            )


class TestApplicationMPTMetadata:
    """Test suite for ApplicationMPTMetadata schema."""

    def test_valid_application_creation(self):
        """Test creating a valid application metadata object."""
        now = datetime.now()
        expiry = now + timedelta(days=30)

        app = ApplicationMPTMetadata(
            borrower_addr="rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
            pool_addr="0000000092C5C1F67F6F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F",
            application_date=now,
            dissolution_date=expiry,
            state=ApplicationState.PENDING,
            principal=Decimal("1000.0"),
            interest=Decimal("55.0")
        )

        assert app.borrower_addr == "rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1"
        assert app.state == ApplicationState.PENDING
        assert app.principal == Decimal("1000.0")

    def test_application_json_serialization(self):
        """Test that application metadata serializes to valid JSON."""
        now = datetime.now()
        expiry = now + timedelta(days=30)

        app = ApplicationMPTMetadata(
            borrower_addr="rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
            pool_addr="0000000092C5C1F67F6F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F",
            application_date=now,
            dissolution_date=expiry,
            state=ApplicationState.PENDING,
            principal=Decimal("1000.0"),
            interest=Decimal("55.0")
        )

        json_dict = app.to_json_dict()

        # Verify it's JSON-serializable
        json_str = json.dumps(json_dict)
        assert json_str is not None

        # Verify structure
        assert json_dict["borrower_addr"] == "rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1"
        assert json_dict["state"] == "PENDING"
        assert json_dict["principal"] == 1000.0
        assert json_dict["interest"] == 55.0

        # Verify datetime serialization
        assert isinstance(json_dict["application_date"], str)
        assert isinstance(json_dict["dissolution_date"], str)

    def test_application_invalid_dates(self):
        """Test that dissolution_date <= application_date raises validation error."""
        now = datetime.now()
        past = now - timedelta(days=1)

        with pytest.raises(ValueError, match="dissolution_date must be after application_date"):
            ApplicationMPTMetadata(
                borrower_addr="rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
                pool_addr="0000000092C5C1F67F6F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F",
                application_date=now,
                dissolution_date=past,  # Before application_date (invalid)
                state=ApplicationState.PENDING,
                principal=Decimal("1000.0"),
                interest=Decimal("55.0")
            )


class TestLoanMPTMetadata:
    """Test suite for LoanMPTMetadata schema."""

    def test_valid_loan_creation(self):
        """Test creating a valid loan metadata object."""
        start = datetime.now()
        end = start + timedelta(days=30)

        loan = LoanMPTMetadata(
            pool_addr="0000000092C5C1F67F6F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F",
            borrower_addr="rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
            lender_addr="rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",
            start_date=start,
            end_date=end,
            principal=Decimal("1000.0"),
            interest=Decimal("55.0"),
            state=LoanState.ONGOING
        )

        assert loan.borrower_addr == "rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1"
        assert loan.lender_addr == "rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x"
        assert loan.state == LoanState.ONGOING

    def test_loan_json_serialization(self):
        """Test that loan metadata serializes to valid JSON."""
        start = datetime.now()
        end = start + timedelta(days=30)

        loan = LoanMPTMetadata(
            pool_addr="0000000092C5C1F67F6F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F",
            borrower_addr="rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
            lender_addr="rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",
            start_date=start,
            end_date=end,
            principal=Decimal("1000.0"),
            interest=Decimal("55.0"),
            state=LoanState.ONGOING
        )

        json_dict = loan.to_json_dict()

        # Verify it's JSON-serializable
        json_str = json.dumps(json_dict)
        assert json_str is not None

        # Verify structure
        assert json_dict["state"] == "ONGOING"
        assert json_dict["principal"] == 1000.0
        assert json_dict["interest"] == 55.0

    def test_loan_same_borrower_lender(self):
        """Test that borrower == lender raises validation error."""
        start = datetime.now()
        end = start + timedelta(days=30)

        with pytest.raises(ValueError, match="borrower_addr and lender_addr must be different"):
            LoanMPTMetadata(
                pool_addr="0000000092C5C1F67F6F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F",
                borrower_addr="rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",
                lender_addr="rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",  # Same as borrower (invalid)
                start_date=start,
                end_date=end,
                principal=Decimal("1000.0"),
                interest=Decimal("55.0"),
                state=LoanState.ONGOING
            )

    def test_loan_invalid_dates(self):
        """Test that end_date <= start_date raises validation error."""
        start = datetime.now()
        end = start - timedelta(days=1)

        with pytest.raises(ValueError, match="end_date must be after start_date"):
            LoanMPTMetadata(
                pool_addr="0000000092C5C1F67F6F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F0F",
                borrower_addr="rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
                lender_addr="rN7n7otQDd6FczFgLdlqtyMVrn3HMzve5x",
                start_date=start,
                end_date=end,  # Before start_date (invalid)
                principal=Decimal("1000.0"),
                interest=Decimal("55.0"),
                state=LoanState.ONGOING
            )


class TestDefaultMPTMetadata:
    """Test suite for DefaultMPTMetadata schema."""

    def test_valid_default_creation(self):
        """Test creating a valid default metadata object."""
        default = DefaultMPTMetadata(
            borrower_addr="rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
            default_amount=Decimal("500.0")
        )

        assert default.borrower_addr == "rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1"
        assert default.default_amount == Decimal("500.0")

    def test_default_json_serialization(self):
        """Test that default metadata serializes to valid JSON."""
        default = DefaultMPTMetadata(
            borrower_addr="rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
            default_amount=Decimal("500.0")
        )

        json_dict = default.to_json_dict()

        # Verify it's JSON-serializable
        json_str = json.dumps(json_dict)
        assert json_str is not None

        # Verify structure
        assert json_dict["borrower_addr"] == "rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1"
        assert json_dict["default_amount"] == 500.0

        # Verify types
        assert isinstance(json_dict["borrower_addr"], str)
        assert isinstance(json_dict["default_amount"], float)

    def test_default_negative_amount(self):
        """Test that negative default_amount raises validation error."""
        with pytest.raises(ValueError):
            DefaultMPTMetadata(
                borrower_addr="rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1",
                default_amount=Decimal("-100.0")  # Negative (invalid)
            )


class TestEnums:
    """Test suite for enum types."""

    def test_application_state_values(self):
        """Test ApplicationState enum values."""
        assert ApplicationState.PENDING.value == "PENDING"
        assert ApplicationState.APPROVED.value == "APPROVED"
        assert ApplicationState.REJECTED.value == "REJECTED"
        assert ApplicationState.EXPIRED.value == "EXPIRED"

    def test_loan_state_values(self):
        """Test LoanState enum values."""
        assert LoanState.ONGOING.value == "ONGOING"
        assert LoanState.PAID.value == "PAID"
        assert LoanState.DEFAULTED.value == "DEFAULTED"
