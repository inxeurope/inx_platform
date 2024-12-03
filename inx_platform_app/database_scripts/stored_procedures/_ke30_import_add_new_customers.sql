CREATE PROCEDURE [_ke30_import_add_new_customers]
-- This porocedure insert NEW customers that are present in KE30 and not yet present in Customers table
-- This procedure marks thos NEW customers as "New Customers, pending definition" in KE30_ImportStatus
AS
BEGIN
    SET NOCOUNT ON
    BEGIN TRY
        BEGIN TRANSACTION

            -- Selection of new customers and creation of a temporary table
            DROP TABLE IF EXISTS #new_customers
            SELECT DISTINCT
                ke30.customer_number
            INTO #new_customers
            FROM inx_platform_app_ke30line ke30
            LEFT JOIN inx_platform_app_customer c
                ON c.number = ke30.customer_number
            WHERE c.number IS NULL

            INSERT INTO inx_platform_app_customer (
                [number],
                [name],
                active,
                is_new,
                import_note
                )
            SELECT DISTINCT 
                ke30.customer_number,
                ke30.customer_name,
                0 as [active],
                1 as [is_new],
                'SAP country: ' + ke30.sap_country + ' -- SAP sales employee: ' + ke30.sap_sales_employee + ' -- Imported on: ' + CAST(GETDATE() AS NVARCHAR) AS import_note
            FROM inx_platform_app_ke30line ke30
            LEFT JOIN #new_customers nc
            ON nc.customer_number = ke30.customer_number
            WHERE nc.customer_number = ke30.customer_number
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsg, 16, 1);
    END CATCH;

    SELECT
        [number],
        [name]
    FROM inx_platform_app_customer
    WHERE is_new=1;

END
