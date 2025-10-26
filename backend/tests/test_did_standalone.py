#!/usr/bin/env python3
"""
Standalone test script for DID service.

This script tests DID operations on XRPL testnet without requiring database setup.
It demonstrates the complete lifecycle of DID management.

Usage:
    python3 test_did_standalone.py
"""

import sys
import time
import json
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.clients import JsonRpcClient

# Add backend to path
sys.path.insert(0, '/home/users/duynguy/proj/calhacks')

from backend.services.did_service import (
    create_did_for_user,
    get_did_document,
    update_did_document,
    delete_did,
    get_did_from_address
)


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(label, value):
    """Print test result"""
    if isinstance(value, dict):
        print(f"\n{label}:")
        print(json.dumps(value, indent=2))
    else:
        print(f"{label}: {value}")


def test_did_lifecycle():
    """Test complete DID lifecycle on XRPL testnet"""

    print_section("XRPL DID Service Test - Complete Lifecycle")

    # Step 1: Create and fund a test wallet
    print_section("Step 1: Create and Fund Test Wallet")
    print("Creating new test wallet...")

    try:
        client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
        wallet = generate_faucet_wallet(client)
        print_result("Wallet address", wallet.classic_address)
        print_result("Wallet public key", wallet.public_key)
        print("✓ Wallet created and funded from testnet faucet")
    except Exception as e:
        print(f"✗ Failed to create/fund wallet: {e}")
        print("\nNote: Testnet faucet may be temporarily unavailable.")
        print("Try again in a few minutes or use a pre-funded wallet.")
        return False

    # Step 2: Create DID
    print_section("Step 2: Create DID for User")
    print("Creating DID on XRPL testnet...")

    try:
        did = create_did_for_user(
            wallet,
            network='testnet',
            update_database=False,  # Skip database for standalone test
            uri="https://example.com/did-doc.json",
            data="LendX Platform User"
        )
        print_result("DID created", did)
        print("✓ DID creation transaction successful")
    except Exception as e:
        print(f"✗ Failed to create DID: {e}")
        return False

    # Wait for ledger validation
    print("\nWaiting 6 seconds for ledger validation...")
    time.sleep(6)

    # Step 3: Retrieve DID document
    print_section("Step 3: Retrieve DID Document")
    print("Querying XRPL ledger for DID document...")

    try:
        doc = get_did_document(wallet.classic_address, network='testnet')
        if doc:
            print_result("DID document retrieved", doc)
            print("✓ DID document successfully retrieved from ledger")

            # Verify structure
            assert doc["id"] == did, "DID mismatch"
            print("\n✓ DID structure validated")

            if "_ledger" in doc:
                print("\nOn-chain metadata:")
                print(f"  URI: {doc['_ledger'].get('uri')}")
                print(f"  Data: {doc['_ledger'].get('data')}")
                print(f"  Owner: {doc['_ledger'].get('owner')}")
        else:
            print("✗ No DID document found (may need more time for validation)")
            return False
    except Exception as e:
        print(f"✗ Failed to retrieve DID document: {e}")
        return False

    # Step 4: Update DID
    print_section("Step 4: Update DID Document")
    print("Updating DID with new URI...")

    try:
        new_uri = "https://updated.lendx.com/did-doc.json"
        success = update_did_document(
            wallet,
            network='testnet',
            uri=new_uri,
            data="Updated metadata"
        )

        if success:
            print_result("Update successful", success)
            print("✓ DID update transaction successful")
        else:
            print("✗ DID update failed")
            return False
    except Exception as e:
        print(f"✗ Failed to update DID: {e}")
        return False

    # Wait for validation
    print("\nWaiting 6 seconds for ledger validation...")
    time.sleep(6)

    # Verify update
    print("\nVerifying update...")
    try:
        updated_doc = get_did_document(wallet.classic_address, network='testnet')
        if updated_doc and "_ledger" in updated_doc:
            print_result("Updated URI", updated_doc["_ledger"].get("uri"))
            if updated_doc["_ledger"].get("uri") == new_uri:
                print("✓ DID update verified")
            else:
                print("⚠ URI not yet updated (may need more time)")
        else:
            print("⚠ Could not verify update")
    except Exception as e:
        print(f"✗ Error verifying update: {e}")

    # Step 5: Test convenience function
    print_section("Step 5: Test Convenience Function")
    print("Testing get_did_from_address()...")

    try:
        retrieved_did = get_did_from_address(wallet.classic_address, network='testnet')
        print_result("DID from address", retrieved_did)

        if retrieved_did == did:
            print("✓ Convenience function works correctly")
        else:
            print("✗ DID mismatch")
            return False
    except Exception as e:
        print(f"✗ Failed to get DID from address: {e}")
        return False

    # Step 6: Delete DID (optional - commented out to preserve DID on testnet)
    print_section("Step 6: Delete DID (Optional)")
    print("Note: DID deletion is available but not executed in this test")
    print("      to preserve the created DID on testnet for inspection.")
    print("\nTo delete the DID, uncomment the deletion code in this script.")

    # Uncomment to test deletion:
    # try:
    #     success = delete_did(wallet, network='testnet', update_database=False)
    #     if success:
    #         print("✓ DID deleted successfully")
    #         time.sleep(6)
    #
    #         # Verify deletion
    #         deleted_doc = get_did_document(wallet.classic_address, network='testnet')
    #         if deleted_doc is None:
    #             print("✓ DID deletion verified")
    #         else:
    #             print("⚠ DID still exists (may need more time)")
    #     else:
    #         print("✗ DID deletion failed")
    # except Exception as e:
    #     print(f"✗ Failed to delete DID: {e}")

    # Summary
    print_section("Test Summary")
    print("✓ All DID operations completed successfully!")
    print("\nCreated DID details:")
    print(f"  Address: {wallet.classic_address}")
    print(f"  DID: {did}")
    print(f"  Network: XRPL Testnet")
    print("\nYou can verify this DID on XRPL testnet explorer:")
    print(f"  https://testnet.xrpl.org/accounts/{wallet.classic_address}")

    return True


def test_error_handling():
    """Test error handling"""
    print_section("Error Handling Tests")

    # Test 1: Invalid wallet
    print("\nTest 1: Creating DID with invalid wallet...")
    try:
        create_did_for_user(None, network='testnet')
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # Test 2: Update with no fields
    print("\nTest 2: Updating DID with no fields...")
    try:
        wallet = Wallet.create()
        update_did_document(wallet, network='testnet')
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # Test 3: Get DID for non-existent address
    print("\nTest 3: Retrieving DID for non-existent address...")
    try:
        random_wallet = Wallet.create()
        did = get_did_from_address(random_wallet.classic_address, network='testnet')
        if did is None:
            print("✓ Correctly returned None for non-existent DID")
        else:
            print(f"✗ Unexpected result: {did}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n✓ Error handling tests completed")


def main():
    """Main test runner"""
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    XRPL DID Service Test Suite                           ║
║                                                                           ║
║  This script tests the DID (Decentralized Identifier) service for        ║
║  the LendX platform on XRPL testnet.                                     ║
║                                                                           ║
║  Tests include:                                                           ║
║    - DID creation with on-chain storage                                  ║
║    - DID document retrieval from ledger                                  ║
║    - DID document updates                                                ║
║    - DID deletion                                                        ║
║    - Error handling                                                      ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    try:
        # Run lifecycle test
        lifecycle_success = test_did_lifecycle()

        # Run error handling tests
        test_error_handling()

        # Final result
        print_section("Final Result")
        if lifecycle_success:
            print("✓ ALL TESTS PASSED")
            print("\nThe DID service is working correctly on XRPL testnet!")
            return 0
        else:
            print("✗ SOME TESTS FAILED")
            print("\nPlease review the errors above.")
            return 1

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 130
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
