<template>
  <div class="admin-notifications">
    <AdminNavigation />

    <div class="notifications-content">
      <div class="notifications-header">
        <h1>{{ $t('admin.notifications.title') }}</h1>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="error-banner">
        {{ error }}
        <button @click="error = ''" class="close-error">×</button>
      </div>

      <!-- Success Display -->
      <div v-if="successMessage" class="success-banner">
        {{ successMessage }}
        <button @click="successMessage = ''" class="close-success">×</button>
      </div>

      <!-- Notification Form -->
      <div class="notification-form-container">
        <h2>{{ $t('admin.notifications.sendNotification') }}</h2>
        
        <form @submit.prevent="sendNotification" class="notification-form">
          <!-- Recipient Selection -->
          <div class="form-group">
            <label>{{ $t('admin.notifications.recipients') }}</label>
            <div class="recipient-options">
              <label class="radio-option">
                <input type="radio" v-model="recipientType" value="all" />
                <span>{{ $t('admin.notifications.allDrivers') }}</span>
              </label>
              <label class="radio-option">
                <input type="radio" v-model="recipientType" value="selected" />
                <span>{{ $t('admin.notifications.selectedDrivers') }}</span>
              </label>
              <label class="radio-option">
                <input type="radio" v-model="recipientType" value="single" />
                <span>{{ $t('admin.notifications.singleDriver') }}</span>
              </label>
            </div>
          </div>

          <!-- Driver Selection (for selected/single) -->
          <div v-if="recipientType !== 'all'" class="form-group">
            <label>{{ $t('admin.notifications.selectDrivers') }}</label>
            <div class="driver-select-container">
              <div v-if="isLoadingDrivers" class="loading-drivers">
                {{ $t('common.loading') }}
              </div>
              <div v-else class="driver-checkboxes">
                <label
                  v-for="driver in availableDrivers"
                  :key="driver.id"
                  class="driver-checkbox"
                  :class="{ 'selected': selectedDriverIds.includes(driver.id) }"
                >
                  <input
                    type="checkbox"
                    v-if="recipientType === 'selected'"
                    :value="driver.id"
                    v-model="selectedDriverIds"
                  />
                  <input
                    type="radio"
                    v-else
                    name="singleDriver"
                    :value="driver.id"
                    v-model="singleDriverId"
                  />
                  <span class="driver-info">
                    <strong>{{ driver.nick_name || driver.user_name }}</strong>
                    <small>{{ driver.phonenumber || driver.phone }}</small>
                  </span>
                </label>
              </div>
            </div>
          </div>

          <!-- Notification Title -->
          <div class="form-group">
            <label for="title">{{ $t('admin.notifications.notificationTitle') }}</label>
            <input
              id="title"
              v-model="notificationTitle"
              type="text"
              :placeholder="$t('admin.notifications.titlePlaceholder')"
              required
              maxlength="200"
            />
          </div>

          <!-- Notification Message -->
          <div class="form-group">
            <label for="message">{{ $t('admin.notifications.message') }}</label>
            <textarea
              id="message"
              v-model="notificationMessage"
              :placeholder="$t('admin.notifications.messagePlaceholder')"
              required
              maxlength="1000"
              rows="4"
            ></textarea>
            <small class="char-count">{{ notificationMessage.length }}/1000</small>
          </div>

          <!-- Priority Selection -->
          <div class="form-group">
            <label>{{ $t('admin.notifications.priority') }}</label>
            <div class="priority-options">
              <label class="priority-option" :class="{ 'selected': priority === 'low' }">
                <input type="radio" v-model="priority" value="low" />
                <span class="priority-badge low">{{ $t('admin.notifications.priorityLow') }}</span>
              </label>
              <label class="priority-option" :class="{ 'selected': priority === 'normal' }">
                <input type="radio" v-model="priority" value="normal" />
                <span class="priority-badge normal">{{ $t('admin.notifications.priorityNormal') }}</span>
              </label>
              <label class="priority-option" :class="{ 'selected': priority === 'high' }">
                <input type="radio" v-model="priority" value="high" />
                <span class="priority-badge high">{{ $t('admin.notifications.priorityHigh') }}</span>
              </label>
              <label class="priority-option" :class="{ 'selected': priority === 'urgent' }">
                <input type="radio" v-model="priority" value="urgent" />
                <span class="priority-badge urgent">{{ $t('admin.notifications.priorityUrgent') }}</span>
              </label>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="form-actions">
            <button type="submit" class="send-button" :disabled="isSending || !isFormValid">
              <span v-if="isSending">{{ $t('admin.notifications.sending') }}</span>
              <span v-else>
                🔔 {{ $t('admin.notifications.send') }}
              </span>
            </button>
          </div>
        </form>
      </div>

      <!-- Recent Notifications Info -->
      <div class="recent-info">
        <h3>{{ $t('admin.notifications.howItWorks') }}</h3>
        <ul>
          <li>{{ $t('admin.notifications.info1') }}</li>
          <li>{{ $t('admin.notifications.info2') }}</li>
          <li>{{ $t('admin.notifications.info3') }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useI18n } from '@/composables/useI18n';
import AdminNavigation from '@/components/AdminNavigation.vue';
import { broadcastNotification, sendDriverNotification, getAllDrivers } from '@/api/admin';
import type { Driver } from '@/api/admin';

const { t } = useI18n();

// Form state
const recipientType = ref<'all' | 'selected' | 'single'>('all');
const selectedDriverIds = ref<number[]>([]);
const singleDriverId = ref<number | null>(null);
const notificationTitle = ref('');
const notificationMessage = ref('');
const priority = ref<'low' | 'normal' | 'high' | 'urgent'>('normal');

// UI state
const isSending = ref(false);
const isLoadingDrivers = ref(false);
const error = ref('');
const successMessage = ref('');

// Driver list
const availableDrivers = ref<Driver[]>([]);

// Form validation
const isFormValid = computed(() => {
  if (!notificationTitle.value.trim() || !notificationMessage.value.trim()) {
    return false;
  }
  if (recipientType.value === 'selected' && selectedDriverIds.value.length === 0) {
    return false;
  }
  if (recipientType.value === 'single' && !singleDriverId.value) {
    return false;
  }
  return true;
});

// Load drivers when recipient type changes
watch(recipientType, async (newType) => {
  if (newType !== 'all' && availableDrivers.value.length === 0) {
    await loadDrivers();
  }
});

// Load active drivers
const loadDrivers = async () => {
  isLoadingDrivers.value = true;
  try {
    availableDrivers.value = await getAllDrivers({ status: '1', limit: 100 });
  } catch (err) {
    console.error('Failed to load drivers:', err);
    error.value = t('admin.notifications.loadDriversError');
  } finally {
    isLoadingDrivers.value = false;
  }
};

// Send notification
const sendNotification = async () => {
  if (!isFormValid.value) return;

  isSending.value = true;
  error.value = '';
  successMessage.value = '';

  try {
    let result;

    if (recipientType.value === 'single' && singleDriverId.value) {
      // Send to single driver
      result = await sendDriverNotification(singleDriverId.value, {
        title: notificationTitle.value,
        message: notificationMessage.value,
        priority: priority.value
      });
    } else {
      // Broadcast to all or selected drivers
      const driverIds = recipientType.value === 'selected' ? selectedDriverIds.value : undefined;
      result = await broadcastNotification({
        title: notificationTitle.value,
        message: notificationMessage.value,
        priority: priority.value,
        driver_ids: driverIds
      });
    }

    if (result.success) {
      successMessage.value = t('admin.notifications.sendSuccess', { count: result.count });
      resetForm();
    } else {
      error.value = result.message || t('admin.notifications.sendError');
    }
  } catch (err: any) {
    console.error('Failed to send notification:', err);
    error.value = err.response?.data?.detail || t('admin.notifications.sendError');
  } finally {
    isSending.value = false;
  }
};

// Reset form
const resetForm = () => {
  notificationTitle.value = '';
  notificationMessage.value = '';
  priority.value = 'normal';
  selectedDriverIds.value = [];
  singleDriverId.value = null;
};

onMounted(() => {
  // Pre-load drivers if needed
  if (recipientType.value !== 'all') {
    loadDrivers();
  }
});
</script>

<style scoped>
.admin-notifications {
  min-height: 100vh;
  background-color: var(--color-bg-lighter);
}

.notifications-content {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

.notifications-header {
  margin-bottom: var(--spacing-xl);
}

.notifications-header h1 {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.error-banner,
.success-banner {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-banner {
  background: var(--color-error-light);
  color: var(--color-error);
}

.success-banner {
  background: var(--color-success-light);
  color: var(--color-success-dark);
}

.close-error,
.close-success {
  background: none;
  border: none;
  font-size: var(--font-size-lg);
  cursor: pointer;
  color: inherit;
}

.notification-form-container {
  background: var(--color-white);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-md);
  margin-bottom: var(--spacing-xl);
}

.notification-form-container h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
}

.notification-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.form-group label {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.form-group input[type="text"],
.form-group textarea {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-md);
  font-family: inherit;
  transition: border-color var(--transition-base);
}

.form-group input[type="text"]:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-group textarea {
  resize: vertical;
  min-height: 100px;
}

.char-count {
  text-align: right;
  color: var(--color-text-light);
  font-size: var(--font-size-xs);
}

.recipient-options,
.priority-options {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.radio-option,
.priority-option {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.radio-option:hover,
.priority-option:hover {
  border-color: var(--color-primary);
}

.radio-option input,
.priority-option input {
  margin: 0;
}

.priority-badge {
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-xs);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.priority-badge.low {
  background: var(--color-gray-lighter, #f5f5f5);
  color: var(--color-text-secondary);
}

.priority-badge.normal {
  background: var(--color-info-light);
  color: var(--color-info-dark);
}

.priority-badge.high {
  background: var(--color-warning-light);
  color: var(--color-warning-dark);
}

.priority-badge.urgent {
  background: var(--color-error-light);
  color: var(--color-error);
}

.priority-option.selected {
  border-color: var(--color-primary);
  background: var(--color-bg-lighter);
}

.driver-select-container {
  max-height: 300px;
  overflow-y: auto;
  border: 2px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm);
}

.loading-drivers {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--color-text-light);
}

.driver-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-sm);
}

.driver-checkbox {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-base);
}

.driver-checkbox:hover {
  border-color: var(--color-primary);
  background: var(--color-bg-lighter);
}

.driver-checkbox.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-light, #e3f2fd);
}

.driver-checkbox input {
  margin: 0;
}

.driver-info {
  display: flex;
  flex-direction: column;
}

.driver-info strong {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.driver-info small {
  font-size: var(--font-size-xs);
  color: var(--color-text-light);
}

.form-actions {
  margin-top: var(--spacing-md);
}

.send-button {
  width: 100%;
  padding: var(--spacing-md) var(--spacing-xl);
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
}

.send-button:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
}

.send-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.recent-info {
  background: var(--color-white);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-md);
}

.recent-info h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}

.recent-info ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.recent-info li {
  padding: var(--spacing-sm) 0;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-gray-light);
}

.recent-info li:last-child {
  border-bottom: none;
}

.recent-info li::before {
  content: "✓ ";
  color: var(--color-success);
}

@media (max-width: 768px) {
  .notifications-content {
    padding: var(--spacing-md);
  }

  .recipient-options,
  .priority-options {
    flex-direction: column;
  }

  .driver-checkboxes {
    grid-template-columns: 1fr;
  }
}
</style>
