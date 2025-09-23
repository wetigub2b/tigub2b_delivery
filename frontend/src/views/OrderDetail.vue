<template>
  <article class="detail">
    <RouterLink class="detail__back" to="/">{{ $t('orderDetail.backToAssignments') }}</RouterLink>

    <header class="detail__header">
      <h2>{{ $t('orderDetail.order') }} {{ order?.orderSn }}</h2>
      <p>{{ $t('orderDetail.customer') }}: {{ order?.receiverName }} · {{ order?.receiverPhone }}</p>
    </header>

    <section class="detail__grid">
      <div class="detail__card">
        <h3>{{ $t('orderDetail.pickup') }}</h3>
        <p>{{ order?.pickupLocation?.name }}</p>
        <p>{{ order?.pickupLocation?.address }}</p>
      </div>
      <div class="detail__card">
        <h3>{{ $t('orderDetail.dropOff') }}</h3>
        <p>{{ order?.receiverAddress }}</p>
        <p>{{ order?.receiverCity }}, {{ order?.receiverProvince }} {{ order?.receiverPostalCode }}</p>
      </div>
      <div class="detail__card">
        <h3>{{ $t('orderDetail.status') }}</h3>
        <p>{{ order?.shippingStatusLabel }}</p>
        <p>{{ order?.orderStatusLabel }}</p>
      </div>
    </section>

    <section class="detail__card">
      <h3>{{ $t('orderDetail.items') }}</h3>
      <ul>
        <li v-for="item in order?.items" :key="item.skuId">
          <strong>{{ item.productName }}</strong>
          <span>SKU: {{ item.skuCode }}</span>
          <span>Qty: {{ item.quantity }}</span>
        </li>
      </ul>
    </section>

    <section class="detail__actions">
      <button @click="markShipped" class="detail__button detail__button--primary">{{ $t('orderDetail.markPickedUp') }}</button>
      <button @click="markDelivered" class="detail__button detail__button--success">{{ $t('orderDetail.markDelivered') }}</button>
      <button @click="reportIssue" class="detail__button detail__button--ghost">{{ $t('orderDetail.reportIssue') }}</button>
    </section>
  </article>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { useOrdersStore } from '@/store/orders';

const route = useRoute();
const ordersStore = useOrdersStore();
const orderSn = String(route.params.orderSn);

onMounted(() => {
  ordersStore.fetchOrderDetail(orderSn);
});

const order = computed(() => ordersStore.activeBySn(orderSn));

function markShipped() {
  ordersStore.updateShippingStatus(orderSn, 1);
}

function markDelivered() {
  ordersStore.updateShippingStatus(orderSn, 3);
}

function reportIssue() {
  // placeholder for future modal integration
  console.warn('Report issue for order', orderSn);
}
</script>

<style scoped>
.detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail__back {
  color: #2563eb;
  text-decoration: none;
}

.detail__header {
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

.detail__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.detail__card {
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

.detail__card ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 12px;
}

.detail__card li {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.detail__button {
  border: none;
  padding: 12px 18px;
  border-radius: 8px;
  cursor: pointer;
}

.detail__button--primary {
  background: #2563eb;
  color: #ffffff;
}

.detail__button--success {
  background: #16a34a;
  color: #ffffff;
}

.detail__button--ghost {
  background: transparent;
  color: #1f2937;
  border: 1px solid #cbd5f5;
}
</style>
