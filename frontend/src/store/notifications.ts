import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import supabase, { type Notification, type NotificationType } from '@/lib/supabase';
import { useOrdersStore } from '@/store/orders';
import type { RealtimeChannel } from '@supabase/supabase-js';

export const useNotificationStore = defineStore('notifications', () => {
  // State
  const notifications = ref<Notification[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const isConnected = ref(false);
  const lastFetchedAt = ref<Date | null>(null);

  // Private
  let realtimeChannel: RealtimeChannel | null = null;

  // Computed
  const unreadCount = computed(() =>
    notifications.value.filter(n => !n.is_read && !n.is_dismissed).length
  );

  const unreadNotifications = computed(() =>
    notifications.value.filter(n => !n.is_read && !n.is_dismissed)
  );

  const recentNotifications = computed(() =>
    notifications.value
      .filter(n => !n.is_dismissed)
      .slice(0, 50)
  );

  const urgentNotifications = computed(() =>
    notifications.value.filter(n =>
      n.priority === 'urgent' && !n.is_read && !n.is_dismissed
    )
  );

  const notificationsByType = computed(() => {
    const grouped: Record<NotificationType, Notification[]> = {
      order_assigned: [],
      order_status_change: [],
      order_pickup_ready: [],
      order_urgent: [],
      system_alert: [],
      system_announcement: []
    };

    notifications.value.forEach(n => {
      if (grouped[n.type]) {
        grouped[n.type].push(n);
      }
    });

    return grouped;
  });

  // Actions
  async function fetchNotifications(params?: { limit?: number; offset?: number; unreadOnly?: boolean }) {
    if (!supabase) {
      console.warn('Supabase not configured');
      return;
    }

    const ordersStore = useOrdersStore();
    const driverPhone = ordersStore.currentUserPhone;

    if (!driverPhone) {
      console.warn('No driver phone available for notifications');
      return;
    }

    isLoading.value = true;
    error.value = null;

    try {
      let query = supabase
        .from('notifications')
        .select('*')
        .eq('driver_phone', driverPhone)
        .eq('is_dismissed', false)
        .order('created_at', { ascending: false })
        .limit(params?.limit || 100);

      if (params?.unreadOnly) {
        query = query.eq('is_read', false);
      }

      const { data, error: fetchError } = await query;

      if (fetchError) throw fetchError;

      notifications.value = data || [];
      lastFetchedAt.value = new Date();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch notifications';
      console.error('Failed to fetch notifications:', err);
    } finally {
      isLoading.value = false;
    }
  }

  async function markAsRead(notificationId: string) {
    if (!supabase) return;

    try {
      const { error: updateError } = await supabase
        .from('notifications')
        .update({
          is_read: true,
          read_at: new Date().toISOString()
        })
        .eq('id', notificationId);

      if (updateError) throw updateError;

      // Update local state
      const notification = notifications.value.find(n => n.id === notificationId);
      if (notification) {
        notification.is_read = true;
        notification.read_at = new Date().toISOString();
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  }

  async function markAllAsRead() {
    if (!supabase) return;

    const ordersStore = useOrdersStore();
    const driverPhone = ordersStore.currentUserPhone;

    if (!driverPhone) return;

    try {
      const { error: updateError } = await supabase
        .from('notifications')
        .update({
          is_read: true,
          read_at: new Date().toISOString()
        })
        .eq('driver_phone', driverPhone)
        .eq('is_read', false);

      if (updateError) throw updateError;

      // Update local state
      notifications.value.forEach(n => {
        if (!n.is_read) {
          n.is_read = true;
          n.read_at = new Date().toISOString();
        }
      });
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err);
    }
  }

  async function dismissNotification(notificationId: string) {
    if (!supabase) return;

    try {
      const { error: updateError } = await supabase
        .from('notifications')
        .update({
          is_dismissed: true,
          dismissed_at: new Date().toISOString()
        })
        .eq('id', notificationId);

      if (updateError) throw updateError;

      // Remove from local state
      notifications.value = notifications.value.filter(n => n.id !== notificationId);
    } catch (err) {
      console.error('Failed to dismiss notification:', err);
    }
  }

  async function clearAllNotifications() {
    if (!supabase) return;

    const ordersStore = useOrdersStore();
    const driverPhone = ordersStore.currentUserPhone;

    if (!driverPhone) return;

    try {
      const { error: updateError } = await supabase
        .from('notifications')
        .update({
          is_dismissed: true,
          dismissed_at: new Date().toISOString()
        })
        .eq('driver_phone', driverPhone);

      if (updateError) throw updateError;

      notifications.value = [];
    } catch (err) {
      console.error('Failed to clear notifications:', err);
    }
  }

  function subscribeToRealtime() {
    if (!supabase) {
      console.warn('Supabase not configured, skipping realtime subscription');
      return;
    }

    const ordersStore = useOrdersStore();
    const driverPhone = ordersStore.currentUserPhone;

    if (!driverPhone) {
      console.warn('No driver phone available for realtime subscription');
      return;
    }

    // Unsubscribe from existing channel if any
    unsubscribeFromRealtime();

    // Subscribe to notifications for this driver
    realtimeChannel = supabase
      .channel(`notifications:${driverPhone}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `driver_phone=eq.${driverPhone}`
        },
        (payload) => {
          const newNotification = payload.new as Notification;

          // Add to beginning of list
          notifications.value.unshift(newNotification);

          // Show notification alert
          showNotificationAlert(newNotification);

          // Play notification sound for urgent/high priority
          if (newNotification.priority === 'urgent' || newNotification.priority === 'high') {
            playNotificationSound();
          }
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'notifications',
          filter: `driver_phone=eq.${driverPhone}`
        },
        (payload) => {
          const updatedNotification = payload.new as Notification;
          const index = notifications.value.findIndex(n => n.id === updatedNotification.id);

          if (index !== -1) {
            if (updatedNotification.is_dismissed) {
              // Remove dismissed notifications
              notifications.value.splice(index, 1);
            } else {
              // Update the notification
              notifications.value[index] = updatedNotification;
            }
          }
        }
      )
      .subscribe((status) => {
        isConnected.value = status === 'SUBSCRIBED';
        console.log('Realtime subscription status:', status);
      });
  }

  function unsubscribeFromRealtime() {
    if (realtimeChannel && supabase) {
      supabase.removeChannel(realtimeChannel);
      realtimeChannel = null;
      isConnected.value = false;
    }
  }

  function showNotificationAlert(notification: Notification) {
    // Show browser notification if permitted
    if ('Notification' in window && Notification.permission === 'granted') {
      new window.Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.svg',
        tag: notification.id
      });
    }

    // Dispatch custom event for UI components to handle
    window.dispatchEvent(new CustomEvent('new-notification', {
      detail: notification
    }));
  }

  function playNotificationSound() {
    try {
      const audio = new Audio('/notification.mp3');
      audio.volume = 0.5;
      audio.play().catch(() => {
        // Ignore autoplay errors
      });
    } catch {
      // Ignore audio errors
    }
  }

  async function requestNotificationPermission(): Promise<boolean> {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return false;
  }

  function cleanup() {
    unsubscribeFromRealtime();
    notifications.value = [];
    error.value = null;
    lastFetchedAt.value = null;
  }

  // Initialize realtime when user phone changes
  const ordersStore = useOrdersStore();
  watch(
    () => ordersStore.currentUserPhone,
    (newPhone, oldPhone) => {
      if (newPhone && newPhone !== oldPhone) {
        fetchNotifications();
        subscribeToRealtime();
      } else if (!newPhone) {
        cleanup();
      }
    },
    { immediate: true }
  );

  return {
    // State
    notifications,
    isLoading,
    error,
    isConnected,
    lastFetchedAt,

    // Computed
    unreadCount,
    unreadNotifications,
    recentNotifications,
    urgentNotifications,
    notificationsByType,

    // Actions
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    dismissNotification,
    clearAllNotifications,
    subscribeToRealtime,
    unsubscribeFromRealtime,
    requestNotificationPermission,
    cleanup
  };
});
