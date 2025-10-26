import client from './client';

export interface OrderItemDto {
  skuId: number;
  skuCode: string;
  productName: string;
  quantity: number;
}

export interface DeliveryOrderDto {
  orderSn: string;
  shippingStatus: number;
  orderStatus: number;
  receiverName: string;
  receiverPhone: string;
  receiverAddress: string;
  receiverCity: string;
  receiverProvince: string;
  receiverPostalCode: string;
  pickupLocation?: {
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

export async function fetchAssignedOrders() {
  const { data } = await client.get<DeliveryOrderDto[]>('/orders/assigned');
  return data;
}

export async function fetchAvailableOrders() {
  const { data } = await client.get<DeliveryOrderDto[]>('/orders/available');
  return data;
}

export async function pickupOrder(orderSn: string) {
  await client.post(`/orders/${orderSn}/pickup`);
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
