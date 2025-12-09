<template>
  <div class="admin-orders">
    <AdminNavigation />

    <div class="orders-content">
      <div class="orders-header">
        <h1>{{ $t('admin.orders.title') }}</h1>
        <div class="header-actions">
          <button @click="refreshOrders" :disabled="isLoading" class="refresh-button">
            <span :class="{ 'spinning': isLoading }">🔄</span>
            {{ $t('common.refresh') }}
          </button>
        </div>
      </div>

      <!-- Filters and Search -->
      <div class="filters-section">
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="$t('admin.orders.searchPlaceholder')"
            @input="debouncedSearch"
          />
          <span class="search-icon">🔍</span>
        </div>

        <div class="filter-controls">
          <select v-model="statusFilter" @change="applyFilters">
            <option value="">{{ $t('admin.orders.allStatus') }}</option>
            <option value="0">已备货</option>
            <option value="1">司机已确认取货</option>
            <option value="2">司机送达仓库</option>
            <option value="3">仓库已收货</option>
            <option value="6">司机已认领</option>
            <option value="7">已送达</option>
          </select>

          <select v-model="driverFilter" @change="applyFilters">
            <option value="">{{ $t('admin.orders.allDrivers') }}</option>
            <option value="unassigned">{{ $t('admin.orders.unassigned') }}</option>
            <!-- Add driver options dynamically -->
          </select>
        </div>
      </div>

      <!-- Orders Table -->
      <div class="orders-table-container">
        <table class="orders-table">
          <thead>
            <tr>
              <th>备货单号</th>
              <th>订单数</th>
              <th>{{ $t('admin.orders.customer') }}</th>
              <th>{{ $t('admin.orders.driver') }}</th>
              <th>{{ $t('admin.orders.status') }}</th>
              <th>{{ $t('admin.orders.address') }}</th>
              <th>{{ $t('admin.orders.createdAt') }}</th>
              <th>{{ $t('admin.orders.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders" :key="order.prepare_sn" class="order-row">
              <td>
                <strong>{{ order.prepare_sn }}</strong>
              </td>
              <td>
                <span class="order-count">{{ order.order_count }}</span>
              </td>
              <td>
                <div class="customer-info">
                  <strong>{{ order.receiver_name || '-' }}</strong>
                  <small>{{ order.receiver_phone || '-' }}</small>
                </div>
              </td>
              <td>
                <span v-if="order.driver_name" class="driver-name">
                  {{ order.driver_name }}
                </span>
                <span v-else class="unassigned">
                  {{ $t('admin.orders.unassigned') }}
                </span>
              </td>
              <td>
                <span class="status-badge" :class="getStatusClass(order.prepare_status)">
                  {{ order.prepare_status_label }}
                </span>
              </td>
              <td>
                <div class="address-info">
                  {{ order.receiver_address || '-' }}
                  <small v-if="order.receiver_city || order.receiver_province">{{ order.receiver_city }}, {{ order.receiver_province }}</small>
                </div>
              </td>
              <td>
                {{ formatDate(order.create_time) }}
              </td>
              <td>
                <div class="action-buttons">
                  <button @click="viewOrder(order)" class="action-btn view" :title="$t('admin.orders.view')">
                    👁️
                  </button>
                  <button
                    v-if="!order.driver_id"
                    @click="assignOrder(order)"
                    class="action-btn assign"
                    :title="$t('admin.orders.assign')"
                  >
                    👤
                  </button>
                  <button
                    v-if="order.driver_id"
                    @click="reassignOrder(order)"
                    class="action-btn reassign"
                    :title="$t('admin.orders.reassign')"
                  >
                    🔄
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="isLoading" class="loading-overlay">
          <div class="loading-spinner">{{ $t('common.loading') }}...</div>
        </div>

        <div v-if="!isLoading && orders.length === 0" class="empty-state">
          <div class="empty-icon">📦</div>
          <h3>{{ $t('admin.orders.noOrders') }}</h3>
          <p>{{ $t('admin.orders.noOrdersDesc') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from '@/composables/useI18n';
import AdminNavigation from '@/components/AdminNavigation.vue';
import { getAdminOrders, type AdminOrderSummary } from '@/api/admin';

const { t } = useI18n();

// State
const searchQuery = ref('');
const statusFilter = ref('');
const driverFilter = ref('');
const isLoading = ref(false);
const orders = ref<AdminOrderSummary[]>([]);

const buildQueryParams = () => {
  const params: Record<string, string | number | boolean> = {};
  if (searchQuery.value.trim()) {
    params.search = searchQuery.value.trim();
  }
  if (statusFilter.value !== '') {
    params.status = Number(statusFilter.value);
  }
  if (driverFilter.value === 'unassigned') {
    params.unassigned = true;
  }
  return params;
};

const loadOrders = async () => {
  isLoading.value = true;
  try {
    orders.value = await getAdminOrders(buildQueryParams());
  } catch (error) {
    console.error('Failed to load orders:', error);
    orders.value = [];
  } finally {
    isLoading.value = false;
  }
};

// Methods
const refreshOrders = async () => {
  await loadOrders();
};

const debouncedSearch = (() => {
  let timeout: NodeJS.Timeout;
  return () => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      loadOrders();
    }, 300);
  };
})();

const applyFilters = () => {
  loadOrders();
};

const getStatusClass = (status?: number) => {
  switch (status) {
    case null:
    case undefined: return 'pending';
    case 0: return 'prepared';
    case 1: return 'pickup';
    case 2: return 'to-warehouse';
    case 3: return 'warehouse-received';
    case 6: return 'claimed';
    case 7: return 'delivered';
    default: return 'unknown';
  }
};

const viewOrder = (order: AdminOrderSummary) => {
  console.log('View order:', order);
  // Implement order detail view
};

const assignOrder = (order: AdminOrderSummary) => {
  console.log('Assign order:', order);
  // Implement order assignment
};

const reassignOrder = (order: AdminOrderSummary) => {
  console.log('Reassign order:', order);
  // Implement order reassignment
};

const formatDate = (dateString?: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString();
};

// Lifecycle
onMounted(() => {
  loadOrders();
});
</script>

<style scoped>
.admin-orders {
  min-height: 100vh;
  background-color: var(--color-bg-lighter);
}

.orders-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2xl);
}

.orders-header h1 {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.refresh-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-base);
}

.refresh-button:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.refresh-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.filters-section {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  align-items: center;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 300px;
}

.search-box input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-sm) 40px;
  border: 2px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-md);
}

.search-box input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.search-icon {
  position: absolute;
  left: var(--spacing-sm);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-light);
}

.filter-controls {
  display: flex;
  gap: var(--spacing-sm);
}

.filter-controls select {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  background: var(--color-white);
  font-size: var(--font-size-sm);
  min-width: 140px;
}

.orders-table-container {
  background: var(--color-white);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  position: relative;
}

.orders-table {
  width: 100%;
  border-collapse: collapse;
}

.orders-table th {
  background: var(--color-bg-lighter);
  padding: var(--spacing-md) var(--spacing-sm);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  border-bottom: 2px solid var(--color-gray-light);
}

.orders-table td {
  padding: var(--spacing-md) var(--spacing-sm);
  border-bottom: 1px solid var(--color-gray-light);
}

.order-row:hover {
  background: var(--color-bg-lighter);
}

.customer-info strong {
  display: block;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.customer-info small {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.driver-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.unassigned {
  color: var(--color-error);
  font-style: italic;
}

.address-info {
  max-width: 200px;
}

.address-info small {
  display: block;
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.status-badge {
  padding: var(--spacing-xxs) var(--spacing-xs);
  border-radius: var(--radius-xs);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.status-badge.pending { background: var(--color-warning-light); color: var(--color-warning-dark); }
.status-badge.prepared { background: var(--color-info-light); color: var(--color-info-dark); }
.status-badge.pickup { background: #e3f2fd; color: #1565c0; }
.status-badge.to-warehouse { background: #fff3e0; color: #e65100; }
.status-badge.warehouse-received { background: #e8f5e9; color: #2e7d32; }
.status-badge.claimed { background: #f3e5f5; color: #7b1fa2; }
.status-badge.delivered { background: var(--color-success-light); color: var(--color-success-dark); }
.status-badge.unknown { background: var(--color-error-light); color: var(--color-error); }

.order-count {
  display: inline-block;
  background: var(--color-primary-light);
  color: var(--color-primary);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
}

.action-buttons {
  display: flex;
  gap: var(--spacing-xxs);
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--radius-xs);
  font-size: var(--font-size-sm);
  transition: all var(--transition-base);
}

.action-btn:hover {
  background: var(--color-bg-lighter);
}

.action-btn.view:hover { background: var(--color-info-light); }
.action-btn.assign:hover { background: var(--color-success-light); }
.action-btn.reassign:hover { background: var(--color-warning-light); }

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-spinner {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
}

.empty-state {
  text-align: center;
  padding: 60px var(--spacing-lg);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: var(--spacing-md);
}

.empty-state h3 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.empty-state p {
  color: var(--color-text-secondary);
}

@media (max-width: 768px) {
  .orders-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }

  .filters-section {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    min-width: unset;
  }

  .orders-table-container {
    overflow-x: auto;
  }

  .orders-table {
    min-width: 800px;
  }
}
</style>
