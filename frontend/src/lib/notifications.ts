export type NotificationType =
  | 'order_assigned'
  | 'order_status_change'
  | 'order_pickup_ready'
  | 'order_urgent'
  | 'system_alert'
  | 'system_announcement';

export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';

export interface Notification {
  id: number;
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
