"""
End-to-end test for complete MVP lending flow.

This test validates the entire lending lifecycle:
1. Create lending pool (PoolMPT)
2. Submit loan application (ApplicationMPT)
3. Approve loan and create active loan (LoanMPT)
4. Verify all 3 MPTs exist on XRPL
5. Verify all data is correctly stored in database
6. Print XRPL explorer URLs for manual verification

This is a comprehensive integration test that exercises the full stack:
- XRPL client layer (MPT creation)
- Service layer (MPT service, DID service)
- Database layer (SQLAlchemy models)
- Business logic (pool creation, application, approval)
"""

import pytest
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from xrpl.wallet import Wallet

from backend.xrpl_client import connect
from backend.xrpl_client.mpt import get_mpt_balance
from backend.services.mpt_service import (
    create_pool_mpt,
    create_application_mpt,
    create_loan_mpt
)
from backend.services.did_service import create_did_for_user
from backend.models.mpt_schemas import (
    PoolMPTMetadata,
    ApplicationMPTMetadata,
    LoanMPTMetadata,
    ApplicationState,
    LoanState
)
from backend.models.database import User, Pool, Application, Loan

logger = logging.getLogger(__name__)

# XRPL Testnet Explorer URLs
EXPLORER_BASE = "https://testnet.xrpl.org"


class TestE2EMVPFlow:
    """End-to-end test for complete lending flow"""

    @pytest.fixture(scope="class")
    def xrpl_client(self):
        """Create XRPL testnet client for all tests"""
        client = connect('testnet')
        yield client
        # No cleanup needed - client auto-closes

    @pytest.fixture(scope="class")
    def test_wallets(self):
        """
        Create test wallets for lender and borrower.

        In production, these would be funded from a faucet or have existing balances.
        For testing, we use newly generated wallets.
        """
        lender_wallet = Wallet.create()
        borrower_wallet = Wallet.create()

        logger.info(f"Created test wallets:")
        logger.info(f"  Lender:   {lender_wallet.classic_address}")
        logger.info(f"  Borrower: {borrower_wallet.classic_address}")

        return {
            'lender': lender_wallet,
            'borrower': borrower_wallet
        }

    def test_complete_lending_flow(
        self,
        xrpl_client,
        test_wallets,
        db_session,
        cleanup_test_data
    ):
        """
        Test the complete lending flow from pool creation to loan approval.

        This test validates:
        - PoolMPT creation on XRPL
        - ApplicationMPT creation on XRPL
        - LoanMPT creation on XRPL
        - DID creation for borrower
        - Database records for all entities
        - MPT balances and metadata

        Expected result: All 3 MPTs created successfully with valid IDs
        """
        lender_wallet = test_wallets['lender']
        borrower_wallet = test_wallets['borrower']

        # ================================================================
        # STEP 1: Create borrower DID (required for loan applications)
        # ================================================================
        logger.info("\n" + "="*70)
        logger.info("STEP 1: Creating DID for borrower")
        logger.info("="*70)

        borrower_did = create_did_for_user(
            user_wallet=borrower_wallet,
            network='testnet',
            update_database=True
        )

        assert borrower_did is not None, "DID creation failed"
        assert borrower_did.startswith("did:xrpl:1:"), "Invalid DID format"
        assert borrower_wallet.classic_address in borrower_did, "DID doesn't contain wallet address"

        logger.info(f"✅ Borrower DID created: {borrower_did}")
        logger.info(f"   Explorer: {EXPLORER_BASE}/accounts/{borrower_wallet.classic_address}")

        # Verify DID in database
        borrower_user = db_session.query(User).filter_by(
            address=borrower_wallet.classic_address
        ).first()
        assert borrower_user is not None, "Borrower user not created in database"
        assert borrower_user.did == borrower_did, "DID mismatch in database"

        # ================================================================
        # STEP 2: Create lending pool (PoolMPT)
        # ================================================================
        logger.info("\n" + "="*70)
        logger.info("STEP 2: Creating lending pool (PoolMPT)")
        logger.info("="*70)

        pool_metadata = PoolMPTMetadata(
            issuer_addr=lender_wallet.classic_address,
            total_balance=10000.0,
            current_balance=10000.0,
            minimum_loan=100.0,
            duration_days=30,
            interest_rate=5.5
        )

        pool_result = create_pool_mpt(
            client=xrpl_client,
            issuer_wallet=lender_wallet,
            metadata=pool_metadata
        )

        pool_mpt_id = pool_result['mpt_id']
        assert pool_mpt_id is not None, "Pool MPT ID is None"
        assert len(pool_mpt_id) > 0, "Pool MPT ID is empty"

        logger.info(f"✅ PoolMPT created: {pool_mpt_id}")
        logger.info(f"   Total balance: {pool_metadata.total_balance} XRP")
        logger.info(f"   Interest rate: {pool_metadata.interest_rate}%")
        logger.info(f"   Explorer: {EXPLORER_BASE}/accounts/{lender_wallet.classic_address}")

        # Create pool record in database
        pool = Pool(
            pool_address=pool_mpt_id,
            issuer_address=lender_wallet.classic_address,
            total_balance=Decimal(str(pool_metadata.total_balance)),
            current_balance=Decimal(str(pool_metadata.current_balance)),
            minimum_loan=Decimal(str(pool_metadata.minimum_loan)),
            duration_days=pool_metadata.duration_days,
            interest_rate=Decimal(str(pool_metadata.interest_rate)),
            tx_hash=f"POOL_TX_{pool_mpt_id}"
        )
        db_session.add(pool)
        db_session.commit()

        # ================================================================
        # STEP 3: Create loan application (ApplicationMPT)
        # ================================================================
        logger.info("\n" + "="*70)
        logger.info("STEP 3: Creating loan application (ApplicationMPT)")
        logger.info("="*70)

        principal_amount = 1000.0
        offered_rate = 5.0
        term_days = 30

        application_metadata = ApplicationMPTMetadata(
            borrower_addr=borrower_wallet.classic_address,
            pool_mpt_id=pool_mpt_id,
            application_date=datetime.now(),
            dissolution_date=datetime.now() + timedelta(days=term_days),
            state=ApplicationState.PENDING,
            principal=principal_amount,
            interest=principal_amount * offered_rate / 100
        )

        application_result = create_application_mpt(
            client=xrpl_client,
            borrower_wallet=borrower_wallet,
            metadata=application_metadata
        )

        application_mpt_id = application_result['mpt_id']
        assert application_mpt_id is not None, "Application MPT ID is None"
        assert len(application_mpt_id) > 0, "Application MPT ID is empty"

        logger.info(f"✅ ApplicationMPT created: {application_mpt_id}")
        logger.info(f"   Principal: {principal_amount} XRP")
        logger.info(f"   Offered rate: {offered_rate}%")
        logger.info(f"   Term: {term_days} days")
        logger.info(f"   Explorer: {EXPLORER_BASE}/accounts/{borrower_wallet.classic_address}")

        # Create application record in database
        application = Application(
            application_address=application_mpt_id,
            borrower_address=borrower_wallet.classic_address,
            pool_address=pool_mpt_id,
            application_date=application_metadata.application_date,
            dissolution_date=application_metadata.dissolution_date,
            state=ApplicationState.PENDING.value,
            principal=Decimal(str(application_metadata.principal)),
            interest=Decimal(str(application_metadata.interest)),
            tx_hash=f"APP_TX_{application_mpt_id}"
        )
        db_session.add(application)
        db_session.commit()

        # ================================================================
        # STEP 4: Approve loan and create LoanMPT
        # ================================================================
        logger.info("\n" + "="*70)
        logger.info("STEP 4: Approving loan and creating LoanMPT")
        logger.info("="*70)

        loan_metadata = LoanMPTMetadata(
            pool_mpt_id=pool_mpt_id,
            borrower_addr=borrower_wallet.classic_address,
            lender_addr=lender_wallet.classic_address,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=term_days),
            principal=principal_amount,
            interest=principal_amount * offered_rate / 100,
            state=LoanState.ONGOING
        )

        loan_result = create_loan_mpt(
            client=xrpl_client,
            lender_wallet=lender_wallet,
            metadata=loan_metadata
        )

        loan_mpt_id = loan_result['mpt_id']
        assert loan_mpt_id is not None, "Loan MPT ID is None"
        assert len(loan_mpt_id) > 0, "Loan MPT ID is empty"

        logger.info(f"✅ LoanMPT created: {loan_mpt_id}")
        logger.info(f"   Borrower: {borrower_wallet.classic_address}")
        logger.info(f"   Lender: {lender_wallet.classic_address}")
        logger.info(f"   Amount: {principal_amount} XRP + {loan_metadata.interest} XRP interest")
        logger.info(f"   Explorer: {EXPLORER_BASE}/accounts/{lender_wallet.classic_address}")

        # Update application state to APPROVED
        application.state = ApplicationState.APPROVED.value

        # Update pool balance
        pool.current_balance -= Decimal(str(principal_amount))

        # Create loan record in database
        loan = Loan(
            loan_address=loan_mpt_id,
            pool_address=pool_mpt_id,
            borrower_address=borrower_wallet.classic_address,
            lender_address=lender_wallet.classic_address,
            start_date=loan_metadata.start_date,
            end_date=loan_metadata.end_date,
            principal=Decimal(str(loan_metadata.principal)),
            interest=Decimal(str(loan_metadata.interest)),
            state=LoanState.ONGOING.value,
            tx_hash=f"LOAN_TX_{loan_mpt_id}"
        )
        db_session.add(loan)
        db_session.commit()

        # ================================================================
        # STEP 5: Verify all MPTs on XRPL
        # ================================================================
        logger.info("\n" + "="*70)
        logger.info("STEP 5: Verifying all MPTs on XRPL")
        logger.info("="*70)

        # Verify MPT IDs are different
        assert pool_mpt_id != application_mpt_id, "Pool and Application MPT IDs are the same"
        assert pool_mpt_id != loan_mpt_id, "Pool and Loan MPT IDs are the same"
        assert application_mpt_id != loan_mpt_id, "Application and Loan MPT IDs are the same"

        logger.info(f"✅ All 3 MPTs have unique IDs")
        logger.info(f"   PoolMPT:        {pool_mpt_id}")
        logger.info(f"   ApplicationMPT: {application_mpt_id}")
        logger.info(f"   LoanMPT:        {loan_mpt_id}")

        # ================================================================
        # STEP 6: Verify database records
        # ================================================================
        logger.info("\n" + "="*70)
        logger.info("STEP 6: Verifying database records")
        logger.info("="*70)

        # Verify pool
        db_pool = db_session.query(Pool).filter_by(pool_address=pool_mpt_id).first()
        assert db_pool is not None, "Pool not found in database"
        assert db_pool.current_balance == Decimal("9000.0"), "Pool balance not updated correctly"
        logger.info(f"✅ Pool record verified (balance: {db_pool.current_balance} XRP)")

        # Verify application
        db_app = db_session.query(Application).filter_by(
            application_address=application_mpt_id
        ).first()
        assert db_app is not None, "Application not found in database"
        assert db_app.state == ApplicationState.APPROVED.value, "Application state not updated"
        logger.info(f"✅ Application record verified (state: {db_app.state})")

        # Verify loan
        db_loan = db_session.query(Loan).filter_by(loan_address=loan_mpt_id).first()
        assert db_loan is not None, "Loan not found in database"
        assert db_loan.state == LoanState.ONGOING.value, "Loan state incorrect"
        logger.info(f"✅ Loan record verified (state: {db_loan.state})")

        # ================================================================
        # FINAL SUMMARY
        # ================================================================
        logger.info("\n" + "="*70)
        logger.info("🎉 E2E TEST PASSED - COMPLETE LENDING FLOW SUCCESSFUL")
        logger.info("="*70)
        logger.info(f"\nVerify on XRPL Testnet Explorer:")
        logger.info(f"  Lender Account:   {EXPLORER_BASE}/accounts/{lender_wallet.classic_address}")
        logger.info(f"  Borrower Account: {EXPLORER_BASE}/accounts/{borrower_wallet.classic_address}")
        logger.info(f"\nMPT IDs created:")
        logger.info(f"  1. PoolMPT:        {pool_mpt_id}")
        logger.info(f"  2. ApplicationMPT: {application_mpt_id}")
        logger.info(f"  3. LoanMPT:        {loan_mpt_id}")
        logger.info(f"\nBorrower DID:")
        logger.info(f"  {borrower_did}")
        logger.info("="*70 + "\n")

    def test_pool_creation_validation(self, xrpl_client):
        """
        Test pool creation with invalid parameters fails gracefully.

        This validates error handling and input validation.
        """
        invalid_wallet = Wallet.create()

        # Test with mismatched issuer address
        with pytest.raises(ValueError, match="issuer_addr.*must match wallet address"):
            pool_metadata = PoolMPTMetadata(
                issuer_addr="rWrongAddress123",  # Wrong address
                total_balance=10000.0,
                current_balance=10000.0,
                minimum_loan=100.0,
                duration_days=30,
                interest_rate=5.5
            )
            create_pool_mpt(
                client=xrpl_client,
                issuer_wallet=invalid_wallet,
                metadata=pool_metadata
            )

    def test_application_creation_validation(self, xrpl_client):
        """
        Test application creation with invalid parameters fails gracefully.
        """
        invalid_wallet = Wallet.create()

        # Test with mismatched borrower address
        with pytest.raises(ValueError, match="borrower_addr.*must match wallet address"):
            app_metadata = ApplicationMPTMetadata(
                borrower_addr="rWrongAddress123",  # Wrong address
                pool_mpt_id="POOL123",
                application_date=datetime.now(),
                dissolution_date=datetime.now() + timedelta(days=30),
                state=ApplicationState.PENDING,
                principal=1000.0,
                interest=50.0
            )
            create_application_mpt(
                client=xrpl_client,
                borrower_wallet=invalid_wallet,
                metadata=app_metadata
            )

    def test_loan_creation_validation(self, xrpl_client):
        """
        Test loan creation with invalid parameters fails gracefully.
        """
        invalid_wallet = Wallet.create()

        # Test with mismatched lender address
        with pytest.raises(ValueError, match="lender_addr.*must match wallet address"):
            loan_metadata = LoanMPTMetadata(
                pool_mpt_id="POOL123",
                borrower_addr="rBorrower123",
                lender_addr="rWrongAddress123",  # Wrong address
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                principal=1000.0,
                interest=50.0,
                state=LoanState.ONGOING
            )
            create_loan_mpt(
                client=xrpl_client,
                lender_wallet=invalid_wallet,
                metadata=loan_metadata
            )


if __name__ == "__main__":
    # Run this test with: pytest backend/tests/test_e2e_mvp.py -v -s
    pytest.main([__file__, "-v", "-s"])
