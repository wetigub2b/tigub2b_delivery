<template>
  <div class="order-selector">
    <div class="selector-header">
      <h3 class="selector-title">{{ $t('prepareGoods.selectOrders') }}</h3>
      <div class="selection-summary">
        {{ $t('prepareGoods.selectedCount', { count: selectedOrders.length }) }}
      </div>
    </div>

    <!-- Search and filter -->
    <div class="search-bar">
      <input
        v-model="searchQuery"
        type="text"
        class="search-input"
        :placeholder="$t('prepareGoods.searchOrderPlaceholder')"
      />
      <button v-if="selectedOrders.length > 0" class="clear-button" @click="clearAll">
        {{ $t('common.clearAll') }}
      </button>
    </div>

    <!-- Orders list -->
    <div class="orders-list">
      <div v-if="isLoading" class="loading-state">
        {{ $t('common.loading') }}
      </div>

      <div v-else-if="filteredOrders.length === 0" class="empty-state">
        <p>{{ $t('prepareGoods.noOrdersAvailable') }}</p>
      </div>

      <div v-else class="order-items">
        <div
          v-for="order in filteredOrders"
          :key="order.id"
          class="order-item"
          :class="{ selected: isSelected(order.id) }"
          @click="toggleOrder(order)"
        >
          <div class="order-checkbox">
            <input
              type="checkbox"
              :checked="isSelected(order.id)"
              @click.stop="toggleOrder(order)"
            />
          </div>

          <div class="order-content">
            <div class="order-header">
              <span class="order-sn">{{ order.orderSn }}</span>
              <span class="order-status" :class="`status-${order.orderStatus}`">
                {{ getOrderStatusLabel(order.orderStatus) }}
              </span>
            </div>

            <div class="order-details">
              <div class="detail-item">
                <span class="detail-icon">📍</span>
                <span class="detail-text">{{ order.receiverAddress }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-icon">👤</span>
                <span class="detail-text">{{ order.receiverName }} - {{ order.receiverPhone }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-icon">📦</span>
                <span class="detail-text">{{ order.items?.length || 0 }} {{ $t('prepareGoods.items') }}</span>
              </div>
            </div>

            <!-- Order items preview -->
            <div v-if="order.items && order.items.length > 0" class="items-preview">
              <div
                v-for="(item, index) in order.items.slice(0, 2)"
                :key="index"
                class="item-preview"
              >
                <span class="item-name">{{ item.productName }}</span>
                <span class="item-qty">×{{ item.quantity }}</span>
              </div>
              <div v-if="order.items.length > 2" class="more-items">
                +{{ order.items.length - 2 }} {{ $t('prepareGoods.moreItems') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Selected orders summary -->
    <div v-if="selectedOrders.length > 0" class="selected-summary">
      <div class="summary-header">
        <span class="summary-title">{{ $t('prepareGoods.selectedOrders') }}</span>
        <button class="collapse-button" @click="isCollapsed = !isCollapsed">
          {{ isCollapsed ? $t('common.expand') : $t('common.collapse') }}
        </button>
      </div>

      <div v-if="!isCollapsed" class="summary-content">
        <div
          v-for="order in selectedOrderDetails"
          :key="order.id"
          class="summary-item"
        >
          <span class="summary-order-sn">{{ order.orderSn }}</span>
          <button class="remove-button" @click="removeOrder(order.id)">
            ✕
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

interface OrderItem {
  skuId: number;
  productName: string;
  quantity: number;
  skuImage?: string;
}

interface Order {
  id: number;
  orderSn: string;
  orderStatus: number;
  receiverName: string;
  receiverPhone: string;
  receiverAddress: string;
  items?: OrderItem[];
}

const props = defineProps<{
  modelValue: number[];
  orders: Order[];
  isLoading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: number[]): void;
}>();

const searchQuery = ref('');
const isCollapsed = ref(false);

const selectedOrders = computed({
  get: () => props.modelValue,
  set: (value: number[]) => emit('update:modelValue', value)
});

const filteredOrders = computed(() => {
  if (!searchQuery.value) {
    return props.orders;
  }

  const query = searchQuery.value.toLowerCase();
  return props.orders.filter(
    order =>
      order.orderSn.toLowerCase().includes(query) ||
      order.receiverName.toLowerCase().includes(query) ||
      order.receiverPhone.includes(query) ||
      order.receiverAddress.toLowerCase().includes(query)
  );
});

const selectedOrderDetails = computed(() => {
  return props.orders.filter(order => selectedOrders.value.includes(order.id));
});

function isSelected(orderId: number): boolean {
  return selectedOrders.value.includes(orderId);
}

function toggleOrder(order: Order) {
  const index = selectedOrders.value.indexOf(order.id);
  if (index >= 0) {
    // Remove
    const newValue = [...selectedOrders.value];
    newValue.splice(index, 1);
    selectedOrders.value = newValue;
  } else {
    // Add
    selectedOrders.value = [...selectedOrders.value, order.id];
  }
}

function removeOrder(orderId: number) {
  const index = selectedOrders.value.indexOf(orderId);
  if (index >= 0) {
    const newValue = [...selectedOrders.value];
    newValue.splice(index, 1);
    selectedOrders.value = newValue;
  }
}

function clearAll() {
  selectedOrders.value = [];
}

function getOrderStatusLabel(status: number): string {
  const labels: Record<number, string> = {
    0: 'Pending Payment',
    1: 'Pending Shipment',
    2: 'Pending Receipt',
    3: 'Completed',
    4: 'Cancelled',
    5: 'After-Sales'
  };
  return labels[status] || 'Unknown';
}
</script>

<style scoped>
.order-selector {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: white;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.selector-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.selection-summary {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.search-bar {
  padding: 1rem;
  display: flex;
  gap: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.search-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.clear-button {
  padding: 0.5rem 1rem;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-button:hover {
  background: #e5e7eb;
}

.orders-list {
  max-height: 400px;
  overflow-y: auto;
}

.loading-state,
.empty-state {
  padding: 2rem;
  text-align: center;
  color: #6b7280;
}

.order-items {
  padding: 0.5rem;
}

.order-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.order-item:hover {
  background: #f9fafb;
  border-color: #3b82f6;
}

.order-item.selected {
  background: #eff6ff;
  border-color: #3b82f6;
}

.order-checkbox {
  display: flex;
  align-items: flex-start;
  padding-top: 0.25rem;
}

.order-checkbox input[type='checkbox'] {
  width: 1.25rem;
  height: 1.25rem;
  cursor: pointer;
}

.order-content {
  flex: 1;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.order-sn {
  font-weight: 600;
  color: #1f2937;
  font-size: 0.875rem;
}

.order-status {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-weight: 500;
}

.status-1 {
  background: #fef3c7;
  color: #92400e;
}

.status-2 {
  background: #dbeafe;
  color: #1e40af;
}

.order-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.detail-icon {
  font-size: 0.875rem;
}

.items-preview {
  background: #f9fafb;
  border-radius: 0.25rem;
  padding: 0.5rem;
  margin-top: 0.5rem;
}

.item-preview {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #374151;
  padding: 0.125rem 0;
}

.item-name {
  font-weight: 500;
}

.item-qty {
  color: #6b7280;
}

.more-items {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
  font-style: italic;
}

.selected-summary {
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
}

.summary-title {
  font-weight: 600;
  color: #1f2937;
  font-size: 0.875rem;
}

.collapse-button {
  font-size: 0.75rem;
  color: #3b82f6;
  background: none;
  border: none;
  cursor: pointer;
  font-weight: 500;
}

.summary-content {
  padding: 0 1rem 0.75rem;
  max-height: 150px;
  overflow-y: auto;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.25rem;
  margin-bottom: 0.25rem;
}

.summary-order-sn {
  font-size: 0.75rem;
  font-weight: 500;
  color: #374151;
}

.remove-button {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  border: none;
  background: #fee2e2;
  color: #991b1b;
  cursor: pointer;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.remove-button:hover {
  background: #fecaca;
}
</style>
