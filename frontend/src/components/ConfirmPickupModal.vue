<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="modal-overlay" @click="handleCancel">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3>{{ $t('orderCard.confirmPickup') }}</h3>
            <button class="modal-close" @click="handleCancel" aria-label="Close">
              ✕
            </button>
          </div>

          <div class="modal-body">
            <div class="order-summary">
              <div class="order-row">
                <span class="order-label">{{ $t('orderDetail.orderNumber') }}:</span>
                <span class="order-value">{{ order.orderSn }}</span>
              </div>
              <div class="order-row">
                <span class="order-label">{{ $t('orderDetail.receiver') }}:</span>
                <span class="order-value">{{ order.receiverName }}</span>
              </div>
              <div class="order-row">
                <span class="order-label">{{ $t('orderCard.pickup') }}:</span>
                <span class="order-value">{{ order.pickupLocation?.name || '-' }}</span>
              </div>
              <div class="order-row">
                <span class="order-label">{{ $t('orderCard.dropOff') }}:</span>
                <span class="order-value">{{ order.receiverAddress }}</span>
              </div>
              <div class="order-row">
                <span class="order-label">{{ $t('orderCard.items') }}:</span>
                <span class="order-value">{{ order.items.length }}</span>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="modal-button modal-button--cancel" @click="handleCancel">
              {{ $t('common.cancel') }}
            </button>
            <button class="modal-button modal-button--confirm" @click="handleConfirm" :disabled="isProcessing">
              {{ isProcessing ? $t('common.loading') : $t('common.confirm') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { DeliveryOrder } from '@/store/orders';

const props = defineProps<{
  show: boolean;
  order: DeliveryOrder;
  isProcessing?: boolean;
}>();

const emit = defineEmits<{
  confirm: [];
  cancel: [];
}>();

function handleConfirm() {
  if (!props.isProcessing) {
    emit('confirm');
  }
}

function handleCancel() {
  if (!props.isProcessing) {
    emit('cancel');
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: var(--spacing-md);
}

.modal-container {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--color-gray-lighter);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-dark);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-gray);
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  transition: all var(--transition-base);
}

.modal-close:hover {
  background: var(--color-gray-lighter);
  color: var(--color-gray-dark);
}

.modal-body {
  padding: var(--spacing-xl);
  overflow-y: auto;
  flex: 1;
}

.order-summary {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.order-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-gray-lightest);
}

.order-row:last-child {
  border-bottom: none;
}

.order-label {
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray);
  flex-shrink: 0;
  min-width: 100px;
}

.order-value {
  color: var(--color-gray-dark);
  text-align: right;
  word-break: break-word;
}

.modal-footer {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-lg) var(--spacing-xl);
  border-top: 1px solid var(--color-gray-lighter);
  background: var(--color-gray-lightest);
}

.modal-button {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-full);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  border: none;
}

.modal-button--cancel {
  background: var(--color-white);
  color: var(--color-gray-dark);
  border: 1px solid var(--color-gray-light);
}

.modal-button--cancel:hover {
  background: var(--color-gray-lighter);
  border-color: var(--color-gray);
}

.modal-button--confirm {
  background: var(--color-primary);
  color: var(--color-white);
}

.modal-button--confirm:hover:not(:disabled) {
  background: var(--color-primary-dark);
  color: var(--color-white);
}

.modal-button--confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-base);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--transition-base);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
}

@media (max-width: 768px) {
  .modal-container {
    max-width: 100%;
    margin: var(--spacing-md);
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .modal-button {
    width: 100%;
  }

  .order-label {
    min-width: 80px;
    font-size: var(--font-size-sm);
  }

  .order-value {
    font-size: var(--font-size-sm);
  }
}
</style>
