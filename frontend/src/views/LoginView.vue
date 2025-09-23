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
}

.login__form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 24px;
  background: #ffffff;
  border-radius: 12px;
  width: 320px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

button {
  background: #2563eb;
  border: none;
  color: #ffffff;
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
}

input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #cbd5f5;
  border-radius: 6px;
}
</style>
