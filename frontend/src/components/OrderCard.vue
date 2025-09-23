<template>
  <article class="card">
    <header class="card__header">
      <div>
        <h3>{{ order.orderSn }}</h3>
        <p>{{ order.receiverName }} · {{ order.receiverCity }}</p>
      </div>
      <span class="card__badge">{{ order.shippingStatusLabel }}</span>
    </header>

    <section class="card__body">
      <p><strong>{{ $t('orderCard.pickup') }}</strong> {{ order.pickupLocation?.name }}</p>
      <p><strong>{{ $t('orderCard.dropOff') }}</strong> {{ order.receiverAddress }}</p>
      <p><strong>{{ $t('orderCard.items') }}</strong> {{ order.items.length }}</p>
    </section>

    <footer class="card__footer">
      <RouterLink :to="`/orders/${order.orderSn}`" class="card__link">{{ $t('orderCard.openDetails') }}</RouterLink>
      <div class="card__actions">
        <button @click="emitStatus(1)" class="card__button">{{ $t('orderCard.pickedUp') }}</button>
        <button @click="emitStatus(3)" class="card__button card__button--primary">{{ $t('orderCard.delivered') }}</button>
      </div>
    </footer>
  </article>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';
import type { DeliveryOrder } from '@/store/orders';

const props = defineProps<{ order: DeliveryOrder }>();
const emit = defineEmits(['status-update']);

function emitStatus(shippingStatus: number) {
  emit('status-update', { orderSn: props.order.orderSn, shippingStatus });
}
</script>

<style scoped>
.card {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

.card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card__badge {
  background: #2563eb;
  color: #ffffff;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 14px;
}

.card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card__link {
  color: #2563eb;
  text-decoration: none;
}

.card__actions {
  display: flex;
  gap: 8px;
}

.card__button {
  border: 1px solid #cbd5f5;
  background: #ffffff;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
}

.card__button--primary {
  background: #2563eb;
  color: #ffffff;
  border: none;
}
</style>
