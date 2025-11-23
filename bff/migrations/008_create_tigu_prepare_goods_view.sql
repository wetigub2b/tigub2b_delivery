-- Migration: Create view for tigu_prepare_goods with lookup descriptions
-- Created: 2025-11-23
-- Description: Create a readable view joining tigu_prepare_goods with tigu_lookup table for all enum fields

CREATE OR REPLACE VIEW vw_tigu_prepare_goods AS
SELECT 
    pg.id,
    pg.prepare_sn,
    pg.shop_id,
    pg.delivery_type,
    l_delivery.lookup_string AS delivery_type_string,
    l_delivery.lookup_desc AS delivery_type_desc,
    pg.shipping_type,
    l_shipping.lookup_string AS shipping_type_string,
    l_shipping.lookup_desc AS shipping_type_desc,
    pg.prepare_status,
    l_prepare.lookup_string AS prepare_status_string,
    l_prepare.lookup_desc AS prepare_status_desc,
    pg.type,
    l_type.lookup_string AS type_string,
    l_type.lookup_desc AS type_desc,
    pg.receiver_name,
    pg.receiver_phone,
    pg.receiver_province,
    pg.receiver_city,
    pg.receiver_district,
    pg.receiver_address,
    pg.receiver_postal_code,
    pg.warehouse_id,
    pg.total_quantity,
    pg.total_weight,
    pg.total_volume,
    pg.total_value,
    pg.order_ids,
    pg.package_count,
    pg.logistics_number,
    pg.logistics_fee,
    pg.driver_id,
    pg.prepare_complete_time,
    pg.shipping_time,
    pg.actual_arrival_time,
    pg.cancel_reason,
    pg.cancel_time,
    pg.prepare_remark,
    pg.create_by,
    pg.create_time,
    pg.update_by,
    pg.update_time,
    pg.remark,
    pg.vouchers_json
FROM 
    tigu_prepare_goods pg
    LEFT JOIN tigu_lookup l_delivery 
        ON pg.delivery_type = l_delivery.lookup_number 
        AND l_delivery.map_table_name = 'tigu_prepare_goods' 
        AND l_delivery.map_column_name = 'delivery_type'
    LEFT JOIN tigu_lookup l_shipping 
        ON pg.shipping_type = l_shipping.lookup_number 
        AND l_shipping.map_table_name = 'tigu_prepare_goods' 
        AND l_shipping.map_column_name = 'shipping_type'
    LEFT JOIN tigu_lookup l_prepare 
        ON (pg.prepare_status = l_prepare.lookup_number OR (pg.prepare_status IS NULL AND l_prepare.lookup_number IS NULL))
        AND l_prepare.map_table_name = 'tigu_prepare_goods' 
        AND l_prepare.map_column_name = 'prepare_status'
    LEFT JOIN tigu_lookup l_type 
        ON pg.type = l_type.lookup_number 
        AND l_type.map_table_name = 'tigu_prepare_goods' 
        AND l_type.map_column_name = 'type';
