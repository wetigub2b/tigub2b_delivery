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

    <!-- Package Detail Modal -->
    <PackageOrdersModal
      v-if="selectedOrder"
      :show="showDetailModal"
      :packageSn="selectedOrder.prepare_sn"
      :orderCount="selectedOrder.order_count"
      @close="closeDetailModal"
    />

    <!-- Assign Driver Modal -->
    <div v-if="showAssignModal" class="modal-overlay" @click.self="closeAssignModal">
      <div class="assign-modal">
        <div class="modal-header">
          <h2>{{ assigningOrder?.driver_id ? $t('admin.orders.reassign') : $t('admin.orders.assign') }}</h2>
          <button @click="closeAssignModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="order-info">
            <p><strong>备货单号:</strong> {{ assigningOrder?.prepare_sn }}</p>
            <p><strong>{{ $t('admin.orders.customer') }}:</strong> {{ assigningOrder?.receiver_name }}</p>
            <p><strong>{{ $t('admin.orders.address') }}:</strong> {{ assigningOrder?.receiver_address }}</p>
          </div>

          <div class="form-group">
            <label>{{ $t('admin.orders.selectDriver') }}</label>
            <select v-model="selectedDriverId" class="driver-select">
              <option value="">-- {{ $t('admin.orders.selectDriver') }} --</option>
              <option
                v-for="driver in availableDrivers"
                :key="driver.driver_id"
                :value="driver.driver_id"
              >
                {{ driver.name }} ({{ driver.nick_name }}) - {{ driver.phone }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>{{ $t('admin.orders.notes') }}</label>
            <textarea
              v-model="assignmentNotes"
              :placeholder="$t('admin.orders.notesPlaceholder')"
              rows="3"
            ></textarea>
          </div>

          <div v-if="assignError" class="error-message">
            {{ assignError }}
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeAssignModal" class="btn-cancel">
            {{ $t('common.cancel') }}
          </button>
          <button
            @click="confirmAssign"
            :disabled="!selectedDriverId || isAssigning"
            class="btn-confirm"
          >
            <span v-if="isAssigning">{{ $t('common.loading') }}...</span>
            <span v-else>{{ $t('common.confirm') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from '@/composables/useI18n';
import AdminNavigation from '@/components/AdminNavigation.vue';
import PackageOrdersModal from '@/components/PackageOrdersModal.vue';
import { getAdminOrders, getDispatchDrivers, assignOrderToDriver, type AdminOrderSummary, type DispatchDriver } from '@/api/admin';

const { t } = useI18n();

// State
const searchQuery = ref('');
const statusFilter = ref('');
const driverFilter = ref('');
const isLoading = ref(false);
const orders = ref<AdminOrderSummary[]>([]);
const showDetailModal = ref(false);
const selectedOrder = ref<AdminOrderSummary | null>(null);

// Assignment modal state
const showAssignModal = ref(false);
const assigningOrder = ref<AdminOrderSummary | null>(null);
const availableDrivers = ref<DispatchDriver[]>([]);
const selectedDriverId = ref<number | ''>('');
const assignmentNotes = ref('');
const isAssigning = ref(false);
const assignError = ref('');

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
  selectedOrder.value = order;
  showDetailModal.value = true;
};

const closeDetailModal = () => {
  showDetailModal.value = false;
  selectedOrder.value = null;
};

const loadDrivers = async () => {
  try {
    availableDrivers.value = await getDispatchDrivers();
  } catch (error) {
    console.error('Failed to load drivers:', error);
    availableDrivers.value = [];
  }
};

const openAssignModal = (order: AdminOrderSummary) => {
  assigningOrder.value = order;
  selectedDriverId.value = '';
  assignmentNotes.value = '';
  assignError.value = '';
  showAssignModal.value = true;
};

const closeAssignModal = () => {
  showAssignModal.value = false;
  assigningOrder.value = null;
  selectedDriverId.value = '';
  assignmentNotes.value = '';
  assignError.value = '';
};

const confirmAssign = async () => {
  if (!assigningOrder.value || !selectedDriverId.value) return;

  isAssigning.value = true;
  assignError.value = '';

  try {
    await assignOrderToDriver(
      assigningOrder.value.prepare_sn,
      selectedDriverId.value as number,
      assignmentNotes.value || undefined
    );
    closeAssignModal();
    await loadOrders(); // Refresh the orders list
  } catch (error: any) {
    console.error('Failed to assign order:', error);
    assignError.value = error.response?.data?.detail || t('admin.orders.assignFailed');
  } finally {
    isAssigning.value = false;
  }
};

const assignOrder = (order: AdminOrderSummary) => {
  openAssignModal(order);
};

const reassignOrder = (order: AdminOrderSummary) => {
  openAssignModal(order);
};

const formatDate = (dateString?: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString();
};

// Lifecycle
onMounted(() => {
  loadOrders();
  loadDrivers();
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

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.assign-modal {
  background: var(--color-white);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-gray-light);
}

.modal-header h2 {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-text-secondary);
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: var(--color-text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
}

.order-info {
  background: var(--color-bg-lighter);
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-lg);
}

.order-info p {
  margin: var(--spacing-xs) 0;
  color: var(--color-text-primary);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.driver-select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-md);
  background: var(--color-white);
}

.driver-select:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-group textarea {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 2px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-md);
  resize: vertical;
  font-family: inherit;
}

.form-group textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.error-message {
  color: var(--color-error);
  background: var(--color-error-light);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  margin-top: var(--spacing-md);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-gray-light);
}

.btn-cancel {
  padding: var(--spacing-sm) var(--spacing-lg);
  border: 2px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  background: var(--color-white);
  cursor: pointer;
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
}

.btn-cancel:hover {
  background: var(--color-bg-lighter);
}

.btn-confirm {
  padding: var(--spacing-sm) var(--spacing-lg);
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: var(--color-white);
  cursor: pointer;
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-base);
}

.btn-confirm:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

  .assign-modal {
    width: 95%;
    max-height: 80vh;
  }
}
</style>
