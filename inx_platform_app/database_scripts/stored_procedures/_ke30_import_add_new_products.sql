CREATE PROCEDURE [_ke30_import_add_new_products]
-- This porocedure insert NEW products that are present in KE30 and not yet present in Products table
-- This procedure marks thos NEW products as "New item, pending definition" in KE30_ImportStatus
AS
BEGIN
    SET NOCOUNT ON
    BEGIN TRY
        BEGIN TRANSACTION

            -- Selection of new products and creation of a temporary table
            DROP TABLE IF EXISTS #new_products
            SELECT DISTINCT
                ke30.product_number
            INTO #new_products
            FROM inx_platform_app_ke30line ke30
            LEFT JOIN inx_platform_app_product p
                ON p.number = ke30.product_number
            WHERE p.number IS NULL

            INSERT INTO inx_platform_app_product (
                [number],
                [name], 
                is_ink,
                is_new,
                import_note
                )
                SELECT DISTINCT
                    ke30.product_number,
                    ke30.product_name,
                    0 as is_ink,
                    1 as is_new,
                    'Brand SAP: ' + ke30.sap_brand + ' -- MarketSegment SAP: ' + ke30.sap_market_segment + ' -- MaterialGroup SAP: ' + ke30.sap_material_group + ' --Color SAP: ' + ke30.sap_color + ' -- Imported on: ' + CAST(GETDATE() AS NVARCHAR) AS [import_note]
                FROM inx_platform_app_ke30line ke30
                JOIN #new_products np
                ON ke30.product_number = np.product_number
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE()
        RAISERROR(@ErrMsg, 16, 1)
    END CATCH;
    SELECT
        [number],
        [name]
    FROM inx_platform_app_product
    WHERE is_new=1;

END
