<template>
  <div class="admin-dispatch">
    <AdminNavigation />

    <div class="dispatch-content">
      <div class="dispatch-header">
        <h1>{{ $t('admin.dispatch.title') }}</h1>
        <div class="header-actions">
          <button @click="autoDispatch" :disabled="isLoading" class="auto-dispatch-btn">
            <span class="button-icon">🤖</span>
            {{ $t('admin.dispatch.autoDispatch') }}
          </button>
          <button @click="bulkDispatch" :disabled="selectedOrders.length === 0" class="bulk-dispatch-btn">
            <span class="button-icon">🚀</span>
            {{ $t('admin.dispatch.bulkDispatch') }}
          </button>
        </div>
      </div>

      <!-- Dispatch Stats -->
      <div class="dispatch-stats">
        <div class="stat-card pending">
          <div class="stat-icon">⏳</div>
          <div class="stat-content">
            <h3>{{ $t('admin.dispatch.pendingOrders') }}</h3>
            <div class="stat-number">{{ pendingOrders.length }}</div>
          </div>
        </div>

        <div class="stat-card drivers">
          <div class="stat-icon">👥</div>
          <div class="stat-content">
            <h3>{{ $t('admin.dispatch.availableDrivers') }}</h3>
            <div class="stat-number">{{ availableDrivers.length }}</div>
          </div>
        </div>

        <div class="stat-card assignments">
          <div class="stat-icon">✅</div>
          <div class="stat-content">
            <h3>{{ $t('admin.dispatch.todayAssignments') }}</h3>
            <div class="stat-number">{{ todayAssignments }}</div>
          </div>
        </div>
      </div>

      <!-- Dispatch Interface -->
      <div class="dispatch-interface">
        <!-- Pending Orders Column -->
        <div class="dispatch-column">
          <div class="column-header">
            <h3>{{ $t('admin.dispatch.pendingOrders') }}</h3>
            <div class="column-actions">
              <button @click="selectAllOrders" class="select-all-btn">
                {{ $t('admin.dispatch.selectAll') }}
              </button>
            </div>
          </div>

          <div class="order-list">
            <div v-if="ordersLoading" class="order-loading">
              {{ $t('common.loading') }}...
            </div>
            <div
              v-for="order in pendingOrders"
              :key="order.order_sn"
              class="order-card"
              :class="{ 'selected': selectedOrders.includes(order.order_sn) }"
              @click="toggleOrderSelection(order.order_sn)"
            >
              <div class="order-header">
                <input
                  type="checkbox"
                  :checked="selectedOrders.includes(order.order_sn)"
                  @click.stop
                  @change="toggleOrderSelection(order.order_sn)"
                />
                <strong>{{ order.order_sn }}</strong>
                <span class="priority-badge" :class="getPriorityClass(order)">
                  {{ getPriorityLabel(order) }}
                </span>
              </div>

              <div class="order-details">
                <div class="customer-info">
                  <strong>{{ order.receiver_name }}</strong>
                  <small>{{ order.receiver_phone }}</small>
                </div>
                <div class="address-info">
                  {{ order.receiver_address }}
                  <small>{{ order.receiver_city }}</small>
                </div>
                <div class="order-meta">
                  <span class="item-count">{{ order.items?.length || 0 }} items</span>
                  <span class="created-time">{{ formatTime(order.create_time) }}</span>
                </div>
              </div>

              <div class="order-actions">
                <button @click.stop="assignToDriver(order)" class="assign-btn">
                  {{ $t('admin.dispatch.assign') }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Available Drivers Column -->
        <div class="dispatch-column">
          <div class="column-header">
            <h3>{{ $t('admin.dispatch.availableDrivers') }}</h3>
            <div class="column-actions">
              <select v-model="driverSortBy" @change="sortDrivers">
                <option value="name">{{ $t('admin.dispatch.sortByName') }}</option>
                <option value="load">{{ $t('admin.dispatch.sortByLoad') }}</option>
                <option value="location">{{ $t('admin.dispatch.sortByLocation') }}</option>
              </select>
            </div>
          </div>

          <div class="driver-list">
            <div
              v-for="driver in availableDrivers"
              :key="driver.user_id ?? driver.driver_id"
              class="driver-card"
              @click="selectDriver(driver)"
              :class="{ 'selected': selectedDriver?.driver_id === driver.driver_id }"
            >
              <div class="driver-header">
                <div class="driver-avatar">
                  {{ driver.nick_name.charAt(0).toUpperCase() }}
                </div>
                <div class="driver-info">
                  <strong>{{ driver.nick_name }}</strong>
                  <small>{{ driver.vehicle_type || 'Vehicle' }}</small>
                </div>
                <div class="driver-status">
                  <span class="status-dot active"></span>
                  {{ $t('admin.dispatch.available') }}
                </div>
              </div>

              <div class="driver-details">
                <div class="driver-stats">
                  <div class="stat">
                    <span class="stat-label">{{ $t('admin.dispatch.currentLoad') }}</span>
                    <span class="stat-value">{{ driver.current_load }}/{{ driver.max_load || 10 }}</span>
                  </div>
                  <div class="stat">
                    <span class="stat-label">{{ $t('admin.dispatch.rating') }}</span>
                    <span class="stat-value">{{ driver.rating || 4.5 }}/5</span>
                  </div>
                </div>
                <div class="driver-location">
                  📍 {{ driver.current_location || 'Location updating...' }}
                </div>
              </div>

              <div class="driver-actions">
                <button @click.stop="assignSelectedToDriver(driver)"
                        :disabled="selectedOrders.length === 0"
                        class="assign-all-btn">
                  {{ $t('admin.dispatch.assignSelected') }} ({{ selectedOrders.length }})
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Assignment History Column -->
        <div class="dispatch-column">
          <div class="column-header">
            <h3>{{ $t('admin.dispatch.recentAssignments') }}</h3>
          </div>

          <div class="assignment-list">
            <div v-for="assignment in recentAssignments" :key="assignment.id" class="assignment-card">
              <div class="assignment-time">
                {{ formatTime(assignment.assigned_at) }}
              </div>
              <div class="assignment-details">
                <strong>{{ assignment.order_sn }}</strong>
                <span class="arrow">→</span>
                <strong>{{ assignment.driver_name }}</strong>
              </div>
              <div class="assignment-status">
                <span class="status-badge" :class="assignment.status">
                  {{ getAssignmentStatusLabel(assignment.status) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Assignment Modal -->
    <div v-if="showAssignmentModal" class="modal-overlay" @click="closeAssignmentModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ $t('admin.dispatch.assignOrder') }}</h3>
          <button @click="closeAssignmentModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="assignment-form">
            <div class="form-group">
              <label>{{ $t('admin.dispatch.order') }}</label>
              <div class="order-summary">
                <strong>{{ currentOrder?.order_sn }}</strong>
                <small>{{ currentOrder?.receiver_name }} - {{ currentOrder?.receiver_address }}</small>
              </div>
            </div>
            <div class="form-group">
              <label>{{ $t('admin.dispatch.selectDriver') }}</label>
              <select v-model="selectedDriverId">
                <option value="">{{ $t('admin.dispatch.chooseDriver') }}</option>
                <option v-for="driver in availableDrivers" :key="driver.user_id ?? driver.driver_id" :value="driver.driver_id">
                  {{ driver.nick_name }} ({{ driver.current_load || 0 }}/{{ driver.max_load || 10 }})
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>{{ $t('admin.dispatch.priority') }}</label>
              <select v-model="assignmentPriority">
                <option value="1">{{ $t('admin.dispatch.normal') }}</option>
                <option value="2">{{ $t('admin.dispatch.high') }}</option>
                <option value="3">{{ $t('admin.dispatch.urgent') }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>{{ $t('admin.dispatch.notes') }}</label>
              <textarea v-model="assignmentNotes" :placeholder="$t('admin.dispatch.notesPlaceholder')"></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeAssignmentModal" class="cancel-btn">{{ $t('common.cancel') }}</button>
          <button @click="confirmAssignment" :disabled="!selectedDriverId" class="confirm-btn">
            {{ $t('admin.dispatch.confirmAssignment') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useI18n } from '@/composables/useI18n';
import AdminNavigation from '@/components/AdminNavigation.vue';
import { getDispatchDrivers, getAdminOrders, type DispatchDriver, type AdminOrderSummary } from '@/api/admin';

const { t } = useI18n();

// State
const isLoading = ref(false);
const selectedOrders = ref<string[]>([]);
const selectedDriver = ref<DispatchDriver | null>(null);
const selectedDriverId = ref('');
const assignmentPriority = ref('1');
const assignmentNotes = ref('');
const driverSortBy = ref('name');
const showAssignmentModal = ref(false);
const currentOrder = ref<any>(null);
const todayAssignments = ref(15);
const driversLoading = ref(false);
const ordersLoading = ref(false);

// Mock data
const pendingOrders = ref<AdminOrderSummary[]>([]);

const availableDrivers = ref<DispatchDriver[]>([]);

const recentAssignments = ref([
  {
    id: 1,
    order_sn: 'ORD-2024-003',
    driver_name: 'Mike Johnson',
    assigned_at: '2024-01-15T12:00:00Z',
    status: 'accepted'
  },
  {
    id: 2,
    order_sn: 'ORD-2024-004',
    driver_name: 'Sarah Wilson',
    assigned_at: '2024-01-15T11:45:00Z',
    status: 'in_progress'
  }
]);

// Methods
const autoDispatch = async () => {
  isLoading.value = true;
  try {
    // Simulate auto dispatch logic
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log('Auto dispatch completed');
  } finally {
    isLoading.value = false;
  }
};

const bulkDispatch = () => {
  if (selectedOrders.value.length === 0) return;
  console.log('Bulk dispatch:', selectedOrders.value);
};

const toggleOrderSelection = (orderSn: string) => {
  const index = selectedOrders.value.indexOf(orderSn);
  if (index >= 0) {
    selectedOrders.value.splice(index, 1);
  } else {
    selectedOrders.value.push(orderSn);
  }
};

const selectAllOrders = () => {
  if (selectedOrders.value.length === pendingOrders.value.length) {
    selectedOrders.value = [];
  } else {
    selectedOrders.value = pendingOrders.value.map(order => order.order_sn);
  }
};

const selectDriver = (driver: DispatchDriver) => {
  selectedDriver.value = driver;
};

const assignToDriver = (order: AdminOrderSummary) => {
  currentOrder.value = order;
  showAssignmentModal.value = true;
};

const assignSelectedToDriver = (driver: DispatchDriver) => {
  if (selectedOrders.value.length === 0) return;
  console.log('Assign selected orders to driver:', { orders: selectedOrders.value, driver: driver.nick_name });
  selectedOrders.value = [];
};

const closeAssignmentModal = () => {
  showAssignmentModal.value = false;
  currentOrder.value = null;
  selectedDriverId.value = '';
  assignmentNotes.value = '';
  assignmentPriority.value = '1';
};

const confirmAssignment = () => {
  console.log('Confirm assignment:', {
    order: currentOrder.value?.order_sn,
    driver: selectedDriverId.value,
    priority: assignmentPriority.value,
    notes: assignmentNotes.value
  });
  closeAssignmentModal();
};

const sortDrivers = () => {
  // Implement driver sorting logic
  console.log('Sort drivers by:', driverSortBy.value);
};

const getPriorityLabel = (order: AdminOrderSummary) => {
  // Placeholder mapping; extend when backend exposes explicit priority.
  return t('admin.dispatch.normal');
};

const getPriorityClass = (order: AdminOrderSummary) => {
  return 'normal';
};

const getAssignmentStatusLabel = (status: string) => {
  switch (status) {
    case 'accepted': return t('admin.dispatch.accepted');
    case 'in_progress': return t('admin.dispatch.inProgress');
    case 'completed': return t('admin.dispatch.completed');
    default: return status;
  }
};

const formatTime = (dateString: string) => {
  return new Date(dateString).toLocaleTimeString();
};

const loadAvailableDrivers = async () => {
  driversLoading.value = true;
  try {
    availableDrivers.value = await getDispatchDrivers();
  } catch (error) {
    console.error('Failed to fetch available drivers', error);
  } finally {
    driversLoading.value = false;
  }
};

const loadPendingOrders = async () => {
  ordersLoading.value = true;
  try {
    pendingOrders.value = await getAdminOrders({
      status: 0,
      unassigned: true,
      limit: 200
    });
  } catch (error) {
    console.error('Failed to fetch pending orders', error);
    pendingOrders.value = [];
  } finally {
    ordersLoading.value = false;
  }
};

const refreshData = () => {
  loadAvailableDrivers();
  loadPendingOrders();
};

onMounted(() => {
  refreshData();
});
</script>

<style scoped>
.admin-dispatch {
  min-height: 100vh;
  background-color: #f7fafc;
}

.dispatch-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: 20px;
}

.dispatch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.dispatch-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.auto-dispatch-btn, .bulk-dispatch-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.auto-dispatch-btn {
  background: #667eea;
  color: white;
}

.bulk-dispatch-btn {
  background: #48bb78;
  color: white;
}

.auto-dispatch-btn:hover { background: #5a67d8; }
.bulk-dispatch-btn:hover { background: #38a169; }

.auto-dispatch-btn:disabled, .bulk-dispatch-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button-icon {
  font-size: 16px;
}

.dispatch-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card.pending { border-left: 4px solid #f6ad55; }
.stat-card.drivers { border-left: 4px solid #4299e1; }
.stat-card.assignments { border-left: 4px solid #48bb78; }

.stat-icon {
  font-size: 40px;
  opacity: 0.8;
}

.stat-content h3 {
  font-size: 14px;
  color: #718096;
  margin-bottom: 4px;
  font-weight: 600;
  text-transform: uppercase;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
}

.dispatch-interface {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
  min-height: 600px;
}

.dispatch-column {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  overflow: hidden;
}

.column-header {
  background: #f7fafc;
  padding: 16px 20px;
  border-bottom: 2px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.column-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
}

.column-actions button, .column-actions select {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  font-size: 12px;
  cursor: pointer;
}

.order-list, .driver-list, .assignment-list {
  max-height: 600px;
  overflow-y: auto;
  padding: 16px;
}

.order-loading {
  padding: 12px;
  text-align: center;
  color: #718096;
  font-weight: 500;
}

.order-card, .driver-card, .assignment-card {
  background: #f7fafc;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.order-card:hover, .driver-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
}

.order-card.selected, .driver-card.selected {
  border-color: #667eea;
  background: #edf2f7;
}

.order-header, .driver-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.priority-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}

.priority-badge.normal { background: #bee3f8; color: #2b6cb0; }
.priority-badge.high { background: #fbb6ce; color: #b83280; }
.priority-badge.urgent { background: #fed7d7; color: #c53030; }

.driver-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #667eea;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.driver-status {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.active { background: #48bb78; }

.order-details, .driver-details {
  margin-bottom: 12px;
}

.customer-info, .driver-info {
  margin-bottom: 8px;
}

.customer-info strong, .driver-info strong {
  display: block;
  font-weight: 600;
}

.customer-info small, .driver-info small {
  color: #718096;
  font-size: 12px;
}

.address-info {
  margin-bottom: 8px;
  color: #4a5568;
}

.address-info small {
  display: block;
  color: #718096;
  font-size: 12px;
}

.order-meta, .driver-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #718096;
}

.driver-stats {
  gap: 16px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 10px;
  text-transform: uppercase;
}

.stat-value {
  font-weight: 600;
  color: #2d3748;
}

.driver-location {
  font-size: 12px;
  color: #718096;
  margin-top: 8px;
}

.order-actions, .driver-actions {
  display: flex;
  gap: 8px;
}

.assign-btn, .assign-all-btn {
  flex: 1;
  padding: 8px 12px;
  background: #48bb78;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.assign-btn:hover, .assign-all-btn:hover { background: #38a169; }
.assign-all-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.assignment-card {
  cursor: default;
}

.assignment-time {
  font-size: 12px;
  color: #718096;
  margin-bottom: 8px;
}

.assignment-details {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.arrow {
  color: #718096;
}

.assignment-status {
  text-align: right;
}

.status-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}

.status-badge.accepted { background: #c6f6d5; color: #276749; }
.status-badge.in_progress { background: #bee3f8; color: #2b6cb0; }
.status-badge.completed { background: #fbb6ce; color: #b83280; }

/* Modal styles */
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

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #2d3748;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #718096;
}

.modal-body {
  padding: 20px;
}

.assignment-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #2d3748;
}

.order-summary {
  padding: 12px;
  background: #f7fafc;
  border-radius: 6px;
}

.order-summary strong {
  display: block;
  margin-bottom: 4px;
}

.order-summary small {
  color: #718096;
}

.form-group select, .form-group textarea {
  padding: 12px;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
}

.form-group textarea {
  min-height: 80px;
  resize: vertical;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #e2e8f0;
}

.cancel-btn, .confirm-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn {
  background: #e2e8f0;
  color: #4a5568;
}

.confirm-btn {
  background: #48bb78;
  color: white;
}

.cancel-btn:hover { background: #cbd5e0; }
.confirm-btn:hover { background: #38a169; }
.confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 1200px) {
  .dispatch-interface {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .dispatch-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .dispatch-stats {
    grid-template-columns: 1fr;
  }
}
</style>
