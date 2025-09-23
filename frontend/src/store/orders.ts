import { defineStore } from 'pinia';
import {
  fetchAssignedOrders,
  fetchOrderBySn,
  fetchRoutePlan,
  login,
  updateShippingStatus
} from '@/api/orders';

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
    orders: [] as DeliveryOrder[],
    routePlan: null as RoutePlan | null,
    isLoading: false
  }),
  getters: {
    activeBySn: state => (orderSn: string) => state.orders.find(order => order.orderSn === orderSn),
    byWorkflowState: state => (workflowState: string) => {
      switch (workflowState) {
        case 'pending_pickup':
          return state.orders.filter(order => order.shippingStatus === 0);
        case 'in_transit':
          return state.orders.filter(order => order.shippingStatus === 1 || order.shippingStatus === 2);
        case 'completed':
          return state.orders.filter(order => order.shippingStatus === 3);
        default:
          return state.orders;
      }
    }
  },
  actions: {
    async login(phone: string, code: string) {
      const tokens = await login(phone, code);
      localStorage.setItem('delivery_token', tokens.accessToken);
      return tokens;
    },
    logout() {
      localStorage.removeItem('delivery_token');
      this.orders = [];
      this.routePlan = null;
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
    async fetchRoutePlan() {
      const data = await fetchRoutePlan();
      this.routePlan = data;
    }
  }
});
