<template>
  <div class="notification-bell" ref="bellRef">
    <button
      class="notification-bell__button"
      @click="toggleDropdown"
      :aria-label="$t('notifications.label', { count: unreadCount })"
    >
      <span class="notification-bell__icon">🔔</span>
      <span
        v-if="unreadCount > 0"
        class="notification-bell__badge"
        :class="{ 'notification-bell__badge--urgent': hasUrgent }"
      >
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <Transition name="dropdown">
      <div
        v-if="isOpen"
        class="notification-dropdown"
      >
        <div class="notification-dropdown__header">
          <h3>{{ $t('notifications.title') }}</h3>
          <div class="notification-dropdown__actions">
            <button
              v-if="unreadCount > 0"
              @click="markAllAsRead"
              class="notification-dropdown__action"
            >
              {{ $t('notifications.markAllRead') }}
            </button>
            <button
              v-if="notifications.length > 0"
              @click="clearAll"
              class="notification-dropdown__action notification-dropdown__action--danger"
            >
              {{ $t('notifications.clearAll') }}
            </button>
          </div>
        </div>

        <div class="notification-dropdown__content">
          <div v-if="isLoading" class="notification-dropdown__loading">
            <span class="spinner"></span>
            {{ $t('common.loading') }}
          </div>

          <div
            v-else-if="notifications.length === 0"
            class="notification-dropdown__empty"
          >
            <span class="notification-dropdown__empty-icon">📭</span>
            <p>{{ $t('notifications.empty') }}</p>
          </div>

          <ul v-else class="notification-list">
            <li
              v-for="notification in notifications"
              :key="notification.id"
              class="notification-item"
              :class="{
                'notification-item--unread': !notification.is_read,
                'notification-item--urgent': notification.priority === 'urgent',
                'notification-item--high': notification.priority === 'high'
              }"
              @click="handleNotificationClick(notification)"
            >
              <div class="notification-item__icon">
                {{ getNotificationIcon(notification.type) }}
              </div>
              <div class="notification-item__content">
                <div class="notification-item__title">{{ notification.title }}</div>
                <div class="notification-item__message">{{ notification.message }}</div>
                <div class="notification-item__time">
                  {{ formatTime(notification.created_at) }}
                </div>
              </div>
              <button
                class="notification-item__dismiss"
                @click.stop="dismiss(notification.id)"
                :aria-label="$t('notifications.dismiss')"
              >
                ✕
              </button>
            </li>
          </ul>
        </div>

        <div class="notification-dropdown__footer">
          <div
            class="notification-dropdown__status"
            :class="{ 'notification-dropdown__status--connected': isConnected }"
          >
            <span class="status-dot"></span>
            {{ isConnected ? $t('notifications.connected') : $t('notifications.disconnected') }}
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useNotificationStore } from '@/store/notifications';
import { storeToRefs } from 'pinia';
import type { Notification, NotificationType } from '@/lib/supabase';

const router = useRouter();
const notificationStore = useNotificationStore();
const {
  recentNotifications: notifications,
  unreadCount,
  urgentNotifications,
  isLoading,
  isConnected
} = storeToRefs(notificationStore);

const isOpen = ref(false);
const bellRef = ref<HTMLElement | null>(null);

const hasUrgent = computed(() => urgentNotifications.value.length > 0);

const notificationIcons: Record<NotificationType, string> = {
  order_assigned: '📦',
  order_status_change: '🔄',
  order_pickup_ready: '✅',
  order_urgent: '🚨',
  system_alert: '⚠️',
  system_announcement: '📢'
};

function getNotificationIcon(type: NotificationType): string {
  return notificationIcons[type] || '📬';
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;

  return date.toLocaleDateString();
}

function toggleDropdown() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    notificationStore.fetchNotifications({ limit: 20 });
  }
}

function handleNotificationClick(notification: Notification) {
  notificationStore.markAsRead(notification.id);

  if (notification.action_url) {
    router.push(notification.action_url);
    isOpen.value = false;
  } else if (notification.order_sn) {
    router.push(`/order/${notification.order_sn}`);
    isOpen.value = false;
  }
}

function dismiss(notificationId: string) {
  notificationStore.dismissNotification(notificationId);
}

function markAllAsRead() {
  notificationStore.markAllAsRead();
}

function clearAll() {
  notificationStore.clearAllNotifications();
  isOpen.value = false;
}

// Close dropdown when clicking outside
function handleClickOutside(event: MouseEvent) {
  if (bellRef.value && !bellRef.value.contains(event.target as Node)) {
    isOpen.value = false;
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  notificationStore.requestNotificationPermission();
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.notification-bell {
  position: relative;
}

.notification-bell__button {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px;
  position: relative;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s ease;
}

.notification-bell__button:hover {
  background: rgba(0, 0, 0, 0.05);
}

.notification-bell__badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: #1976d2;
  color: white;
  font-size: 0.65rem;
  font-weight: 600;
  min-width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.notification-bell__badge--urgent {
  background: #d32f2f;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 340px;
  max-height: 450px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid #e0e0e0;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.notification-dropdown__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
}

.notification-dropdown__header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.notification-dropdown__actions {
  display: flex;
  gap: 8px;
}

.notification-dropdown__action {
  background: none;
  border: none;
  color: #1976d2;
  font-size: 0.75rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.notification-dropdown__action:hover {
  background: rgba(25, 118, 210, 0.1);
}

.notification-dropdown__action--danger {
  color: #d32f2f;
}

.notification-dropdown__action--danger:hover {
  background: rgba(211, 47, 47, 0.1);
}

.notification-dropdown__content {
  flex: 1;
  overflow-y: auto;
  max-height: 320px;
}

.notification-dropdown__loading,
.notification-dropdown__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #666;
}

.notification-dropdown__empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.notification-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s ease;
}

.notification-item:hover {
  background: #f5f5f5;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item--unread {
  background: #e3f2fd;
}

.notification-item--unread:hover {
  background: #bbdefb;
}

.notification-item--urgent {
  border-left: 3px solid #d32f2f;
}

.notification-item--high {
  border-left: 3px solid #ff9800;
}

.notification-item__icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.notification-item__content {
  flex: 1;
  min-width: 0;
}

.notification-item__title {
  font-weight: 600;
  font-size: 0.875rem;
  color: #333;
  margin-bottom: 4px;
}

.notification-item__message {
  font-size: 0.8rem;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.notification-item__time {
  font-size: 0.7rem;
  color: #999;
  margin-top: 4px;
}

.notification-item__dismiss {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 4px;
  font-size: 0.875rem;
  opacity: 0;
  transition: opacity 0.2s ease;
  align-self: flex-start;
}

.notification-item:hover .notification-item__dismiss {
  opacity: 1;
}

.notification-item__dismiss:hover {
  color: #d32f2f;
}

.notification-dropdown__footer {
  padding: 8px 16px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
}

.notification-dropdown__status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  color: #999;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #bdbdbd;
}

.notification-dropdown__status--connected .status-dot {
  background: #4caf50;
}

/* Transitions */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Spinner */
.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #e0e0e0;
  border-top-color: #1976d2;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 480px) {
  .notification-dropdown {
    position: fixed;
    top: 60px;
    right: 8px;
    left: 8px;
    width: auto;
    max-height: calc(100vh - 120px);
  }
}
</style>
