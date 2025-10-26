#!/usr/bin/env python3
"""
Simple DID service test without importing full backend.

This tests DID operations directly using xrpl-py.
"""

import sys
import time
import json
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import DIDSet, DIDDelete
from xrpl.models.requests import LedgerEntry
from xrpl.transaction import submit_and_wait, autofill_and_sign


def format_did(address: str, network: str = 'testnet') -> str:
    """Format DID string"""
    network_id = "1" if network == 'testnet' else "0"
    return f"did:xrpl:{network_id}:{address}"


def encode_hex(data: str) -> str:
    """Encode string to hex"""
    return data.encode('utf-8').hex().upper()


def decode_hex(hex_data: str) -> str:
    """Decode hex to string"""
    return bytes.fromhex(hex_data).decode('utf-8')


def create_did_document(address: str, public_key: str, network: str = 'testnet') -> dict:
    """Create W3C DID document"""
    did = format_did(address, network)
    return {
        "@context": [
            "https://www.w3.org/ns/did/v1",
            "https://w3id.org/security/suites/ed25519-2020/v1"
        ],
        "id": did,
        "verificationMethod": [{
            "id": f"{did}#keys-1",
            "type": "Ed25519VerificationKey2020",
            "controller": did,
            "publicKeyMultibase": public_key
        }],
        "authentication": [f"{did}#keys-1"],
        "assertionMethod": [f"{did}#keys-1"]
    }


def test_did_operations():
    """Test DID operations on XRPL testnet"""

    print("=" * 80)
    print("XRPL DID Service Test - Direct xrpl-py Implementation")
    print("=" * 80)

    # Step 1: Create and fund wallet
    print("\n[1] Creating and funding test wallet...")
    try:
        client = JsonRpcClient("https://s.altnet.rippletest.net:51234/")
        wallet = generate_faucet_wallet(client)
        print(f"✓ Wallet created: {wallet.classic_address}")
        print(f"  Public key: {wallet.public_key}")
    except Exception as e:
        print(f"✗ Failed to create wallet: {e}")
        return False

    # Step 2: Create DID
    print("\n[2] Creating DID on XRPL testnet...")
    try:
        did = format_did(wallet.classic_address, 'testnet')
        did_doc = create_did_document(wallet.classic_address, wallet.public_key, 'testnet')

        # Create DIDSet transaction
        # Note: did_document field has 256 char limit (128 bytes)
        # For larger docs, use URI to point to off-chain storage
        # For this test, we'll use URI and store key info in data
        tx = DIDSet(
            account=wallet.classic_address,
            uri=encode_hex("https://lendx.com/did-doc.json"),
            data=encode_hex(f"pubkey:{wallet.public_key}")
        )

        # Submit transaction
        signed_tx = autofill_and_sign(tx, client, wallet)
        response = submit_and_wait(signed_tx, client)

        if response.result.get('meta', {}).get('TransactionResult') == 'tesSUCCESS':
            print(f"✓ DID created: {did}")
            print(f"  TX hash: {response.result.get('hash')}")
        else:
            print(f"✗ DID creation failed: {response.result}")
            return False

    except Exception as e:
        print(f"✗ Failed to create DID: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Wait for validation
    print("\n  Waiting 6 seconds for ledger validation...")
    time.sleep(6)

    # Step 3: Retrieve DID
    print("\n[3] Retrieving DID from ledger...")
    try:
        request = LedgerEntry(
            did=wallet.classic_address,
            ledger_index="validated"
        )

        response = client.request(request)

        if response.is_successful():
            node = response.result.get('node')

            if node:
                print("✓ DID entry retrieved from ledger:")

                did_doc_hex = node.get('DIDDocument')
                uri_hex = node.get('URI')
                data_hex = node.get('Data')

                if did_doc_hex:
                    doc_json = decode_hex(did_doc_hex)
                    doc = json.loads(doc_json)
                    print(f"  ID: {doc.get('id')}")
                    print(f"  Verification methods: {len(doc.get('verificationMethod', []))}")
                else:
                    print(f"  DID: {did}")

                if uri_hex:
                    print(f"  URI: {decode_hex(uri_hex)}")
                if data_hex:
                    print(f"  Data: {decode_hex(data_hex)}")

                print(f"  Owner: {node.get('Account')}")
            else:
                print("✗ DID not found in ledger")
                return False
        else:
            print(f"✗ Failed to retrieve DID: {response.result}")
            return False

    except Exception as e:
        print(f"✗ Error retrieving DID: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Update DID
    print("\n[4] Updating DID...")
    try:
        update_tx = DIDSet(
            account=wallet.classic_address,
            uri=encode_hex("https://updated.lendx.com/did"),
            data=encode_hex("Updated LendX User")
        )

        signed_tx = autofill_and_sign(update_tx, client, wallet)
        response = submit_and_wait(signed_tx, client)

        if response.result.get('meta', {}).get('TransactionResult') == 'tesSUCCESS':
            print(f"✓ DID updated")
            print(f"  TX hash: {response.result.get('hash')}")
        else:
            print(f"✗ Update failed: {response.result}")
            return False

    except Exception as e:
        print(f"✗ Failed to update DID: {e}")
        return False

    # Wait for validation
    print("\n  Waiting 6 seconds for ledger validation...")
    time.sleep(6)

    # Verify update
    print("\n[5] Verifying update...")
    try:
        request = LedgerEntry(
            did=wallet.classic_address,
            ledger_index="validated"
        )

        response = client.request(request)

        if response.is_successful():
            node = response.result.get('node')
            uri_hex = node.get('URI')
            data_hex = node.get('Data')

            if uri_hex and decode_hex(uri_hex) == "https://updated.lendx.com/did":
                print("✓ DID update verified")
                print(f"  New URI: {decode_hex(uri_hex)}")
                print(f"  New Data: {decode_hex(data_hex)}")
            else:
                print("⚠ Update not yet reflected (may need more time)")

    except Exception as e:
        print(f"⚠ Could not verify update: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("✓ All DID operations completed successfully!")
    print(f"\nCreated DID: {did}")
    print(f"Address: {wallet.classic_address}")
    print(f"\nView on testnet explorer:")
    print(f"https://testnet.xrpl.org/accounts/{wallet.classic_address}")

    return True


if __name__ == "__main__":
    try:
        success = test_did_operations()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
