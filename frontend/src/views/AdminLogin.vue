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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 8px;
}

.login-header p {
  color: #718096;
  font-size: 16px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #2d3748;
  font-size: 14px;
}

.form-group input {
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input:disabled {
  background-color: #f7fafc;
  cursor: not-allowed;
}

.error-message {
  color: #e53e3e;
  font-size: 14px;
  text-align: center;
  padding: 12px;
  background-color: #fed7d7;
  border-radius: 6px;
  border: 1px solid #feb2b2;
}

.login-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 14px 20px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.login-footer {
  margin-top: 30px;
  text-align: center;
}

.back-link {
  color: #667eea;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s ease;
}

.back-link:hover {
  color: #5a67d8;
  text-decoration: underline;
}

@media (max-width: 480px) {
  .login-container {
    padding: 30px 20px;
  }

  .login-header h1 {
    font-size: 24px;
  }
}
</style>