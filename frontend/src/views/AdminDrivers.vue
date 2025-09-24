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
            <option value="0">{{ $t('admin.drivers.active') }}</option>
            <option value="1">{{ $t('admin.drivers.inactive') }}</option>
          </select>

          <select v-model="roleFilter" @change="applyFilters">
            <option value="">{{ $t('admin.drivers.allRoles') }}</option>
            <option value="driver">{{ $t('admin.drivers.driver') }}</option>
            <option value="admin">{{ $t('admin.drivers.admin') }}</option>
            <option value="super_admin">{{ $t('admin.drivers.superAdmin') }}</option>
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
              <th>{{ $t('admin.drivers.vehicle') }}</th>
              <th>{{ $t('admin.drivers.role') }}</th>
              <th>{{ $t('admin.drivers.status') }}</th>
              <th>{{ $t('admin.drivers.lastLogin') }}</th>
              <th>{{ $t('admin.drivers.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="driver in drivers" :key="driver.user_id" class="driver-row">
              <td>
                <input
                  type="checkbox"
                  :checked="selectedDrivers.includes(driver.user_id)"
                  @change="toggleDriverSelection(driver.user_id)"
                />
              </td>
              <td>
                <div class="driver-info">
                  <strong>{{ driver.nick_name }}</strong>
                  <small>{{ driver.user_name }}</small>
                </div>
              </td>
              <td>{{ driver.phonenumber || '-' }}</td>
              <td>
                <div v-if="driver.vehicle_type || driver.license_plate" class="vehicle-info">
                  <div>{{ driver.vehicle_type || '-' }}</div>
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
                <span class="status-badge" :class="driver.status === '0' ? 'active' : 'inactive'">
                  {{ driver.status === '0' ? $t('admin.drivers.active') : $t('admin.drivers.inactive') }}
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
                    v-if="driver.status === '1'"
                    @click="activateDriver(driver.user_id)"
                    class="action-btn success"
                    :title="$t('admin.drivers.activate')"
                  >
                    ✅
                  </button>
                  <button
                    v-else
                    @click="deactivateDriver(driver.user_id)"
                    class="action-btn warning"
                    :title="$t('admin.drivers.deactivate')"
                  >
                    ⏸️
                  </button>
                  <button @click="deleteDriver(driver.user_id)" class="action-btn danger" :title="$t('admin.drivers.delete')">
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAdminStore } from '@/store/admin';
import { useI18n } from '@/composables/useI18n';
import AdminNavigation from '@/components/AdminNavigation.vue';
import DriverModal from '@/components/DriverModal.vue';
import DriverDetailModal from '@/components/DriverDetailModal.vue';
import type { Driver } from '@/api/admin';

const { t } = useI18n();
const adminStore = useAdminStore();

// State
const searchQuery = ref('');
const statusFilter = ref('');
const roleFilter = ref('');
const showCreateModal = ref(false);
const showEditModal = ref(false);
const showDetailModal = ref(false);
const selectedDriver = ref<Driver | null>(null);

// Computed
const drivers = computed(() => adminStore.drivers);
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
  } catch (err) {
    console.error('Failed to activate driver:', err);
  }
};

const deactivateDriver = async (driverId: number) => {
  if (!confirm(t('admin.drivers.confirmDeactivate'))) return;

  try {
    await adminStore.deactivateDriver(driverId);
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

const handleDriverSuccess = () => {
  closeModals();
  loadDrivers();
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
  background-color: #f7fafc;
}

.drivers-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.drivers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.drivers-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
}

.create-button {
  background: #48bb78;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s ease;
}

.create-button:hover {
  background: #38a169;
}

.button-icon {
  font-size: 16px;
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

.bulk-actions {
  background: white;
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.selection-count {
  font-weight: 600;
  color: #4a5568;
}

.bulk-buttons {
  display: flex;
  gap: 8px;
}

.bulk-button {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s ease;
}

.bulk-button.success { background: #48bb78; color: white; }
.bulk-button.warning { background: #ed8936; color: white; }
.bulk-button.danger { background: #e53e3e; color: white; }
.bulk-button.secondary { background: #718096; color: white; }

.bulk-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.error-banner {
  background: #fed7d7;
  color: #c53030;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-error {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #c53030;
}

.drivers-table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  overflow: hidden;
  position: relative;
}

.drivers-table {
  width: 100%;
  border-collapse: collapse;
}

.drivers-table th {
  background: #f7fafc;
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  color: #2d3748;
  border-bottom: 2px solid #e2e8f0;
}

.drivers-table td {
  padding: 16px 12px;
  border-bottom: 1px solid #e2e8f0;
}

.driver-row:hover {
  background: #f7fafc;
}

.driver-info strong {
  display: block;
  font-weight: 600;
  color: #2d3748;
}

.driver-info small {
  color: #718096;
  font-size: 12px;
}

.vehicle-info div {
  font-weight: 500;
}

.vehicle-info small {
  color: #718096;
  font-size: 12px;
}

.role-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.role-badge.driver { background: #bee3f8; color: #2b6cb0; }
.role-badge.admin { background: #fbb6ce; color: #b83280; }
.role-badge.super_admin { background: #fed7af; color: #c05621; }

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.active { background: #c6f6d5; color: #276749; }
.status-badge.inactive { background: #fed7d7; color: #c53030; }

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
.action-btn.edit:hover { background: #fef5e7; }
.action-btn.success:hover { background: #f0fff4; }
.action-btn.warning:hover { background: #fffaf0; }
.action-btn.danger:hover { background: #fff5f5; }

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
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .drivers-header {
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

  .filter-controls {
    flex-wrap: wrap;
  }

  .bulk-actions {
    flex-direction: column;
    gap: 16px;
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