# Test Suite for functionsV2 APIs

This directory contains comprehensive test cases for all Cloud Functions in the `functionsV2` folder.

## Test Coverage

The test suite covers the following APIs:

1. **dev_v2_getEmployee** - Fetch all employees
2. **dev_v2_getEmployeeCertificates** - Fetch all employee certificates
3. **dev_v2_getEmployeeSkill** - Fetch employee skills by email (supports GET and POST)
4. **dev_v2_getMasteDiscipline** - Fetch all master disciplines
5. **dev_v2_getMasterCertificate** - Fetch all master certificates
6. **dev_v2_getMasterDomain** - Fetch all master domains
7. **dev_v2_getMasterFramework** - Fetch all master frameworks
8. **dev_v2_getMasterSkill** - Fetch master skills (with optional search parameter)
9. **dev_v2_getSkillHierarchyLink** - Fetch all skill hierarchy links

## Test Structure

Each test file follows a consistent structure:
- **Test classes** for each function (e.g., `TestFetchEmployee`, `TestDevV2GetEmployee`)
- **Unit tests** using mocks to isolate database dependencies
- **Success cases** - Testing normal operation
- **Error cases** - Testing database errors and exceptions
- **Edge cases** - Testing empty results, missing parameters, etc.
- **CORS tests** - Testing OPTIONS preflight requests

## Setup

1. Install test dependencies:
```bash
cd functionsV2/tests
pip install -r requirements.txt
```

2. Ensure the parent directory is in your Python path. You can either:
   - Run tests from the `functionsV2` directory, or
   - Set the `PYTHONPATH` environment variable:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
   ```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run tests for a specific API:
```bash
pytest test_get_employee.py
pytest test_get_employee_skill.py
```

### Run tests with coverage:
```bash
pytest --cov=.. --cov-report=html
```

### Run tests with verbose output:
```bash
pytest -v
```

### Run a specific test:
```bash
pytest test_get_employee.py::TestDevV2GetEmployee::test_get_employee_success
```

## Test Categories

### Unit Tests
- Test individual functions in isolation
- Mock database connections and queries
- Verify function logic and data transformation

### Integration Tests (Future)
- Would require a test database
- Currently commented out as they need real database setup
- Can be enabled when test database is configured

## Mocking Strategy

The tests use `unittest.mock` to:
- Mock database connections (`mock_db_connection` fixture)
- Mock Flask request objects (`mock_flask_request_get`, `mock_flask_request_post`, etc.)
- Mock database query results
- Isolate unit tests from database dependencies

## Example Test Output

```
============================= test session starts ==============================
platform win32 -- Python 3.10.0, pytest-7.4.3
collected 45 items

test_get_employee.py ................                                    [ 35%]
test_get_employee_certificates.py ...                                    [ 42%]
test_get_employee_skill.py ..........                                    [ 64%]
test_get_master_certificate.py ...                                      [ 71%]
test_get_master_discipline.py ...                                      [ 78%]
test_get_master_domain.py ...                                          [ 85%]
test_get_master_framework.py ...                                       [ 92%]
test_get_master_skill.py ........                                      [100%]

============================= 45 passed in 2.34s ==============================
```

## Notes

- Tests are designed to run without a real database connection
- All database operations are mocked
- Tests verify both success and error scenarios
- CORS headers are tested for all endpoints
- Datetime serialization is tested where applicable

## Adding New Tests

When adding new APIs or modifying existing ones:

1. Create a new test file following the naming convention: `test_<api_name>.py`
2. Import the necessary functions from the API module
3. Use the shared fixtures from `conftest.py`
4. Follow the existing test structure and patterns
5. Ensure all edge cases and error scenarios are covered

