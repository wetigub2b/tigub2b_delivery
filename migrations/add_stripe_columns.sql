-- Migration: Add Stripe Connect columns to tigu_driver table
-- Date: 2024-12-17
-- Purpose: Enable driver payment setup via Stripe Connect

-- Add Stripe-related columns to tigu_driver table
ALTER TABLE tigu_driver
ADD COLUMN stripe_account_id VARCHAR(255) NULL COMMENT 'Stripe Connect account ID (acct_xxxxx)',
ADD COLUMN stripe_status ENUM('pending', 'onboarding', 'verified', 'restricted') DEFAULT 'pending' COMMENT 'Stripe onboarding status',
ADD COLUMN stripe_payouts_enabled TINYINT(1) DEFAULT 0 COMMENT 'Whether driver can receive payouts',
ADD COLUMN stripe_details_submitted TINYINT(1) DEFAULT 0 COMMENT 'Whether driver completed Stripe form',
ADD COLUMN stripe_onboarding_url VARCHAR(512) NULL COMMENT 'Current onboarding URL if in progress',
ADD COLUMN stripe_connected_at TIMESTAMP NULL COMMENT 'When driver completed Stripe setup';

-- Add index for faster lookups
ALTER TABLE tigu_driver ADD INDEX idx_stripe_account_id (stripe_account_id);
ALTER TABLE tigu_driver ADD INDEX idx_stripe_status (stripe_status);

-- Verify the changes
-- SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
-- FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME = 'tigu_driver' AND COLUMN_NAME LIKE 'stripe%';
