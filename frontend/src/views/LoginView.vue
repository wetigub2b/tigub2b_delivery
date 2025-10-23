<template>
  <div class="login">
    <form class="login__form" @submit.prevent="submit">
      <h2>{{ $t('login.title') }}</h2>
      <label>
        {{ $t('login.phoneNumber') }}
        <input v-model="form.phone" placeholder="+1 555 123 4567" required />
      </label>
      <label>
        {{ $t('login.oneTimeCode') }}
        <input v-model="form.code" placeholder="123456" required />
      </label>
      <button type="submit">{{ $t('login.signIn') }}</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useOrdersStore } from '@/store/orders';

const router = useRouter();
const ordersStore = useOrdersStore();

const form = reactive({ phone: '', code: '' });

async function submit() {
  await ordersStore.login(form.phone, form.code);
  router.push('/');
}
</script>

<style scoped>
.login {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 160px);
  background: var(--color-bg-light);
}

.login__form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  padding: var(--spacing-3xl);
  background: var(--color-white);
  border-radius: var(--radius-md);
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-md);
}

.login__form h2 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-dark);
  text-align: center;
  margin-bottom: var(--spacing-md);
}

.login__form label {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-dark);
}

.login__form button {
  background: var(--color-primary);
  border: 1px solid var(--color-primary);
  color: var(--color-white);
  padding: var(--spacing-md) var(--spacing-xl);
  border-radius: var(--radius-full);
  cursor: pointer;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  font-family: var(--font-family-base);
  transition: all var(--transition-base);
  margin-top: var(--spacing-md);
}

.login__form button:hover {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

.login__form button:active {
  transform: translateY(1px);
}

.login__form input {
  width: 100%;
  padding: var(--spacing-md);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-md);
  font-family: var(--font-family-base);
  transition: border-color var(--transition-base);
}

.login__form input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(251, 110, 1, 0.2);
}

.login__form input::placeholder {
  color: var(--color-text-light);
}

@media (max-width: 480px) {
  .login__form {
    padding: var(--spacing-xl);
    margin: var(--spacing-lg);
  }

  .login__form h2 {
    font-size: var(--font-size-xl);
  }
}
</style>
