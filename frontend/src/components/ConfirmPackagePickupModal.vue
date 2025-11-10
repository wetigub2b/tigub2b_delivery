<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="modal-overlay" @click="handleCancel">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3>{{ $t('taskBoard.confirmPickup') }}</h3>
            <button class="modal-close" @click="handleCancel" aria-label="Close">
              ✕
            </button>
          </div>

          <div class="modal-body">
            <div class="package-summary">
              <div class="summary-icon">📦</div>
              <div class="package-row">
                <span class="package-label">{{ $t('packageModal.packageNumber') }}:</span>
                <span class="package-value">{{ packageData.prepareSn }}</span>
              </div>
              <div class="package-row">
                <span class="package-label">{{ $t('packageModal.totalOrders') }}:</span>
                <span class="package-value">{{ packageData.orderCount }}</span>
              </div>
              <div class="package-row">
                <span class="package-label">{{ $t('taskBoard.workflow') }}:</span>
                <span class="package-value">{{ packageData.workflowLabel }}</span>
              </div>
              <div v-if="packageData.warehouseName" class="package-row">
                <span class="package-label">{{ $t('taskBoard.warehouse') }}:</span>
                <span class="package-value">{{ packageData.warehouseName }}</span>
              </div>
            </div>

            <div class="confirmation-message">
              <p>{{ $t('taskBoard.confirmPickupMessage') }}</p>
            </div>
          </div>

          <div class="modal-footer">
            <button class="modal-button modal-button--cancel" @click="handleCancel" :disabled="isProcessing">
              {{ $t('common.cancel') }}
            </button>
            <button class="modal-button modal-button--confirm" @click="handleConfirm" :disabled="isProcessing">
              {{ isProcessing ? $t('common.loading') : $t('taskBoard.confirmPickupButton') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  show: boolean;
  packageData: {
    prepareSn: string;
    orderCount: number;
    workflowLabel: string;
    warehouseName?: string | null;
  };
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
  font-size: 1.25rem;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
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
  color: var(--color-text-primary);
}

.modal-body {
  padding: var(--spacing-xl);
  overflow-y: auto;
  flex: 1;
}

.package-summary {
  background: var(--color-gray-lighter);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.summary-icon {
  font-size: 3rem;
  text-align: center;
  margin-bottom: var(--spacing-md);
}

.package-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-white);
}

.package-row:last-child {
  border-bottom: none;
}

.package-label {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  flex-shrink: 0;
  font-size: 0.875rem;
}

.package-value {
  color: var(--color-text-primary);
  text-align: right;
  word-break: break-word;
  font-weight: var(--font-weight-semibold);
  font-size: 0.875rem;
}

.confirmation-message {
  text-align: center;
  padding: var(--spacing-md);
}

.confirmation-message p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 0.9375rem;
  line-height: 1.5;
}

.modal-footer {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-lg) var(--spacing-xl);
  border-top: 1px solid var(--color-gray-lighter);
}

.modal-button {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  border: none;
}

.modal-button--cancel {
  background: var(--color-white);
  color: var(--color-text-primary);
  border: 1px solid var(--color-gray-light);
}

.modal-button--cancel:hover:not(:disabled) {
  background: var(--color-gray-lighter);
  border-color: var(--color-gray);
}

.modal-button--confirm {
  background: var(--color-primary);
  color: var(--color-white);
}

.modal-button--confirm:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.modal-button:disabled {
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
  transform: scale(0.95);
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
}
</style>
