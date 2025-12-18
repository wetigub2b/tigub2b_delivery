<template>
  <div class="admin-dashboard">
    <AdminNavigation />

    <div class="dashboard-content">
      <div class="dashboard-header">
        <h1>{{ $t('admin.dashboard.title') }}</h1>
        <button @click="refreshData" :disabled="isLoading" class="refresh-button">
          <span :class="{ 'spinning': isLoading }">🔄</span>
          {{ $t('admin.dashboard.refresh') }}
        </button>
      </div>

      <div v-if="error" class="error-banner">
        {{ error }}
        <button @click="clearError" class="close-error">×</button>
      </div>

      <!-- Stats Overview -->
      <div class="stats-grid">
        <div class="stat-card drivers">
          <div class="stat-icon">👥</div>
          <div class="stat-content">
            <h3>{{ $t('admin.dashboard.totalDrivers') }}</h3>
            <div class="stat-number">{{ dashboardStats?.total_drivers || 0 }}</div>
            <div class="stat-detail">
              {{ dashboardStats?.active_drivers || 0 }} {{ $t('admin.dashboard.active') }}
            </div>
          </div>
        </div>

        <div class="stat-card orders">
          <div class="stat-icon">📦</div>
          <div class="stat-content">
            <h3>{{ $t('admin.dashboard.totalOrders') }}</h3>
            <div class="stat-number">{{ dashboardStats?.total_orders || 0 }}</div>
            <div class="stat-detail">
              {{ dashboardStats?.pending_orders || 0 }} {{ $t('admin.dashboard.pending') }}
            </div>
          </div>
        </div>

        <div class="stat-card completion">
          <div class="stat-icon">✅</div>
          <div class="stat-content">
            <h3>{{ $t('admin.dashboard.completionRate') }}</h3>
            <div class="stat-number">{{ Math.round(dashboardStats?.completion_rate || 0) }}%</div>
            <div class="stat-detail">
              {{ dashboardStats?.completed_orders || 0 }} {{ $t('admin.dashboard.completed') }}
            </div>
          </div>
        </div>

        <div class="stat-card transit">
          <div class="stat-icon">🚚</div>
          <div class="stat-content">
            <h3>{{ $t('admin.dashboard.inTransit') }}</h3>
            <div class="stat-number">{{ dashboardStats?.in_transit_orders || 0 }}</div>
            <div class="stat-detail">
              {{ $t('admin.dashboard.activeDeliveries') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="quick-actions">
        <h2>{{ $t('admin.dashboard.quickActions') }}</h2>
        <div class="action-buttons">
          <router-link to="/admin/drivers" class="action-button primary">
            <span class="action-icon">👥</span>
            {{ $t('admin.dashboard.manageDrivers') }}
          </router-link>

          <router-link to="/admin/orders" class="action-button secondary">
            <span class="action-icon">📋</span>
            {{ $t('admin.dashboard.manageOrders') }}
          </router-link>

          <router-link v-if="featureFlags.adminDispatch" to="/admin/dispatch" class="action-button accent">
            <span class="action-icon">🚀</span>
            {{ $t('admin.dashboard.dispatchOrders') }}
          </router-link>

          <router-link v-if="featureFlags.adminReports" to="/admin/reports" class="action-button info">
            <span class="action-icon">📊</span>
            {{ $t('admin.dashboard.viewReports') }}
          </router-link>

          <router-link to="/admin/notifications" class="action-button notify">
            <span class="action-icon">🔔</span>
            {{ $t('admin.dashboard.sendNotifications') }}
          </router-link>
        </div>
      </div>

      <!-- Performance Alerts -->
      <div v-if="criticalAlerts.length > 0" class="alerts-section">
        <h2>🚨 Critical Performance Alerts</h2>
        <div class="alerts-grid">
          <div v-for="alert in criticalAlerts.slice(0, 3)" :key="alert.id" class="alert-card">
            <div class="alert-header">
              <span class="alert-title">{{ alert.title }}</span>
              <span :class="['alert-severity', alert.severity]">{{ alert.severity.toUpperCase() }}</span>
            </div>
            <p class="alert-description">{{ alert.description }}</p>
            <div class="alert-footer">
              <span class="alert-driver">{{ alert.driver_name }}</span>
              <div class="alert-actions">
                <button @click="handleAlert(alert.id, 'acknowledge')" class="alert-btn">
                  Acknowledge
                </button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="criticalAlerts.length > 3 && featureFlags.adminReports" class="view-all-alerts">
          <router-link to="/admin/reports" class="view-all-link">
            View All {{ criticalAlerts.length }} Alerts →
          </router-link>
        </div>
      </div>

      <!-- Top Performers -->
      <div v-if="topPerformers.length > 0" class="top-performers">
        <h2>🏆 Top Performing Drivers</h2>
        <div class="performers-grid">
          <div v-for="(driver, index) in topPerformers" :key="driver.driver_id" class="performer-card">
            <div class="performer-rank">{{ index + 1 }}</div>
            <div class="performer-info">
              <h3>{{ driver.driver_name }}</h3>
              <div class="performer-stats">
                <div class="stat">
                  <span class="stat-label">Success Rate</span>
                  <span :class="['stat-value', getPerformanceColor('success_rate', driver.success_rate)]">
                    {{ formatPercentage(driver.success_rate) }}
                  </span>
                </div>
                <div class="stat">
                  <span class="stat-label">Deliveries</span>
                  <span class="stat-value">{{ driver.total_deliveries }}</span>
                </div>
                <div v-if="driver.customer_rating" class="stat">
                  <span class="stat-label">Rating</span>
                  <span :class="['stat-value', getPerformanceColor('customer_rating', driver.customer_rating)]">
                    {{ formatRating(driver.customer_rating) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="recent-activity">
        <h2>{{ $t('admin.dashboard.recentActivity') }}</h2>
        <div class="activity-list">
          <div class="activity-item">
            <span class="activity-time">{{ $t('admin.dashboard.justNow') }}</span>
            <span class="activity-text">{{ $t('admin.dashboard.systemStatus') }}</span>
          </div>
          <!-- Add more activity items dynamically -->
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useAdminStore } from '@/store/admin';
import { useI18n } from '@/composables/useI18n';
import AdminNavigation from '@/components/AdminNavigation.vue';
import featureFlags from '@/config/features';

const { t } = useI18n();
const adminStore = useAdminStore();

const dashboardStats = computed(() => adminStore.dashboardStats);
const isLoading = computed(() => adminStore.isLoading);
const error = computed(() => adminStore.error);

// Performance monitoring computed properties
const criticalAlerts = computed(() => adminStore.getCriticalAlerts());
const topPerformers = computed(() => {
  return adminStore.performanceMetrics
    .sort((a, b) => b.success_rate - a.success_rate)
    .slice(0, 3);
});

const refreshData = async () => {
  try {
    await Promise.all([
      adminStore.fetchDashboardStats(),
      adminStore.fetchPerformanceAlerts(),
      adminStore.fetchDriversPerformance({
        start_date: getDateString(-30),
        end_date: getDateString(0)
      })
    ]);
  } catch (err) {
    console.error('Failed to refresh dashboard data:', err);
  }
};

const clearError = () => {
  adminStore.clearError();
};

const handleAlert = async (alertId: number, action: 'acknowledge' | 'resolve' | 'dismiss') => {
  try {
    await adminStore.handlePerformanceAlert(alertId, action);
  } catch (error) {
    console.error(`Failed to ${action} alert:`, error);
  }
};

// Helper functions
function getDateString(daysOffset: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysOffset);
  return date.toISOString().split('T')[0];
}

const formatPercentage = (value: number) => {
  return `${value.toFixed(1)}%`;
};

const formatRating = (value: number) => {
  return `${value.toFixed(1)}/5.0`;
};

const getPerformanceColor = (metric: string, value: number) => {
  switch (metric) {
    case 'success_rate':
      return value >= 95 ? 'excellent' : value >= 85 ? 'good' : value >= 70 ? 'fair' : 'poor';
    case 'customer_rating':
      return value >= 4.5 ? 'excellent' : value >= 4.0 ? 'good' : value >= 3.5 ? 'fair' : 'poor';
    case 'on_time_percentage':
      return value >= 90 ? 'excellent' : value >= 80 ? 'good' : value >= 70 ? 'fair' : 'poor';
    default:
      return 'neutral';
  }
};

onMounted(() => {
  refreshData();
});
</script>

<style scoped>
.admin-dashboard {
  min-height: 100vh;
  background-color: var(--color-bg-lighter);
}

.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2xl);
}

.dashboard-header h1 {
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-2xl);
}

.stat-card {
  background: var(--color-white);
  padding: var(--spacing-xl);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  transition: all var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.stat-card.drivers { border-left: 4px solid var(--color-info); }
.stat-card.orders { border-left: 4px solid var(--color-warning); }
.stat-card.completion { border-left: 4px solid var(--color-success); }
.stat-card.transit { border-left: 4px solid var(--color-primary); }

.stat-icon {
  font-size: 40px;
  opacity: 0.8;
}

.stat-content h3 {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-xxs);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-number {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xxs);
}

.stat-detail {
  font-size: var(--font-size-xs);
  color: var(--color-text-light);
}

.quick-actions {
  margin-bottom: var(--spacing-2xl);
}

.quick-actions h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.action-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  text-decoration: none;
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-base);
  color: var(--color-white);
}

.action-button.primary { background: var(--color-primary); }
.action-button.secondary { background: var(--color-text-secondary); }
.action-button.accent { background: var(--color-warning); }
.action-button.info { background: var(--color-info); }
.action-button.notify { background: var(--color-success); }

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.action-icon {
  font-size: var(--font-size-lg);
}

.recent-activity {
  background: var(--color-white);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-md);
}

.recent-activity h2 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-md);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.activity-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-gray-light);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-light);
  font-weight: var(--font-weight-medium);
}

.activity-text {
  color: var(--color-text-secondary);
}

/* Performance alerts styles */
.alerts-section {
  margin-bottom: var(--spacing-2xl);
}

.alerts-section h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
}

.alerts-grid {
  display: grid;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.alert-card {
  background: var(--color-white);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-md);
  border-left: 4px solid var(--color-error);
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.alert-title {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.alert-severity {
  padding: var(--spacing-xxs) var(--spacing-xs);
  border-radius: var(--radius-xs);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.alert-severity.critical {
  background: var(--color-error-light);
  color: var(--color-error);
}

.alert-description {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
  font-size: var(--font-size-sm);
}

.alert-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-driver {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
}

.alert-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: var(--color-white);
  cursor: pointer;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
}

.alert-btn:hover {
  background: var(--color-primary-dark);
  transform: translateY(-1px);
}

.view-all-alerts {
  text-align: center;
}

.view-all-link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: var(--font-weight-medium);
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.view-all-link:hover {
  background: var(--color-bg-lighter);
}

/* Top performers styles */
.top-performers {
  margin-bottom: var(--spacing-2xl);
}

.top-performers h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-lg);
}

.performers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
}

.performer-card {
  background: var(--color-white);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-md);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  transition: all var(--transition-base);
}

.performer-card:hover {
  transform: translateY(-2px);
}

.performer-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-circle);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-lg);
  color: var(--color-white);
}

.performer-card:nth-child(1) .performer-rank {
  background: var(--color-warning); /* Gold */
}

.performer-card:nth-child(2) .performer-rank {
  background: var(--color-text-light); /* Silver */
}

.performer-card:nth-child(3) .performer-rank {
  background: var(--color-primary); /* Bronze */
}

.performer-info h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.performer-stats {
  display: flex;
  gap: var(--spacing-md);
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xxs);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
}

.stat-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  padding: 2px var(--spacing-xs);
  border-radius: var(--radius-xs);
}

.stat-value.excellent {
  background: var(--color-success-light);
  color: var(--color-success-dark);
}

.stat-value.good {
  background: var(--color-info-light);
  color: var(--color-info-dark);
}

.stat-value.fair {
  background: var(--color-warning-light);
  color: var(--color-warning-dark);
}

.stat-value.poor {
  background: var(--color-error-light);
  color: var(--color-error);
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: var(--spacing-md);
    align-items: flex-start;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    grid-template-columns: 1fr;
  }
}
</style>