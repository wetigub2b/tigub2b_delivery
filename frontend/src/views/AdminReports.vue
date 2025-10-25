<template>
  <div class="admin-reports">
    <AdminNavigation />

    <div class="reports-content">
      <div class="reports-header">
        <h1>{{ $t('admin.reports.title') }}</h1>
        <div class="header-actions">
          <div class="date-range-picker">
            <input
              v-model="startDate"
              type="date"
              @change="fetchPerformanceData"
              class="date-input"
            />
            <span class="date-separator">to</span>
            <input
              v-model="endDate"
              type="date"
              @change="fetchPerformanceData"
              class="date-input"
            />
          </div>
          <button @click="refreshData" :disabled="isLoading" class="refresh-button">
            <span :class="{ 'spinning': isLoading }">🔄</span>
            Refresh
          </button>
          <button @click="exportReports" class="export-button">
            <span class="button-icon">📊</span>
            Export
          </button>
        </div>
      </div>

      <!-- Performance Alerts -->
      <div v-if="criticalAlerts.length > 0" class="alerts-section">
        <h2>🚨 Critical Performance Alerts</h2>
        <div class="alerts-list">
          <div v-for="alert in criticalAlerts" :key="alert.id" class="alert-card critical">
            <div class="alert-header">
              <strong>{{ alert.title }}</strong>
              <span class="alert-severity">{{ alert.severity.toUpperCase() }}</span>
            </div>
            <p class="alert-description">{{ alert.description }}</p>
            <div class="alert-driver">Driver: {{ alert.driver_name }}</div>
            <div class="alert-actions">
              <button @click="handleAlert(alert.id, 'acknowledge')" class="alert-btn acknowledge">
                Acknowledge
              </button>
              <button @click="handleAlert(alert.id, 'resolve')" class="alert-btn resolve">
                Resolve
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Performance Metrics Overview -->
      <div v-if="performanceMetrics.length > 0" class="performance-summary">
        <h2>📊 Performance Summary</h2>
        <div class="summary-cards">
          <div class="summary-card">
            <div class="summary-icon">🚚</div>
            <div class="summary-content">
              <h3>Total Deliveries</h3>
              <div class="summary-value">
                {{ performanceMetrics.reduce((sum, m) => sum + m.total_deliveries, 0) }}
              </div>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-icon">✅</div>
            <div class="summary-content">
              <h3>Average Success Rate</h3>
              <div class="summary-value">
                {{ formatPercentage(performanceMetrics.reduce((sum, m) => sum + m.success_rate, 0) / performanceMetrics.length) }}
              </div>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-icon">⭐</div>
            <div class="summary-content">
              <h3>Average Rating</h3>
              <div class="summary-value">
                {{ formatRating(performanceMetrics.filter(m => m.customer_rating).reduce((sum, m) => sum + (m.customer_rating || 0), 0) / performanceMetrics.filter(m => m.customer_rating).length || 0) }}
              </div>
            </div>
          </div>
          <div class="summary-card">
            <div class="summary-icon">⏰</div>
            <div class="summary-content">
              <h3>Average On-Time Rate</h3>
              <div class="summary-value">
                {{ formatPercentage(performanceMetrics.filter(m => m.on_time_percentage).reduce((sum, m) => sum + (m.on_time_percentage || 0), 0) / performanceMetrics.filter(m => m.on_time_percentage).length || 0) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Driver Performance Table -->
      <div v-if="performanceMetrics.length > 0" class="performance-table-section">
        <div class="table-container">
          <div class="table-header">
            <h3>🏆 Driver Performance Metrics</h3>
          </div>
          <div class="performance-table">
            <table>
              <thead>
                <tr>
                  <th>Driver</th>
                  <th>Total Deliveries</th>
                  <th>Success Rate</th>
                  <th>Avg Delivery Time</th>
                  <th>Customer Rating</th>
                  <th>On-Time Rate</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="metric in performanceMetrics" :key="metric.driver_id" class="performance-row">
                  <td>
                    <div class="driver-info">
                      <strong>{{ metric.driver_name }}</strong>
                    </div>
                  </td>
                  <td>{{ formatNumber(metric.total_deliveries) }}</td>
                  <td>
                    <span :class="['performance-badge', getPerformanceColor('success_rate', metric.success_rate)]">
                      {{ formatPercentage(metric.success_rate) }}
                    </span>
                  </td>
                  <td>
                    {{ metric.avg_delivery_time ? `${metric.avg_delivery_time} min` : 'N/A' }}
                  </td>
                  <td>
                    <span v-if="metric.customer_rating" :class="['performance-badge', getPerformanceColor('customer_rating', metric.customer_rating)]">
                      {{ formatRating(metric.customer_rating) }}
                    </span>
                    <span v-else class="text-muted">N/A</span>
                  </td>
                  <td>
                    <span v-if="metric.on_time_percentage" :class="['performance-badge', getPerformanceColor('on_time_percentage', metric.on_time_percentage)]">
                      {{ formatPercentage(metric.on_time_percentage) }}
                    </span>
                    <span v-else class="text-muted">N/A</span>
                  </td>
                  <td>
                    <span class="status-indicator active">Active</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Charts Section -->
      <div class="charts-section">
        <div class="chart-row">
          <!-- Delivery Performance Chart -->
          <div class="chart-container">
            <div class="chart-header">
              <h3>{{ $t('admin.reports.deliveryPerformance') }}</h3>
              <div class="chart-controls">
                <select v-model="performanceChartType">
                  <option value="daily">{{ $t('admin.reports.daily') }}</option>
                  <option value="weekly">{{ $t('admin.reports.weekly') }}</option>
                  <option value="monthly">{{ $t('admin.reports.monthly') }}</option>
                </select>
              </div>
            </div>
            <div class="chart-placeholder">
              <div class="placeholder-content">
                <div class="placeholder-icon">📈</div>
                <p>{{ $t('admin.reports.chartPlaceholder') }}</p>
                <small>{{ $t('admin.reports.chartIntegration') }}</small>
              </div>
            </div>
          </div>

          <!-- Driver Performance Chart -->
          <div class="chart-container">
            <div class="chart-header">
              <h3>{{ $t('admin.reports.driverPerformance') }}</h3>
            </div>
            <div class="chart-placeholder">
              <div class="placeholder-content">
                <div class="placeholder-icon">👥</div>
                <p>{{ $t('admin.reports.driverChartPlaceholder') }}</p>
                <small>{{ $t('admin.reports.chartIntegration') }}</small>
              </div>
            </div>
          </div>
        </div>

        <div class="chart-row">
          <!-- Revenue Trends -->
          <div class="chart-container full-width">
            <div class="chart-header">
              <h3>{{ $t('admin.reports.revenueTrends') }}</h3>
              <div class="chart-legend">
                <span class="legend-item">
                  <span class="legend-color primary"></span>
                  {{ $t('admin.reports.revenue') }}
                </span>
                <span class="legend-item">
                  <span class="legend-color secondary"></span>
                  {{ $t('admin.reports.costs') }}
                </span>
                <span class="legend-item">
                  <span class="legend-color accent"></span>
                  {{ $t('admin.reports.profit') }}
                </span>
              </div>
            </div>
            <div class="chart-placeholder large">
              <div class="placeholder-content">
                <div class="placeholder-icon">💹</div>
                <p>{{ $t('admin.reports.revenueChartPlaceholder') }}</p>
                <small>{{ $t('admin.reports.chartIntegration') }}</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Data Tables Section -->
      <div class="tables-section">
        <div class="table-row">
          <!-- Top Performing Drivers -->
          <div class="table-container">
            <div class="table-header">
              <h3>{{ $t('admin.reports.topDrivers') }}</h3>
              <select v-model="driverMetric">
                <option value="deliveries">{{ $t('admin.reports.byDeliveries') }}</option>
                <option value="revenue">{{ $t('admin.reports.byRevenue') }}</option>
                <option value="rating">{{ $t('admin.reports.byRating') }}</option>
              </select>
            </div>
            <div class="data-table">
              <table>
                <thead>
                  <tr>
                    <th>{{ $t('admin.reports.rank') }}</th>
                    <th>{{ $t('admin.reports.driver') }}</th>
                    <th>{{ $t('admin.reports.deliveries') }}</th>
                    <th>{{ $t('admin.reports.revenue') }}</th>
                    <th>{{ $t('admin.reports.rating') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(driver, index) in topDrivers" :key="driver.id">
                    <td>
                      <span class="rank-badge" :class="getRankClass(index)">
                        {{ index + 1 }}
                      </span>
                    </td>
                    <td>
                      <div class="driver-info">
                        <strong>{{ driver.name }}</strong>
                        <small>{{ driver.vehicle }}</small>
                      </div>
                    </td>
                    <td>{{ driver.deliveries }}</td>
                    <td>${{ formatNumber(driver.revenue) }}</td>
                    <td>
                      <div class="rating">
                        <span class="stars">⭐</span>
                        {{ driver.rating }}
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Recent Activity Log -->
          <div class="table-container">
            <div class="table-header">
              <h3>{{ $t('admin.reports.recentActivity') }}</h3>
            </div>
            <div class="activity-log">
              <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
                <div class="activity-time">
                  {{ formatTime(activity.timestamp) }}
                </div>
                <div class="activity-content">
                  <span class="activity-icon" :class="activity.type">
                    {{ getActivityIcon(activity.type) }}
                  </span>
                  <div class="activity-details">
                    <strong>{{ activity.title }}</strong>
                    <small>{{ activity.description }}</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Export Options -->
      <div class="export-section">
        <div class="export-card">
          <h3>{{ $t('admin.reports.exportOptions') }}</h3>
          <p>{{ $t('admin.reports.exportDescription') }}</p>
          <div class="export-buttons">
            <button @click="exportToPDF" class="export-btn pdf">
              <span class="export-icon">📄</span>
              {{ $t('admin.reports.exportPDF') }}
            </button>
            <button @click="exportToExcel" class="export-btn excel">
              <span class="export-icon">📊</span>
              {{ $t('admin.reports.exportExcel') }}
            </button>
            <button @click="exportToCSV" class="export-btn csv">
              <span class="export-icon">📋</span>
              {{ $t('admin.reports.exportCSV') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAdminStore } from '@/store/admin';
import AdminNavigation from '@/components/AdminNavigation.vue';

const adminStore = useAdminStore();

// State
const isLoading = ref(false);
const startDate = ref(getDateString(-30)); // 30 days ago
const endDate = ref(getDateString(0)); // today

// Computed properties
const criticalAlerts = computed(() => adminStore.getCriticalAlerts());
const performanceMetrics = computed(() => adminStore.performanceMetrics);
const performanceAlerts = computed(() => adminStore.performanceAlerts);
const performanceAnalytics = computed(() => adminStore.performanceAnalytics);

// Helper functions
function getDateString(daysOffset: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysOffset);
  return date.toISOString().split('T')[0];
}

// Methods
const fetchPerformanceData = async () => {
  if (!startDate.value || !endDate.value) return;

  isLoading.value = true;
  try {
    await Promise.all([
      adminStore.fetchDriversPerformance({
        start_date: startDate.value,
        end_date: endDate.value
      }),
      adminStore.fetchPerformanceAlerts(),
      adminStore.fetchPerformanceAnalytics({
        start_date: startDate.value,
        end_date: endDate.value,
        metrics: ['delivery_rate', 'avg_time', 'customer_rating', 'on_time_percentage', 'efficiency']
      })
    ]);
  } catch (error) {
    console.error('Failed to fetch performance data:', error);
  } finally {
    isLoading.value = false;
  }
};

const refreshData = async () => {
  await fetchPerformanceData();
};

const handleAlert = async (alertId: number, action: 'acknowledge' | 'resolve' | 'dismiss') => {
  try {
    await adminStore.handlePerformanceAlert(alertId, action);
  } catch (error) {
    console.error(`Failed to ${action} alert:`, error);
  }
};

const exportReports = () => {
  console.log('Exporting performance reports');
  // Implement export functionality
  const csvData = generateCSVData();
  downloadCSV(csvData, `performance-report-${startDate.value}-to-${endDate.value}.csv`);
};

const generateCSVData = () => {
  const headers = ['Driver Name', 'Total Deliveries', 'Success Rate', 'Avg Delivery Time', 'Customer Rating', 'On Time %'];
  const rows = performanceMetrics.value.map(metric => [
    metric.driver_name,
    metric.total_deliveries,
    `${metric.success_rate.toFixed(1)}%`,
    metric.avg_delivery_time ? `${metric.avg_delivery_time} min` : 'N/A',
    metric.customer_rating ? metric.customer_rating.toFixed(1) : 'N/A',
    metric.on_time_percentage ? `${metric.on_time_percentage}%` : 'N/A'
  ]);

  return [headers, ...rows].map(row => row.join(',')).join('\n');
};

const downloadCSV = (csvData: string, filename: string) => {
  const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

const formatNumber = (value: number) => {
  return value.toLocaleString();
};

const formatPercentage = (value: number) => {
  return `${value.toFixed(1)}%`;
};

const formatRating = (value: number) => {
  return `${value.toFixed(1)}/5.0`;
};

const getSeverityClass = (severity: string) => {
  return severity.toLowerCase();
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
  fetchPerformanceData();
});
</script>

<style scoped>
.admin-reports {
  min-height: 100vh;
  background-color: #f7fafc;
}

/* Date range picker styles */
.date-range-picker {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-input {
  padding: 8px 12px;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  font-size: 14px;
}

.date-separator {
  color: #718096;
  font-weight: 500;
}

.refresh-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s ease;
}

.refresh-button:hover:not(:disabled) {
  background: #3182ce;
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

/* Alert styles */
.alerts-section {
  margin-bottom: 30px;
}

.alerts-section h2 {
  font-size: 24px;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 20px;
}

.alerts-list {
  display: grid;
  gap: 16px;
}

.alert-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  border-left: 4px solid transparent;
}

.alert-card.critical {
  border-left-color: #e53e3e;
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.alert-severity {
  background: #fed7d7;
  color: #c53030;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.alert-description {
  color: #718096;
  margin-bottom: 12px;
}

.alert-driver {
  font-size: 14px;
  color: #4a5568;
  margin-bottom: 16px;
}

.alert-actions {
  display: flex;
  gap: 8px;
}

.alert-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.alert-btn.acknowledge {
  background: #fbb6ce;
  color: #b83280;
}

.alert-btn.resolve {
  background: #c6f6d5;
  color: #276749;
}

.alert-btn:hover {
  transform: translateY(-1px);
}

/* Performance summary styles */
.performance-summary {
  margin-bottom: 30px;
}

.performance-summary h2 {
  font-size: 24px;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 20px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.summary-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
}

.summary-icon {
  font-size: 40px;
  opacity: 0.8;
}

.summary-content h3 {
  font-size: 14px;
  color: #718096;
  margin-bottom: 8px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #2d3748;
}

/* Performance table styles */
.performance-table-section {
  margin-bottom: 30px;
}

.performance-table {
  overflow-x: auto;
}

.performance-table table {
  width: 100%;
  border-collapse: collapse;
}

.performance-table th {
  background: #f7fafc;
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  color: #2d3748;
  border-bottom: 2px solid #e2e8f0;
  font-size: 14px;
}

.performance-table td {
  padding: 16px 12px;
  border-bottom: 1px solid #e2e8f0;
}

.performance-row:hover {
  background: #f7fafc;
}

.performance-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  display: inline-block;
}

.performance-badge.excellent {
  background: #c6f6d5;
  color: #276749;
}

.performance-badge.good {
  background: #bee3f8;
  color: #2b6cb0;
}

.performance-badge.fair {
  background: #fbb6ce;
  color: #b83280;
}

.performance-badge.poor {
  background: #fed7d7;
  color: #c53030;
}

.performance-badge.neutral {
  background: #e2e8f0;
  color: #4a5568;
}

.status-indicator {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.status-indicator.active {
  background: #c6f6d5;
  color: #276749;
}

.text-muted {
  color: #a0aec0;
  font-style: italic;
}

.reports-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.reports-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.reports-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.period-selector {
  padding: 10px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  font-size: 14px;
  font-weight: 500;
}

.export-button {
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

.export-button:hover {
  background: #5a67d8;
}

.button-icon {
  font-size: 16px;
}

.metrics-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.metric-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
}

.metric-card.revenue { border-left: 4px solid #48bb78; }
.metric-card.deliveries { border-left: 4px solid #4299e1; }
.metric-card.efficiency { border-left: 4px solid #f6ad55; }
.metric-card.satisfaction { border-left: 4px solid #ed8936; }

.metric-icon {
  font-size: 40px;
  opacity: 0.8;
}

.metric-content h3 {
  font-size: 14px;
  color: #718096;
  margin-bottom: 4px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 4px;
}

.metric-change {
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.metric-change.positive { color: #48bb78; }
.metric-change.negative { color: #48bb78; }

.charts-section {
  margin-bottom: 40px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-row:last-child {
  margin-bottom: 0;
}

.chart-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  overflow: hidden;
}

.chart-container.full-width {
  grid-column: 1 / -1;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.chart-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
}

.chart-controls select {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  font-size: 12px;
}

.chart-legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #718096;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.primary { background: #667eea; }
.legend-color.secondary { background: #f6ad55; }
.legend-color.accent { background: #48bb78; }

.chart-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7fafc;
}

.chart-placeholder.large {
  height: 400px;
}

.placeholder-content {
  text-align: center;
  color: #718096;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.placeholder-content p {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.placeholder-content small {
  font-size: 12px;
  opacity: 0.7;
}

.tables-section {
  margin-bottom: 40px;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e2e8f0;
}

.table-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
}

.table-header select {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  font-size: 12px;
}

.data-table {
  overflow-x: auto;
}

.data-table table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #f7fafc;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #718096;
  font-size: 12px;
  text-transform: uppercase;
  border-bottom: 1px solid #e2e8f0;
}

.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  color: white;
}

.rank-badge.gold { background: #f6ad55; }
.rank-badge.silver { background: #a0aec0; }
.rank-badge.bronze { background: #ed8936; }
.rank-badge.regular { background: #718096; }

.driver-info strong {
  display: block;
  font-weight: 600;
  color: #2d3748;
}

.driver-info small {
  color: #718096;
  font-size: 12px;
}

.rating {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stars {
  color: #f6ad55;
}

.activity-log {
  max-height: 400px;
  overflow-y: auto;
  padding: 16px;
}

.activity-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #e2e8f0;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-time {
  font-size: 12px;
  color: #a0aec0;
  white-space: nowrap;
  min-width: 80px;
}

.activity-content {
  display: flex;
  gap: 8px;
  flex: 1;
}

.activity-icon {
  font-size: 16px;
}

.activity-details strong {
  display: block;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 2px;
}

.activity-details small {
  color: #718096;
  font-size: 12px;
}

.export-section {
  margin-bottom: 20px;
}

.export-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
}

.export-card h3 {
  font-size: 20px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 8px;
}

.export-card p {
  color: #718096;
  margin-bottom: 16px;
}

.export-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.export-btn.pdf {
  background: #e53e3e;
  color: white;
}

.export-btn.excel {
  background: #38a169;
  color: white;
}

.export-btn.csv {
  background: #4299e1;
  color: white;
}

.export-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.export-icon {
  font-size: 16px;
}

@media (max-width: 1200px) {
  .chart-row {
    grid-template-columns: 1fr;
  }

  .table-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .reports-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .metrics-overview {
    grid-template-columns: 1fr;
  }

  .export-buttons {
    flex-direction: column;
  }
}
</style>