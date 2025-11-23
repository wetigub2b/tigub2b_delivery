<template>
  <div class="modal-overlay" @click.self="handleClose">
    <div class="modal-content" :class="type">
      <div class="modal-header">
        <span class="icon" :class="type">{{ iconMap[type] }}</span>
        <h2>{{ title || defaultTitles[type] }}</h2>
        <button class="close-button" @click="handleClose">✕</button>
      </div>

      <div class="modal-body">
        <p>{{ message }}</p>
      </div>

      <div class="modal-actions">
        <button @click="handleClose" class="btn-primary">
          {{ buttonText || $t('common.ok') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from '@/composables/useI18n';

const { t } = useI18n();

interface Props {
  type?: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  buttonText?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'info'
});

const emit = defineEmits<{
  close: [];
}>();

const iconMap = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ'
};

const defaultTitles = computed(() => ({
  success: t('common.success'),
  error: t('common.error'),
  warning: t('common.warning'),
  info: t('common.info')
}));

const handleClose = () => {
  emit('close');
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
  z-index: 1001;
  padding: var(--spacing-lg);
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: var(--color-white);
  border-radius: var(--radius-md);
  width: 100%;
  max-width: 480px;
  box-shadow: var(--shadow-lg);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
  border-bottom: 1px solid var(--color-gray-lighter);
}

.modal-header .icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  flex-shrink: 0;
}

.icon.success {
  background: var(--color-success-light, #d4edda);
  color: var(--color-success, #28a745);
}

.icon.error {
  background: var(--color-error-light, #fee);
  color: var(--color-error, #d32f2f);
}

.icon.warning {
  background: var(--color-warning-light, #fff3cd);
  color: var(--color-warning, #ffc107);
}

.icon.info {
  background: var(--color-info-light, #e3f2fd);
  color: var(--color-info, #2196f3);
}

.modal-header h2 {
  flex: 1;
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
  flex-shrink: 0;
}

.close-button:hover {
  color: var(--color-gray-dark);
}

.modal-body {
  padding: var(--spacing-xl);
}

.modal-body p {
  font-size: var(--font-size-md);
  line-height: 1.6;
  color: var(--color-text-secondary);
  margin: 0;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-top: 1px solid var(--color-gray-lighter);
}

.btn-primary {
  min-width: 100px;
  padding: var(--spacing-md) var(--spacing-xl);
  border-radius: var(--radius-full);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
  border: 1px solid;
  background: var(--color-primary);
  color: var(--color-white);
  border-color: var(--color-primary);
}

.btn-primary:hover {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

@media (max-width: 768px) {
  .modal-overlay {
    padding: var(--spacing-md);
  }

  .modal-header {
    padding: var(--spacing-lg);
  }

  .modal-body {
    padding: var(--spacing-lg);
  }

  .modal-actions {
    padding: var(--spacing-md) var(--spacing-lg);
  }

  .btn-primary {
    width: 100%;
  }
}
</style>
