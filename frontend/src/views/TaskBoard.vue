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

    <!-- Packages List (All Tabs) -->
    <section v-if="filteredPackages.length" class="board__list">
      <div class="prepare-packages-grid">
        <div
          v-for="pkg in filteredPackages"
          :key="pkg.prepareSn"
          class="prepare-package-card"
        >
          <div class="package-header">
            <span class="package-sn">{{ pkg.prepareSn }}</span>
            <span class="package-status" :class="`status-${pkg.prepareStatus}`">
              {{ pkg.prepareStatusLabel }}
            </span>
          </div>
          <div class="package-body">
            <div class="package-info-row">
              <span>📦 {{ pkg.orderCount }} {{ t('taskBoard.orders') }}</span>
            </div>
            <div class="package-info-row">
              <span>🏷️ {{ pkg.workflowLabel }}</span>
            </div>
            <div v-if="pkg.warehouseName" class="package-info-row">
              <span>🏭 {{ pkg.warehouseName }}</span>
            </div>
          </div>
          <div class="package-footer">
            <button class="package-action-button" @click="handlePackageAction(pkg)">
              {{ getPackageActionLabel(pkg.prepareStatus) }} →
            </button>
          </div>
        </div>
      </div>
    </section>

    <EmptyState v-else :message="t('taskBoard.noPackages')" />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { usePrepareGoodsStore } from '@/store/prepareGoods';
import EmptyState from '@/components/EmptyState.vue';

const { t } = useI18n();
const prepareGoodsStore = usePrepareGoodsStore();
const activeStatus = ref('available');

const statuses = computed(() => [
  { key: 'available', label: t('taskBoard.available'), prepareStatus: 0 },
  { key: 'pending_pickup', label: t('taskBoard.pendingPickup'), prepareStatus: 1 },
  { key: 'in_transit', label: t('taskBoard.inTransit'), prepareStatus: [2, 3, 4, 5] },
  { key: 'completed', label: t('taskBoard.completed'), prepareStatus: 6 }
]);

// TODO: Get actual driver ID from auth store
const driverId = ref(1);

onMounted(() => {
  prepareGoodsStore.fetchDriverPackages(driverId.value);
});

// Filter packages by prepare_status based on active tab
const filteredPackages = computed(() => {
  const currentTab = statuses.value.find(s => s.key === activeStatus.value);
  if (!currentTab) return [];

  const allPackages = prepareGoodsStore.driverPackages;
  const targetStatus = currentTab.prepareStatus;

  if (Array.isArray(targetStatus)) {
    // In Transit - multiple statuses
    return allPackages.filter(pkg => targetStatus.includes(pkg.prepareStatus));
  } else {
    // Single status
    return allPackages.filter(pkg => pkg.prepareStatus === targetStatus);
  }
});

function getPackageActionLabel(status: number | null): string {
  if (status === null || status === 0) return t('taskBoard.pickupPackage');
  if (status === 1) return t('taskBoard.deliverToWarehouse');
  if (status === 2) return t('taskBoard.confirmWarehouseDelivery');
  return t('taskBoard.viewDetails');
}

async function handlePackageAction(pkg: any) {
  // TODO: Implement package action handling
  // For now, navigate to detail view
  console.log('Package action:', pkg.prepareSn, 'Status:', pkg.prepareStatus);
  alert(`Package: ${pkg.prepareSn}\nStatus: ${pkg.prepareStatusLabel}\n\nAction handling to be implemented.`);
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

.board__filter--active:hover {
  background: var(--color-primary-dark);
  color: var(--color-white);
  border-color: var(--color-primary-dark);
}

.board__list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--spacing-lg);
}

/* Prepare Packages Styles */
.prepare-packages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}

.prepare-package-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  transition: all 0.2s;
}

.prepare-package-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  border-color: #3b82f6;
}

.package-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.package-sn {
  font-weight: 600;
  color: #1f2937;
  font-size: 0.875rem;
}

.package-status {
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-0 {
  background: #fef3c7;
  color: #92400e;
}

.status-1,
.status-2 {
  background: #dbeafe;
  color: #1e40af;
}

.package-body {
  margin-bottom: 1rem;
}

.package-info-row {
  padding: 0.5rem 0;
  font-size: 0.875rem;
  color: #374151;
}

.package-footer {
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.package-action-button {
  width: 100%;
  padding: 0.5rem;
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #dbeafe;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.package-action-button:hover {
  background: #dbeafe;
}
</style>
