#!/bin/bash
# Script to remove completed test orders from database
# Usage: ./cleanup_completed_orders.sh

echo "=================================="
echo "Removing Completed Test Orders"
echo "=================================="

sudo mysql tigu_b2b < test_data_completed_orders_cleanup.sql

echo ""
echo "✅ Completed orders removed successfully!"
