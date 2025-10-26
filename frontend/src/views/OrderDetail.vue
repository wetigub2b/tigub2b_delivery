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
        <li v-for="item in order?.items" :key="item.skuId" class="detail__item">
          <img
            v-if="item.skuImage"
            :src="item.skuImage"
            :alt="item.productName"
            class="detail__item-image"
          />
          <div v-else class="detail__item-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" viewBox="0 0 16 16">
              <path d="M6.002 5.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/>
              <path d="M2.002 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2h-12zm12 1a1 1 0 0 1 1 1v6.5l-3.777-1.947a.5.5 0 0 0-.577.093l-3.71 3.71-2.66-1.772a.5.5 0 0 0-.63.062L1.002 12V3a1 1 0 0 1 1-1h12z"/>
            </svg>
          </div>
          <div class="detail__item-info">
            <strong>{{ item.productName }}</strong>
            <span>SKU: {{ item.skuCode }}</span>
            <span>Qty: {{ item.quantity }}</span>
          </div>
        </li>
      </ul>
    </section>

    <section v-if="order?.deliveryProof" class="detail__card">
      <h3>{{ $t('orderDetail.deliveryProof') }}</h3>
      <div class="detail__proof">
        <img
          :src="order.deliveryProof.photoUrl"
          alt="Delivery Proof"
          class="detail__proof-image"
        />
        <div v-if="order.deliveryProof.notes" class="detail__proof-notes">
          <strong>{{ $t('orderDetail.notes') }}:</strong>
          <p>{{ order.deliveryProof.notes }}</p>
        </div>
        <div class="detail__proof-date">
          <small>{{ $t('orderDetail.deliveredAt') }}: {{ new Date(order.deliveryProof.createdAt).toLocaleString() }}</small>
        </div>
      </div>
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

.detail__item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
  padding: 12px;
  border-radius: 8px;
  background: #f8fafc;
}

.detail__item-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
  border: 1px solid #e2e8f0;
}

.detail__item-placeholder {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e2e8f0;
  border-radius: 8px;
  flex-shrink: 0;
  color: #94a3b8;
}

.detail__item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.detail__item-info strong {
  font-size: 16px;
  color: #1f2937;
}

.detail__item-info span {
  font-size: 14px;
  color: #6b7280;
}

.detail__proof {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail__proof-image {
  width: 100%;
  max-width: 500px;
  height: auto;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  object-fit: contain;
}

.detail__proof-notes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.detail__proof-notes strong {
  font-size: 14px;
  color: #1f2937;
}

.detail__proof-notes p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.detail__proof-date {
  color: #6b7280;
  font-size: 13px;
}
</style>
