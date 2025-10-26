-- LendX Initial Database Schema
-- This migration creates the core tables for the lending marketplace

-- Users table: Stores XRP wallet addresses and DIDs
CREATE TABLE users (
    address VARCHAR(34) PRIMARY KEY,  -- XRP address (rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX format)
    did VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pools table: Indexes PoolMPT data from XRPL
CREATE TABLE pools (
    pool_address VARCHAR(66) PRIMARY KEY,  -- MPT ID from XRPL
    issuer_address VARCHAR(34) NOT NULL REFERENCES users(address),
    total_balance DECIMAL(20,6) NOT NULL,
    current_balance DECIMAL(20,6) NOT NULL,
    minimum_loan DECIMAL(20,6) NOT NULL,
    duration_days INTEGER NOT NULL,
    interest_rate DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    tx_hash VARCHAR(64) NOT NULL  -- XRPL transaction hash for verification
);

-- Applications table: Indexes ApplicationMPT data from XRPL
CREATE TABLE applications (
    application_address VARCHAR(66) PRIMARY KEY,  -- MPT ID from XRPL
    borrower_address VARCHAR(34) NOT NULL REFERENCES users(address),
    pool_address VARCHAR(66) NOT NULL REFERENCES pools(pool_address),
    application_date TIMESTAMP NOT NULL,
    dissolution_date TIMESTAMP NOT NULL,
    state VARCHAR(20) NOT NULL CHECK (state IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
    principal DECIMAL(20,6) NOT NULL,
    interest DECIMAL(20,6) NOT NULL,
    tx_hash VARCHAR(64) NOT NULL  -- XRPL transaction hash
);

-- Loans table: Indexes LoanMPT data from XRPL
CREATE TABLE loans (
    loan_address VARCHAR(66) PRIMARY KEY,  -- MPT ID from XRPL
    pool_address VARCHAR(66) NOT NULL REFERENCES pools(pool_address),
    borrower_address VARCHAR(34) NOT NULL REFERENCES users(address),
    lender_address VARCHAR(34) NOT NULL REFERENCES users(address),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    principal DECIMAL(20,6) NOT NULL,
    interest DECIMAL(20,6) NOT NULL,
    state VARCHAR(20) NOT NULL CHECK (state IN ('ONGOING', 'PAID', 'DEFAULTED')),
    tx_hash VARCHAR(64) NOT NULL  -- XRPL transaction hash
);

-- User MPT Balances table: Cache of on-chain MPT balances for performance
CREATE TABLE user_mpt_balances (
    user_address VARCHAR(34) NOT NULL REFERENCES users(address),
    mpt_id VARCHAR(66) NOT NULL,
    balance DECIMAL(20,6) NOT NULL DEFAULT 0,
    last_synced TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_address, mpt_id)
);

-- Indexes for performance optimization
CREATE INDEX idx_pools_issuer ON pools(issuer_address);
CREATE INDEX idx_applications_borrower ON applications(borrower_address);
CREATE INDEX idx_applications_pool ON applications(pool_address);
CREATE INDEX idx_applications_state ON applications(state);
CREATE INDEX idx_loans_borrower ON loans(borrower_address);
CREATE INDEX idx_loans_lender ON loans(lender_address);
CREATE INDEX idx_loans_pool ON loans(pool_address);
CREATE INDEX idx_loans_state ON loans(state);
CREATE INDEX idx_user_mpt_balances_mpt ON user_mpt_balances(mpt_id);

-- Comments for documentation
COMMENT ON TABLE users IS 'Stores user wallet addresses and decentralized identifiers';
COMMENT ON TABLE pools IS 'Indexes PoolMPT data - lending pools created by lenders';
COMMENT ON TABLE applications IS 'Indexes ApplicationMPT data - loan applications from borrowers';
COMMENT ON TABLE loans IS 'Indexes LoanMPT data - active and completed loans';
COMMENT ON TABLE user_mpt_balances IS 'Cache of on-chain MPT balances to reduce XRPL API calls';

COMMENT ON COLUMN pools.pool_address IS 'MPT issuance ID from XRPL';
COMMENT ON COLUMN pools.current_balance IS 'Available balance for new loans';
COMMENT ON COLUMN applications.dissolution_date IS 'Expiration date for pending applications';
COMMENT ON COLUMN loans.state IS 'Loan status: ONGOING (active), PAID (completed), DEFAULTED (overdue)';
