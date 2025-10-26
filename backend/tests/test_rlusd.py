"""
Tests for RLUSD integration functions.

These tests verify RLUSD constants, configuration, and validation logic.
Full integration tests with XRPL mocking would require more complex setup.
"""

import pytest
from decimal import Decimal


class TestRLUSDConstants:
    """Test RLUSD configuration constants"""

    def test_rlusd_issuer_address(self):
        """Test RLUSD issuer address is correctly set"""
        from backend.xrpl_client.rlusd import RLUSD_ISSUER

        # Testnet issuer
        assert RLUSD_ISSUER == "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV"
        assert RLUSD_ISSUER.startswith('r')
        assert len(RLUSD_ISSUER) >= 25

    def test_rlusd_currency_code(self):
        """Test RLUSD currency code is correctly set"""
        from backend.xrpl_client.rlusd import RLUSD_CURRENCY

        assert RLUSD_CURRENCY == "RLUSD"
        assert len(RLUSD_CURRENCY) <= 3 or len(RLUSD_CURRENCY) == 40  # Standard or hex code

    def test_get_rlusd_issuer(self):
        """Test get_rlusd_issuer function"""
        from backend.xrpl_client.rlusd import get_rlusd_issuer

        issuer = get_rlusd_issuer()
        assert issuer == "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV"
        assert issuer.startswith('r')


class TestRLUSDValidation:
    """Test RLUSD amount validation"""

    def test_validate_positive_amount(self):
        """Test validation of positive amounts"""
        from backend.xrpl_client.rlusd import validate_rlusd_amount

        assert validate_rlusd_amount(Decimal("100.50")) is True
        assert validate_rlusd_amount(Decimal("0.01")) is True
        assert validate_rlusd_amount(Decimal("999999.99")) is True

    def test_validate_negative_amount(self):
        """Test validation rejects negative amounts"""
        from backend.xrpl_client.rlusd import validate_rlusd_amount

        assert validate_rlusd_amount(Decimal("-100")) is False
        assert validate_rlusd_amount(Decimal("-0.01")) is False

    def test_validate_zero_amount(self):
        """Test validation rejects zero"""
        from backend.xrpl_client.rlusd import validate_rlusd_amount

        assert validate_rlusd_amount(Decimal("0")) is False
        assert validate_rlusd_amount(Decimal("0.00")) is False

    def test_validate_decimal_precision(self):
        """Test validation of decimal precision"""
        from backend.xrpl_client.rlusd import validate_rlusd_amount

        # Valid precision
        assert validate_rlusd_amount(Decimal("100.123456")) is True

        # Too many decimal places (over XRPL limit of 15 significant digits)
        # This would fail validation
        assert validate_rlusd_amount(Decimal("1.1234567890123456")) is False


class TestRLUSDModuleImports:
    """Test that RLUSD module can be imported and has expected functions"""

    def test_import_rlusd_module(self):
        """Test that rlusd module can be imported"""
        try:
            import backend.xrpl_client.rlusd as rlusd
            assert rlusd is not None
        except ImportError as e:
            pytest.fail(f"Failed to import rlusd module: {e}")

    def test_rlusd_functions_exist(self):
        """Test that expected functions exist in rlusd module"""
        from backend.xrpl_client import rlusd

        assert hasattr(rlusd, 'setup_rlusd_trustline')
        assert hasattr(rlusd, 'get_rlusd_balance')
        assert hasattr(rlusd, 'transfer_rlusd')
        assert hasattr(rlusd, 'check_trustline_exists')
        assert hasattr(rlusd, 'get_rlusd_issuer')
        assert hasattr(rlusd, 'validate_rlusd_amount')

    def test_rlusd_functions_callable(self):
        """Test that RLUSD functions are callable"""
        from backend.xrpl_client import rlusd

        assert callable(rlusd.setup_rlusd_trustline)
        assert callable(rlusd.get_rlusd_balance)
        assert callable(rlusd.transfer_rlusd)
        assert callable(rlusd.check_trustline_exists)
        assert callable(rlusd.get_rlusd_issuer)
        assert callable(rlusd.validate_rlusd_amount)


class TestRLUSDExports:
    """Test that RLUSD functions are properly exported"""

    def test_rlusd_exported_from_xrpl_client(self):
        """Test that RLUSD functions are exported from xrpl_client package"""
        from backend import xrpl_client

        assert hasattr(xrpl_client, 'setup_rlusd_trustline')
        assert hasattr(xrpl_client, 'get_rlusd_balance')
        assert hasattr(xrpl_client, 'transfer_rlusd')
        assert hasattr(xrpl_client, 'check_trustline_exists')
        assert hasattr(xrpl_client, 'RLUSD_ISSUER')
        assert hasattr(xrpl_client, 'RLUSD_CURRENCY')

    def test_rlusd_constants_exported(self):
        """Test that RLUSD constants are exported"""
        from backend.xrpl_client import RLUSD_ISSUER, RLUSD_CURRENCY

        assert RLUSD_ISSUER == "rQhWct2fv4Vc4KRjRgMrxa8xPN9Zx9iLKV"
        assert RLUSD_CURRENCY == "RLUSD"
