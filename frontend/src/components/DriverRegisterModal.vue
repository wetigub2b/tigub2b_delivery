<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ $t('login.createAccount') }}</h2>
        <button class="close-button" @click="$emit('close')">✕</button>
      </div>

      <form @submit.prevent="handleSubmit" class="modal-form">
        <div class="form-group">
          <label>{{ $t('admin.drivers.name') }} *</label>
          <input
            v-model="form.name"
            type="text"
            :placeholder="$t('admin.drivers.namePlaceholder')"
            required
          />
        </div>

        <div class="form-group">
          <label>{{ $t('admin.drivers.phone') }} *</label>
          <input
            v-model="form.phone"
            type="tel"
            :placeholder="$t('admin.drivers.phonePlaceholder')"
            required
          />
        </div>

        <div class="form-group">
          <label>{{ $t('admin.drivers.email') }}</label>
          <input
            v-model="form.email"
            type="email"
            :placeholder="$t('admin.drivers.emailPlaceholder')"
          />
        </div>

        <div class="form-group">
          <label>{{ $t('admin.drivers.password') }} *</label>
          <input
            v-model="form.password"
            type="password"
            :placeholder="$t('admin.drivers.passwordPlaceholder')"
            minlength="6"
            required
          />
          <small class="form-hint">{{ $t('admin.drivers.passwordHint') }}</small>
        </div>

        <div class="form-group">
          <label>{{ $t('admin.drivers.vehicleType') }}</label>
          <select v-model="form.vehicleType">
            <option value="">{{ $t('admin.drivers.selectVehicle') }}</option>
            <option value="van">{{ $t('admin.drivers.van') }}</option>
            <option value="truck">{{ $t('admin.drivers.truck') }}</option>
            <option value="car">{{ $t('admin.drivers.car') }}</option>
            <option value="motorcycle">{{ $t('admin.drivers.motorcycle') }}</option>
          </select>
        </div>

        <div class="form-group">
          <label>{{ $t('admin.drivers.licensePlate') }}</label>
          <input
            v-model="form.licensePlate"
            type="text"
            :placeholder="$t('admin.drivers.licensePlatePlaceholder')"
          />
        </div>

        <div class="form-group">
          <label>{{ $t('admin.drivers.vehicleModel') }}</label>
          <input
            v-model="form.vehicleModel"
            type="text"
            :placeholder="$t('admin.drivers.vehicleModelPlaceholder')"
          />
        </div>

        <div class="form-group">
          <label>{{ $t('admin.drivers.licenseNumber') }} *</label>
          <input
            v-model="form.licenseNumber"
            type="text"
            :placeholder="$t('admin.drivers.licenseNumberPlaceholder')"
            required
          />
        </div>

        <div class="info-message">
          <span class="info-icon">ℹ️</span>
          {{ $t('login.registrationNote') }}
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <div class="modal-actions">
          <button type="button" @click="$emit('close')" class="btn-secondary">
            {{ $t('common.cancel') }}
          </button>
          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            {{ isSubmitting ? $t('common.loading') : $t('login.register') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useI18n } from '@/composables/useI18n';

const { t } = useI18n();

const emit = defineEmits<{
  close: [];
  success: [];
}>();

const form = reactive({
  name: '',
  phone: '',
  email: '',
  password: '',
  vehicleType: '',
  licensePlate: '',
  vehicleModel: '',
  licenseNumber: ''
});

const isSubmitting = ref(false);
const errorMessage = ref('');

const handleSubmit = async () => {
  isSubmitting.value = true;
  errorMessage.value = '';

  try {
    // Always use /api path - Vite proxy (dev) or nginx (prod) will route it correctly
    const response = await fetch('/api/auth/register-driver', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: form.name,
        phone: form.phone,
        email: form.email || undefined,
        password: form.password,
        license_number: form.licenseNumber || undefined,
        vehicle_type: form.vehicleType || undefined,
        vehicle_plate: form.licensePlate || undefined,
        vehicle_model: form.vehicleModel || undefined
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    emit('success');
  } catch (error: any) {
    errorMessage.value = error.message || t('login.registrationFailed');
  } finally {
    isSubmitting.value = false;
  }
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
  z-index: 1000;
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

.modal-form {
  padding: var(--spacing-xl);
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
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-dark);
}

.form-group input,
.form-group select {
  width: 100%;
  padding: var(--spacing-md);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-md);
  font-family: var(--font-family-base);
  transition: border-color var(--transition-base);
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(251, 110, 1, 0.2);
}

.form-hint {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
}

.info-message {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--color-info-light, #e3f2fd);
  border-left: 3px solid var(--color-info, #2196f3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.info-icon {
  font-size: var(--font-size-lg);
}

.error-message {
  padding: var(--spacing-md);
  background: var(--color-error-light, #fee);
  border-left: 3px solid var(--color-error, #d32f2f);
  border-radius: var(--radius-sm);
  color: var(--color-error);
  font-size: var(--font-size-sm);
}

.modal-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
  padding-top: var(--spacing-md);
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

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  .modal-form {
    padding: var(--spacing-lg);
  }

  .modal-actions {
    flex-direction: column;
  }

  .modal-actions button {
    width: 100%;
  }
}
</style>
