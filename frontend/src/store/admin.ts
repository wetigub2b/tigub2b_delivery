import { defineStore } from 'pinia';
import {
  adminLogin,
  getAllDrivers,
  getDriver,
  createDriver,
  updateDriver,
  deleteDriver,
  activateDriver,
  deactivateDriver,
  getDashboardStats,
  getDriverPerformance,
  bulkDriverAction,
  assignOrderToDriver,
  dispatchOrders,
  getDriversPerformance,
  getDriverPerformanceLogs,
  getPerformanceAlerts,
  handleAlertAction,
  getPerformanceAnalytics,
  logDriverAction,
  type AdminLoginRequest,
  type Driver,
  type DriverCreate,
  type DriverUpdate,
  type DashboardStats,
  type DriverPerformance,
  type BulkActionRequest,
  type OrderDispatch,
  type DriverPerformanceMetrics,
  type DriverPerformanceLogEntry,
  type DriverAlert,
  type PerformanceAnalyticsRequest,
  type PerformanceComparisonResponse
} from '@/api/admin';

export interface AdminState {
  isAuthenticated: boolean;
  currentAdmin: any | null;
  drivers: Driver[];
  selectedDrivers: number[];
  dashboardStats: DashboardStats | null;

  // Performance monitoring state
  performanceMetrics: DriverPerformanceMetrics[];
  performanceLogs: DriverPerformanceLogEntry[];
  performanceAlerts: DriverAlert[];
  performanceAnalytics: PerformanceComparisonResponse[];

  isLoading: boolean;
  error: string | null;
}

export const useAdminStore = defineStore('admin', {
  state: (): AdminState => ({
    isAuthenticated: false,
    currentAdmin: null,
    drivers: [],
    selectedDrivers: [],
    dashboardStats: null,

    // Performance monitoring state
    performanceMetrics: [],
    performanceLogs: [],
    performanceAlerts: [],
    performanceAnalytics: [],

    isLoading: false,
    error: null
  }),

  getters: {
    activeDrivers: (state) => state.drivers.filter(d => d.status === '0' && d.del_flag === '0'),
    inactiveDrivers: (state) => state.drivers.filter(d => d.status === '1' && d.del_flag === '0'),
    adminDrivers: (state) => state.drivers.filter(d => d.role === 'admin' || d.role === 'super_admin'),
    regularDrivers: (state) => state.drivers.filter(d => d.role === 'driver'),
    hasSelectedDrivers: (state) => state.selectedDrivers.length > 0
  },

  actions: {
    async login(credentials: AdminLoginRequest) {
      this.isLoading = true;
      this.error = null;
      try {
        const tokens = await adminLogin(credentials);
        localStorage.setItem('admin_token', tokens.accessToken);
        localStorage.setItem('admin_refresh_token', tokens.refreshToken);
        this.isAuthenticated = true;
        return tokens;
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Login failed';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    logout() {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_refresh_token');
      this.isAuthenticated = false;
      this.currentAdmin = null;
      this.drivers = [];
      this.selectedDrivers = [];
      this.dashboardStats = null;
    },

    checkAuthStatus() {
      const token = localStorage.getItem('admin_token');
      this.isAuthenticated = !!token;
    },

    async fetchDashboardStats() {
      this.isLoading = true;
      try {
        this.dashboardStats = await getDashboardStats();
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch dashboard stats';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchDrivers(params?: {
      skip?: number;
      limit?: number;
      search?: string;
      role?: string;
      status?: string;
    }) {
      this.isLoading = true;
      try {
        this.drivers = await getAllDrivers(params);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch drivers';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchDriver(driverId: number) {
      this.isLoading = true;
      try {
        return await getDriver(driverId);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch driver';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async createDriver(driverData: DriverCreate) {
      this.isLoading = true;
      try {
        const newDriver = await createDriver(driverData);
        this.drivers.unshift(newDriver);
        return newDriver;
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to create driver';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async updateDriver(driverId: number, driverData: DriverUpdate) {
      this.isLoading = true;
      try {
        const updatedDriver = await updateDriver(driverId, driverData);
        const index = this.drivers.findIndex(d => d.user_id === driverId);
        if (index >= 0) {
          this.drivers.splice(index, 1, updatedDriver);
        }
        return updatedDriver;
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to update driver';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async deleteDriver(driverId: number) {
      this.isLoading = true;
      try {
        await deleteDriver(driverId);
        this.drivers = this.drivers.filter(d => d.user_id !== driverId);
        this.selectedDrivers = this.selectedDrivers.filter(id => id !== driverId);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to delete driver';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async activateDriver(driverId: number) {
      try {
        await activateDriver(driverId);
        const driver = this.drivers.find(d => d.user_id === driverId);
        if (driver) {
          driver.status = '0';
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to activate driver';
        throw error;
      }
    },

    async deactivateDriver(driverId: number) {
      try {
        await deactivateDriver(driverId);
        const driver = this.drivers.find(d => d.user_id === driverId);
        if (driver) {
          driver.status = '1';
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to deactivate driver';
        throw error;
      }
    },

    async getDriverPerformance(driverId: number) {
      this.isLoading = true;
      try {
        return await getDriverPerformance(driverId);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch driver performance';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async performBulkAction(actionData: BulkActionRequest) {
      this.isLoading = true;
      try {
        await bulkDriverAction(actionData);

        // Update local state based on action
        if (actionData.action === 'activate') {
          this.drivers.forEach(driver => {
            if (actionData.driver_ids.includes(driver.user_id)) {
              driver.status = '0';
            }
          });
        } else if (actionData.action === 'deactivate') {
          this.drivers.forEach(driver => {
            if (actionData.driver_ids.includes(driver.user_id)) {
              driver.status = '1';
            }
          });
        } else if (actionData.action === 'delete') {
          this.drivers = this.drivers.filter(d => !actionData.driver_ids.includes(d.user_id));
        } else if (actionData.action === 'assign_role' && actionData.value) {
          this.drivers.forEach(driver => {
            if (actionData.driver_ids.includes(driver.user_id)) {
              driver.role = actionData.value!;
            }
          });
        }

        this.selectedDrivers = [];
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Bulk action failed';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async assignOrder(orderSn: string, driverId: number, notes?: string) {
      try {
        await assignOrderToDriver(orderSn, driverId, notes);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to assign order';
        throw error;
      }
    },

    async dispatchOrders(dispatches: OrderDispatch[]) {
      this.isLoading = true;
      try {
        await dispatchOrders(dispatches);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to dispatch orders';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    // Selection management
    selectDriver(driverId: number) {
      if (!this.selectedDrivers.includes(driverId)) {
        this.selectedDrivers.push(driverId);
      }
    },

    deselectDriver(driverId: number) {
      this.selectedDrivers = this.selectedDrivers.filter(id => id !== driverId);
    },

    toggleDriverSelection(driverId: number) {
      if (this.selectedDrivers.includes(driverId)) {
        this.deselectDriver(driverId);
      } else {
        this.selectDriver(driverId);
      }
    },

    selectAllDrivers() {
      this.selectedDrivers = this.drivers.map(d => d.user_id);
    },

    clearSelection() {
      this.selectedDrivers = [];
    },

    clearError() {
      this.error = null;
    },

    // Performance monitoring actions
    async fetchDriversPerformance(params: {
      start_date: string;
      end_date: string;
      driver_ids?: number[];
    }) {
      this.isLoading = true;
      try {
        this.performanceMetrics = await getDriversPerformance(params);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch performance metrics';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchDriverPerformanceLogs(
      driverId: number,
      params?: {
        start_date?: string;
        end_date?: string;
        action_type?: string;
        skip?: number;
        limit?: number;
      }
    ) {
      this.isLoading = true;
      try {
        this.performanceLogs = await getDriverPerformanceLogs(driverId, params);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch performance logs';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchPerformanceAlerts(params?: {
      status?: string;
      severity?: string;
      driver_id?: number;
      skip?: number;
      limit?: number;
    }) {
      this.isLoading = true;
      try {
        this.performanceAlerts = await getPerformanceAlerts(params);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch performance alerts';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async handlePerformanceAlert(alertId: number, action: 'acknowledge' | 'resolve' | 'dismiss', notes?: string) {
      try {
        await handleAlertAction(alertId, action, notes);

        // Update local alert status
        const alert = this.performanceAlerts.find(a => a.id === alertId);
        if (alert) {
          alert.status = action === 'acknowledge' ? 'acknowledged' : action === 'resolve' ? 'resolved' : 'dismissed';
          if (action === 'acknowledge') {
            alert.acknowledged_at = new Date().toISOString();
          } else if (action === 'resolve') {
            alert.resolved_at = new Date().toISOString();
          }
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || `Failed to ${action} alert`;
        throw error;
      }
    },

    async fetchPerformanceAnalytics(analyticsRequest: PerformanceAnalyticsRequest) {
      this.isLoading = true;
      try {
        this.performanceAnalytics = await getPerformanceAnalytics(analyticsRequest);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch performance analytics';
        throw error;
      } finally {
        this.isLoading = false;
      }
    },

    async logDriverAction(params: {
      driver_id: number;
      action_type: string;
      latitude?: number;
      longitude?: number;
      order_id?: number;
      duration_minutes?: number;
      distance_km?: number;
      notes?: string;
    }) {
      try {
        await logDriverAction(params);
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to log driver action';
        throw error;
      }
    },

    // Performance monitoring getters
    getDriverPerformanceMetric(driverId: number, metric: string) {
      const driverMetrics = this.performanceMetrics.find(m => m.driver_id === driverId);
      return driverMetrics ? (driverMetrics as any)[metric] : null;
    },

    getActiveAlerts() {
      return this.performanceAlerts.filter(a => a.status === 'open');
    },

    getCriticalAlerts() {
      return this.performanceAlerts.filter(a => a.severity === 'critical' && a.status === 'open');
    },

    getDriverAlerts(driverId: number) {
      return this.performanceAlerts.filter(a => a.driver_id === driverId);
    }
  }
});