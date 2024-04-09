SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER PROCEDURE [dbo].[_zaq_import]

AS
BEGIN
    SET NOCOUNT ON

    BEGIN TRY
        BEGIN TRANSACTION
            DROP TABLE IF EXISTS #Procedure_log
            CREATE TABLE #Procedurelog(
                Message_text TEXT NULL
            );
            DECLARE @message_text NVARCHAR(MAX);

            DECLARE @MAX_DATE AS DATE
            DECLARE @MIN_DATE AS DATE
            SELECT @MAX_DATE = MAX([billing_date]) FROM inx_platform_app_zaqcodmi9_import_line
            SELECT @MIN_DATE = MIN([billing_date]) FROM inx_platform_app_zaqcodmi9_import_line
            
            -- SELECT COUNT([billing_date]) FROM inx_platform_app_zaqcodmi9_import_line
            -- SELECT COUNT([billing_date]) FROM inx_platform_app_zaqcodmi9_line

            DELETE FROM inx_platform_app_zaqcodmi9_line
            WHERE [billing_date] >= @MIN_DATE AND [billing_date] <= @MAX_DATE

            DECLARE @Before_zaq AS INT
            SELECT @Before_zaq = COUNT([billing_date]) FROM inx_platform_app_zaqcodmi9_line
            SET @message_text = N'Length of zaqcodmi9_line before: ' + CAST(@Before_zaq AS VARCHAR);
            PRINT (@message_text);
            INSERT INTO #Procedurelog VALUES(@message_text);

            INSERT INTO inx_platform_app_zaqcodmi9_line
                SELECT
                [billing_date]
                ,[material]
                ,[description]
                ,[sold_to]
                ,[name]
                ,[billing_doc]
                ,[invoice_qty]
                ,[UoM]
                ,[unit_price]
                ,[invoice_sales]
                ,[curr]
                ,[batch]
                ,[gm_perc]
                ,[prof]
                ,[ptrm]
                ,[curr_1]
                ,[cost]
                ,[can]
                ,[bill]
                ,[item]
                ,[tax_amount]
                ,[curr_2]
                ,[dv]
                ,[shpt]
                ,[sales_doc]
                ,[import_date]
                FROM inx_platform_app_zaqcodmi9_import_line

            DECLARE @After_zaq AS INT
            SELECT @After_zaq = COUNT([billing_date]) FROM inx_platform_app_zaqcodmi9_line

            SET @message_text = N'Length of zaqcodmi9_line after: ' + CAST(@After_zaq AS VARCHAR);
            PRINT (@message_text);

            INSERT INTO #Procedurelog VALUES(@message_text);

        COMMIT TRANSACTION
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE()
        RAISERROR(@ErrMsg, 16, 1)
        INSERT INTO #Procedurelog VALUES(@ErrMsg);

    END CATCH

    SELECT [Message_text] FROM #ProcedureLog;

END