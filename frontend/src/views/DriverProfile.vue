<template>
  <section class="profile">
    <header class="profile__header">
      <div>
        <h2>{{ $t('profile.title') }}</h2>
        <p>{{ $t('profile.description') }}</p>
      </div>
      <RouterLink class="profile__back" to="/">{{ $t('common.back') }}</RouterLink>
    </header>

    <div v-if="isLoading" class="profile__loading">
      {{ $t('common.loading') }}
    </div>

    <div v-else-if="errorMessage" class="profile__error">
      {{ errorMessage }}
    </div>

    <form v-else @submit.prevent="handleSubmit" class="profile__form">
      <!-- Read-only info section -->
      <div class="profile__section">
        <h3>{{ $t('profile.accountInfo') }}</h3>
        <div class="profile__readonly">
          <div class="profile__field">
            <label>{{ $t('admin.drivers.phone') }}</label>
            <span class="profile__value">{{ profile.phone }}</span>
          </div>
          <div class="profile__field">
            <label>{{ $t('profile.rating') }}</label>
            <span class="profile__value">{{ profile.rating }} / 5.00</span>
          </div>
          <div class="profile__field">
            <label>{{ $t('profile.totalDeliveries') }}</label>
            <span class="profile__value">{{ profile.total_deliveries }}</span>
          </div>
          <div class="profile__field">
            <label>{{ $t('profile.memberSince') }}</label>
            <span class="profile__value">{{ formatDate(profile.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Editable personal info section -->
      <div class="profile__section">
        <h3>{{ $t('profile.personalInfo') }}</h3>
        <div class="profile__grid">
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
            <label>{{ $t('admin.drivers.email') }}</label>
            <input
              v-model="form.email"
              type="email"
              :placeholder="$t('admin.drivers.emailPlaceholder')"
            />
          </div>

          <div class="form-group">
            <label>{{ $t('admin.drivers.licenseNumber') }}</label>
            <input
              v-model="form.license_number"
              type="text"
              :placeholder="$t('admin.drivers.licenseNumberPlaceholder')"
            />
          </div>
        </div>
      </div>

      <!-- Editable vehicle info section -->
      <div class="profile__section">
        <h3>{{ $t('profile.vehicleInfo') }}</h3>
        <div class="profile__grid">
          <div class="form-group">
            <label>{{ $t('admin.drivers.vehicleType') }}</label>
            <select v-model="form.vehicle_type">
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
              v-model="form.vehicle_plate"
              type="text"
              :placeholder="$t('admin.drivers.licensePlatePlaceholder')"
            />
          </div>

          <div class="form-group">
            <label>{{ $t('admin.drivers.vehicleModel') }}</label>
            <input
              v-model="form.vehicle_model"
              type="text"
              :placeholder="$t('admin.drivers.vehicleModelPlaceholder')"
            />
          </div>
        </div>
      </div>

      <div v-if="submitError" class="error-message">
        {{ submitError }}
      </div>

      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>

      <div class="profile__actions">
        <button type="submit" class="btn-primary" :disabled="isSubmitting">
          {{ isSubmitting ? $t('common.loading') : $t('common.save') }}
        </button>
      </div>
    </form>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

interface DriverProfile {
  id: number;
  name: string;
  phone: string;
  email: string | null;
  license_number: string | null;
  vehicle_type: string | null;
  vehicle_plate: string | null;
  vehicle_model: string | null;
  status: number;
  rating: string;
  total_deliveries: number;
  created_at: string | null;
}

const isLoading = ref(true);
const errorMessage = ref('');
const submitError = ref('');
const successMessage = ref('');
const isSubmitting = ref(false);

const profile = ref<DriverProfile>({
  id: 0,
  name: '',
  phone: '',
  email: null,
  license_number: null,
  vehicle_type: null,
  vehicle_plate: null,
  vehicle_model: null,
  status: 0,
  rating: '5.00',
  total_deliveries: 0,
  created_at: null
});

const form = reactive({
  name: '',
  email: '',
  license_number: '',
  vehicle_type: '',
  vehicle_plate: '',
  vehicle_model: ''
});

const formatDate = (dateString: string | null): string => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

const fetchProfile = async () => {
  isLoading.value = true;
  errorMessage.value = '';

  try {
    const token = localStorage.getItem('delivery_token');
    const response = await fetch('/api/driver/profile', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch profile');
    }

    const data = await response.json();
    profile.value = data;

    // Populate form with current values
    form.name = data.name || '';
    form.email = data.email || '';
    form.license_number = data.license_number || '';
    form.vehicle_type = data.vehicle_type || '';
    form.vehicle_plate = data.vehicle_plate || '';
    form.vehicle_model = data.vehicle_model || '';
  } catch (error: any) {
    errorMessage.value = error.message || t('errors.unknownError');
  } finally {
    isLoading.value = false;
  }
};

const handleSubmit = async () => {
  isSubmitting.value = true;
  submitError.value = '';
  successMessage.value = '';

  try {
    const token = localStorage.getItem('delivery_token');
    const response = await fetch('/api/driver/profile', {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: form.name || undefined,
        email: form.email || undefined,
        license_number: form.license_number || undefined,
        vehicle_type: form.vehicle_type || undefined,
        vehicle_plate: form.vehicle_plate || undefined,
        vehicle_model: form.vehicle_model || undefined
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update profile');
    }

    const data = await response.json();
    profile.value = data;
    successMessage.value = t('profile.updateSuccess');

    // Clear success message after 3 seconds
    setTimeout(() => {
      successMessage.value = '';
    }, 3000);
  } catch (error: any) {
    submitError.value = error.message || t('errors.unknownError');
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(() => {
  fetchProfile();
});
</script>

<style scoped>
.profile {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  max-width: 800px;
  margin: 0 auto;
}

.profile__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-white);
  padding: var(--spacing-lg) var(--spacing-xl);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.profile__header h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-dark);
  margin: 0 0 var(--spacing-xs) 0;
}

.profile__header p {
  font-size: var(--font-size-md);
  color: var(--color-text-secondary);
  margin: 0;
}

.profile__back {
  background: var(--color-white);
  color: var(--color-primary);
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-full);
  text-decoration: none;
  font-weight: var(--font-weight-semibold);
  border: 1px solid var(--color-primary);
  transition: all var(--transition-base);
}

.profile__back:hover {
  background: var(--color-primary);
  color: var(--color-white);
}

.profile__loading,
.profile__error {
  background: var(--color-white);
  padding: var(--spacing-xl);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  text-align: center;
}

.profile__error {
  color: var(--color-error);
}

.profile__form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.profile__section {
  background: var(--color-white);
  padding: var(--spacing-xl);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.profile__section h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-dark);
  margin: 0 0 var(--spacing-lg) 0;
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-gray-lighter);
}

.profile__readonly {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--spacing-lg);
}

.profile__field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.profile__field label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.profile__value {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.profile__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
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

.error-message {
  padding: var(--spacing-md);
  background: var(--color-error-light, #fee);
  border-left: 3px solid var(--color-error, #d32f2f);
  border-radius: var(--radius-sm);
  color: var(--color-error);
  font-size: var(--font-size-sm);
}

.success-message {
  padding: var(--spacing-md);
  background: var(--color-success-light, #e8f5e9);
  border-left: 3px solid var(--color-success, #4caf50);
  border-radius: var(--radius-sm);
  color: var(--color-success);
  font-size: var(--font-size-sm);
}

.profile__actions {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-lg);
  background: var(--color-white);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.btn-primary {
  padding: var(--spacing-md) var(--spacing-xl);
  border-radius: var(--radius-full);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  border: none;
  background: var(--color-primary);
  color: var(--color-white);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .profile__header {
    flex-direction: column;
    gap: var(--spacing-md);
    text-align: center;
  }

  .profile__section {
    padding: var(--spacing-lg);
  }

  .profile__readonly {
    grid-template-columns: repeat(2, 1fr);
  }

  .profile__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .profile__readonly {
    grid-template-columns: 1fr;
  }
}
</style>
