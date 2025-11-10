import { defineStore } from 'pinia';
import {
  fetchOrderBySn,
  fetchRoutePlan,
  login
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
  orderStatus: number;
  receiverName: string;
  receiverPhone: string;
  receiverAddress: string;
  receiverCity: string;
  receiverProvince: string;
  receiverPostalCode: string;
  shippingStatusLabel: string;
  orderStatusLabel: string;
  deliveryProof?: DeliveryProof;
  pickupLocation?: {
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
  2: 'Partially Shipped',
  3: 'Delivered'
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
    orderDetails: new Map<string, DeliveryOrder>(), // Cache for order details
    routePlan: null as RoutePlan | null,
    isLoading: false,
    userPhone: localStorage.getItem('user_phone') || getPhoneFromToken()
  }),
  getters: {
    activeBySn: state => (orderSn: string) => state.orderDetails.get(orderSn),
    currentUserPhone: state => state.userPhone || getPhoneFromToken()
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
      this.orderDetails.clear();
      this.routePlan = null;
      this.userPhone = '';
    },
    async fetchOrderDetail(orderSn: string) {
      const detail = await fetchOrderBySn(orderSn);
      const decorated = decorate({
        ...detail,
        shippingStatusLabel: detail.shippingStatusLabel || '',
        orderStatusLabel: detail.orderStatusLabel || ''
      });
      this.orderDetails.set(orderSn, decorated);
    },
    async fetchRoutePlan() {
      const data = await fetchRoutePlan();
      this.routePlan = data;
    }
  }
});
