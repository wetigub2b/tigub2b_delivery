<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="modal-overlay" @click="handleClose">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3>{{ $t('packageModal.orderDetails') }}</h3>
            <button class="modal-close" @click="handleClose" aria-label="Close">
              ✕
            </button>
          </div>

          <div class="modal-body">
            <div class="package-summary">
              <div class="summary-row">
                <span class="summary-label">{{ $t('packageModal.packageNumber') }}:</span>
                <span class="summary-value">{{ packageSn }}</span>
              </div>
              <div class="summary-row">
                <span class="summary-label">{{ $t('packageModal.totalOrders') }}:</span>
                <span class="summary-value">{{ orderCount }}</span>
              </div>
              <div v-if="totalValue !== null" class="summary-row">
                <span class="summary-label">{{ $t('packageModal.totalValue') }}:</span>
                <span class="summary-value summary-value--amount">{{ formatAmount(totalValue) }}</span>
              </div>
              <div v-if="receiverAddress" class="summary-row summary-row--address">
                <span class="summary-label">{{ $t('packageModal.deliveryAddress') }}:</span>
                <a class="summary-value summary-value--link" @click="openAddressMap(receiverAddress)">📍 {{ receiverAddress }}</a>
              </div>
            </div>

            <!-- Address Map Modal -->
            <AddressMapModal
              v-if="selectedAddress"
              :show="showAddressMapModal"
              :address="selectedAddress"
              @close="closeAddressMapModal"
            />

            <!-- Pickup Photos Section -->
            <div v-if="pickupPhotos.length > 0" class="photos-section">
              <h4>{{ $t('packageModal.pickupPhotos') }}</h4>
              <div class="photos-grid">
                <div
                  v-for="photo in pickupPhotos"
                  :key="photo.id"
                  class="photo-card"
                >
                  <img :src="photo.fileUrl" :alt="photo.fileName" class="photo-image" />
                  <div class="photo-info">
                    <div class="photo-meta">
                      <span class="photo-uploader">📷 {{ photo.uploaderName || 'Unknown' }}</span>
                      <span class="photo-size">{{ formatFileSize(photo.fileSize) }}</span>
                    </div>
                    <div class="photo-time">{{ formatDateTime(photo.createTime) }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="orders-section">
              <h4>{{ $t('packageModal.orderList') }}</h4>
              <div v-if="isLoading" class="loading-state">
                {{ $t('common.loading') }}
              </div>
              <div v-else-if="orderSerialNumbers.length > 0" class="orders-list">
                <div
                  v-for="(orderSn, index) in orderSerialNumbers"
                  :key="orderSn"
                  class="order-item"
                >
                  <span class="order-index">{{ index + 1 }}.</span>
                  <span class="order-id">{{ orderSn }}</span>
                </div>
              </div>
              <div v-else class="empty-state">
                {{ $t('packageModal.noOrders') }}
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="modal-button modal-button--primary" @click="handleClose">
              {{ $t('common.ok') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { usePrepareGoodsStore } from '@/store/prepareGoods';
import AddressMapModal from '@/components/AddressMapModal.vue';

const props = defineProps<{
  show: boolean;
  packageSn: string;
  orderCount: number;
}>();

const emit = defineEmits<{
  close: [];
}>();

import type { UploadedFileDto } from '@/api/prepareGoods';

const prepareGoodsStore = usePrepareGoodsStore();
const orderSerialNumbers = ref<string[]>([]);
const receiverAddress = ref<string | null>(null);
const totalValue = ref<number | null>(null);
const pickupPhotos = ref<UploadedFileDto[]>([]);
const isLoading = ref(false);

// Fetch package details when modal opens
watch(() => props.show, async (newValue) => {
  if (newValue && props.packageSn) {
    await fetchPackageDetails();
  } else {
    // Clear data when modal closes
    orderSerialNumbers.value = [];
    receiverAddress.value = null;
    totalValue.value = null;
    pickupPhotos.value = [];
  }
}, { immediate: true });

async function fetchPackageDetails() {
  isLoading.value = true;
  try {
    const detail = await prepareGoodsStore.fetchPackageDetail(props.packageSn);
    if (detail) {
      orderSerialNumbers.value = detail.orderSerialNumbers || [];
      receiverAddress.value = detail.receiverAddress || null;
      totalValue.value = detail.totalValue || null;
      pickupPhotos.value = detail.pickupPhotos || [];
    } else {
      orderSerialNumbers.value = [];
      receiverAddress.value = null;
      totalValue.value = null;
      pickupPhotos.value = [];
    }
  } catch (error) {
    console.error('Failed to fetch package details:', error);
    orderSerialNumbers.value = [];
    receiverAddress.value = null;
    totalValue.value = null;
    pickupPhotos.value = [];
  } finally {
    isLoading.value = false;
  }
}

function formatAmount(amount: number): string {
  return `$${amount.toFixed(2)}`;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString();
}

// Address map modal state
const showAddressMapModal = ref(false);
const selectedAddress = ref<string | null>(null);

function openAddressMap(address: string) {
  selectedAddress.value = address;
  showAddressMapModal.value = true;
}

function closeAddressMapModal() {
  showAddressMapModal.value = false;
  selectedAddress.value = null;
}

function handleClose() {
  emit('close');
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2147483647;
  padding: var(--spacing-lg);
}

.modal-container {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-gray-light);
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
  padding: var(--spacing-xs);
  line-height: 1;
  transition: color var(--transition-base);
}

.modal-close:hover {
  color: var(--color-text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.package-summary {
  background: var(--color-gray-lighter);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs) 0;
}

.summary-label {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

.summary-value {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  font-size: 0.875rem;
}

.summary-value--amount {
  color: var(--color-success);
}

.summary-row--address {
  flex-direction: column;
  align-items: flex-start;
  gap: var(--spacing-xs);
}

.summary-row--address .summary-value {
  font-size: 0.8rem;
  line-height: 1.4;
}

.summary-value--link {
  color: var(--color-primary);
  cursor: pointer;
  text-decoration: underline;
  transition: color var(--transition-base);
}

.summary-value--link:hover {
  color: var(--color-primary-dark);
}

.photos-section {
  margin-bottom: var(--spacing-lg);
}

.photos-section h4 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1rem;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.photo-card {
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: all var(--transition-base);
}

.photo-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.photo-image {
  width: 100%;
  height: 150px;
  object-fit: cover;
  display: block;
  cursor: pointer;
}

.photo-info {
  padding: var(--spacing-sm);
  background: var(--color-gray-lightest);
}

.photo-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
  font-size: 0.75rem;
}

.photo-uploader {
  color: var(--color-text-primary);
  font-weight: var(--font-weight-medium);
}

.photo-size {
  color: var(--color-text-secondary);
}

.photo-time {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
}

.orders-section h4 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1rem;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.order-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  background: var(--color-white);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
}

.order-item:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

.order-index {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  margin-right: var(--spacing-sm);
  min-width: 2rem;
}

.order-id {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  font-family: monospace;
  font-size: 0.875rem;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-gray-light);
}

.modal-button {
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  border: 1px solid transparent;
  font-size: 0.875rem;
}

.modal-button--primary {
  background: var(--color-primary);
  color: var(--color-white);
  border-color: var(--color-primary);
}

.modal-button--primary:hover {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
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

/* Responsive */
@media (max-width: 768px) {
  .modal-overlay {
    padding: var(--spacing-md);
  }

  .modal-container {
    max-height: 90vh;
  }
}
</style>
