#!/bin/bash
# Cleanup Test Data Script
# Description: Removes all test data from database

set -e  # Exit on error

# Database name
DB_NAME="tigu_b2b"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Migration directory
MIGRATION_DIR="$(dirname "$0")"

echo -e "${YELLOW}Starting test data cleanup...${NC}"
echo ""

# Function to run a cleanup script
run_cleanup() {
    local file=$1
    local description=$2

    echo -e "${YELLOW}Running: ${description}${NC}"
    if sudo mysql "${DB_NAME}" < "${MIGRATION_DIR}/${file}"; then
        echo -e "${GREEN}✓ Success: ${description}${NC}"
        echo ""
    else
        echo -e "${RED}✗ Failed: ${description}${NC}"
        exit 1
    fi
}

# Run cleanup scripts in order
run_cleanup "test_data_orders_cleanup.sql" "Step 1: Remove test orders"
run_cleanup "test_data_drivers_cleanup.sql" "Step 2: Remove test drivers"

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}All test data removed successfully!${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""
echo -e "${YELLOW}To re-insert test data, run:${NC}"
echo -e "  ${YELLOW}bash ${MIGRATION_DIR}/run_migrations.sh${NC}"
