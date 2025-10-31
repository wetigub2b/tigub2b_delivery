import client from './client';

export interface OrderItemDto {
  skuId: number;
  skuCode: string;
  productName: string;
  quantity: number;
  skuImage?: string;
}

export interface DeliveryOrderDto {
  orderSn: string;
  shippingStatus: number;
  shippingType: number; // 0=Direct to user, 1=Via warehouse
  orderStatus: number;
  driverId?: number;
  driverName?: string;
  receiverName: string;
  receiverPhone: string;
  receiverAddress: string;
  receiverCity: string;
  receiverProvince: string;
  receiverPostalCode: string;
  shippingStatusLabel: string;
  orderStatusLabel: string;
  createTime: string;
  // Timestamp fields for workflow tracking
  driverReceiveTime?: string;
  arriveWarehouseTime?: string;
  warehouseShippingTime?: string;
  shippingTime?: string;
  finishTime?: string;
  pickupLocation?: {
    id: number;
    name: string;
    address: string;
    latitude?: number;
    longitude?: number;
  };
  items: OrderItemDto[];
}

export interface RoutePlanDto {
  id: string;
  stops: Array<{
    orderSn: string;
    sequence: number;
    address: string;
    receiverName: string;
    eta: string;
    latitude?: number;
    longitude?: number;
  }>;
}

export interface DeliveryProofDto {
  status: string;
  photoUrl: string;
  orderSn: string;
  uploadedAt: string;
}

export interface PickupRequest {
  photo: string; // Base64 encoded image or data URL
  notes?: string;
}

export interface PickupResponse {
  success: boolean;
  message: string;
  orderSn: string;
  shippingStatus: number;
  actionId: number;
}

export async function fetchAssignedOrders() {
  const { data } = await client.get<DeliveryOrderDto[]>('/orders/assigned');
  return data;
}

export async function fetchAvailableOrders() {
  const { data } = await client.get<DeliveryOrderDto[]>('/orders/available');
  return data;
}

export async function pickupOrder(orderSn: string, photo: string, notes?: string) {
  const { data } = await client.post<PickupResponse>(
    `/orders/${orderSn}/pickup`,
    { photo, notes }
  );
  return data;
}

export async function arriveWarehouse(orderSn: string, photo: string, notes?: string) {
  const { data } = await client.post<PickupResponse>(
    `/orders/${orderSn}/arrive-warehouse`,
    { photo, notes }
  );
  return data;
}

export async function warehouseShip(orderSn: string, photo: string, notes?: string) {
  const { data } = await client.post<PickupResponse>(
    `/orders/${orderSn}/warehouse-ship`,
    { photo, notes }
  );
  return data;
}

export async function fetchOrderBySn(orderSn: string) {
  const { data } = await client.get<DeliveryOrderDto>(`/orders/${orderSn}`);
  return data;
}

export async function updateShippingStatus(orderSn: string, payload: { shippingStatus: number }) {
  await client.post(`/orders/${orderSn}/status`, payload);
}

export async function fetchRoutePlan() {
  const { data } = await client.post<RoutePlanDto>('/routes/optimize');
  return data;
}

export async function uploadDeliveryProof(orderSn: string, photo: string, notes?: string) {
  const { data } = await client.post<DeliveryProofDto>(
    `/orders/${orderSn}/proof`,
    { photo, notes }
  );
  return data;
}

export async function login(phone: string, code: string) {
  const { data } = await client.post<{ accessToken: string; refreshToken: string }>(
    '/auth/login',
    { phone, code }
  );
  return data;
}
