# RAG System Test Suite

Comprehensive test suite for the RAG (Retrieval-Augmented Generation) chatbot system.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_ai_generator.py     # AI generator unit tests (existing)
├── test_api.py             # FastAPI endpoint tests (new)
└── README.md               # This file
```

## Test Categories

### API Endpoint Tests (`test_api.py`)

Tests for FastAPI endpoints covering:

- **POST /api/query** - Query processing with session management
  - Session creation and reuse
  - Answer and source generation
  - Error handling (RAG system errors, validation errors)
  - Request/response model validation

- **GET /api/courses** - Course statistics retrieval
  - Course count and titles
  - Empty catalog handling
  - Error scenarios

- **Health Check** - System health endpoint

- **CORS Middleware** - Cross-origin request handling

- **Request Validation** - Input validation and error handling

- **Integration Tests** - Multi-endpoint workflows

**Total API Tests:** 26

### AI Generator Tests (`test_ai_generator.py`)

Tests for Claude API integration covering:

- Direct responses without tools
- Two-stage API pattern with tool use
- Multi-round tool calling
- Error handling (authentication, rate limits, network)
- Conversation history management
- Message preservation across rounds

**Total AI Tests:** 18 (2 expected to fail due to API changes)

## Running Tests

### Using the Test Runner Script (Recommended)

From the project root:

```bash
# Run all tests
./run_tests.sh

# Run only API tests
./run_tests.sh api

# Run only AI generator tests
./run_tests.sh ai

# Run tests matching a pattern
./run_tests.sh -k "test_query"

# Run with verbose output
./run_tests.sh -v
```

### Using pytest Directly

From the `backend/` directory:

```bash
# Run all tests
PYTHONPATH=. pytest tests/ -v

# Run specific test file
PYTHONPATH=. pytest tests/test_api.py -v

# Run specific test class
PYTHONPATH=. pytest tests/test_api.py::TestQueryEndpoint -v

# Run specific test
PYTHONPATH=. pytest tests/test_api.py::TestQueryEndpoint::test_query_with_new_session -v

# Run with coverage (if pytest-cov installed)
PYTHONPATH=. pytest tests/ --cov=. --cov-report=html
```

### Using uv

From the `backend/` directory:

```bash
PYTHONPATH=. uv run pytest tests/ -v
```

## Test Fixtures

The `conftest.py` file provides shared fixtures for all tests:

### Configuration Fixtures

- `test_config` - Test configuration with safe defaults

### Mock Component Fixtures

- `mock_vector_store` - Mock vector database
- `mock_ai_generator` - Mock Claude API client
- `mock_session_manager` - Mock session storage
- `mock_tool_manager` - Mock tool execution
- `mock_document_processor` - Mock document parsing

### Test Data Fixtures

- `sample_course` - Sample Course object
- `sample_course_chunks` - Sample CourseChunk objects
- `sample_query_request` - Sample API query request
- `sample_query_response` - Sample API query response

### API Test Client Fixtures

- `test_app` - FastAPI test application (without static file mounting)
- `test_client` - FastAPI TestClient for making HTTP requests

### Anthropic API Mock Fixtures

- `mock_anthropic_client` - Mock Anthropic client
- `mock_anthropic_with_tool_use` - Mock for two-stage tool pattern

## Pytest Configuration

Configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["backend/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

addopts = [
    "-v",                  # Verbose output
    "--tb=short",          # Shorter traceback format
    "--strict-markers",    # Raise error on unknown markers
    "--disable-warnings",  # Disable warnings for cleaner output
    "-ra",                 # Show summary of all test outcomes
]

markers = [
    "unit: Unit tests for individual components",
    "integration: Integration tests across components",
    "api: API endpoint tests",
    "slow: Tests that take longer to execute",
]
```

## Test Markers

Use markers to categorize and run specific test groups:

```bash
# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"
```

## Writing New Tests

### API Endpoint Test Example

```python
def test_new_endpoint(test_client, test_app):
    """Test description"""
    # Arrange
    request_data = {"key": "value"}

    # Act
    response = test_client.post("/api/endpoint", json=request_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["field"] == "expected_value"
```

### Component Unit Test Example

```python
@patch('module.dependency')
def test_component(mock_dependency):
    """Test description"""
    # Arrange
    mock_dependency.method.return_value = "mocked_value"
    component = Component()

    # Act
    result = component.do_something()

    # Assert
    assert result == "expected"
    mock_dependency.method.assert_called_once()
```

## Test Isolation

Tests are isolated through:

1. **Mocking**: All external dependencies (database, API, file system) are mocked
2. **Test App**: API tests use a separate test app without static file mounting
3. **In-Memory Config**: Test configuration uses in-memory databases
4. **Fresh Fixtures**: Each test gets fresh fixture instances

## Continuous Integration

To run tests in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: |
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt

- name: Run tests
  run: |
    cd backend
    PYTHONPATH=. ../.venv/bin/pytest tests/ -v --junitxml=test-results.xml
```

## Troubleshooting

### Import Errors

If you encounter import errors, ensure `PYTHONPATH=.` is set when running from the `backend/` directory:

```bash
PYTHONPATH=. pytest tests/
```

### Module Not Found

Ensure dependencies are installed:

```bash
uv sync
# or
uv pip install anthropic pytest fastapi httpx
```

### Static File Mounting Errors

API tests use a separate `test_app` fixture that doesn't mount static files. If you need to test the main app, ensure frontend files exist or use the test app.

## Coverage

To generate test coverage reports (requires pytest-cov):

```bash
# Install pytest-cov
uv pip add pytest-cov

# Run tests with coverage
PYTHONPATH=. pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Open coverage report
open htmlcov/index.html
```

## Known Issues

- 2 AI generator tests fail due to anthropic library API changes (error construction signature changes)
- Tests require PYTHONPATH to be set when running from backend/ directory
- Virtual environment must be activated or use absolute path to pytest

## Future Improvements

- [ ] Add integration tests for full RAG pipeline
- [ ] Add performance/load tests for API endpoints
- [ ] Add tests for document processing
- [ ] Add tests for vector store operations
- [ ] Increase coverage to 90%+
- [ ] Add mutation testing
- [ ] Add contract tests for API responses
