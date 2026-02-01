#!/bin/bash
# Test runner script for RAG system tests
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh api          # Run only API tests
#   ./run_tests.sh ai           # Run only AI generator tests
#   ./run_tests.sh -k pattern   # Run tests matching pattern

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}RAG System Test Runner${NC}"
echo "========================================"

# Check if virtual environment exists, create if not
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    uv venv
    echo -e "${BLUE}Installing dependencies...${NC}"
    source .venv/bin/activate
    uv pip install anthropic pytest fastapi httpx sentence-transformers chromadb python-dotenv
else
    source .venv/bin/activate
fi

# Change to backend directory
cd backend

# Determine which tests to run
case "${1:-all}" in
    api)
        echo -e "${BLUE}Running API endpoint tests...${NC}"
        PYTHONPATH=. ../.venv/bin/pytest tests/test_api.py -v
        ;;
    ai)
        echo -e "${BLUE}Running AI generator tests...${NC}"
        PYTHONPATH=. ../.venv/bin/pytest tests/test_ai_generator.py -v
        ;;
    all)
        echo -e "${BLUE}Running all tests...${NC}"
        PYTHONPATH=. ../.venv/bin/pytest tests/ -v
        ;;
    *)
        # Pass through any other arguments to pytest
        echo -e "${BLUE}Running tests with custom arguments: $@${NC}"
        PYTHONPATH=. ../.venv/bin/pytest tests/ "$@"
        ;;
esac

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
fi

exit $exit_code
