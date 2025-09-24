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

          <router-link to="/admin/dispatch" class="action-button accent">
            <span class="action-icon">🚀</span>
            {{ $t('admin.dashboard.dispatchOrders') }}
          </router-link>

          <router-link to="/admin/reports" class="action-button info">
            <span class="action-icon">📊</span>
            {{ $t('admin.dashboard.viewReports') }}
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
        <div v-if="criticalAlerts.length > 3" class="view-all-alerts">
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
  background-color: #f7fafc;
}

.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.dashboard-header h1 {
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

.stats-grid {
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
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
}

.stat-card.drivers { border-left: 4px solid #4299e1; }
.stat-card.orders { border-left: 4px solid #f6ad55; }
.stat-card.completion { border-left: 4px solid #48bb78; }
.stat-card.transit { border-left: 4px solid #ed8936; }

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
  letter-spacing: 0.5px;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 4px;
}

.stat-detail {
  font-size: 12px;
  color: #a0aec0;
}

.quick-actions {
  margin-bottom: 40px;
}

.quick-actions h2 {
  font-size: 24px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 20px;
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.action-button {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s ease;
  color: white;
}

.action-button.primary { background: #667eea; }
.action-button.secondary { background: #718096; }
.action-button.accent { background: #f6ad55; }
.action-button.info { background: #4299e1; }

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
}

.action-icon {
  font-size: 20px;
}

.recent-activity {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
}

.recent-activity h2 {
  font-size: 20px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 16px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e2e8f0;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-time {
  font-size: 12px;
  color: #a0aec0;
  font-weight: 500;
}

.activity-text {
  color: #4a5568;
}

/* Performance alerts styles */
.alerts-section {
  margin-bottom: 40px;
}

.alerts-section h2 {
  font-size: 24px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 20px;
}

.alerts-grid {
  display: grid;
  gap: 16px;
  margin-bottom: 16px;
}

.alert-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  border-left: 4px solid #e53e3e;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.alert-title {
  font-weight: 600;
  color: #2d3748;
}

.alert-severity {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.alert-severity.critical {
  background: #fed7d7;
  color: #c53030;
}

.alert-description {
  color: #718096;
  margin-bottom: 16px;
  font-size: 14px;
}

.alert-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-driver {
  font-size: 14px;
  color: #4a5568;
  font-weight: 500;
}

.alert-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: #667eea;
  color: white;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.alert-btn:hover {
  background: #5a67d8;
  transform: translateY(-1px);
}

.view-all-alerts {
  text-align: center;
}

.view-all-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 6px;
  transition: background-color 0.2s ease;
}

.view-all-link:hover {
  background: #f7fafc;
}

/* Top performers styles */
.top-performers {
  margin-bottom: 40px;
}

.top-performers h2 {
  font-size: 24px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 20px;
}

.performers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.performer-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s ease;
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
  border-radius: 50%;
  font-weight: 700;
  font-size: 18px;
  color: white;
}

.performer-card:nth-child(1) .performer-rank {
  background: #f6ad55; /* Gold */
}

.performer-card:nth-child(2) .performer-rank {
  background: #a0aec0; /* Silver */
}

.performer-card:nth-child(3) .performer-rank {
  background: #ed8936; /* Bronze */
}

.performer-info h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 8px;
}

.performer-stats {
  display: flex;
  gap: 16px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #718096;
  font-weight: 500;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.stat-value.excellent {
  background: #c6f6d5;
  color: #276749;
}

.stat-value.good {
  background: #bee3f8;
  color: #2b6cb0;
}

.stat-value.fair {
  background: #fbb6ce;
  color: #b83280;
}

.stat-value.poor {
  background: #fed7d7;
  color: #c53030;
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    gap: 16px;
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