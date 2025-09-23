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
  gap: 16px;
}

.board__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

.board__route {
  background: #2563eb;
  color: #ffffff;
  padding: 10px 16px;
  border-radius: 8px;
  text-decoration: none;
}

.board__filters {
  display: flex;
  gap: 8px;
}

.board__filter {
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid #cbd5f5;
  background: #ffffff;
  cursor: pointer;
}

.board__filter--active {
  background: #2563eb;
  color: #ffffff;
}

.board__list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}
</style>
