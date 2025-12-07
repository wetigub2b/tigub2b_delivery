<template>
  <Transition name="modal">
    <div v-if="show" class="modal-overlay" @click="handleClose">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <div class="header-info">
            <span class="location-type" :class="`type-${mark.type?.toLowerCase()}`">
              {{ mark.type === 'Vendor' ? '🏪' : '🏭' }} {{ mark.type }}
            </span>
            <h3>{{ mark.name }}</h3>
          </div>
          <button class="modal-close" @click="handleClose" aria-label="Close">
            ✕
          </button>
        </div>

        <div class="modal-body">
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>{{ $t('common.loading') }}</p>
          </div>

          <div v-else-if="error" class="error-state">
            <p>{{ error }}</p>
            <button @click="fetchPackages" class="retry-button">{{ $t('map.retry') }}</button>
          </div>

          <div v-else-if="packages.length === 0" class="empty-state">
            <div class="empty-icon">📦</div>
              <p>{{ $t('pickupLocation.noPackages') }}</p>
            </div>

            <div v-else class="packages-list">
              <div class="packages-header">
                <span>{{ $t('pickupLocation.availablePackages') }}</span>
                <span class="package-count">{{ packages.length }}</span>
              </div>

              <div
                v-for="pkg in packages"
                :key="pkg.prepareSn"
                class="package-card"
              >
                <div class="package-header">
                  <span class="package-sn">{{ pkg.prepareSn }}</span>
                  <span class="package-status" :class="`status-${pkg.prepareStatus}`">
                    {{ pkg.prepareStatusLabel }}
                  </span>
                </div>
                <div class="package-body">
                  <div class="package-info-row package-info-row--with-action">
                    <span>📦 {{ pkg.orderCount }} {{ $t('taskBoard.orders') }}</span>
                    <button class="detail-button" @click="openOrdersModal(pkg)">
                      {{ $t('packageModal.viewDetails') }}
                    </button>
                  </div>
                  <div class="package-info-row">
                    <span>🏷️ {{ pkg.workflowLabel }}</span>
                  </div>
                  <div v-if="pkg.totalValue" class="package-info-row">
                    <span>💰 {{ formatAmount(pkg.totalValue) }}</span>
                  </div>
                  <!-- Pickup Address -->
                  <div v-if="pkg.pickupAddress" class="package-info-row package-info-row--address">
                    <span class="address-label">{{ $t('taskBoard.pickupAddress') }}:</span>
                    <a class="address-link" @click.stop="openAddressMap(pkg.pickupAddress)">📍 {{ pkg.pickupAddress }}</a>
                  </div>
                  <!-- Warehouse Address (for workflow Driver -> Warehouse -> User) -->
                  <div v-if="pkg.shippingType === 1 && pkg.warehouseAddress" class="package-info-row package-info-row--address">
                    <span class="address-label">{{ $t('taskBoard.warehouseAddress') }}:</span>
                    <a class="address-link" @click.stop="openAddressMap(pkg.warehouseAddress)">🏭 {{ pkg.warehouseAddress }}</a>
                  </div>
                  <!-- Receiver Address -->
                  <div v-if="pkg.receiverAddress" class="package-info-row package-info-row--address">
                    <span class="address-label">{{ $t('taskBoard.receiverAddress') }}:</span>
                    <a class="address-link" @click.stop="openAddressMap(pkg.receiverAddress)">📍 {{ pkg.receiverAddress }}</a>
                  </div>
                </div>
                <div class="package-footer">
                  <button
                    class="package-action-button"
                    @click="handlePickup(pkg)"
                    :disabled="isPickingUp"
                  >
                    {{ isPickingUp ? $t('common.loading') : $t('taskBoard.pickupPackage') }} →
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="modal-button modal-button--close" @click="handleClose">
              {{ $t('common.close') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Package Orders Modal -->
    <PackageOrdersModal
      v-if="selectedPackage"
      :show="showOrdersModal"
      :package-sn="selectedPackage.prepareSn"
      :order-count="selectedPackage.orderCount"
      @close="closeOrdersModal"
    />

    <!-- Address Map Modal -->
    <AddressMapModal
      v-if="selectedAddress"
      :show="showAddressMapModal"
      :address="selectedAddress"
      @close="closeAddressMapModal"
    />
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { usePrepareGoodsStore } from '@/store/prepareGoods';
import PackageOrdersModal from './PackageOrdersModal.vue';
import AddressMapModal from './AddressMapModal.vue';

const { t } = useI18n();
const prepareGoodsStore = usePrepareGoodsStore();

interface Mark {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  type?: string;
  description?: string;
  shop_id?: string;  // String to preserve bigint precision
  warehouse_id?: string;  // String to preserve bigint precision
  order_count: number;
}

const props = defineProps<{
  show: boolean;
  mark: Mark;
}>();

const emit = defineEmits<{
  close: [];
}>();

const loading = ref(false);
const error = ref<string | null>(null);
const isPickingUp = ref(false);

// Modal state for package orders detail
const showOrdersModal = ref(false);
const selectedPackage = ref<{ prepareSn: string; orderCount: number } | null>(null);

// Address map modal state
const showAddressMapModal = ref(false);
const selectedAddress = ref<string | null>(null);

// Filter available packages from store by shop_id or warehouse_id
const packages = computed(() => {
  const allPackages = prepareGoodsStore.availablePackages;
  
  if (props.mark.shop_id) {
    return allPackages.filter(pkg => pkg.shopId === props.mark.shop_id);
  }
  if (props.mark.warehouse_id) {
    return allPackages.filter(pkg => pkg.warehouseId === props.mark.warehouse_id);
  }
  return [];
});

watch(() => props.show, async (newVal) => {
  if (newVal) {
    await fetchPackages();
  }
});

async function fetchPackages() {
  loading.value = true;
  error.value = null;

  try {
    // Refresh the store's available packages
    await prepareGoodsStore.fetchAvailablePackages();
  } catch (err: any) {
    console.error('Error fetching packages:', err);
    error.value = err.response?.data?.detail || err.message || t('pickupLocation.fetchError');
  } finally {
    loading.value = false;
  }
}

async function handlePickup(pkg: any) {
  isPickingUp.value = true;
  try {
    await prepareGoodsStore.pickupPackage(pkg.prepareSn);
    // Refresh available packages list (computed will auto-filter)
    await prepareGoodsStore.fetchAvailablePackages();
  } catch (err: any) {
    alert(`Error: ${err.response?.data?.detail || err.message}`);
  } finally {
    isPickingUp.value = false;
  }
}

function handleClose() {
  emit('close');
}

function formatAmount(amount: number): string {
  return `$${amount.toFixed(2)}`;
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

function openAddressMap(address: string) {
  selectedAddress.value = address;
  showAddressMapModal.value = true;
}

function closeAddressMapModal() {
  showAddressMapModal.value = false;
  selectedAddress.value = null;
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2147483647;
  padding: var(--spacing-md);
}

.modal-container {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-width: 600px;
  width: 100%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--color-gray-lighter);
  gap: var(--spacing-md);
}

.header-info {
  flex: 1;
}

.location-type {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: var(--font-weight-medium);
  margin-bottom: var(--spacing-xs);
}

.type-vendor {
  background: #fff3e0;
  color: #e65100;
}

.type-warehouse {
  background: #e3f2fd;
  color: #1565c0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  transition: all var(--transition-base);
  flex-shrink: 0;
}

.modal-close:hover {
  background: var(--color-gray-lighter);
  color: var(--color-text-primary);
}

.modal-body {
  padding: var(--spacing-lg) var(--spacing-xl);
  overflow-y: auto;
  flex: 1;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  text-align: center;
  gap: var(--spacing-md);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-gray-light);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

.error-state p {
  color: var(--color-danger);
}

.retry-button {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}

.packages-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.packages-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-gray-lighter);
}

.package-count {
  background: var(--color-primary);
  color: var(--color-white);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-full);
  font-size: 0.875rem;
}

.package-card {
  background: var(--color-gray-lighter);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  transition: all var(--transition-base);
}

.package-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary);
}

.package-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-white);
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

.package-body {
  margin-bottom: var(--spacing-sm);
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
  padding-top: var(--spacing-sm);
  border-top: 1px solid var(--color-white);
}

.package-action-button {
  width: 100%;
  padding: var(--spacing-sm);
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  font-size: 0.875rem;
}

.package-action-button:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.package-action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-footer {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-lg) var(--spacing-xl);
  border-top: 1px solid var(--color-gray-lighter);
}

.modal-button {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  border: none;
}

.modal-button--close {
  background: var(--color-white);
  color: var(--color-text-primary);
  border: 1px solid var(--color-gray-light);
}

.modal-button--close:hover {
  background: var(--color-gray-lighter);
  border-color: var(--color-gray);
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-base);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--transition-base);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}

@media (max-width: 768px) {
  .modal-container {
    max-width: 100%;
    margin: var(--spacing-md);
    max-height: 90vh;
  }
}
</style>
