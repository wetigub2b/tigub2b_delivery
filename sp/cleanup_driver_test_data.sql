DELIMITER //

DROP PROCEDURE IF EXISTS sp_cleanup_driver_test_data //

CREATE PROCEDURE sp_cleanup_driver_test_data()
BEGIN
    -- tigu_prepare_goods cleanup: reset prepare_status and driver_id
    UPDATE tigu_prepare_goods
    SET prepare_status = 0, driver_id = NULL
    WHERE order_ids IN (
        '1996399174144208898,1996399174152597506',
        '1996398875891445762'
    );

    -- delete records from tigu_order_action
    DELETE FROM tigu_order_action
    WHERE create_by = 'mic'
    AND order_id IN (
        1996399174144208898,
        1996399174152597506,
        1996398875891445762
    );

    -- tigu_order table: intentionally not deleted

    -- tigu_uploaded_files cleanup
    DELETE FROM tigu_uploaded_files
    WHERE create_by = 'mic';

END //

DELIMITER ;
