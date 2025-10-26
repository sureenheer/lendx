# LendX Backend Tests

## Test Suite Overview

The test suite follows **Test-Driven Development (TDD)** methodology and provides comprehensive coverage for the database layer.

## Test Files

- **test_database.py**: Database connection and basic operations
- **test_users.py**: User model CRUD operations
- **test_pools.py**: Pool model operations (lending pools)
- **test_applications.py**: Application model operations (loan applications)
- **test_loans.py**: Loan model operations (active and completed loans)

## Running Tests

### Prerequisites

1. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your SUPABASE_DB_PASSWORD
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   # Or with system override:
   pip install --break-system-packages xrpl-py fastapi uvicorn pydantic pytest supabase python-dotenv sqlalchemy psycopg2-binary
   ```

### Run All Tests

```bash
# Export password first
export SUPABASE_DB_PASSWORD="your_password_here"

# Run all tests
PYTHONPATH=/home/users/duynguy/proj/calhacks pytest backend/tests/ -v
```

### Run Specific Test Files

```bash
# Test database connection only
pytest backend/tests/test_database.py -v

# Test user operations only
pytest backend/tests/test_users.py -v
```

### Run Single Test

```bash
pytest backend/tests/test_users.py::TestUserModel::test_create_user -v
```

## Test Structure

All tests use pytest fixtures defined in `conftest.py`:

- **db_session**: Provides a database session with automatic rollback
- **create_test_user**: Factory for creating test users
- **create_test_pool**: Factory for creating test pools
- **create_test_application**: Factory for creating test applications
- **create_test_loan**: Factory for creating test loans

## Connection Issues

If you encounter "Tenant or user not found" errors, this means the database password is incorrect or not set.

**Solution**:
1. Get the correct database password from Supabase dashboard
2. Set it in your `.env` file or export it:
   ```bash
   export SUPABASE_DB_PASSWORD="your_actual_password"
   ```

## Test Coverage

The test suite covers:

- [x] Database connection and initialization
- [x] User CRUD operations (create, read, update, delete)
- [x] Pool CRUD operations with decimal precision
- [x] Application state management (PENDING, APPROVED, REJECTED, EXPIRED)
- [x] Loan state management (ONGOING, PAID, DEFAULTED)
- [x] Foreign key constraints
- [x] Unique constraints (DID uniqueness)
- [x] Check constraints (state validation)
- [x] Index performance (covered in conftest fixtures)

## Integration with Supabase

The tests connect to the actual Supabase PostgreSQL database using the credentials from `.env`:

- **Project**: sspwpkhajtooztzisioo.supabase.co
- **Connection**: Uses connection pooling via SQLAlchemy
- **Security**: SSL required, enforced by Supabase

## TDD Workflow

1. **Red Phase**: Tests were written first and failed (no implementation)
2. **Green Phase**: Database config and ORM models implemented, tests pass
3. **Refactor Phase**: Connection pooling, error handling, and validation added

## Next Steps

After tests pass:
1. Integrate with FastAPI endpoints
2. Add API-level tests
3. Add end-to-end tests with XRPL integration
4. Set up CI/CD pipeline with automated tests
