import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import client from '@/api/client';
import type { Notification, NotificationType } from '@/lib/notifications';
import { useOrdersStore } from '@/store/orders';

export const useNotificationStore = defineStore('notifications', () => {
  // State
  const notifications = ref<Notification[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const isConnected = ref(false);
  const lastFetchedAt = ref<Date | null>(null);

  // Private - polling interval
  let pollingInterval: ReturnType<typeof setInterval> | null = null;
  const POLLING_INTERVAL_MS = 30000; // Poll every 30 seconds

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

  // Actions — backed by local BFF (SQLite), no Supabase.
  async function fetchNotifications(params?: { limit?: number; offset?: number; unreadOnly?: boolean }) {
    const ordersStore = useOrdersStore();
    const driverPhone = ordersStore.currentUserPhone;

    if (!driverPhone) {
      console.warn('No driver phone available for notifications');
      return;
    }

    isLoading.value = true;
    error.value = null;

    try {
      const { data } = await client.get<{ notifications: Notification[] }>(
        '/notifications/mine',
        { params: { limit: params?.limit || 100, unread_only: params?.unreadOnly || false } }
      );

      notifications.value = data.notifications || [];
      lastFetchedAt.value = new Date();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch notifications';
      console.error('Failed to fetch notifications:', err);
    } finally {
      isLoading.value = false;
    }
  }

  async function markAsRead(notificationId: number) {
    try {
      await client.post(`/notifications/mine/${notificationId}/read`);

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
    const ordersStore = useOrdersStore();
    const driverPhone = ordersStore.currentUserPhone;

    if (!driverPhone) return;

    try {
      await client.post('/notifications/mine/read-all');

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

  async function dismissNotification(notificationId: number) {
    try {
      await client.post(`/notifications/mine/${notificationId}/dismiss`);

      // Remove from local state
      notifications.value = notifications.value.filter(n => n.id !== notificationId);
    } catch (err) {
      console.error('Failed to dismiss notification:', err);
    }
  }

  async function clearAllNotifications() {
    const ordersStore = useOrdersStore();
    const driverPhone = ordersStore.currentUserPhone;

    if (!driverPhone) return;

    try {
      await client.post('/notifications/mine/clear');

      notifications.value = [];
    } catch (err) {
      console.error('Failed to clear notifications:', err);
    }
  }

  function startPolling() {
    const ordersStore = useOrdersStore();
    const driverPhone = ordersStore.currentUserPhone;

    if (!driverPhone) {
      console.warn('No driver phone available for polling');
      return;
    }

    // Stop existing polling
    stopPolling();

    // Mark as connected (polling mode)
    isConnected.value = true;

    // Initial fetch
    fetchNotifications();

    // Start polling interval
    pollingInterval = setInterval(async () => {
      const currentPhone = ordersStore.currentUserPhone;
      if (currentPhone) {
        const previousCount = notifications.value.filter(n => !n.is_read).length;
        await fetchNotifications();
        const newCount = notifications.value.filter(n => !n.is_read).length;

        // If we have new unread notifications, show alert for the newest one
        if (newCount > previousCount && notifications.value.length > 0) {
          const newestNotification = notifications.value[0];
          if (!newestNotification.is_read) {
            showNotificationAlert(newestNotification);
            if (newestNotification.priority === 'urgent' || newestNotification.priority === 'high') {
              playNotificationSound();
            }
          }
        }
      }
    }, POLLING_INTERVAL_MS);

    console.log('Notification polling started');
  }

  function stopPolling() {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
    }
    isConnected.value = false;
  }

  // Keep subscribeToRealtime as alias for startPolling for backward compatibility
  function subscribeToRealtime() {
    startPolling();
  }

  function unsubscribeFromRealtime() {
    stopPolling();
  }

  function showNotificationAlert(notification: Notification) {
    // Show browser notification if permitted
    if ('Notification' in window && Notification.permission === 'granted') {
      new window.Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.svg',
        tag: String(notification.id)
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
    stopPolling();
    notifications.value = [];
    error.value = null;
    lastFetchedAt.value = null;
  }

  // Initialize polling when user phone changes
  const ordersStore = useOrdersStore();
  watch(
    () => ordersStore.currentUserPhone,
    (newPhone, oldPhone) => {
      if (newPhone && newPhone !== oldPhone) {
        startPolling();
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
    startPolling,
    stopPolling,
    requestNotificationPermission,
    cleanup
  };
});
