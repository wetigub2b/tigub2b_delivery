<template>
  <div class="delivery-type-selector">
    <h3 class="selector-title">{{ $t('prepareGoods.selectWorkflow') }}</h3>

    <div class="workflow-grid">
      <!-- Workflow 1: Merchant → Warehouse → User -->
      <div
        class="workflow-card"
        :class="{ selected: isSelected(0, 0) }"
        @click="selectWorkflow(0, 0)"
      >
        <div class="workflow-icon">📦🏭</div>
        <div class="workflow-title">{{ $t('workflow.workflow1.title') }}</div>
        <div class="workflow-description">{{ $t('workflow.workflow1.description') }}</div>
        <div class="workflow-path">
          <span class="path-step">{{ $t('workflow.merchant') }}</span>
          <span class="path-arrow">→</span>
          <span class="path-step">{{ $t('workflow.warehouse') }}</span>
          <span class="path-arrow">→</span>
          <span class="path-step">{{ $t('workflow.user') }}</span>
        </div>
        <div class="workflow-details">
          <div class="detail-row">
            <span class="detail-label">{{ $t('workflow.deliveryType') }}:</span>
            <span class="detail-value">{{ $t('workflow.merchantSelf') }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ $t('workflow.shippingType') }}:</span>
            <span class="detail-value">{{ $t('workflow.toWarehouse') }}</span>
          </div>
        </div>
      </div>

      <!-- Workflow 2: Merchant → User -->
      <div
        class="workflow-card"
        :class="{ selected: isSelected(0, 1) }"
        @click="selectWorkflow(0, 1)"
      >
        <div class="workflow-icon">📦✅</div>
        <div class="workflow-title">{{ $t('workflow.workflow2.title') }}</div>
        <div class="workflow-description">{{ $t('workflow.workflow2.description') }}</div>
        <div class="workflow-path">
          <span class="path-step">{{ $t('workflow.merchant') }}</span>
          <span class="path-arrow">→</span>
          <span class="path-step">{{ $t('workflow.user') }}</span>
        </div>
        <div class="workflow-details">
          <div class="detail-row">
            <span class="detail-label">{{ $t('workflow.deliveryType') }}:</span>
            <span class="detail-value">{{ $t('workflow.merchantSelf') }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ $t('workflow.shippingType') }}:</span>
            <span class="detail-value">{{ $t('workflow.toUser') }}</span>
          </div>
        </div>
      </div>

      <!-- Workflow 3: Driver → Warehouse → User -->
      <div
        class="workflow-card"
        :class="{ selected: isSelected(1, 0) }"
        @click="selectWorkflow(1, 0)"
      >
        <div class="workflow-icon">🚗🏭</div>
        <div class="workflow-title">{{ $t('workflow.workflow3.title') }}</div>
        <div class="workflow-description">{{ $t('workflow.workflow3.description') }}</div>
        <div class="workflow-path">
          <span class="path-step">{{ $t('workflow.driver') }}</span>
          <span class="path-arrow">→</span>
          <span class="path-step">{{ $t('workflow.warehouse') }}</span>
          <span class="path-arrow">→</span>
          <span class="path-step">{{ $t('workflow.user') }}</span>
        </div>
        <div class="workflow-details">
          <div class="detail-row">
            <span class="detail-label">{{ $t('workflow.deliveryType') }}:</span>
            <span class="detail-value">{{ $t('workflow.thirdParty') }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ $t('workflow.shippingType') }}:</span>
            <span class="detail-value">{{ $t('workflow.toWarehouse') }}</span>
          </div>
        </div>
      </div>

      <!-- Workflow 4: Driver → User -->
      <div
        class="workflow-card"
        :class="{ selected: isSelected(1, 1) }"
        @click="selectWorkflow(1, 1)"
      >
        <div class="workflow-icon">🚗✅</div>
        <div class="workflow-title">{{ $t('workflow.workflow4.title') }}</div>
        <div class="workflow-description">{{ $t('workflow.workflow4.description') }}</div>
        <div class="workflow-path">
          <span class="path-step">{{ $t('workflow.driver') }}</span>
          <span class="path-arrow">→</span>
          <span class="path-step">{{ $t('workflow.user') }}</span>
        </div>
        <div class="workflow-details">
          <div class="detail-row">
            <span class="detail-label">{{ $t('workflow.deliveryType') }}:</span>
            <span class="detail-value">{{ $t('workflow.thirdParty') }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ $t('workflow.shippingType') }}:</span>
            <span class="detail-value">{{ $t('workflow.toUser') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Warehouse selection for workflows that need it (Workflow 1 & 3) -->
    <div v-if="requiresWarehouse" class="warehouse-selection">
      <label class="warehouse-label">{{ $t('prepareGoods.selectWarehouse') }}</label>
      <select
        v-model="selectedWarehouseId"
        class="warehouse-select"
        @change="onWarehouseChange"
      >
        <option :value="null">{{ $t('prepareGoods.selectWarehousePlaceholder') }}</option>
        <option
          v-for="warehouse in warehouses"
          :key="warehouse.id"
          :value="warehouse.id"
        >
          {{ warehouse.name }} - {{ warehouse.address }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

const props = defineProps<{
  modelValue?: {
    deliveryType: number;
    shippingType: number;
    warehouseId?: number | null;
  } | null;
  warehouses?: Array<{ id: number; name: string; address: string }>;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: {
    deliveryType: number;
    shippingType: number;
    warehouseId?: number | null;
  }): void;
}>();

const selectedDeliveryType = ref<number | null>(props.modelValue?.deliveryType ?? null);
const selectedShippingType = ref<number | null>(props.modelValue?.shippingType ?? null);
const selectedWarehouseId = ref<number | null>(props.modelValue?.warehouseId ?? null);

const requiresWarehouse = computed(() => {
  // Workflows 1 and 3 require warehouse (shippingType = 0)
  return selectedShippingType.value === 0;
});

function isSelected(deliveryType: number, shippingType: number): boolean {
  return (
    selectedDeliveryType.value === deliveryType &&
    selectedShippingType.value === shippingType
  );
}

function selectWorkflow(deliveryType: number, shippingType: number) {
  selectedDeliveryType.value = deliveryType;
  selectedShippingType.value = shippingType;

  // Reset warehouse if not required (only required for shippingType=1)
  if (shippingType !== 1) {
    selectedWarehouseId.value = null;
  }

  emitValue();
}

function onWarehouseChange() {
  emitValue();
}

function emitValue() {
  if (
    selectedDeliveryType.value !== null &&
    selectedShippingType.value !== null
  ) {
    const value: any = {
      deliveryType: selectedDeliveryType.value,
      shippingType: selectedShippingType.value
    };

    // Only include warehouseId if shipping to warehouse
    if (selectedShippingType.value === 0) {
      value.warehouseId = selectedWarehouseId.value;
    }

    emit('update:modelValue', value);
  }
}

// Watch for external changes
watch(
  () => props.modelValue,
  newValue => {
    if (newValue) {
      selectedDeliveryType.value = newValue.deliveryType;
      selectedShippingType.value = newValue.shippingType;
      selectedWarehouseId.value = newValue.warehouseId ?? null;
    }
  }
);
</script>

<style scoped>
.delivery-type-selector {
  padding: 1rem;
}

.selector-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #1f2937;
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.workflow-card {
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.workflow-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.workflow-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
}

.workflow-icon {
  font-size: 2rem;
  text-align: center;
  margin-bottom: 0.5rem;
}

.workflow-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.workflow-description {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 1rem;
  min-height: 2.5rem;
}

.workflow-path {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 0.375rem;
}

.path-step {
  font-size: 0.75rem;
  font-weight: 500;
  color: #374151;
}

.path-arrow {
  color: #9ca3af;
  font-weight: bold;
}

.workflow-details {
  font-size: 0.75rem;
  color: #6b7280;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
}

.detail-label {
  font-weight: 500;
}

.detail-value {
  font-weight: 600;
  color: #3b82f6;
}

.warehouse-selection {
  padding: 1rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.warehouse-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.warehouse-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #1f2937;
  background: white;
}

.warehouse-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
