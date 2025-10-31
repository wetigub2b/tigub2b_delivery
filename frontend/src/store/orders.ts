import { defineStore } from 'pinia';
import {
  fetchAssignedOrders,
  fetchAvailableOrders,
  fetchOrderBySn,
  fetchRoutePlan,
  login,
  pickupOrder,
  arriveWarehouse,
  warehouseShip,
  updateShippingStatus,
  uploadDeliveryProof
} from '@/api/orders';

// Helper function to decode JWT token
function decodeJWT(token: string): any {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
}

// Get phone number from stored token
function getPhoneFromToken(): string {
  const token = localStorage.getItem('delivery_token');
  if (!token) return '';

  const payload = decodeJWT(token);
  return payload?.phonenumber || payload?.phone || payload?.sub || '';
}

export interface DeliveryProof {
  photoUrl: string;
  notes?: string;
  createdAt: string;
}

export interface DeliveryOrder {
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
  deliveryProof?: DeliveryProof;
  pickupLocation?: {
    id: number;
    name: string;
    address: string;
    latitude?: number;
    longitude?: number;
  };
  items: Array<{
    skuId: number;
    skuCode: string;
    productName: string;
    quantity: number;
    skuImage?: string;
  }>;
}

export interface RoutePlan {
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

const shippingLabels: Record<number, string> = {
  0: 'Not Shipped',
  1: 'Shipped',
  2: 'Driver Received',
  3: 'Arrived Warehouse',
  4: 'Warehouse Shipped',
  5: 'Delivered'
};

const orderLabels: Record<number, string> = {
  0: 'Pending Payment',
  1: 'Pending Shipment',
  2: 'Pending Receipt',
  3: 'Completed',
  4: 'Cancelled',
  5: 'After-Sales'
};

function decorate(order: DeliveryOrder): DeliveryOrder {
  return {
    ...order,
    shippingStatusLabel: order.shippingStatusLabel || shippingLabels[order.shippingStatus] || 'Unknown',
    orderStatusLabel: order.orderStatusLabel || orderLabels[order.orderStatus] || 'Unknown'
  };
}

export const useOrdersStore = defineStore('orders', {
  state: () => ({
    orders: [] as DeliveryOrder[],
    availableOrders: [] as DeliveryOrder[],
    routePlan: null as RoutePlan | null,
    isLoading: false,
    userPhone: localStorage.getItem('user_phone') || getPhoneFromToken()
  }),
  getters: {
    activeBySn: state => (orderSn: string) => state.orders.find(order => order.orderSn === orderSn),
    currentUserPhone: state => state.userPhone || getPhoneFromToken(),
    byWorkflowState: state => (workflowState: string) => {
      switch (workflowState) {
        case 'available':
          return state.availableOrders.filter(order => order.orderStatus !== 4);
        case 'pending_pickup':
          return state.orders.filter(order => order.shippingStatus === 0);
        case 'in_transit':
          // Status 2 (Driver Received), 3 (Arrived Warehouse), 4 (Warehouse Shipped)
          return state.orders.filter(order =>
            order.shippingStatus === 2 ||
            order.shippingStatus === 3 ||
            order.shippingStatus === 4
          );
        case 'completed':
          return state.orders.filter(order => order.shippingStatus === 5);
        default:
          return state.orders;
      }
    }
  },
  actions: {
    async login(phone: string, code: string) {
      const tokens = await login(phone, code);
      localStorage.setItem('delivery_token', tokens.accessToken);
      localStorage.setItem('user_phone', phone);
      this.userPhone = phone;
      return tokens;
    },
    logout() {
      localStorage.removeItem('delivery_token');
      localStorage.removeItem('user_phone');
      this.orders = [];
      this.availableOrders = [];
      this.routePlan = null;
      this.userPhone = '';
    },
    async fetchAssignedOrders() {
      this.isLoading = true;
      try {
        const orders = await fetchAssignedOrders();
        this.orders = orders.map(order => decorate({
          ...order,
          shippingStatusLabel: order.shippingStatusLabel || '',
          orderStatusLabel: order.orderStatusLabel || ''
        }));
      } finally {
        this.isLoading = false;
      }
    },
    async fetchAvailableOrders() {
      this.isLoading = true;
      try {
        const orders = await fetchAvailableOrders();
        this.availableOrders = orders.map(order => decorate({
          ...order,
          shippingStatusLabel: order.shippingStatusLabel || '',
          orderStatusLabel: order.orderStatusLabel || ''
        }));
      } finally {
        this.isLoading = false;
      }
    },
    async pickupOrder(orderSn: string, photo: string, notes?: string) {
      const result = await pickupOrder(orderSn, photo, notes);
      // Remove from available orders
      const index = this.availableOrders.findIndex(order => order.orderSn === orderSn);
      if (index >= 0) {
        const order = this.availableOrders[index];
        this.availableOrders.splice(index, 1);
        // Add to assigned orders with new shipping_status from response
        this.orders.push({
          ...order,
          shippingStatus: result.shippingStatus,
          shippingStatusLabel: shippingLabels[result.shippingStatus]
        });
      }
      return result;
    },
    async arriveWarehouse(orderSn: string, photo: string, notes?: string) {
      const result = await arriveWarehouse(orderSn, photo, notes);
      this.patchOrderStatus({ orderSn, shippingStatus: result.shippingStatus });
      return result;
    },
    async warehouseShip(orderSn: string, photo: string, notes?: string) {
      const result = await warehouseShip(orderSn, photo, notes);
      this.patchOrderStatus({ orderSn, shippingStatus: result.shippingStatus });
      return result;
    },
    async fetchOrderDetail(orderSn: string) {
      const detail = await fetchOrderBySn(orderSn);
      const decorated = decorate({
        ...detail,
        shippingStatusLabel: detail.shippingStatusLabel || '',
        orderStatusLabel: detail.orderStatusLabel || ''
      });
      const index = this.orders.findIndex(order => order.orderSn === orderSn);
      if (index >= 0) {
        this.orders.splice(index, 1, decorated);
      } else {
        this.orders.push(decorated);
      }
    },
    async updateShippingStatus(orderSn: string, shippingStatus: number) {
      await updateShippingStatus(orderSn, { shippingStatus });
      this.patchOrderStatus({ orderSn, shippingStatus });
    },
    patchOrderStatus(payload: { orderSn: string; shippingStatus: number }) {
      const order = this.orders.find(item => item.orderSn === payload.orderSn);
      if (order) {
        order.shippingStatus = payload.shippingStatus;
        order.shippingStatusLabel = shippingLabels[payload.shippingStatus] || 'Unknown';
      }
    },
    async uploadDeliveryProof(orderSn: string, photo: string, notes?: string) {
      const result = await uploadDeliveryProof(orderSn, photo, notes);
      // Order status is automatically updated to delivered (5) by the backend
      this.patchOrderStatus({ orderSn, shippingStatus: 5 });
      return result;
    },
    async fetchRoutePlan() {
      const data = await fetchRoutePlan();
      this.routePlan = data;
    }
  }
});
