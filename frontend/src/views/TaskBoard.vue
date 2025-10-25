<template>
  <section class="board">
    <header class="board__header">
      <div>
        <h2>{{ $t('taskBoard.assignments') }}</h2>
        <p>{{ $t('taskBoard.description') }}</p>
      </div>
      <RouterLink class="board__route" to="/route-planner">{{ $t('taskBoard.openRoutePlanner') }}</RouterLink>
    </header>

    <nav class="board__filters">
      <button
        v-for="status in statuses"
        :key="status.key"
        :class="['board__filter', { 'board__filter--active': status.key === activeStatus }]"
        @click="activeStatus = status.key"
      >
        {{ status.label }}
      </button>
    </nav>

    <section class="board__list" v-if="filteredOrders.length">
      <OrderCard
        v-for="order in filteredOrders"
        :key="order.orderSn"
        :order="order"
        @status-update="updateStatus"
      />
    </section>

    <EmptyState v-else :message="$t('taskBoard.noTasks')" />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useOrdersStore } from '@/store/orders';
import OrderCard from '@/components/OrderCard.vue';
import EmptyState from '@/components/EmptyState.vue';

const { t } = useI18n();
const ordersStore = useOrdersStore();
const activeStatus = ref('pending_pickup');

const statuses = computed(() => [
  { key: 'pending_pickup', label: t('taskBoard.pendingPickup') },
  { key: 'in_transit', label: t('taskBoard.inTransit') },
  { key: 'completed', label: t('taskBoard.completed') }
]);

onMounted(() => {
  ordersStore.fetchAssignedOrders();
});

const filteredOrders = computed(() => ordersStore.byWorkflowState(activeStatus.value));

function updateStatus(payload: { orderSn: string; shippingStatus: number }) {
  ordersStore.patchOrderStatus(payload);
}
</script>

<style scoped>
.board {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.board__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-white);
  padding: var(--spacing-lg) var(--spacing-xl);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.board__route {
  background: var(--color-primary);
  color: var(--color-white);
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-full);
  text-decoration: none;
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-base);
}

.board__route:hover {
  background: var(--color-primary-dark);
  color: var(--color-white);
}

.board__filters {
  display: flex;
  gap: var(--spacing-sm);
}

.board__filter {
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-full);
  border: 1px solid var(--color-gray-light);
  background: var(--color-white);
  cursor: pointer;
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
  color: var(--color-text-primary);
}

.board__filter:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.board__filter--active {
  background: var(--color-primary);
  color: var(--color-white);
  border-color: var(--color-primary);
}

.board__list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--spacing-lg);
}
</style>
