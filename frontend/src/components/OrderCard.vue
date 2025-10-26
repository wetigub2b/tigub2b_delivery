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
        <button @click="showProofModal = true" class="card__button card__button--primary">{{ $t('orderCard.delivered') }}</button>
      </div>
    </footer>

    <DeliveryProofModal
      :show="showProofModal"
      :order="order"
      @submit="handleProofSubmit"
      @cancel="showProofModal = false"
    />
  </article>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOrdersStore } from '@/store/orders';
import type { DeliveryOrder } from '@/store/orders';
import DeliveryProofModal from './DeliveryProofModal.vue';

const props = defineProps<{ order: DeliveryOrder }>();
const emit = defineEmits(['status-update']);

const { t } = useI18n();
const ordersStore = useOrdersStore();
const showProofModal = ref(false);

function emitStatus(shippingStatus: number) {
  emit('status-update', { orderSn: props.order.orderSn, shippingStatus });
}

async function handleProofSubmit(photo: string, notes: string) {
  try {
    await ordersStore.uploadDeliveryProof(props.order.orderSn, photo, notes);
    showProofModal.value = false;
    alert(t('orderCard.deliverySuccess'));
  } catch (error) {
    console.error('Failed to upload delivery proof:', error);
    alert(t('orderCard.deliveryError'));
  }
}
</script>

<style scoped>
.card {
  background: var(--color-white);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  box-shadow: var(--shadow-md);
  transition: box-shadow var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-lg);
}

.card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-md);
}

.card__header h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-dark);
  margin-bottom: var(--spacing-xs);
}

.card__header p {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.card__badge {
  background: var(--color-primary);
  color: var(--color-white);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
}

.card__body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.card__body p {
  font-size: var(--font-size-md);
  color: var(--color-text-primary);
  line-height: var(--line-height-base);
}

.card__body strong {
  color: var(--color-gray-dark);
  font-weight: var(--font-weight-semibold);
}

.card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-gray-lighter);
  gap: var(--spacing-md);
}

.card__link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-md);
  transition: color var(--transition-base);
}

.card__link:hover {
  color: var(--color-primary-dark);
  text-decoration: underline;
}

.card__actions {
  display: flex;
  gap: var(--spacing-sm);
}

.card__button {
  border: 1px solid var(--color-gray-light);
  background: var(--color-white);
  color: var(--color-black);
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-full);
  cursor: pointer;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
  white-space: nowrap;
}

.card__button:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.card__button--primary {
  background: var(--color-primary);
  color: var(--color-white);
  border: 1px solid var(--color-primary);
}

.card__button--primary:hover {
  background: var(--color-primary-dark);
  color: var(--color-white);
  border-color: var(--color-primary-dark);
}

@media (max-width: 768px) {
  .card__footer {
    flex-direction: column;
    align-items: stretch;
  }

  .card__actions {
    width: 100%;
  }

  .card__button {
    flex: 1;
    justify-content: center;
  }
}
</style>
