-- Migration: Insert lookup data for tigu_prepare_goods table
-- Created: 2025-11-23
-- Description: Insert lookup values for delivery_type, shipping_type, type, and prepare_status

-- Insert delivery_type lookup values
INSERT INTO tigu_lookup (lookup_number, lookup_string, lookup_desc, map_table_name, map_column_name) VALUES
(0, 'SELF_DELIVERY', '商家自行配送', 'tigu_prepare_goods', 'delivery_type'),
(1, 'THIRD_PARTY_DELIVERY', '第三方配送', 'tigu_prepare_goods', 'delivery_type');

-- Insert shipping_type lookup values
INSERT INTO tigu_lookup (lookup_number, lookup_string, lookup_desc, map_table_name, map_column_name) VALUES
(1, 'TO_WAREHOUSE', '货物配送到仓库', 'tigu_prepare_goods', 'shipping_type'),
(0, 'TO_USER', '货物配送到用户', 'tigu_prepare_goods', 'shipping_type');

-- Insert type lookup values (merchant/warehouse type)
INSERT INTO tigu_lookup (lookup_number, lookup_string, lookup_desc, map_table_name, map_column_name) VALUES
(0, 'MERCHANT', '商家', 'tigu_prepare_goods', 'type'),
(1, 'WAREHOUSE', '仓库', 'tigu_prepare_goods', 'type');

-- Insert prepare_status lookup values
INSERT INTO tigu_lookup (lookup_number, lookup_string, lookup_desc, map_table_name, map_column_name) VALUES
(NULL, 'PENDING_PREPARATION', '待备货', 'tigu_prepare_goods', 'prepare_status'),
(0, 'PREPARED', '已备货', 'tigu_prepare_goods', 'prepare_status'),
(1, 'DRIVER_PICKING_UP', '司机收货中', 'tigu_prepare_goods', 'prepare_status'),
(2, 'DRIVER_CONFIRMED_PICKUP', '司机确认收货', 'tigu_prepare_goods', 'prepare_status'),
(3, 'DRIVER_DELIVERED_TO_WAREHOUSE', '司机收货完成送货仓库', 'tigu_prepare_goods', 'prepare_status'),
(4, 'WAREHOUSE_RECEIVED', '仓库已收货', 'tigu_prepare_goods', 'prepare_status'),
(12, 'DELIVERED_TO_USER', '已送达', 'tigu_prepare_goods', 'prepare_status'),
(13, 'ORDER_COMPLETED', '订单完成', 'tigu_prepare_goods', 'prepare_status');
