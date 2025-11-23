select * from tigu_driver where name='mic';
select * from tigu_prepare_goods where driver_id in (select id from tigu_driver where name='mic');
select * from tigu_order_action where create_by ='mic';
select * from tigu_uploaded_files tuf where create_by='mic';
select * from tigu_order where driver_id=26;
#to cleanup the data , run this 

delete from tigu_uploaded_files where create_by='mic';
delete from tigu_order_action where create_by='mic';
update tigu_prepare_goods set prepare_status=0, driver_id=null where driver_id in (select id from tigu_driver where name='mic');

