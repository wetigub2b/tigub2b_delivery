#!/bin/bash
# Migration Runner Script
# Description: Runs all database migrations and inserts test data

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

echo -e "${YELLOW}Starting database migrations...${NC}"
echo ""

# Function to run a migration
run_migration() {
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
# Run migrations in order
run_migration "001_create_driver_table.sql" "Step 1: Create driver table"
run_migration "002_add_driver_id_to_orders.sql" "Step 2: Add driver_id column and foreign key to orders"
run_migration "test_data_driver_15888888888.sql" "Step 3: Create test driver with phone 15888888888"
run_migration "test_data_orders_insert.sql" "Step 4: Create test orders assigned to driver"

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}All migrations completed successfully!${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""
echo -e "${YELLOW}You can now:${NC}"
echo "  1. Login with phone: 15888888888"
echo "  2. See 6 test orders in the driver app"
echo "  3. Run cleanup script when needed:"
echo -e "     ${YELLOW}bash ${MIGRATION_DIR}/cleanup_test_data.sh${NC}"
