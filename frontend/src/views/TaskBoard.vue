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
            <div class="package-info-row package-info-row--with-action">
              <span>📦 {{ pkg.orderCount }} {{ t('taskBoard.orders') }}</span>
              <button class="detail-button" @click="openOrdersModal(pkg)">
                {{ $t('packageModal.viewDetails') }}
              </button>
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

    <!-- Package Orders Modal -->
    <PackageOrdersModal
      v-if="selectedPackage"
      :show="showOrdersModal"
      :package-sn="selectedPackage.prepareSn"
      :order-count="selectedPackage.orderCount"
      @close="closeOrdersModal"
    />

    <!-- Confirm Pickup Modal -->
    <ConfirmPackagePickupModal
      v-if="packageToPickup"
      :show="showPickupModal"
      :package-data="{
        prepareSn: packageToPickup.prepareSn,
        orderCount: packageToPickup.orderCount,
        workflowLabel: packageToPickup.workflowLabel,
        warehouseName: packageToPickup.warehouseName
      }"
      :is-processing="isPickingUp"
      @confirm="confirmPickup"
      @cancel="cancelPickup"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { usePrepareGoodsStore } from '@/store/prepareGoods';
import EmptyState from '@/components/EmptyState.vue';
import PackageOrdersModal from '@/components/PackageOrdersModal.vue';
import ConfirmPackagePickupModal from '@/components/ConfirmPackagePickupModal.vue';

const { t } = useI18n();
const prepareGoodsStore = usePrepareGoodsStore();
const activeStatus = ref('available');

// Modal state
const showOrdersModal = ref(false);
const selectedPackage = ref<{ prepareSn: string; orderCount: number } | null>(null);

// Pickup confirmation modal state
const showPickupModal = ref(false);
const packageToPickup = ref<any>(null);
const isPickingUp = ref(false);

const statuses = computed(() => [
  { key: 'available', label: t('taskBoard.available'), prepareStatus: 0 },
  { key: 'pending_pickup', label: t('taskBoard.pendingPickup'), prepareStatus: 1 },
  { key: 'in_transit', label: t('taskBoard.inTransit'), prepareStatus: [2, 3, 4, 5] },
  { key: 'completed', label: t('taskBoard.completed'), prepareStatus: 6 }
]);

onMounted(() => {
  // Fetch both available (unassigned) and driver's assigned packages
  prepareGoodsStore.fetchAvailablePackages();
  prepareGoodsStore.fetchMyDriverPackages();
});

// Filter packages by prepare_status based on active tab
const filteredPackages = computed(() => {
  const currentTab = statuses.value.find(s => s.key === activeStatus.value);
  if (!currentTab) return [];

  // For "Available" tab, use availablePackages (unassigned)
  // For other tabs, use driverPackages (assigned to this driver)
  const allPackages = currentTab.key === 'available'
    ? prepareGoodsStore.availablePackages
    : prepareGoodsStore.driverPackages;

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
  if (status === 1) return t('taskBoard.confirmPickupButton');
  if (status === 2) return t('taskBoard.confirmWarehouseDelivery');
  return t('taskBoard.viewDetails');
}

function handlePackageAction(pkg: any) {
  if (pkg.prepareStatus === null || pkg.prepareStatus === 0) {
    // Available package - show pickup confirmation modal
    packageToPickup.value = pkg;
    showPickupModal.value = true;
  } else {
    // For other statuses, show detail view (to be implemented)
    console.log('Package action:', pkg.prepareSn, 'Status:', pkg.prepareStatus);
    alert(`Package: ${pkg.prepareSn}\nStatus: ${pkg.prepareStatusLabel}\n\nDetail view to be implemented.`);
  }
}

async function confirmPickup() {
  if (!packageToPickup.value) return;

  isPickingUp.value = true;
  try {
    await prepareGoodsStore.pickupPackage(packageToPickup.value.prepareSn);
    // Refresh available packages
    await prepareGoodsStore.fetchAvailablePackages();
    // Close modal
    showPickupModal.value = false;
    packageToPickup.value = null;
  } catch (error: any) {
    alert(`Error: ${error.response?.data?.detail || error.message}`);
  } finally {
    isPickingUp.value = false;
  }
}

function cancelPickup() {
  showPickupModal.value = false;
  packageToPickup.value = null;
}

function openOrdersModal(pkg: any) {
  selectedPackage.value = {
    prepareSn: pkg.prepareSn,
    orderCount: pkg.orderCount
  };
  showOrdersModal.value = true;
}

function closeOrdersModal() {
  showOrdersModal.value = false;
  selectedPackage.value = null;
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
  gap: var(--spacing-lg);
}

.prepare-package-card {
  background: var(--color-white);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.prepare-package-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--color-primary);
}

.package-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-gray-light);
}

.package-sn {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  font-size: 0.875rem;
}

.package-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: var(--font-weight-medium);
}

.status-0 {
  background: var(--color-warning);
  color: var(--color-white);
}

.status-1,
.status-2 {
  background: var(--color-info);
  color: var(--color-white);
}

.package-body {
  margin-bottom: var(--spacing-md);
}

.package-info-row {
  padding: var(--spacing-xs) 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.package-info-row--with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-sm);
}

.detail-button {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-white);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
  white-space: nowrap;
}

.detail-button:hover {
  background: var(--color-primary);
  color: var(--color-white);
}

.package-footer {
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-gray-light);
}

.package-action-button {
  width: 100%;
  padding: 0.5rem;
  background: var(--color-primary);
  color: var(--color-white);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  font-size: 0.875rem;
}

.package-action-button:hover {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}
</style>
