<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ $t('admin.drivers.driverDetails') }}</h2>
        <button class="close-button" @click="$emit('close')">✕</button>
      </div>

      <div class="modal-body" v-if="driver">
        <div class="detail-section">
          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.drivers.name') }}</span>
            <span class="detail-value">{{ driver.name }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.drivers.phone') }}</span>
            <span class="detail-value">{{ driver.phone }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.drivers.email') }}</span>
            <span class="detail-value">{{ driver.email }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.drivers.vehicleType') }}</span>
            <span class="detail-value">{{ formatVehicleType(driver.vehicleType) }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.drivers.licensePlate') }}</span>
            <span class="detail-value">{{ driver.licensePlate }}</span>
          </div>

          <div class="detail-row">
            <span class="detail-label">{{ $t('admin.drivers.status') }}</span>
            <span class="status-badge" :class="`status-${driver.status}`">
              {{ formatStatus(driver.status) }}
            </span>
          </div>

          <div class="detail-row" v-if="driver.totalDeliveries !== undefined">
            <span class="detail-label">{{ $t('admin.drivers.totalDeliveries') }}</span>
            <span class="detail-value">{{ driver.totalDeliveries }}</span>
          </div>

          <div class="detail-row" v-if="driver.rating">
            <span class="detail-label">{{ $t('admin.drivers.rating') }}</span>
            <span class="detail-value">⭐ {{ driver.rating.toFixed(1) }}</span>
          </div>

          <div class="detail-row" v-if="driver.createdAt">
            <span class="detail-label">{{ $t('admin.drivers.joinedDate') }}</span>
            <span class="detail-value">{{ formatDate(driver.createdAt) }}</span>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="$emit('close')" class="btn-secondary">
            {{ $t('common.close') }}
          </button>
          <button @click="$emit('edit', driver)" class="btn-primary">
            {{ $t('common.edit') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from '@/composables/useI18n';
import type { Driver } from '@/api/admin';

const props = defineProps<{
  driver: Driver | null;
}>();

const emit = defineEmits<{
  close: [];
  edit: [driver: Driver];
}>();

const { t } = useI18n();

const formatVehicleType = (type: string) => {
  return t(`admin.drivers.${type}`) || type;
};

const formatStatus = (status: string) => {
  return t(`admin.drivers.${status}`) || status;
};

const formatDate = (date: string | Date) => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleDateString();
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--spacing-lg);
}

.modal-content {
  background: var(--color-white);
  border-radius: var(--radius-md);
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-xl);
  border-bottom: 1px solid var(--color-gray-lighter);
}

.modal-header h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-dark);
  margin: 0;
}

.close-button {
  background: none;
  border: none;
  font-size: var(--font-size-2xl);
  color: var(--color-gray);
  cursor: pointer;
  padding: var(--spacing-xs);
  line-height: 1;
  transition: color var(--transition-base);
}

.close-button:hover {
  color: var(--color-gray-dark);
}

.modal-body {
  padding: var(--spacing-xl);
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) 0;
  border-bottom: 1px solid var(--color-gray-lighter);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray);
}

.detail-value {
  font-size: var(--font-size-md);
  color: var(--color-gray-dark);
  font-weight: var(--font-weight-medium);
}

.status-badge {
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-transform: capitalize;
}

.status-active {
  background: #d1fae5;
  color: #065f46;
}

.status-inactive {
  background: #fee2e2;
  color: #991b1b;
}

.status-suspended {
  background: #fef3c7;
  color: #92400e;
}

.modal-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
  padding-top: var(--spacing-xl);
  margin-top: var(--spacing-lg);
  border-top: 1px solid var(--color-gray-lighter);
}

.btn-primary,
.btn-secondary {
  padding: var(--spacing-md) var(--spacing-xl);
  border-radius: var(--radius-full);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
  border: 1px solid;
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-white);
  border-color: var(--color-primary);
}

.btn-primary:hover {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

.btn-secondary {
  background: var(--color-white);
  color: var(--color-black);
  border-color: var(--color-gray-light);
}

.btn-secondary:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
}

@media (max-width: 768px) {
  .modal-overlay {
    padding: var(--spacing-md);
  }

  .modal-header,
  .modal-body {
    padding: var(--spacing-lg);
  }

  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-xs);
  }

  .modal-actions {
    flex-direction: column;
  }

  .modal-actions button {
    width: 100%;
  }
}
</style>
