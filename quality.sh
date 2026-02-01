#!/bin/bash
# Code quality check script

set -e

echo "🔍 Running code quality checks..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2 passed${NC}"
    else
        echo -e "${RED}✗ $2 failed${NC}"
        return 1
    fi
}

# Track overall status
FAILED=0

# Run Black (check mode)
echo -e "${YELLOW}Running Black formatter check...${NC}"
if uv run black --check backend/ main.py; then
    print_status 0 "Black formatting"
else
    print_status 1 "Black formatting" || FAILED=1
    echo "  Run 'uv run black backend/ main.py' to fix"
fi
echo ""

# Run isort (check mode)
echo -e "${YELLOW}Running isort import sorting check...${NC}"
if uv run isort --check-only backend/ main.py; then
    print_status 0 "isort import sorting"
else
    print_status 1 "isort import sorting" || FAILED=1
    echo "  Run 'uv run isort backend/ main.py' to fix"
fi
echo ""

# Run flake8
echo -e "${YELLOW}Running flake8 linting...${NC}"
if uv run flake8 backend/ main.py; then
    print_status 0 "flake8 linting"
else
    print_status 1 "flake8 linting" || FAILED=1
fi
echo ""

# Run mypy
echo -e "${YELLOW}Running mypy type checking...${NC}"
if uv run mypy backend/ main.py; then
    print_status 0 "mypy type checking"
else
    print_status 1 "mypy type checking" || FAILED=1
fi
echo ""

# Run pytest with coverage
echo -e "${YELLOW}Running pytest with coverage...${NC}"
if uv run pytest; then
    print_status 0 "pytest tests"
else
    print_status 1 "pytest tests" || FAILED=1
fi
echo ""

# Final status
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}All quality checks passed! ✓${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Some quality checks failed! ✗${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
