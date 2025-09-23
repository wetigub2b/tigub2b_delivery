import { mount } from '@vue/test-utils';
import OrderCard from '@/components/OrderCard.vue';

const baseOrder = {
  orderSn: 'TOD123',
  shippingStatus: 0,
  orderStatus: 1,
  shippingStatusLabel: 'Pending',
  orderStatusLabel: 'Pending Shipment',
  receiverName: 'John Doe',
  receiverPhone: '555-111-2222',
  receiverAddress: '123 Main St',
  receiverCity: 'Toronto',
  receiverProvince: 'ON',
  receiverPostalCode: 'M5J 2N1',
  pickupLocation: { name: 'Warehouse A', address: '45 Depot Ave' },
  items: [
    { skuId: 1, skuCode: 'SKU-1', productName: 'Cement', quantity: 5 }
  ]
};

describe('OrderCard', () => {
  it('emits status updates', async () => {
    const wrapper = mount(OrderCard, {
      props: {
        order: baseOrder
      }
    });

    await wrapper.findAll('button')[0].trigger('click');

    expect(wrapper.emitted('status-update')?.[0]).toEqual([
      { orderSn: 'TOD123', shippingStatus: 1 }
    ]);
  });
});
