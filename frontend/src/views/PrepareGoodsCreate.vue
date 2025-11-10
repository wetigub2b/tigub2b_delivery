<template>
  <div class="prepare-goods-create">
    <div class="page-header">
      <button class="back-button" @click="goBack">
        ← {{ $t('common.back') }}
      </button>
      <h1 class="page-title">{{ $t('prepareGoods.createPackage') }}</h1>
    </div>

    <div class="create-form">
      <!-- Step 1: Select Workflow -->
      <div class="form-section">
        <div class="section-number">1</div>
        <div class="section-content">
          <DeliveryTypeSelector
            v-model="workflowSelection"
            :warehouses="warehouses"
          />
        </div>
      </div>

      <!-- Step 2: Select Orders -->
      <div class="form-section" :class="{ disabled: !workflowSelection }">
        <div class="section-number">2</div>
        <div class="section-content">
          <OrderSelector
            v-model="selectedOrderIds"
            :orders="availableOrders"
            :is-loading="isLoadingOrders"
          />
        </div>
      </div>

      <!-- Step 3: Confirmation and Submit -->
      <div class="form-section" :class="{ disabled: !canSubmit }">
        <div class="section-number">3</div>
        <div class="section-content">
          <div class="confirmation-panel">
            <h3 class="confirmation-title">{{ $t('prepareGoods.confirmationTitle') }}</h3>

            <div class="summary-grid">
              <div class="summary-item">
                <span class="summary-label">{{ $t('workflow.label') }}:</span>
                <span class="summary-value">{{ workflowLabel }}</span>
              </div>

              <div class="summary-item">
                <span class="summary-label">{{ $t('workflow.deliveryType') }}:</span>
                <span class="summary-value">{{ deliveryTypeLabel }}</span>
              </div>

              <div class="summary-item">
                <span class="summary-label">{{ $t('workflow.shippingType') }}:</span>
                <span class="summary-value">{{ shippingTypeLabel }}</span>
              </div>

              <div v-if="workflowSelection?.warehouseId" class="summary-item">
                <span class="summary-label">{{ $t('prepareGoods.warehouse') }}:</span>
                <span class="summary-value">{{ selectedWarehouseName }}</span>
              </div>

              <div class="summary-item">
                <span class="summary-label">{{ $t('prepareGoods.ordersCount') }}:</span>
                <span class="summary-value">{{ selectedOrderIds.length }}</span>
              </div>
            </div>

            <div v-if="errorMessage" class="error-message">
              {{ errorMessage }}
            </div>

            <div class="action-buttons">
              <button class="cancel-button" @click="goBack" :disabled="isCreating">
                {{ $t('common.cancel') }}
              </button>
              <button
                class="submit-button"
                @click="createPackage"
                :disabled="!canSubmit || isCreating"
              >
                <span v-if="isCreating">{{ $t('common.creating') }}...</span>
                <span v-else>{{ $t('prepareGoods.createPackage') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import DeliveryTypeSelector from '@/components/DeliveryTypeSelector.vue';
import OrderSelector from '@/components/OrderSelector.vue';
import { usePrepareGoodsStore } from '@/store/prepareGoods';

const router = useRouter();
const prepareGoodsStore = usePrepareGoodsStore();

// Form state
const workflowSelection = ref<{
  deliveryType: number;
  shippingType: number;
  warehouseId?: number | null;
} | null>(null);
const selectedOrderIds = ref<number[]>([]);
const isCreating = ref(false);
const errorMessage = ref('');

// Mock data - TODO: Replace with actual API calls
const warehouses = ref([
  { id: 1, name: 'Warehouse A', address: '123 Main St' },
  { id: 2, name: 'Warehouse B', address: '456 Oak Ave' },
  { id: 3, name: 'Warehouse C', address: '789 Pine Rd' }
]);

const availableOrders = ref<any[]>([]);
const isLoadingOrders = ref(false);
const shopId = ref(1); // TODO: Get from auth store

// Computed properties
const workflowLabel = computed(() => {
  if (!workflowSelection.value) return '';
  const key = `${workflowSelection.value.deliveryType},${workflowSelection.value.shippingType}`;
  const workflows: Record<string, string> = {
    '0,0': 'Workflow 1: Merchant → Warehouse → User',
    '0,1': 'Workflow 2: Merchant → User',
    '1,0': 'Workflow 3: Driver → Warehouse → User',
    '1,1': 'Workflow 4: Driver → User'
  };
  return workflows[key] || '';
});

const deliveryTypeLabel = computed(() => {
  if (workflowSelection.value?.deliveryType === 0) return 'Merchant Self-Delivery';
  if (workflowSelection.value?.deliveryType === 1) return 'Third-Party Driver';
  return '';
});

const shippingTypeLabel = computed(() => {
  if (workflowSelection.value?.shippingType === 0) return 'To Warehouse';
  if (workflowSelection.value?.shippingType === 1) return 'To User';
  return '';
});

const selectedWarehouseName = computed(() => {
  if (!workflowSelection.value?.warehouseId) return '';
  const warehouse = warehouses.value.find(w => w.id === workflowSelection.value!.warehouseId);
  return warehouse ? `${warehouse.name} - ${warehouse.address}` : '';
});

const canSubmit = computed(() => {
  if (!workflowSelection.value) return false;
  if (selectedOrderIds.value.length === 0) return false;

  // If shipping to warehouse, warehouse must be selected
  if (workflowSelection.value.shippingType === 0 && !workflowSelection.value.warehouseId) {
    return false;
  }

  return true;
});

// Actions
async function loadAvailableOrders() {
  isLoadingOrders.value = true;
  try {
    // TODO: Replace with actual API call
    // Mock data for now
    availableOrders.value = [
      {
        id: 1,
        orderSn: 'ORD20251109001',
        orderStatus: 1,
        receiverName: 'John Doe',
        receiverPhone: '555-0123',
        receiverAddress: '123 Main St, City',
        items: [
          { skuId: 101, productName: 'Product A', quantity: 2 },
          { skuId: 102, productName: 'Product B', quantity: 1 }
        ]
      },
      {
        id: 2,
        orderSn: 'ORD20251109002',
        orderStatus: 1,
        receiverName: 'Jane Smith',
        receiverPhone: '555-0456',
        receiverAddress: '456 Oak Ave, Town',
        items: [
          { skuId: 103, productName: 'Product C', quantity: 3 }
        ]
      }
    ];
  } finally {
    isLoadingOrders.value = false;
  }
}

async function createPackage() {
  if (!canSubmit.value) return;

  errorMessage.value = '';
  isCreating.value = true;

  try {
    await prepareGoodsStore.createPackage({
      orderIds: selectedOrderIds.value,
      shopId: shopId.value,
      deliveryType: workflowSelection.value!.deliveryType,
      shippingType: workflowSelection.value!.shippingType,
      warehouseId: workflowSelection.value!.warehouseId
    });

    // Navigate to list view on success
    router.push({ name: 'PrepareGoodsList' });
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Failed to create package';
    console.error('Create package error:', error);
  } finally {
    isCreating.value = false;
  }
}

function goBack() {
  router.back();
}

onMounted(() => {
  loadAvailableOrders();
});
</script>

<style scoped>
.prepare-goods-create {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.back-button {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.back-button:hover {
  background: #f3f4f6;
}

.page-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: #1f2937;
}

.create-form {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.form-section {
  display: flex;
  gap: 1.5rem;
  align-items: flex-start;
}

.form-section.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.section-number {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.125rem;
  flex-shrink: 0;
}

.form-section.disabled .section-number {
  background: #d1d5db;
}

.section-content {
  flex: 1;
}

.confirmation-panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.confirmation-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
}

.summary-value {
  font-size: 0.875rem;
  color: #1f2937;
  font-weight: 600;
}

.error-message {
  padding: 0.75rem;
  background: #fee2e2;
  border: 1px solid #fecaca;
  border-radius: 0.375rem;
  color: #991b1b;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.cancel-button,
.submit-button {
  padding: 0.75rem 1.5rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.cancel-button {
  background: white;
  border: 1px solid #d1d5db;
  color: #374151;
}

.cancel-button:hover:not(:disabled) {
  background: #f3f4f6;
}

.submit-button {
  background: #3b82f6;
  border: none;
  color: white;
}

.submit-button:hover:not(:disabled) {
  background: #2563eb;
}

.submit-button:disabled,
.cancel-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .form-section {
    flex-direction: column;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }
}
</style>
