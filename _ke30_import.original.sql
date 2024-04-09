SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [dbo].[_ke30_import]

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

            DECLARE @MaxMonth_long int -- example: 202011
            DECLARE @MinMonth_long int -- example: 202010

            DECLARE @CountBefore INT
            DECLARE @CountAfter INT

            SELECT @MaxMonth_long = MAX(year_month) FROM inx_platform_app_ke30importline   -- in format 202201
            SELECT @MinMonth_long = MIN(year_month) FROM inx_platform_app_ke30importline -- in format 202111
            
            DECLARE @Count_KE30_import INT
            SELECT @Count_KE30_import = COUNT(*) FROM inx_platform_app_ke30importline;
            SET @message_text = N'Count/Moving in KE30_import: ' + CAST(@Count_KE30_import AS VARCHAR);
            PRINT (@message_text);
            INSERT INTO #Procedurelog VALUES(@message_text);

            SELECT @CountBefore = COUNT(*) FROM inx_platform_app_ke30line
            SET @message_text = N'Before: ' + CAST(@CountBefore as VARCHAR);
            PRINT (@message_text);
            INSERT INTO #Procedurelog VALUES(@message_text);
            
            -- Delete from KE30 the date that need to be replaced
            SET @message_text = 'Deleting from ' + CAST(@MinMonth_long as VARCHAR) + ' to ' + CAST(@MaxMonth_long as VARCHAR);
            PRINT (@message_text);
            INSERT INTO #Procedurelog VALUES(@message_text);
            DELETE FROM inx_platform_app_ke30line
                WHERE [year_month]>=@MinMonth_long AND [year_month]<=@MaxMonth_long;

            SELECT @CountAfter = COUNT(*) FROM inx_platform_app_ke30line;

            SET @message_text = N'After: ' + CAST(@CountAfter as VARCHAR) + 'Diff Deleted: ' + CAST((@CountBefore-@CountAfter) as varchar);
            PRINT (@message_text);
            INSERT INTO #Procedurelog VALUES(@message_text);
            
            -- Need to insert data from KE30_import to Sales.KE30
            INSERT INTO inx_platform_app_ke30line (
                [currency],
                [month],
                [year],
                [year_month],
                [fake_date],
                [customer_number],
                [customer_name],
                [sap_country],
                [sap_sales_district],
                [sap_sales_employee],
                [customer_account_group],
                [ship_to_party_number],
                [ship_to_party_name],
                [product_number],
                [product_name],
                [sap_brand],
                [sap_major_label],
                [sap_division],
                [sap_material_group],
                [sap_market_segment],
                [sap_industry],
                [sap_color],
                [sap_product_line],
                [sap_profit_center],
                [sap_UOM],
                [quantity],
                [unit_sales_quantity],
                [net_sales],
                [rebates],
                [gross_sales],
                [rmc_costs],
                [conversion_costs],
                [other_costs],
                [total_costs],
                [gross_margin],
                [gross_margin_perc],
                [margin_perc_actual],
                [contribution_margin_actual],
                [contribution_margin_perc_actual],
                [net_sales_unit_actual],
                [cost_unit_actual],
                [disc_claim_adj_actual],
                [import_timestamp]

            )
                SELECT
                    [currency]
                    ,RIGHT([period],2) as [month]
                    ,[fiscal_year] as [year]
                    ,[fiscal_year]*100+[period] as [year_month]
                    ,CAST(CONCAT(RIGHT([Period],2),'/1/',[fiscal_year]) as DATE) as [fake_date]
                    ,[customer] as [customer_number]
                    ,[customer_1] as [customer_name]
                    ,[country_1] as [sap_country]
                    ,[sales_district_1] as [sap_sales_district]
                    ,[sales_employee_1] as [sap_sales_employee]
                    ,[cust_acct_Assg_grp] as [customer_account_group]
                    ,[ship_to_party] as [ship_to_party_number]
                    ,[ship_to_party_1] as [ship_to_party_name]
                    ,[product] as [product_number]
                    ,[product_1] as [product_name]
                    ,[brand_name_1] as [sap_brand]
                    ,[major_label_1] as [sap_major_label]
                    ,[division_1] as [sap_division]
                    ,[material_group_1] as [sap_material_group]
                    ,[market_segment_1] as [sap_market_segment]
                    ,[industry_1] as [sap_industry]
                    ,[color] as [sap_color]
                    ,[product_line_1] as [sap_product_line]
                    ,[profit_center_1] as [sap_profit_center]
                    ,[unit_of_measure] as [sap_UOM]
                    ,[sales_qty_actual] as [quantity]
                    ,[unit_sales_quantity]
                    ,[net_sales_actual] as [net_sales]
                    ,[rebate_actual] as [rebates]
                    ,[gross_sales_actual] as [gross_sales]
                    ,[rmc_actual] as [rmc_costs]
                    ,[conversion_actual] as [conversion_cost]
                    ,[other_cost_actual] as [other_costs]
                    ,[total_cost_actual] as [total_costs]
                    ,[gross_margin_actual] as [gross_margin]
                    ,iif([gross_sales_actual]=0,0,[gross_margin_actual]/[gross_sales_actual]) as [gross_margin_perc]
                    ,[margin_perc_actual]
                    ,[contribution_margin_actual]
                    ,[contribution_margin_perc_actual]
                    ,[net_sales_unit_actual]
                    ,[cost_unit_actual]
                    ,[disc_claim_adj_actual]
                    ,[import_timestamp]
                    -- Must manage user that is field name owner_id
                FROM inx_platform_app_ke30importline;
            PRINT ('Done with importing');
            -- EXEC spAddingNewProducts;
            -- EXEC spAddingNewCustomers;
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

GO
