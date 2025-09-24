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
            <option value="0">{{ $t('admin.orders.pending') }}</option>
            <option value="1">{{ $t('admin.orders.shipped') }}</option>
            <option value="2">{{ $t('admin.orders.partialShipped') }}</option>
            <option value="3">{{ $t('admin.orders.delivered') }}</option>
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
              <th>{{ $t('admin.orders.orderNumber') }}</th>
              <th>{{ $t('admin.orders.customer') }}</th>
              <th>{{ $t('admin.orders.driver') }}</th>
              <th>{{ $t('admin.orders.status') }}</th>
              <th>{{ $t('admin.orders.address') }}</th>
              <th>{{ $t('admin.orders.createdAt') }}</th>
              <th>{{ $t('admin.orders.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in orders" :key="order.order_sn" class="order-row">
              <td>
                <strong>{{ order.order_sn }}</strong>
              </td>
              <td>
                <div class="customer-info">
                  <strong>{{ order.receiver_name }}</strong>
                  <small>{{ order.receiver_phone }}</small>
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
                <span class="status-badge" :class="getStatusClass(order.shipping_status)">
                  {{ getStatusLabel(order.shipping_status) }}
                </span>
              </td>
              <td>
                <div class="address-info">
                  {{ order.receiver_address }}
                  <small>{{ order.receiver_city }}, {{ order.receiver_province }}</small>
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
import { ref, computed, onMounted } from 'vue';
import { useI18n } from '@/composables/useI18n';
import AdminNavigation from '@/components/AdminNavigation.vue';

const { t } = useI18n();

// State
const searchQuery = ref('');
const statusFilter = ref('');
const driverFilter = ref('');
const isLoading = ref(false);
const orders = ref<any[]>([]);

// Mock data for demonstration
const mockOrders = [
  {
    order_sn: 'ORD-2024-001',
    receiver_name: 'John Doe',
    receiver_phone: '+1234567890',
    receiver_address: '123 Main St',
    receiver_city: 'Toronto',
    receiver_province: 'ON',
    shipping_status: 0,
    driver_id: null,
    driver_name: null,
    create_time: '2024-01-15T10:30:00Z'
  },
  {
    order_sn: 'ORD-2024-002',
    receiver_name: 'Jane Smith',
    receiver_phone: '+1234567891',
    receiver_address: '456 Oak Ave',
    receiver_city: 'Vancouver',
    receiver_province: 'BC',
    shipping_status: 1,
    driver_id: 1,
    driver_name: 'Mike Johnson',
    create_time: '2024-01-15T11:00:00Z'
  }
];

// Methods
const refreshOrders = async () => {
  isLoading.value = true;
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    orders.value = mockOrders;
  } catch (error) {
    console.error('Failed to load orders:', error);
  } finally {
    isLoading.value = false;
  }
};

const debouncedSearch = (() => {
  let timeout: NodeJS.Timeout;
  return () => {
    clearTimeout(timeout);
    timeout = setTimeout(applyFilters, 300);
  };
})();

const applyFilters = () => {
  // Apply filters logic here
  console.log('Applying filters:', { searchQuery: searchQuery.value, statusFilter: statusFilter.value, driverFilter: driverFilter.value });
};

const getStatusClass = (status: number) => {
  switch (status) {
    case 0: return 'pending';
    case 1: return 'shipped';
    case 2: return 'partial';
    case 3: return 'delivered';
    default: return 'unknown';
  }
};

const getStatusLabel = (status: number) => {
  switch (status) {
    case 0: return t('admin.orders.pending');
    case 1: return t('admin.orders.shipped');
    case 2: return t('admin.orders.partialShipped');
    case 3: return t('admin.orders.delivered');
    default: return t('admin.orders.unknown');
  }
};

const viewOrder = (order: any) => {
  console.log('View order:', order);
  // Implement order detail view
};

const assignOrder = (order: any) => {
  console.log('Assign order:', order);
  // Implement order assignment
};

const reassignOrder = (order: any) => {
  console.log('Reassign order:', order);
  // Implement order reassignment
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

// Lifecycle
onMounted(() => {
  refreshOrders();
});
</script>

<style scoped>
.admin-orders {
  min-height: 100vh;
  background-color: #f7fafc;
}

.orders-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.orders-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
}

.refresh-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s ease;
}

.refresh-button:hover:not(:disabled) {
  background: #5a67d8;
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
  gap: 20px;
  margin-bottom: 20px;
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
  padding: 12px 16px 12px 40px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 16px;
}

.search-box input:focus {
  outline: none;
  border-color: #667eea;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #a0aec0;
}

.filter-controls {
  display: flex;
  gap: 12px;
}

.filter-controls select {
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  font-size: 14px;
  min-width: 140px;
}

.orders-table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  overflow: hidden;
  position: relative;
}

.orders-table {
  width: 100%;
  border-collapse: collapse;
}

.orders-table th {
  background: #f7fafc;
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  color: #2d3748;
  border-bottom: 2px solid #e2e8f0;
}

.orders-table td {
  padding: 16px 12px;
  border-bottom: 1px solid #e2e8f0;
}

.order-row:hover {
  background: #f7fafc;
}

.customer-info strong {
  display: block;
  font-weight: 600;
  color: #2d3748;
}

.customer-info small {
  color: #718096;
  font-size: 12px;
}

.driver-name {
  font-weight: 500;
  color: #2d3748;
}

.unassigned {
  color: #e53e3e;
  font-style: italic;
}

.address-info {
  max-width: 200px;
}

.address-info small {
  display: block;
  color: #718096;
  font-size: 12px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.pending { background: #fef5e7; color: #d69e2e; }
.status-badge.shipped { background: #e6fffa; color: #319795; }
.status-badge.partial { background: #fbb6ce; color: #b83280; }
.status-badge.delivered { background: #c6f6d5; color: #276749; }
.status-badge.unknown { background: #fed7d7; color: #c53030; }

.action-buttons {
  display: flex;
  gap: 4px;
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  font-size: 14px;
  transition: background-color 0.2s ease;
}

.action-btn:hover {
  background: #f7fafc;
}

.action-btn.view:hover { background: #e6fffa; }
.action-btn.assign:hover { background: #f0fff4; }
.action-btn.reassign:hover { background: #fef5e7; }

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
  font-size: 18px;
  font-weight: 600;
  color: #667eea;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 24px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 8px;
}

.empty-state p {
  color: #718096;
}

@media (max-width: 768px) {
  .orders-header {
    flex-direction: column;
    gap: 16px;
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