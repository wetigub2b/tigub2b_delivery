import client from './client';
import adminClient from './adminClient';

export interface AdminLoginRequest {
  username: string;
  password: string;
}

export interface Driver {
  user_id: number;
  user_name: string;
  nick_name: string;
  phonenumber?: string;
  email?: string;
  vehicle_type?: string;
  license_plate?: string;
  notes?: string;
  role: string;
  status: string;
  del_flag: string;
  created_at: string;
  last_login?: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface DriverCreate {
  name: string;
  phone: string;
  email?: string;
  password: string;
  license_number?: string;
  vehicle_type?: string;
  vehicle_plate?: string;
  vehicle_model?: string;
  notes?: string;
}

export interface DriverUpdate {
  nick_name?: string;
  phonenumber?: string;
  email?: string;
  vehicle_type?: string;
  license_plate?: string;
  notes?: string;
  status?: string;
  role?: string;
}

export interface DashboardStats {
  total_drivers: number;
  active_drivers: number;
  total_orders: number;
  pending_orders: number;
  in_transit_orders: number;
  completed_orders: number;
  completion_rate: number;
  average_delivery_time?: number;
}

export interface DriverPerformance {
  driver_id: number;
  total_orders: number;
  completed_orders: number;
  completion_rate: number;
  average_delivery_time?: number;
  customer_rating?: number;
  last_delivery?: string;
}

export interface OrderDispatch {
  order_sn: string;
  driver_id: number;
  priority?: number;
  notes?: string;
  estimated_pickup_time?: string;
  estimated_delivery_time?: string;
}

export interface DispatchDriver {
  driver_id: number;
  user_id?: number;
  name: string;
  nick_name: string;
  phone: string;
  vehicle_type?: string;
  vehicle_plate?: string;
  status: number;
  rating: number;
  total_deliveries: number;
  current_load: number;
  max_load?: number;
  current_location?: string;
  is_available: boolean;
}

export interface AdminWarehouseSnapshot {
  id: number;
  name: string;
  address: string;
  latitude?: number;
  longitude?: number;
}

export interface AdminOrderItem {
  sku_id: number;
  sku_code?: string;
  product_name: string;
  quantity: number;
}

export interface AdminOrderSummary {
  order_sn: string;
  shipping_status: number;
  order_status: number;
  driver_id?: number;
  driver_name?: string;
  receiver_name: string;
  receiver_phone: string;
  receiver_address: string;
  receiver_city?: string;
  receiver_province?: string;
  receiver_postal_code?: string;
  shipping_status_label: string;
  order_status_label: string;
  create_time: string;
  pickup_location?: AdminWarehouseSnapshot;
  items: AdminOrderItem[];
}

export interface BulkActionRequest {
  action: 'activate' | 'deactivate' | 'delete' | 'assign_role';
  driver_ids: number[];
  value?: string;
}

// Admin authentication
export async function adminLogin(credentials: AdminLoginRequest) {
  const { data } = await client.post<{ accessToken: string; refreshToken: string }>(
    '/auth/admin/login',
    credentials
  );
  return data;
}

// Dashboard
export async function getDashboardStats() {
  const { data } = await adminClient.get<DashboardStats>('/admin/dashboard');
  return data;
}

// Driver management
export async function getAllDrivers(params?: {
  skip?: number;
  limit?: number;
  search?: string;
  role?: string;
  status?: string;
}) {
  const { data } = await adminClient.get<Driver[]>('/admin/drivers', { params });
  return data;
}

export async function getDriver(driverId: number) {
  const { data } = await adminClient.get<Driver>(`/admin/drivers/${driverId}`);
  return data;
}

export async function createDriver(driverData: DriverCreate) {
  const { data } = await adminClient.post<Driver>('/admin/drivers', driverData);
  return data;
}

export async function updateDriver(driverId: number, driverData: DriverUpdate) {
  const { data } = await adminClient.put<Driver>(`/admin/drivers/${driverId}`, driverData);
  return data;
}

export async function deleteDriver(driverId: number) {
  await adminClient.delete(`/admin/drivers/${driverId}`);
}

export async function activateDriver(driverId: number) {
  await adminClient.post(`/admin/drivers/${driverId}/activate`);
}

export async function deactivateDriver(driverId: number) {
  await adminClient.post(`/admin/drivers/${driverId}/deactivate`);
}

export async function getDriverPerformance(driverId: number) {
  const { data } = await adminClient.get<DriverPerformance>(`/admin/drivers/${driverId}/performance`);
  return data;
}

export async function bulkDriverAction(actionData: BulkActionRequest) {
  await adminClient.post('/admin/drivers/bulk-action', actionData);
}

// Order assignment and dispatch
export async function assignOrderToDriver(orderSn: string, driverId: number, notes?: string) {
  await adminClient.post(`/admin/orders/${orderSn}/assign`, {
    driver_id: driverId,
    order_sn: orderSn,
    notes
  });
}

export async function dispatchOrders(dispatches: OrderDispatch[]) {
  await adminClient.post('/admin/orders/dispatch', dispatches);
}

export async function getDispatchDrivers() {
  const { data } = await adminClient.get<DispatchDriver[]>('/admin/dispatch/drivers');
  return data;
}

export async function getAdminOrders(params?: {
  status?: number;
  driver_id?: number;
  unassigned?: boolean;
  search?: string;
  limit?: number;
}) {
  const { data } = await adminClient.get<AdminOrderSummary[]>('/admin/orders', { params });
  return data;
}

// Performance monitoring interfaces
export interface DriverPerformanceMetrics {
  driver_id: number;
  driver_name: string;
  period_start: string;
  period_end: string;
  total_deliveries: number;
  successful_deliveries: number;
  failed_deliveries: number;
  success_rate: number;
  avg_delivery_time?: number;
  total_active_time?: number;
  total_distance?: number;
  orders_per_hour?: number;
  fuel_efficiency?: number;
  customer_rating?: number;
  on_time_percentage?: number;
}

export interface DriverPerformanceLogEntry {
  id: number;
  driver_id: number;
  order_id?: number;
  action_type: string;
  action_timestamp: string;
  duration_minutes?: number;
  distance_km?: number;
  status: string;
  notes?: string;
}

export interface DriverAlert {
  id: number;
  driver_id: number;
  driver_name: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  metric_value?: number;
  threshold_value?: number;
  status: string;
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

export interface PerformanceAnalyticsRequest {
  driver_ids?: number[];
  start_date: string;
  end_date: string;
  metrics?: string[];
}

export interface PerformanceComparisonResponse {
  driver_id: number;
  driver_name: string;
  metrics: Record<string, number>;
  rank: number;
  percentile: number;
}

export interface AlertActionRequest {
  alert_id: number;
  action: 'acknowledge' | 'resolve' | 'dismiss';
  notes?: string;
}

// Performance monitoring API functions
export async function getDriversPerformance(params: {
  start_date: string;
  end_date: string;
  driver_ids?: number[];
}) {
  const { data } = await adminClient.get<DriverPerformanceMetrics[]>('/admin/performance/drivers', {
    params
  });
  return data;
}

export async function getDriverPerformanceLogs(
  driverId: number,
  params?: {
    start_date?: string;
    end_date?: string;
    action_type?: string;
    skip?: number;
    limit?: number;
  }
) {
  const { data } = await adminClient.get<DriverPerformanceLogEntry[]>(
    `/admin/performance/drivers/${driverId}/logs`,
    { params }
  );
  return data;
}

export async function getPerformanceAlerts(params?: {
  status?: string;
  severity?: string;
  driver_id?: number;
  skip?: number;
  limit?: number;
}) {
  const { data } = await adminClient.get<DriverAlert[]>('/admin/performance/alerts', {
    params
  });
  return data;
}

export async function handleAlertAction(alertId: number, action: AlertActionRequest['action'], notes?: string) {
  await adminClient.post(`/admin/performance/alerts/${alertId}/action`, {
    alert_id: alertId,
    action,
    notes
  });
}

export async function getPerformanceAnalytics(analyticsRequest: PerformanceAnalyticsRequest) {
  const { data } = await adminClient.post<PerformanceComparisonResponse[]>(
    '/admin/performance/analytics',
    analyticsRequest
  );
  return data;
}

export async function logDriverAction(params: {
  driver_id: number;
  action_type: string;
  latitude?: number;
  longitude?: number;
  order_id?: number;
  duration_minutes?: number;
  distance_km?: number;
  notes?: string;
}) {
  await adminClient.post('/admin/performance/log', null, { params });
}
