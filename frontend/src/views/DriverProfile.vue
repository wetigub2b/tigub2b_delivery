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

      <!-- Payment Setup Section -->
      <div class="profile__section profile__payment">
        <h3>{{ $t('profile.paymentSetup') }}</h3>
        <div class="payment-status">
          <div class="payment-status__indicator">
            <span class="payment-status__badge" :class="paymentStatusClass">
              {{ paymentStatusIcon }} {{ paymentStatusText }}
            </span>
          </div>
          <p class="payment-status__description">{{ paymentStatusDescription }}</p>
        </div>

        <div v-if="stripeError" class="error-message">
          {{ stripeError }}
        </div>

        <div class="payment-actions">
          <!-- Not connected - show Connect button -->
          <button
            v-if="profile.stripe_status === 'pending' || !profile.stripe_status"
            @click="initiateStripeConnect"
            class="btn-stripe"
            :disabled="isConnectingStripe"
          >
            {{ isConnectingStripe ? $t('common.loading') : $t('profile.connectBankAccount') }}
          </button>

          <!-- Onboarding in progress - show Continue button -->
          <button
            v-else-if="profile.stripe_status === 'onboarding'"
            @click="continueStripeSetup"
            class="btn-stripe btn-stripe--continue"
            :disabled="isConnectingStripe"
          >
            {{ isConnectingStripe ? $t('common.loading') : $t('profile.completeSetup') }}
          </button>

          <!-- Restricted - show Update button -->
          <button
            v-else-if="profile.stripe_status === 'restricted'"
            @click="continueStripeSetup"
            class="btn-stripe btn-stripe--warning"
            :disabled="isConnectingStripe"
          >
            {{ isConnectingStripe ? $t('common.loading') : $t('profile.updatePaymentInfo') }}
          </button>

          <!-- Verified - show connected info -->
          <div v-else-if="profile.stripe_status === 'verified'" class="payment-connected">
            <span class="payment-connected__text">{{ $t('profile.paymentConnectedSince') }}</span>
            <span class="payment-connected__date">{{ formatDate(profile.stripe_connected_at) }}</span>
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
import { computed, onMounted, reactive, ref } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const route = useRoute();

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
  stripe_status: string | null;
  stripe_payouts_enabled: boolean;
  stripe_details_submitted: boolean;
  stripe_connected_at: string | null;
}

const isLoading = ref(true);
const errorMessage = ref('');
const submitError = ref('');
const successMessage = ref('');
const isSubmitting = ref(false);
const isConnectingStripe = ref(false);
const stripeError = ref('');

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
  created_at: null,
  stripe_status: null,
  stripe_payouts_enabled: false,
  stripe_details_submitted: false,
  stripe_connected_at: null
});

// Computed properties for payment status display
const paymentStatusClass = computed(() => {
  switch (profile.value.stripe_status) {
    case 'verified':
      return 'payment-status__badge--verified';
    case 'onboarding':
      return 'payment-status__badge--onboarding';
    case 'restricted':
      return 'payment-status__badge--restricted';
    default:
      return 'payment-status__badge--pending';
  }
});

const paymentStatusIcon = computed(() => {
  switch (profile.value.stripe_status) {
    case 'verified':
      return '\u2705'; // checkmark
    case 'onboarding':
      return '\uD83D\uDD04'; // arrows
    case 'restricted':
      return '\u26A0\uFE0F'; // warning
    default:
      return '\u274C'; // x
  }
});

const paymentStatusText = computed(() => {
  switch (profile.value.stripe_status) {
    case 'verified':
      return t('profile.paymentStatus.verified');
    case 'onboarding':
      return t('profile.paymentStatus.onboarding');
    case 'restricted':
      return t('profile.paymentStatus.restricted');
    default:
      return t('profile.paymentStatus.pending');
  }
});

const paymentStatusDescription = computed(() => {
  switch (profile.value.stripe_status) {
    case 'verified':
      return t('profile.paymentDescription.verified');
    case 'onboarding':
      return t('profile.paymentDescription.onboarding');
    case 'restricted':
      return t('profile.paymentDescription.restricted');
    default:
      return t('profile.paymentDescription.pending');
  }
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

// Stripe Connect methods
const initiateStripeConnect = async () => {
  isConnectingStripe.value = true;
  stripeError.value = '';

  try {
    const token = localStorage.getItem('delivery_token');
    const response = await fetch('/api/driver/stripe/connect', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to initiate payment setup');
    }

    const data = await response.json();

    // Redirect to Stripe onboarding
    window.location.href = data.onboarding_url;

  } catch (error: any) {
    stripeError.value = error.message || t('errors.unknownError');
  } finally {
    isConnectingStripe.value = false;
  }
};

const continueStripeSetup = async () => {
  isConnectingStripe.value = true;
  stripeError.value = '';

  try {
    const token = localStorage.getItem('delivery_token');
    const response = await fetch('/api/driver/stripe/refresh-link', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get setup link');
    }

    const data = await response.json();

    // Redirect to Stripe onboarding
    window.location.href = data.onboarding_url;

  } catch (error: any) {
    stripeError.value = error.message || t('errors.unknownError');
  } finally {
    isConnectingStripe.value = false;
  }
};

const checkStripeStatus = async () => {
  try {
    const token = localStorage.getItem('delivery_token');
    const response = await fetch('/api/driver/stripe/status', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.ok) {
      const data = await response.json();
      profile.value.stripe_status = data.stripe_status;
      profile.value.stripe_payouts_enabled = data.stripe_payouts_enabled;
      profile.value.stripe_details_submitted = data.stripe_details_submitted;
      profile.value.stripe_connected_at = data.stripe_connected_at;
    }
  } catch (error) {
    console.error('Failed to check Stripe status:', error);
  }
};

onMounted(async () => {
  await fetchProfile();

  // Check if returning from Stripe
  const stripeParam = route.query.stripe;
  if (stripeParam === 'complete') {
    // Refresh status after returning from Stripe
    await checkStripeStatus();
    if (profile.value.stripe_status === 'verified') {
      successMessage.value = t('profile.paymentSetupComplete');
    } else if (profile.value.stripe_status === 'onboarding') {
      successMessage.value = t('profile.paymentSetupPending');
    }
    // Clear the query param
    window.history.replaceState({}, '', '/profile');
  } else if (stripeParam === 'refresh') {
    // Link expired, show message
    stripeError.value = t('profile.stripeRefreshNeeded');
    window.history.replaceState({}, '', '/profile');
  }
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

/* Payment Section Styles */
.profile__payment {
  border: 2px solid var(--color-primary-light, #ffe0b2);
  background: linear-gradient(135deg, var(--color-white) 0%, var(--color-bg-lighter, #fafafa) 100%);
}

.payment-status {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.payment-status__indicator {
  display: flex;
  align-items: center;
}

.payment-status__badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.payment-status__badge--pending {
  background: var(--color-gray-lighter, #f5f5f5);
  color: var(--color-text-secondary);
}

.payment-status__badge--onboarding {
  background: var(--color-info-light, #e3f2fd);
  color: var(--color-info-dark, #1565c0);
}

.payment-status__badge--verified {
  background: var(--color-success-light, #e8f5e9);
  color: var(--color-success-dark, #2e7d32);
}

.payment-status__badge--restricted {
  background: var(--color-warning-light, #fff3e0);
  color: var(--color-warning-dark, #e65100);
}

.payment-status__description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
}

.payment-actions {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.btn-stripe {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md) var(--spacing-xl);
  border-radius: var(--radius-md);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  border: none;
  background: linear-gradient(135deg, #635bff 0%, #7c3aed 100%);
  color: var(--color-white);
  box-shadow: 0 2px 8px rgba(99, 91, 255, 0.3);
}

.btn-stripe:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 91, 255, 0.4);
}

.btn-stripe:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-stripe--continue {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.btn-stripe--continue:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.btn-stripe--warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.btn-stripe--warning:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

.payment-connected {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
  background: var(--color-success-light, #e8f5e9);
  border-radius: var(--radius-md);
  border-left: 4px solid var(--color-success);
}

.payment-connected__text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.payment-connected__date {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-success-dark, #2e7d32);
}
</style>
