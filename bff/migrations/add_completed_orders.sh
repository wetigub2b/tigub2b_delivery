#!/bin/bash
# Script to add completed test orders to database
# Usage: ./add_completed_orders.sh

echo "=================================="
echo "Adding Completed Test Orders"
echo "=================================="

sudo mysql tigu_b2b < test_data_completed_orders_insert.sql

echo ""
echo "✅ Completed orders added successfully!"
echo ""
echo "To remove these orders later, run:"
echo "  ./cleanup_completed_orders.sh"
