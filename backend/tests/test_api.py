"""
Tests for FastAPI endpoints with database integration.

These tests verify that the API properly integrates with the database
and handles all CRUD operations, error cases, and edge conditions.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.api.main import app
from backend.models.database import User, Pool, Application, Loan
from backend.config.database import get_db


# Override get_db dependency for testing
@pytest.fixture
def client(db_session):
    """Create a test client with database session override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns healthy status"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_endpoint(self, client):
        """Test detailed health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "pools_count" in data


class TestPoolEndpoints:
    """Test lending pool endpoints"""

    def test_create_pool_success(self, client, db_session, create_test_user):
        """Test creating a lending pool successfully"""
        # Create lender user first
        lender = create_test_user("rLender123", "did:xrpl:1:lender")

        pool_data = {
            "name": "Test Pool",
            "amount": 10000.0,
            "interest_rate": 5.5,
            "max_term_days": 30,
            "min_loan_amount": 100.0,
            "lender_address": lender.address
        }

        response = client.post("/pools", json=pool_data)
        assert response.status_code == 200
        data = response.json()
        assert "pool_id" in data
        assert "message" in data

        # Verify pool exists in database
        pool = db_session.query(Pool).filter_by(pool_address=data["pool_id"]).first()
        assert pool is not None
        assert pool.issuer_address == lender.address

    def test_create_pool_invalid_lender(self, client):
        """Test creating pool with non-existent lender returns 404"""
        pool_data = {
            "name": "Test Pool",
            "amount": 10000.0,
            "interest_rate": 5.5,
            "max_term_days": 30,
            "min_loan_amount": 100.0,
            "lender_address": "rNonExistent123"
        }

        response = client.post("/pools", json=pool_data)
        assert response.status_code == 404
        assert "lender not found" in response.json()["detail"].lower()

    def test_get_all_pools(self, client, create_test_user, create_test_pool):
        """Test retrieving all lending pools"""
        # Create test data
        lender = create_test_user("rLender123", "did:xrpl:1:lender")
        pool1 = create_test_pool("POOL001", lender.address, total_balance=10000.0)
        pool2 = create_test_pool("POOL002", lender.address, total_balance=5000.0)

        response = client.get("/pools")
        assert response.status_code == 200
        data = response.json()
        assert "pools" in data
        assert len(data["pools"]) >= 2

        pool_addresses = [p["pool_address"] for p in data["pools"]]
        assert pool1.pool_address in pool_addresses
        assert pool2.pool_address in pool_addresses

    def test_get_pool_by_id_success(self, client, create_test_user, create_test_pool):
        """Test retrieving a specific pool by ID"""
        lender = create_test_user("rLender123", "did:xrpl:1:lender")
        pool = create_test_pool("POOL001", lender.address, total_balance=10000.0)

        response = client.get(f"/pools/{pool.pool_address}")
        assert response.status_code == 200
        data = response.json()
        assert "pool" in data
        assert data["pool"]["pool_address"] == pool.pool_address
        assert data["pool"]["issuer_address"] == lender.address

    def test_get_pool_not_found(self, client):
        """Test retrieving non-existent pool returns 404"""
        response = client.get("/pools/NONEXISTENT")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestLoanApplicationEndpoints:
    """Test loan application endpoints"""

    def test_apply_for_loan_success(self, client, db_session, create_test_user, create_test_pool):
        """Test applying for a loan successfully"""
        lender = create_test_user("rLender123", "did:xrpl:1:lender")
        borrower = create_test_user("rBorrower123", "did:xrpl:1:borrower")
        pool = create_test_pool("POOL001", lender.address, total_balance=10000.0)

        application_data = {
            "pool_id": pool.pool_address,
            "amount": 1000.0,
            "purpose": "Business expansion",
            "term_days": 30,
            "borrower_address": borrower.address,
            "offered_rate": 5.0
        }

        response = client.post("/loans/apply", json=application_data)
        assert response.status_code == 200
        data = response.json()
        assert "loan_id" in data
        assert "message" in data

        # Verify application exists in database
        app = db_session.query(Application).filter_by(
            application_address=data["loan_id"]
        ).first()
        assert app is not None
        assert app.borrower_address == borrower.address
        assert app.pool_address == pool.pool_address
        assert app.state == "PENDING"

    def test_apply_for_loan_pool_not_found(self, client, create_test_user):
        """Test applying for loan with non-existent pool returns 404"""
        borrower = create_test_user("rBorrower123", "did:xrpl:1:borrower")

        application_data = {
            "pool_id": "NONEXISTENT",
            "amount": 1000.0,
            "purpose": "Business expansion",
            "term_days": 30,
            "borrower_address": borrower.address,
            "offered_rate": 5.0
        }

        response = client.post("/loans/apply", json=application_data)
        assert response.status_code == 404

    def test_apply_for_loan_insufficient_funds(self, client, create_test_user, create_test_pool):
        """Test applying for loan exceeding pool balance returns 400"""
        lender = create_test_user("rLender123", "did:xrpl:1:lender")
        borrower = create_test_user("rBorrower123", "did:xrpl:1:borrower")
        pool = create_test_pool("POOL001", lender.address, total_balance=1000.0, current_balance=500.0)

        application_data = {
            "pool_id": pool.pool_address,
            "amount": 1000.0,  # More than current_balance
            "purpose": "Business expansion",
            "term_days": 30,
            "borrower_address": borrower.address,
            "offered_rate": 5.0
        }

        response = client.post("/loans/apply", json=application_data)
        assert response.status_code == 400
        assert "insufficient" in response.json()["detail"].lower()

    def test_get_loan_applications_all(self, client, create_test_user, create_test_pool, create_test_application):
        """Test retrieving all loan applications"""
        lender = create_test_user("rLender123", "did:xrpl:1:lender")
        borrower = create_test_user("rBorrower123", "did:xrpl:1:borrower")
        pool = create_test_pool("POOL001", lender.address)

        app1 = create_test_application("APP001", borrower.address, pool.pool_address)
        app2 = create_test_application("APP002", borrower.address, pool.pool_address)

        response = client.get("/loans/applications")
        assert response.status_code == 200
        data = response.json()
        assert "applications" in data
        assert len(data["applications"]) >= 2

    def test_get_loan_applications_filtered_by_pool(self, client, create_test_user, create_test_pool, create_test_application):
        """Test retrieving loan applications filtered by pool"""
        lender = create_test_user("rLender123", "did:xrpl:1:lender")
        borrower = create_test_user("rBorrower123", "did:xrpl:1:borrower")
        pool1 = create_test_pool("POOL001", lender.address)
        pool2 = create_test_pool("POOL002", lender.address)

        app1 = create_test_application("APP001", borrower.address, pool1.pool_address)
        app2 = create_test_application("APP002", borrower.address, pool2.pool_address)

        response = client.get(f"/loans/applications?pool_id={pool1.pool_address}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["applications"]) >= 1
        assert all(app["pool_address"] == pool1.pool_address for app in data["applications"])


class TestLoanApprovalEndpoints:
    """Test loan approval endpoints"""

    def test_approve_loan_success(self, client, db_session, create_test_user, create_test_pool, create_test_application):
        """Test approving a loan application"""
        lender = create_test_user("rLender123", "did:xrpl:1:lender")
        borrower = create_test_user("rBorrower123", "did:xrpl:1:borrower")
        pool = create_test_pool("POOL001", lender.address, total_balance=10000.0, current_balance=10000.0)
        app = create_test_application("APP001", borrower.address, pool.pool_address, principal=1000.0)

        approval_data = {
            "loan_id": app.application_address,
            "approved": True,
            "lender_address": lender.address
        }

        response = client.post(f"/loans/{app.application_address}/approve", json=approval_data)
        assert response.status_code == 200
        data = response.json()
        assert "loan_id" in data

        # Verify application state changed
        db_session.refresh(app)
        assert app.state == "APPROVED"

        # Verify loan was created
        loan = db_session.query(Loan).filter_by(loan_address=data["loan_id"]).first()
        assert loan is not None
        assert loan.borrower_address == borrower.address
        assert loan.lender_address == lender.address
        assert loan.state == "ONGOING"

        # Verify pool balance was updated
        db_session.refresh(pool)
        assert pool.current_balance == Decimal("9000.0")  # 10000 - 1000

    def test_reject_loan_success(self, client, db_session, create_test_user, create_test_pool, create_test_application):
        """Test rejecting a loan application"""
        lender = create_test_user("rLender123", "did:xrpl:1:lender")
        borrower = create_test_user("rBorrower123", "did:xrpl:1:borrower")
        pool = create_test_pool("POOL001", lender.address)
        app = create_test_application("APP001", borrower.address, pool.pool_address)

        approval_data = {
            "loan_id": app.application_address,
            "approved": False,
            "lender_address": lender.address
        }

        response = client.post(f"/loans/{app.application_address}/approve", json=approval_data)
        assert response.status_code == 200

        # Verify application state changed
        db_session.refresh(app)
        assert app.state == "REJECTED"

    def test_approve_loan_not_found(self, client, create_test_user):
        """Test approving non-existent loan returns 404"""
        lender = create_test_user("rLender123", "did:xrpl:1:lender")

        approval_data = {
            "loan_id": "NONEXISTENT",
            "approved": True,
            "lender_address": lender.address
        }

        response = client.post("/loans/NONEXISTENT/approve", json=approval_data)
        assert response.status_code == 404


class TestActiveLoanEndpoints:
    """Test active loan endpoints"""

    def test_get_active_loans_all(self, client, create_test_user, create_test_pool, create_test_loan):
        """Test retrieving all active loans"""
        lender = create_test_user("rLender123", "did:xrpl:1:lender")
        borrower = create_test_user("rBorrower123", "did:xrpl:1:borrower")
        pool = create_test_pool("POOL001", lender.address)

        loan1 = create_test_loan("LOAN001", pool.pool_address, borrower.address, lender.address)
        loan2 = create_test_loan("LOAN002", pool.pool_address, borrower.address, lender.address)

        response = client.get("/loans/active")
        assert response.status_code == 200
        data = response.json()
        assert "loans" in data
        assert len(data["loans"]) >= 2

    def test_get_active_loans_by_lender(self, client, create_test_user, create_test_pool, create_test_loan):
        """Test retrieving loans filtered by lender"""
        lender1 = create_test_user("rLender1", "did:xrpl:1:lender1")
        lender2 = create_test_user("rLender2", "did:xrpl:1:lender2")
        borrower = create_test_user("rBorrower", "did:xrpl:1:borrower")
        pool1 = create_test_pool("POOL001", lender1.address)
        pool2 = create_test_pool("POOL002", lender2.address)

        loan1 = create_test_loan("LOAN001", pool1.pool_address, borrower.address, lender1.address)
        loan2 = create_test_loan("LOAN002", pool2.pool_address, borrower.address, lender2.address)

        response = client.get(f"/loans/active?lender_address={lender1.address}")
        assert response.status_code == 200
        data = response.json()
        assert all(loan["lender_address"] == lender1.address for loan in data["loans"])

    def test_get_active_loans_by_borrower(self, client, create_test_user, create_test_pool, create_test_loan):
        """Test retrieving loans filtered by borrower"""
        lender = create_test_user("rLender", "did:xrpl:1:lender")
        borrower1 = create_test_user("rBorrower1", "did:xrpl:1:borrower1")
        borrower2 = create_test_user("rBorrower2", "did:xrpl:1:borrower2")
        pool = create_test_pool("POOL001", lender.address)

        loan1 = create_test_loan("LOAN001", pool.pool_address, borrower1.address, lender.address)
        loan2 = create_test_loan("LOAN002", pool.pool_address, borrower2.address, lender.address)

        response = client.get(f"/loans/active?borrower_address={borrower1.address}")
        assert response.status_code == 200
        data = response.json()
        assert all(loan["borrower_address"] == borrower1.address for loan in data["loans"])


class TestMissingEndpoints:
    """Test newly added endpoints from SPEC_ALIGNMENT.md"""

    def test_get_loans_borrower_mode(self, client, create_test_user, create_test_pool, create_test_loan):
        """Test GET /api/loans?mode=borrower"""
        lender = create_test_user("rLender", "did:xrpl:1:lender")
        borrower = create_test_user("rBorrower", "did:xrpl:1:borrower")
        pool = create_test_pool("POOL001", lender.address)
        loan = create_test_loan("LOAN001", pool.pool_address, borrower.address, lender.address)

        response = client.get(f"/api/loans?mode=borrower&address={borrower.address}")
        assert response.status_code == 200
        data = response.json()
        assert "loans" in data

    def test_get_loans_lender_mode(self, client, create_test_user, create_test_pool, create_test_loan):
        """Test GET /api/loans?mode=lender"""
        lender = create_test_user("rLender", "did:xrpl:1:lender")
        borrower = create_test_user("rBorrower", "did:xrpl:1:borrower")
        pool = create_test_pool("POOL001", lender.address)
        loan = create_test_loan("LOAN001", pool.pool_address, borrower.address, lender.address)

        response = client.get(f"/api/loans?mode=lender&address={lender.address}")
        assert response.status_code == 200
        data = response.json()
        assert "loans" in data

    def test_verify_user(self, client, create_test_user):
        """Test GET /api/verify?address={}"""
        user = create_test_user("rUser123", "did:xrpl:1:user123")

        response = client.get(f"/api/verify?address={user.address}")
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == user.address
        assert data["did"] == user.did

    def test_verify_user_not_found(self, client):
        """Test GET /api/verify with non-existent user"""
        response = client.get("/api/verify?address=rNonExistent")
        assert response.status_code == 404

    def test_update_application_status(self, client, db_session, create_test_user, create_test_pool, create_test_application):
        """Test PUT /api/application"""
        lender = create_test_user("rLender", "did:xrpl:1:lender")
        borrower = create_test_user("rBorrower", "did:xrpl:1:borrower")
        pool = create_test_pool("POOL001", lender.address)
        app = create_test_application("APP001", borrower.address, pool.pool_address)

        update_data = {
            "application_address": app.application_address,
            "state": "EXPIRED"
        }

        response = client.put("/api/application", json=update_data)
        assert response.status_code == 200

        # Verify state was updated
        db_session.refresh(app)
        assert app.state == "EXPIRED"
