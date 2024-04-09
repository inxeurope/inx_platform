CREATE PROCEDURE [dbo].[_budfordetailline_fill_sales]
AS
BEGIN
    SET NOCOUNT ON
    BEGIN TRY
        BEGIN TRANSACTION

            -- *************************************************************************            
            -- get id of is_asles (it must be unique)
            -- *************************************************************************
            DECLARE @is_sales AS INT
            SELECT @is_sales = is_sales FROM inx_platform_app_scenario
            WHERE is_sales = 1
            PRINT(N'Sales marker is ' + CAST(@is_sales AS NVARCHAR))

            -- *************************************************************************
            -- Drop backup table
            -- *************************************************************************
            DROP TABLE IF EXISTS #_temp_backup_budget_forecast

            -- *************************************************************************
            -- Fill backup table
            -- *************************************************************************
            SELECT *
            INTO #_temp_backup_budget_forecast
            FROM inx_platform_app_budfordetailline
            WHERE scenario_id <> @is_sales
            PRINT(N'Backup table filled')

            -- *************************************************************************
            -- Empty the table
            -- *************************************************************************
            DELETE FROM inx_platform_app_budfordetailline
            -- reset the index counter
            DBCC CHECKIDENT (inx_platform_app_budfordetailline, RESEED, 0)

            -- *************************************************************************
            -- Refill from the backup table
            -- *************************************************************************
            INSERT INTO inx_platform_app_budfordetailline(
                [volume]
                ,[price]
                ,[value]
                ,[year]
                ,[month]
                ,[currency_zaq]
                ,[detail_date]
                ,[sqlapp_id]
                ,[budforline_id]
                ,[scenario_id]
            )
            SELECT
                [volume]
                ,[price]
                ,[value]
                ,[year]
                ,[month]
                ,[currency_zaq]
                ,[detail_date]
                ,[sqlapp_id]
                ,[budforline_id]
                ,[scenario_id]
            FROM #_temp_backup_budget_forecast

            PRINT (N'table refilled from backup')

            -- *************************************************************************
            -- Insert sales at the proper granularity, created by the view, in the table
            -- *************************************************************************
            INSERT INTO dbo.inx_platform_app_budfordetailline (
                volume,
                value,
                year,
                month,
                currency_zaq,
                detail_date,
                -- sqlapp_id,  -- Assuming you have a way to set this, or it can be NULL/Default if not needed
                budforline_id,
                scenario_id  -- You need to determine how to set this, as it's not mentioned in your view
            )
            SELECT
                v.volume,
                v.value,  -- Assuming value in view can be cast to FLOAT as expected in budfordetailline
                v.year,
                v.month_number AS month,
                v.curr AS currency_zaq,
                GETDATE() AS detail_date,
                bl.id AS budforline_id,
                @is_sales AS scenario_id  
            FROM
                _view_budforsales_temporary AS v
            INNER JOIN
                dbo.inx_platform_app_budforline AS bl ON v.brand_id = bl.brand_id
                AND v.colorgroup_id = bl.color_group_id
                AND v._view_customers_id = bl.customer_id  -- Adjust this mapping based on actual column names and logic
            WHERE
                bl.brand_id IS NOT NULL
                AND bl.color_group_id IS NOT NULL

        COMMIT TRANSACTION
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE()
        RAISERROR(@ErrMsg, 16, 1)
        --INSERT INTO #Procedurelog VALUES(@ErrMsg);

    END CATCH


END