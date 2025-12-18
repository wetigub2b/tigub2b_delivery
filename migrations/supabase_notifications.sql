-- Supabase Notifications Table Schema
-- Run this in Supabase Dashboard > SQL Editor

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    driver_id BIGINT NOT NULL,
    driver_phone VARCHAR(20) NOT NULL,
    type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    order_sn VARCHAR(50),
    action_url TEXT,
    metadata JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    is_dismissed BOOLEAN DEFAULT FALSE,
    dismissed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_notifications_driver_phone ON notifications(driver_phone);
CREATE INDEX IF NOT EXISTS idx_notifications_driver_id ON notifications(driver_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(driver_phone, is_read) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);

-- Enable Row Level Security
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any (for re-running)
DROP POLICY IF EXISTS "Drivers can view own notifications" ON notifications;
DROP POLICY IF EXISTS "Drivers can update own notifications" ON notifications;
DROP POLICY IF EXISTS "Service role can insert" ON notifications;
DROP POLICY IF EXISTS "Service role can delete" ON notifications;

-- RLS Policy: Drivers can only read their own notifications
-- This matches the JWT claim 'phonenumber' set during driver authentication
CREATE POLICY "Drivers can view own notifications"
    ON notifications
    FOR SELECT
    USING (
        driver_phone = COALESCE(
            current_setting('request.jwt.claims', true)::json->>'phonenumber',
            current_setting('request.jwt.claims', true)::json->>'phone'
        )
    );

-- RLS Policy: Drivers can update (mark as read/dismissed) their own notifications
CREATE POLICY "Drivers can update own notifications"
    ON notifications
    FOR UPDATE
    USING (
        driver_phone = COALESCE(
            current_setting('request.jwt.claims', true)::json->>'phonenumber',
            current_setting('request.jwt.claims', true)::json->>'phone'
        )
    )
    WITH CHECK (
        driver_phone = COALESCE(
            current_setting('request.jwt.claims', true)::json->>'phonenumber',
            current_setting('request.jwt.claims', true)::json->>'phone'
        )
    );

-- RLS Policy: Service role can insert notifications (backend use)
-- Service role key bypasses RLS, but explicit policy for clarity
CREATE POLICY "Service role can insert"
    ON notifications
    FOR INSERT
    WITH CHECK (TRUE);

-- RLS Policy: Service role can delete notifications
CREATE POLICY "Service role can delete"
    ON notifications
    FOR DELETE
    USING (TRUE);

-- Enable Realtime on the notifications table
-- This allows frontend to subscribe to INSERT/UPDATE events
ALTER PUBLICATION supabase_realtime ADD TABLE notifications;

-- Comment on table for documentation
COMMENT ON TABLE notifications IS 'Driver notifications for order updates and system alerts';
COMMENT ON COLUMN notifications.type IS 'Notification type: order_assigned, order_status_change, order_pickup_ready, order_urgent, system_alert, system_announcement';
COMMENT ON COLUMN notifications.priority IS 'Priority level: low, normal, high, urgent';
