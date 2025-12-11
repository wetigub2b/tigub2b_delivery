<template>
  <section class="board">
    <header class="board__header">
      <div>
        <h2>{{ $t('taskBoard.assignments') }}</h2>
        <p>{{ $t('taskBoard.description') }}</p>
      </div>
      <RouterLink v-if="features.routePlanner" class="board__route" to="/route-planner">{{ $t('taskBoard.openRoutePlanner') }}</RouterLink>
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

    <!-- Map Tab -->
    <MapTab v-if="activeStatus === 'map' && features.mapTab" />

    <!-- Earnings Tab -->
    <section v-if="activeStatus === 'earnings'" class="earnings-section">
      <div class="earnings-table-wrapper">
        <table class="earnings-table">
          <thead>
            <tr>
              <th>{{ $t('taskBoard.packageSN') }}</th>
              <th>{{ $t('packageModal.totalValue') }}</th>
              <th>{{ $t('taskBoard.deliveryEarning') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="pkg in earningsPackages" :key="pkg.prepareSn">
              <td class="package-sn-cell">{{ pkg.prepareSn }}</td>
              <td class="amount-cell">{{ formatAmount(pkg.totalValue || 0) }}</td>
              <td class="amount-cell earning-cell">{{ formatAmount((pkg.totalValue || 0) * 0.1) }}</td>
            </tr>
          </tbody>
          <tfoot v-if="earningsPackages.length > 0">
            <tr class="total-row">
              <td><strong>{{ $t('taskBoard.totalPackages') }}: {{ earningsPackages.length }}</strong></td>
              <td></td>
              <td class="total-earning"><strong>{{ $t('taskBoard.totalEarnings') }}: {{ formatAmount(totalEarnings) }}</strong></td>
            </tr>
          </tfoot>
        </table>
        <EmptyState v-if="earningsPackages.length === 0" :message="t('taskBoard.noPackages')" />
      </div>
    </section>

    <!-- Packages List (All Tabs) -->
    <section v-if="activeStatus !== 'map' && activeStatus !== 'earnings' && filteredPackages.length" class="board__list">
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
              <span>🏷️ {{ $t(pkg.workflowLabel) }}</span>
            </div>
            <div v-if="pkg.totalValue" class="package-info-row">
              <span>💰 {{ formatAmount(pkg.totalValue) }}</span>
            </div>
            <!-- Pickup Address -->
            <div v-if="pkg.pickupAddress" class="package-info-row package-info-row--address">
              <span class="address-label">{{ $t('taskBoard.pickupAddress') }}:</span>
              <a class="address-link" @click.stop="openAddressMap(pkg.pickupAddress, 'pickup')">📍 {{ pkg.pickupAddress }}</a>
            </div>
            <!-- Warehouse Address (for workflow Driver -> Warehouse -> User) -->
            <div v-if="pkg.shippingType === 1 && pkg.warehouseAddress" class="package-info-row package-info-row--address">
              <span class="address-label">{{ $t('taskBoard.warehouseAddress') }}:</span>
              <a class="address-link" @click.stop="openAddressMap(pkg.warehouseAddress, 'warehouse')">🏭 {{ pkg.warehouseAddress }}</a>
            </div>
            <!-- Receiver Address -->
            <div v-if="pkg.receiverAddress" class="package-info-row package-info-row--address">
              <span class="address-label">{{ $t('taskBoard.receiverAddress') }}:</span>
              <a class="address-link" @click.stop="openAddressMap(pkg.receiverAddress, 'receiver')">📍 {{ pkg.receiverAddress }}</a>
            </div>
          </div>
          <div v-if="![2, 3, 7].includes(pkg.prepareStatus)" class="package-footer">
            <button
              class="package-action-button"
              @click="handlePackageAction(pkg)"
            >
              {{ getPackageActionLabel(pkg.prepareStatus) }} →
            </button>
          </div>
        </div>
      </div>
    </section>

    <EmptyState v-else-if="activeStatus !== 'map' && activeStatus !== 'earnings'" :message="t('taskBoard.noPackages')" />

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

    <!-- Pickup Proof Modal -->
    <PickupProofModal
      v-if="packageForProof"
      :show="showPickupProofModal"
      :package-data="{
        prepareSn: packageForProof.prepareSn,
        orderCount: packageForProof.orderCount,
        workflowLabel: packageForProof.workflowLabel,
        warehouseName: packageForProof.warehouseName
      }"
      @submit="submitPickupProof"
      @cancel="cancelPickupProof"
    />

    <!-- Delivery Proof Modal -->
    <PreparePackageDeliveryModal
      v-if="packageForDelivery"
      :show="showDeliveryProofModal"
      :package-data="{
        prepareSn: packageForDelivery.prepareSn,
        orderCount: packageForDelivery.orderCount,
        workflowLabel: packageForDelivery.workflowLabel,
        warehouseName: packageForDelivery.warehouseName
      }"
      @submit="submitDeliveryProof"
      @cancel="cancelDeliveryProof"
    />

    <!-- Address Map Modal -->
    <AddressMapModal
      v-if="selectedAddress"
      :show="showAddressMapModal"
      :address="selectedAddress"
      @close="closeAddressMapModal"
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
import PickupProofModal from '@/components/PickupProofModal.vue';
import PreparePackageDeliveryModal from '@/components/PreparePackageDeliveryModal.vue';
import MapTab from '@/components/MapTab.vue';
import AddressMapModal from '@/components/AddressMapModal.vue';
import features from '@/config/features';

const { t } = useI18n();
const prepareGoodsStore = usePrepareGoodsStore();
const activeStatus = ref(features.mapTab ? 'map' : 'available');

// Modal state
const showOrdersModal = ref(false);
const selectedPackage = ref<{ prepareSn: string; orderCount: number } | null>(null);

// Pickup confirmation modal state
const showPickupModal = ref(false);
const packageToPickup = ref<any>(null);
const isPickingUp = ref(false);

// Pickup proof modal state
const showPickupProofModal = ref(false);
const packageForProof = ref<any>(null);

// Delivery proof modal state
const showDeliveryProofModal = ref(false);
const packageForDelivery = ref<any>(null);

// Address map modal state
const showAddressMapModal = ref(false);
const selectedAddress = ref<string | null>(null);

const statuses = computed(() => {
  const tabs = [];
  
  if (features.mapTab) {
    tabs.push({ key: 'map', label: t('taskBoard.map'), prepareStatus: null });
  }
  
  tabs.push(
    // Available: includes both merchant pickup (status=0) and warehouse pickup (status=5)
    { key: 'available', label: t('taskBoard.available'), prepareStatus: [0, 5] },
    { key: 'pending_pickup', label: t('taskBoard.pendingPickup'), prepareStatus: 6 },
    { key: 'in_transit', label: t('taskBoard.inTransit'), prepareStatus: 1 },
    { key: 'warehouse', label: t('taskBoard.warehouse'), prepareStatus: 2 },
    { key: 'completed', label: t('taskBoard.completed'), prepareStatus: 7 },
    { key: 'earnings', label: t('taskBoard.earnings'), prepareStatus: null }
  );
  
  return tabs;
});

onMounted(() => {
  // Fetch both available (unassigned) and driver's assigned packages
  prepareGoodsStore.fetchAvailablePackages();
  prepareGoodsStore.fetchMyDriverPackages();
});

// Filter packages by prepare_status based on active tab
const filteredPackages = computed(() => {
  const currentTab = statuses.value.find(s => s.key === activeStatus.value);
  if (!currentTab || currentTab.key === 'map' || currentTab.key === 'earnings') return [];

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

// Earnings packages - packages in warehouse (status=2) and completed (status=7)
const earningsPackages = computed(() => {
  return prepareGoodsStore.driverPackages.filter(
    pkg => pkg.prepareStatus === 2 || pkg.prepareStatus === 7
  );
});

// Total earnings calculation (10% of total value)
const totalEarnings = computed(() => {
  return earningsPackages.value.reduce((sum, pkg) => {
    return sum + (pkg.totalValue || 0) * 0.1;
  }, 0);
});

function getPackageActionLabel(status: number | null): string {
  if (status === null || status === 0 || status === 5) return t('taskBoard.pickupPackage');
  if (status === 6) return t('taskBoard.confirmPickupButton');
  if (status === 1) return t('taskBoard.confirmDeliveryButton');
  return t('taskBoard.viewDetails');
}

function formatAmount(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

function openAddressMap(address: string, _type?: string) {
  selectedAddress.value = address;
  showAddressMapModal.value = true;
}

function closeAddressMapModal() {
  showAddressMapModal.value = false;
  selectedAddress.value = null;
}

function handlePackageAction(pkg: any) {
  if (pkg.prepareStatus === null || pkg.prepareStatus === 0 || pkg.prepareStatus === 5) {
    // Available package (merchant or warehouse pickup) - show pickup confirmation modal
    packageToPickup.value = pkg;
    showPickupModal.value = true;
  } else if (pkg.prepareStatus === 6) {
    // Driver claimed - show pickup proof modal
    packageForProof.value = pkg;
    showPickupProofModal.value = true;
  } else if (pkg.prepareStatus === 1) {
    // In transit - show delivery proof modal
    packageForDelivery.value = pkg;
    showDeliveryProofModal.value = true;
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

async function submitPickupProof(photo: string, notes: string) {
  if (!packageForProof.value) return;

  try {
    await prepareGoodsStore.confirmPickupWithProof(
      packageForProof.value.prepareSn,
      photo,
      notes
    );
    // Close modal
    showPickupProofModal.value = false;
    packageForProof.value = null;
    // Refresh driver packages to show updated status
    await prepareGoodsStore.fetchMyDriverPackages();
  } catch (error: any) {
    alert(`Error: ${error.response?.data?.detail || error.message}`);
  }
}

function cancelPickupProof() {
  showPickupProofModal.value = false;
  packageForProof.value = null;
}

async function submitDeliveryProof(photo: string, notes: string) {
  if (!packageForDelivery.value) return;

  try {
    await prepareGoodsStore.confirmDeliveryWithProof(
      packageForDelivery.value.prepareSn,
      photo,
      notes
    );
    // Close modal
    showDeliveryProofModal.value = false;
    packageForDelivery.value = null;
    // Refresh driver packages to show updated status
    await prepareGoodsStore.fetchMyDriverPackages();
  } catch (error: any) {
    alert(`Error: ${error.response?.data?.detail || error.message}`);
  }
}

function cancelDeliveryProof() {
  showDeliveryProofModal.value = false;
  packageForDelivery.value = null;
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
  flex-wrap: wrap;
  overflow-x: auto;
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

.package-info-row--address {
  font-size: 0.8rem;
  line-height: 1.4;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.address-label {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  text-transform: uppercase;
}

.address-link {
  color: var(--color-primary);
  cursor: pointer;
  text-decoration: underline;
  transition: color var(--transition-base);
}

.address-link:hover {
  color: var(--color-primary-dark);
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

.package-action-button--disabled {
  background: var(--color-gray-light);
  color: var(--color-text-secondary);
  border-color: var(--color-gray-light);
  cursor: not-allowed;
  opacity: 0.6;
}

.package-action-button--disabled:hover {
  background: var(--color-gray-light);
  border-color: var(--color-gray-light);
}

/* Earnings Table Styles */
.earnings-section {
  background: var(--color-white);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-md);
  max-width: 100%;
  overflow: hidden;
}

.earnings-table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  max-width: 100%;
}

.earnings-table {
  width: 100%;
  min-width: 320px;
  border-collapse: collapse;
  font-size: 0.875rem;
  table-layout: auto;
}

.earnings-table thead {
  background: var(--color-gray-light);
}

.earnings-table th {
  padding: var(--spacing-sm) var(--spacing-md);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  border-bottom: 2px solid var(--color-gray-light);
  white-space: nowrap;
}

.earnings-table td {
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-gray-light);
  color: var(--color-text-secondary);
  text-align: left;
}

.earnings-table tbody tr:hover {
  background: var(--color-gray-lighter);
}

.package-sn-cell {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  word-break: break-all;
  max-width: 120px;
}

.amount-cell {
  text-align: left;
  font-family: monospace;
  white-space: nowrap;
}

.earning-cell {
  color: var(--color-success);
  font-weight: var(--font-weight-semibold);
}

.earnings-table tfoot {
  background: var(--color-primary-light);
  font-weight: var(--font-weight-semibold);
}

.earnings-table tfoot td {
  padding: var(--spacing-md) var(--spacing-md);
  border-top: 2px solid var(--color-primary);
  border-bottom: none;
  text-align: left;
}

.total-row td {
  color: var(--color-text-primary);
}

.total-earning {
  text-align: left;
  color: var(--color-success);
  font-size: 1rem;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
  .earnings-section {
    padding: var(--spacing-md);
  }

  .earnings-table {
    font-size: 0.75rem;
  }

  .earnings-table th,
  .earnings-table td {
    padding: var(--spacing-xs) var(--spacing-sm);
  }

  .package-sn-cell {
    max-width: 80px;
    font-size: 0.7rem;
  }

  .earnings-table tfoot td {
    padding: var(--spacing-sm) var(--spacing-sm);
    font-size: 0.75rem;
  }

  .total-earning {
    font-size: 0.875rem;
  }
}
</style>
