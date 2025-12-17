<template>
  <div class="admin-drivers">
    <AdminNavigation />

    <div class="drivers-content">
      <div class="drivers-header">
        <h1>{{ $t('admin.drivers.title') }}</h1>
        <div class="header-actions">
          <button @click="showCreateModal = true" class="create-button">
            <span class="button-icon">➕</span>
            {{ $t('admin.drivers.createDriver') }}
          </button>
        </div>
      </div>

      <!-- Filters and Search -->
      <div class="filters-section">
        <div class="search-box">
          <input
            v-model="searchQuery"
            type="text"
            :placeholder="$t('admin.drivers.searchPlaceholder')"
            @input="debouncedSearch"
          />
          <span class="search-icon">🔍</span>
        </div>

        <div class="filter-controls">
          <select v-model="statusFilter" @change="applyFilters">
            <option value="">{{ $t('admin.drivers.allStatus') }}</option>
            <option value="1">{{ $t('admin.drivers.active') }}</option>
            <option value="0">{{ $t('admin.drivers.inactive') }}</option>
          </select>

          <select v-model="roleFilter" @change="applyFilters">
            <option value="">{{ $t('admin.drivers.allRoles') }}</option>
            <option value="driver">{{ $t('admin.drivers.driver') }}</option>
            <option value="admin">{{ $t('admin.drivers.admin') }}</option>
            <option value="super_admin">{{ $t('admin.drivers.superAdmin') }}</option>
          </select>

          <select v-model="paymentFilter" @change="applyFilters">
            <option value="">{{ $t('admin.drivers.allPaymentStatus') }}</option>
            <option value="pending">{{ $t('admin.drivers.paymentNotSet') }}</option>
            <option value="onboarding">{{ $t('admin.drivers.paymentInProgress') }}</option>
            <option value="verified">{{ $t('admin.drivers.paymentReady') }}</option>
            <option value="restricted">{{ $t('admin.drivers.paymentRestricted') }}</option>
          </select>
        </div>
      </div>

      <!-- Bulk Actions -->
      <div v-if="hasSelectedDrivers" class="bulk-actions">
        <span class="selection-count">
          {{ $t('admin.drivers.selectedCount', { count: selectedDrivers.length }) }}
        </span>
        <div class="bulk-buttons">
          <button @click="performBulkAction('activate')" class="bulk-button success">
            {{ $t('admin.drivers.bulkActivate') }}
          </button>
          <button @click="performBulkAction('deactivate')" class="bulk-button warning">
            {{ $t('admin.drivers.bulkDeactivate') }}
          </button>
          <button @click="performBulkAction('delete')" class="bulk-button danger">
            {{ $t('admin.drivers.bulkDelete') }}
          </button>
          <button @click="clearSelection" class="bulk-button secondary">
            {{ $t('admin.drivers.clearSelection') }}
          </button>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="error-banner">
        {{ error }}
        <button @click="clearError" class="close-error">×</button>
      </div>

      <!-- Drivers Table -->
      <div class="drivers-table-container">
        <table class="drivers-table">
          <thead>
            <tr>
              <th>
                <input
                  type="checkbox"
                  :checked="allSelected"
                  @change="toggleSelectAll"
                />
              </th>
              <th>{{ $t('admin.drivers.name') }}</th>
              <th>{{ $t('admin.drivers.phone') }}</th>
              <th>{{ $t('admin.drivers.licenseNumber') }}</th>
              <th>{{ $t('admin.drivers.vehicle') }}</th>
              <th>{{ $t('admin.drivers.role') }}</th>
              <th>{{ $t('admin.drivers.status') }}</th>
              <th>{{ $t('admin.drivers.payment') }}</th>
              <th>{{ $t('admin.drivers.lastLogin') }}</th>
              <th>{{ $t('admin.drivers.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="driver in drivers" :key="driver.id" class="driver-row">
              <td>
                <input
                  type="checkbox"
                  :checked="selectedDrivers.includes(driver.id)"
                  @change="toggleDriverSelection(driver.id)"
                />
              </td>
              <td>
                <div class="driver-info">
                  <strong>{{ driver.nick_name }}</strong>
                  <small>{{ driver.user_name }}</small>
                </div>
              </td>
              <td>{{ driver.phonenumber || '-' }}</td>
              <td>{{ driver.license_number || '-' }}</td>
              <td>
                <div v-if="driver.vehicle_type || driver.license_plate || driver.vehicle_model" class="vehicle-info">
                  <div>{{ driver.vehicle_type || '-' }}</div>
                  <small>{{ driver.vehicle_model || '-' }}</small>
                  <small>{{ driver.license_plate || '-' }}</small>
                </div>
                <span v-else>-</span>
              </td>
              <td>
                <span class="role-badge" :class="driver.role">
                  {{ $t(`admin.drivers.${driver.role}`) }}
                </span>
              </td>
              <td>
                <span class="status-badge" :class="driver.status === 1 || driver.status === '1' ? 'active' : 'inactive'">
                  {{ driver.status === 1 || driver.status === '1' ? $t('admin.drivers.active') : $t('admin.drivers.inactive') }}
                </span>
              </td>
              <td>
                <span class="payment-badge" :class="getPaymentStatusClass(driver.stripe_status)">
                  {{ getPaymentStatusIcon(driver.stripe_status) }} {{ getPaymentStatusText(driver.stripe_status) }}
                </span>
              </td>
              <td>
                {{ driver.last_login ? formatDate(driver.last_login) : $t('admin.drivers.never') }}
              </td>
              <td>
                <div class="action-buttons">
                  <button @click="viewDriver(driver)" class="action-btn view" :title="$t('admin.drivers.view')">
                    👁️
                  </button>
                  <button @click="editDriver(driver)" class="action-btn edit" :title="$t('admin.drivers.edit')">
                    ✏️
                  </button>
                  <button
                    v-if="driver.status === 0 || driver.status === '0'"
                    @click="activateDriver(driver.id)"
                    class="action-btn success"
                    :title="$t('admin.drivers.activate')"
                  >
                    ✅
                  </button>
                  <button
                    v-else
                    @click="deactivateDriver(driver.id)"
                    class="action-btn warning"
                    :title="$t('admin.drivers.deactivate')"
                  >
                    ⏸️
                  </button>
                  <button @click="deleteDriver(driver.id)" class="action-btn danger" :title="$t('admin.drivers.delete')">
                    🗑️
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="isLoading" class="loading-overlay">
          <div class="loading-spinner">{{ $t('admin.drivers.loading') }}...</div>
        </div>

        <div v-if="!isLoading && drivers.length === 0" class="empty-state">
          <div class="empty-icon">👥</div>
          <h3>{{ $t('admin.drivers.noDrivers') }}</h3>
          <p>{{ $t('admin.drivers.noDriversDesc') }}</p>
          <button @click="showCreateModal = true" class="create-button">
            {{ $t('admin.drivers.createFirstDriver') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Driver Modal -->
    <DriverModal
      v-if="showCreateModal || showEditModal"
      :driver="selectedDriver"
      :isEdit="showEditModal"
      @close="closeModals"
      @success="handleDriverSuccess"
    />

    <!-- Driver Detail Modal -->
    <DriverDetailModal
      v-if="showDetailModal"
      :driver="selectedDriver"
      @close="showDetailModal = false"
      @edit="editDriver"
    />

    <!-- Success Notification Modal -->
    <NotificationModal
      v-if="showSuccessModal"
      type="success"
      :title="successTitle"
      :message="successMessage"
      @close="showSuccessModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAdminStore } from '@/store/admin';
import { useI18n } from '@/composables/useI18n';
import AdminNavigation from '@/components/AdminNavigation.vue';
import DriverModal from '@/components/DriverModal.vue';
import DriverDetailModal from '@/components/DriverDetailModal.vue';
import NotificationModal from '@/components/NotificationModal.vue';
import type { Driver } from '@/api/admin';

const { t } = useI18n();
const adminStore = useAdminStore();

// State
const searchQuery = ref('');
const statusFilter = ref('');
const roleFilter = ref('');
const paymentFilter = ref('');
const showCreateModal = ref(false);
const showEditModal = ref(false);
const showDetailModal = ref(false);
const selectedDriver = ref<Driver | null>(null);
const showSuccessModal = ref(false);
const successTitle = ref('');
const successMessage = ref('');

// Payment status helper functions
const getPaymentStatusClass = (stripeStatus: string | null | undefined): string => {
  switch (stripeStatus) {
    case 'verified':
      return 'payment-verified';
    case 'onboarding':
      return 'payment-onboarding';
    case 'restricted':
      return 'payment-restricted';
    default:
      return 'payment-pending';
  }
};

const getPaymentStatusIcon = (stripeStatus: string | null | undefined): string => {
  switch (stripeStatus) {
    case 'verified':
      return '\u2705'; // checkmark
    case 'onboarding':
      return '\uD83D\uDD04'; // arrows
    case 'restricted':
      return '\u26A0\uFE0F'; // warning
    default:
      return '\u274C'; // x
  }
};

const getPaymentStatusText = (stripeStatus: string | null | undefined): string => {
  switch (stripeStatus) {
    case 'verified':
      return t('admin.drivers.paymentReady');
    case 'onboarding':
      return t('admin.drivers.paymentInProgress');
    case 'restricted':
      return t('admin.drivers.paymentRestricted');
    default:
      return t('admin.drivers.paymentNotSet');
  }
};

// Computed
const drivers = computed(() => {
  let result = adminStore.drivers;
  // Filter by payment status (client-side since API doesn't support this filter yet)
  if (paymentFilter.value) {
    result = result.filter(driver => {
      const status = driver.stripe_status || 'pending';
      return status === paymentFilter.value;
    });
  }
  return result;
});
const selectedDrivers = computed(() => adminStore.selectedDrivers);
const hasSelectedDrivers = computed(() => adminStore.hasSelectedDrivers);
const isLoading = computed(() => adminStore.isLoading);
const error = computed(() => adminStore.error);

const allSelected = computed(() => {
  return drivers.value.length > 0 && selectedDrivers.value.length === drivers.value.length;
});

// Methods
const loadDrivers = async () => {
  try {
    await adminStore.fetchDrivers({
      search: searchQuery.value || undefined,
      status: statusFilter.value || undefined,
      role: roleFilter.value || undefined,
      limit: 100
    });
  } catch (err) {
    console.error('Failed to load drivers:', err);
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
  loadDrivers();
};

const toggleSelectAll = () => {
  if (allSelected.value) {
    adminStore.clearSelection();
  } else {
    adminStore.selectAllDrivers();
  }
};

const toggleDriverSelection = (driverId: number) => {
  adminStore.toggleDriverSelection(driverId);
};

const clearSelection = () => {
  adminStore.clearSelection();
};

const performBulkAction = async (action: 'activate' | 'deactivate' | 'delete') => {
  if (!hasSelectedDrivers.value) return;

  const confirmMessage = t(`admin.drivers.confirmBulk${action.charAt(0).toUpperCase() + action.slice(1)}`);
  if (!confirm(confirmMessage)) return;

  try {
    await adminStore.performBulkAction({
      action,
      driver_ids: selectedDrivers.value
    });
    await loadDrivers(); // Refresh the list
  } catch (err) {
    console.error(`Bulk ${action} failed:`, err);
  }
};

const viewDriver = (driver: Driver) => {
  selectedDriver.value = driver;
  showDetailModal.value = true;
};

const editDriver = (driver: Driver) => {
  selectedDriver.value = driver;
  showEditModal.value = true;
  showDetailModal.value = false;
};

const activateDriver = async (driverId: number) => {
  try {
    await adminStore.activateDriver(driverId);
    await loadDrivers(); // Refresh the list to show updated status
  } catch (err) {
    console.error('Failed to activate driver:', err);
  }
};

const deactivateDriver = async (driverId: number) => {
  if (!confirm(t('admin.drivers.confirmDeactivate'))) return;

  try {
    await adminStore.deactivateDriver(driverId);
    await loadDrivers(); // Refresh the list to show updated status
  } catch (err) {
    console.error('Failed to deactivate driver:', err);
  }
};

const deleteDriver = async (driverId: number) => {
  if (!confirm(t('admin.drivers.confirmDelete'))) return;

  try {
    await adminStore.deleteDriver(driverId);
  } catch (err) {
    console.error('Failed to delete driver:', err);
  }
};

const closeModals = () => {
  showCreateModal.value = false;
  showEditModal.value = false;
  selectedDriver.value = null;
};

const handleDriverSuccess = async (formData: any) => {
  try {
    if (showCreateModal.value) {
      // Creating a new driver - map form fields to API schema
      await adminStore.createDriver({
        name: formData.name,
        phone: formData.phone,
        email: formData.email,
        password: formData.password,
        license_number: formData.licenseNumber,
        vehicle_type: formData.vehicleType,
        vehicle_plate: formData.licensePlate,
        vehicle_model: formData.vehicleModel,
        notes: formData.notes
      });
      successTitle.value = t('admin.drivers.createSuccessTitle');
      successMessage.value = t('admin.drivers.createSuccessMessage');
    } else if (showEditModal.value && selectedDriver.value) {
      // Updating existing driver - use driver.id from tigu_driver table
      await adminStore.updateDriver(selectedDriver.value.id, {
        name: formData.name,
        phone: formData.phone,
        email: formData.email,
        license_number: formData.licenseNumber,
        vehicle_type: formData.vehicleType,
        vehicle_plate: formData.licensePlate,
        vehicle_model: formData.vehicleModel,
        notes: formData.notes,
        status: formData.status === 'active' ? 1 : 0
      });
      successTitle.value = t('admin.drivers.updateSuccessTitle');
      successMessage.value = t('admin.drivers.updateSuccessMessage');
    }
    closeModals();
    await loadDrivers();
    showSuccessModal.value = true;
  } catch (err) {
    console.error('Failed to save driver:', err);
  }
};

const clearError = () => {
  adminStore.clearError();
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString();
};

// Lifecycle
onMounted(() => {
  loadDrivers();
});
</script>

<style scoped>
.admin-drivers {
  min-height: 100vh;
  background-color: var(--color-bg-lighter);
}

.drivers-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

.drivers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2xl);
}

.drivers-header h1 {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.create-button {
  background: var(--color-success);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-sm);
  padding: var(--spacing-sm) var(--spacing-xl);
  cursor: pointer;
  font-weight: var(--font-weight-semibold);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  transition: all var(--transition-base);
}

.create-button:hover {
  background: var(--color-success-dark);
}

.button-icon {
  font-size: var(--font-size-md);
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

.bulk-actions {
  background: var(--color-white);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--shadow-sm);
}

.selection-count {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
}

.bulk-buttons {
  display: flex;
  gap: var(--spacing-xs);
}

.bulk-button {
  padding: var(--spacing-xs) var(--spacing-md);
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  transition: all var(--transition-base);
}

.bulk-button.success { background: var(--color-success); color: var(--color-white); }
.bulk-button.warning { background: var(--color-warning); color: var(--color-white); }
.bulk-button.danger { background: var(--color-error); color: var(--color-white); }
.bulk-button.secondary { background: var(--color-text-secondary); color: var(--color-white); }

.bulk-button:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.error-banner {
  background: var(--color-error-light);
  color: var(--color-error);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-lg);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-error {
  background: none;
  border: none;
  font-size: var(--font-size-lg);
  cursor: pointer;
  color: var(--color-error);
}

.drivers-table-container {
  background: var(--color-white);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  position: relative;
}

.drivers-table {
  width: 100%;
  border-collapse: collapse;
}

.drivers-table th {
  background: var(--color-bg-lighter);
  padding: var(--spacing-md) var(--spacing-sm);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  border-bottom: 2px solid var(--color-gray-light);
}

.drivers-table td {
  padding: var(--spacing-md) var(--spacing-sm);
  border-bottom: 1px solid var(--color-gray-light);
}

.driver-row:hover {
  background: var(--color-bg-lighter);
}

.driver-info strong {
  display: block;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.driver-info small {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.vehicle-info div {
  font-weight: var(--font-weight-medium);
}

.vehicle-info small {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
}

.role-badge {
  padding: var(--spacing-xxs) var(--spacing-xs);
  border-radius: var(--radius-xs);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
}

.role-badge.driver { background: var(--color-info-light); color: var(--color-info-dark); }
.role-badge.admin { background: var(--color-warning-light); color: var(--color-warning-dark); }
.role-badge.super_admin { background: var(--color-warning-light); color: var(--color-warning-dark); }

.status-badge {
  padding: var(--spacing-xxs) var(--spacing-xs);
  border-radius: var(--radius-xs);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.status-badge.active { background: var(--color-success-light); color: var(--color-success-dark); }
.status-badge.inactive { background: var(--color-error-light); color: var(--color-error); }

.payment-badge {
  padding: var(--spacing-xxs) var(--spacing-xs);
  border-radius: var(--radius-xs);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  white-space: nowrap;
}

.payment-badge.payment-pending { background: var(--color-gray-lighter, #f5f5f5); color: var(--color-text-secondary); }
.payment-badge.payment-onboarding { background: var(--color-info-light, #e3f2fd); color: var(--color-info-dark, #1565c0); }
.payment-badge.payment-verified { background: var(--color-success-light); color: var(--color-success-dark); }
.payment-badge.payment-restricted { background: var(--color-warning-light, #fff3e0); color: var(--color-warning-dark, #e65100); }

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
.action-btn.edit:hover { background: var(--color-warning-light); }
.action-btn.success:hover { background: var(--color-success-light); }
.action-btn.warning:hover { background: var(--color-warning-light); }
.action-btn.danger:hover { background: var(--color-error-light); }

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
  margin-bottom: var(--spacing-xl);
}

@media (max-width: 768px) {
  .drivers-header {
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

  .filter-controls {
    flex-wrap: wrap;
  }

  .bulk-actions {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: stretch;
  }

  .drivers-table-container {
    overflow-x: auto;
  }

  .drivers-table {
    min-width: 800px;
  }
}
</style>