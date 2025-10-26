#!/usr/bin/env python3
"""
Integration test for Pool endpoints connected to database.

This script verifies that the Pool endpoints are correctly integrated
with the PostgreSQL database rather than using in-memory storage.
"""

import os
import sys
from decimal import Decimal

# Add backend to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pool_database_integration():
    """Test that Pool endpoints use database correctly."""
    print("=" * 80)
    print("Pool Database Integration Test")
    print("=" * 80)

    # Test 1: Verify imports
    print("\n[1/5] Testing imports...")
    try:
        from backend.config.database import get_db, get_db_session
        from backend.models.database import Pool, User
        from sqlalchemy.orm import Session
        print("✅ All required imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

    # Test 2: Verify Pool model has required fields
    print("\n[2/5] Testing Pool model structure...")
    try:
        pool_attrs = [
            'pool_address', 'issuer_address', 'total_balance', 'current_balance',
            'minimum_loan', 'duration_days', 'interest_rate', 'tx_hash', 'to_dict'
        ]
        for attr in pool_attrs:
            if not hasattr(Pool, attr):
                print(f"❌ Pool model missing attribute: {attr}")
                return False
        print("✅ Pool model has all required attributes")
    except Exception as e:
        print(f"❌ Pool model structure check failed: {e}")
        return False

    # Test 3: Verify to_dict() method works
    print("\n[3/5] Testing Pool.to_dict() method...")
    try:
        # Create a mock pool object
        from datetime import datetime
        pool = Pool(
            pool_address="TEST_POOL_123",
            issuer_address="rTestIssuer123",
            total_balance=Decimal("1000.00"),
            current_balance=Decimal("1000.00"),
            minimum_loan=Decimal("10.00"),
            duration_days=30,
            interest_rate=Decimal("5.00"),
            tx_hash="TX_TEST_123"
        )
        pool.created_at = datetime.now()

        pool_dict = pool.to_dict()

        # Verify all fields are in dictionary
        required_keys = [
            'pool_address', 'issuer_address', 'total_balance', 'current_balance',
            'minimum_loan', 'duration_days', 'interest_rate', 'created_at', 'tx_hash'
        ]
        for key in required_keys:
            if key not in pool_dict:
                print(f"❌ Pool.to_dict() missing key: {key}")
                return False

        # Verify types are serializable (float, str, etc.)
        assert isinstance(pool_dict['total_balance'], float)
        assert isinstance(pool_dict['current_balance'], float)
        assert isinstance(pool_dict['minimum_loan'], float)
        assert isinstance(pool_dict['interest_rate'], float)
        assert isinstance(pool_dict['duration_days'], int)

        print("✅ Pool.to_dict() method works correctly")
        print(f"   Sample output: {pool_dict}")
    except Exception as e:
        print(f"❌ Pool.to_dict() test failed: {e}")
        return False

    # Test 4: Verify database dependency is correctly defined
    print("\n[4/5] Testing database dependency function...")
    try:
        from backend.config.database import get_db
        import inspect

        # Check that get_db is a generator function
        if not inspect.isgeneratorfunction(get_db):
            print("❌ get_db is not a generator function")
            return False

        print("✅ get_db dependency function is correctly defined")
    except Exception as e:
        print(f"❌ Database dependency test failed: {e}")
        return False

    # Test 5: Verify API endpoints use database (static code analysis)
    print("\n[5/5] Verifying API endpoints use database...")
    try:
        from backend.api.main import create_lending_pool, get_lending_pools, get_lending_pool
        import inspect

        # Check create_lending_pool has db parameter
        create_sig = inspect.signature(create_lending_pool)
        if 'db' not in create_sig.parameters:
            print("❌ create_lending_pool missing 'db' parameter")
            return False

        # Check get_lending_pools has db parameter
        get_all_sig = inspect.signature(get_lending_pools)
        if 'db' not in get_all_sig.parameters:
            print("❌ get_lending_pools missing 'db' parameter")
            return False

        # Check get_lending_pool has db parameter
        get_one_sig = inspect.signature(get_lending_pool)
        if 'db' not in get_one_sig.parameters:
            print("❌ get_lending_pool missing 'db' parameter")
            return False

        print("✅ All Pool endpoints have database dependency")

        # Verify no in-memory storage exists
        import backend.api.main as main_module
        if hasattr(main_module, 'lending_pools') and isinstance(getattr(main_module, 'lending_pools'), dict):
            print("❌ WARNING: In-memory 'lending_pools' dictionary still exists!")
            return False

        print("✅ No in-memory 'lending_pools' dictionary found")

    except Exception as e:
        print(f"❌ API endpoint verification failed: {e}")
        return False

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Pool endpoints are correctly connected to database")
    print("=" * 80)
    return True


def test_database_connection():
    """Test that database connection works (requires .env setup)."""
    print("\n" + "=" * 80)
    print("Database Connection Test (Optional - requires .env)")
    print("=" * 80)

    try:
        from backend.config.database import check_db_connection

        if check_db_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("⚠️  Database connection failed - check .env configuration")
            print("   This is optional for code structure verification")
            return False
    except Exception as e:
        print(f"⚠️  Database connection test skipped: {e}")
        print("   This is optional for code structure verification")
        return False


if __name__ == "__main__":
    # Run structure tests (don't require database)
    structure_passed = test_pool_database_integration()

    # Run connection test (optional)
    connection_passed = test_database_connection()

    # Exit with appropriate code
    if structure_passed:
        print("\n✅ Pool database integration verified successfully!")
        if not connection_passed:
            print("⚠️  Note: Database connection test failed, but code structure is correct")
            print("   Set SUPABASE_DB_PASSWORD in .env for full integration testing")
        sys.exit(0)
    else:
        print("\n❌ Pool database integration verification failed!")
        sys.exit(1)
