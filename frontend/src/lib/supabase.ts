import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase credentials not configured. Notifications will be disabled.');
}

export const supabase: SupabaseClient | null = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey, {
      realtime: {
        params: {
          eventsPerSecond: 10
        }
      },
      auth: {
        persistSession: false,
        autoRefreshToken: false
      }
    })
  : null;

// Notification types
export type NotificationType =
  | 'order_assigned'
  | 'order_status_change'
  | 'order_pickup_ready'
  | 'order_urgent'
  | 'system_alert'
  | 'system_announcement';

export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';

export interface Notification {
  id: string;
  driver_id: number;
  driver_phone: string;
  type: NotificationType;
  title: string;
  message: string;
  priority: NotificationPriority;
  order_sn: string | null;
  action_url: string | null;
  metadata: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  is_dismissed: boolean;
  dismissed_at: string | null;
  created_at: string;
}

export default supabase;
