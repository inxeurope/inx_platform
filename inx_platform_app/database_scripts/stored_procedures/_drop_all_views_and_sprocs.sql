CREATE PROCEDURE [_drop_all_views_and_sprocs]
AS
BEGIN

    DROP PROCEDURE [_budfordetailline_delete_sales]
    DROP PROCEDURE [_budfordetailline_fill_sales]
    DROP PROCEDURE [_budforline_add_triplets]
    DROP PROCEDURE [_ke30_import]
    DROP PROCEDURE [_ke30_import_add_new_customers]
    DROP PROCEDURE [_ke30_import_add_new_products]
    DROP PROCEDURE [_zaq_import]

    DROP VIEW [01_view_customers]
    DROP VIEW [02_view_products]
    DROP VIEW [03_view_zaq]
    DROP VIEW [04_view_budforsales_temporary]
END