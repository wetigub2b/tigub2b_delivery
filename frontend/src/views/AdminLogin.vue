<template>
  <div class="admin-login">
    <div class="login-container">
      <div class="login-header">
        <h1>{{ $t('admin.title') }}</h1>
        <p>{{ $t('admin.subtitle') }}</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">{{ $t('admin.username') }}</label>
          <input
            id="username"
            v-model="credentials.username"
            type="text"
            required
            :placeholder="$t('admin.usernamePlaceholder')"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="password">{{ $t('admin.password') }}</label>
          <input
            id="password"
            v-model="credentials.password"
            type="password"
            required
            :placeholder="$t('admin.passwordPlaceholder')"
            :disabled="isLoading"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button
          type="submit"
          class="login-button"
          :disabled="isLoading || !credentials.username || !credentials.password"
        >
          <span v-if="isLoading">{{ $t('admin.loggingIn') }}</span>
          <span v-else>{{ $t('admin.login') }}</span>
        </button>
      </form>

      <div class="login-footer">
        <router-link to="/login" class="back-link">
          ← {{ $t('admin.backToDriverLogin') }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAdminStore } from '@/store/admin';
import { useI18n } from '@/composables/useI18n';

const { t } = useI18n();
const router = useRouter();
const adminStore = useAdminStore();

const credentials = reactive({
  username: '',
  password: ''
});

const isLoading = ref(false);
const error = ref('');

const handleLogin = async () => {
  if (!credentials.username || !credentials.password) return;

  isLoading.value = true;
  error.value = '';

  try {
    await adminStore.login(credentials);
    router.push('/admin/dashboard');
  } catch (err: any) {
    error.value = err.response?.data?.detail || t('admin.loginError');
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.admin-login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-light);
  padding: var(--spacing-lg);
}

.login-container {
  background: var(--color-white);
  border-radius: var(--radius-md);
  padding: var(--spacing-3xl);
  box-shadow: var(--shadow-md);
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: var(--spacing-2xl);
}

.login-header h1 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-dark);
  margin-bottom: var(--spacing-sm);
}

.login-header p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-md);
}

.login-form {
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
  color: var(--color-gray-dark);
  font-size: var(--font-size-sm);
}

.form-group input {
  padding: var(--spacing-md);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-md);
  font-family: var(--font-family-base);
  transition: border-color var(--transition-base);
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(251, 110, 1, 0.2);
}

.form-group input:disabled {
  background-color: var(--color-bg-lighter);
  cursor: not-allowed;
}

.error-message {
  color: var(--color-error);
  font-size: var(--font-size-sm);
  text-align: center;
  padding: var(--spacing-md);
  background-color: #fed7d7;
  border-radius: var(--radius-sm);
  border: 1px solid #feb2b2;
}

.login-button {
  background: var(--color-primary);
  color: var(--color-white);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-full);
  padding: var(--spacing-md) var(--spacing-xl);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  font-family: var(--font-family-base);
  cursor: pointer;
  transition: all var(--transition-base);
}

.login-button:hover:not(:disabled) {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

.login-button:active:not(:disabled) {
  transform: translateY(1px);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-footer {
  margin-top: var(--spacing-2xl);
  text-align: center;
}

.back-link {
  color: var(--color-primary);
  text-decoration: none;
  font-size: var(--font-size-sm);
  transition: color var(--transition-base);
}

.back-link:hover {
  color: var(--color-primary-dark);
  text-decoration: underline;
}

@media (max-width: 480px) {
  .login-container {
    padding: var(--spacing-xl);
  }

  .login-header h1 {
    font-size: var(--font-size-xl);
  }
}
</style>