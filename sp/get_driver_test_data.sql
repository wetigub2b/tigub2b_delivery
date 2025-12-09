DELIMITER //

DROP PROCEDURE IF EXISTS sp_get_driver_test_data //

CREATE PROCEDURE sp_get_driver_test_data()
BEGIN
    -- 1. Prepare goods information
    SELECT
prepare_sn,prepare_status,delivery_type,shipping_type,shop_id,warehouse_id,total_value,receiver_address from tigu_prepare_goods where order_ids in (1996399174144208898,1996399174152597506);

    -- 2. Order shipping and status
    SELECT
        id AS order_id,
        shipping_status,
        order_status,
        warehouse_shipping_time, driver_receive_time,finish_time
    FROM tigu_order where id in 
(1996399174144208898,1996399174152597506);

    -- 3. Order action history
    SELECT
        create_by,
        create_time,
        order_id,
        order_status,
        shipping_status, action_type 
    FROM tigu_order_action
where order_id in 
(1996399174144208898,1996399174152597506);

    -- 4. Uploaded files by creator
    SELECT *
    FROM tigu_uploaded_files
    WHERE create_by = 'mic';

END //

DELIMITER ;

