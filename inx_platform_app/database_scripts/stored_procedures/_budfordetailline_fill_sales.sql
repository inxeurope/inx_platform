CREATE PROCEDURE [_budfordetailline_fill_sales]
AS
BEGIN
    SET NOCOUNT ON
    BEGIN TRY
        BEGIN TRANSACTION

            -- *************************************************************************            
            -- get id of is_sales (it must be unique in the table, no 2 lines must be 1)
            -- *************************************************************************
            DECLARE @is_sales AS INT
            SELECT @is_sales = id FROM inx_platform_app_scenario
            WHERE is_sales = 1
            PRINT(N'Sales marker is ' + CAST(@is_sales AS NVARCHAR))

            -- *************************************************************************
            -- Drop backup table
            -- *************************************************************************
            DROP TABLE IF EXISTS #_temp_backup_budget_forecast
            PRINT(N'#_temp_backup_budget_forecast table dropped')

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
            DECLARE @Length_of_table INT
            DECLARE @StartTime DATETIME;
            DECLARE @EndTime DATETIME;
            DECLARE @Duration INT;

            SET @StartTime = GETDATE();
            SELECT @Length_of_table=COUNT(*) FROM inx_platform_app_budfordetailline

            DELETE FROM inx_platform_app_budfordetailline
            
            SET @EndTime = GETDATE();
            SET @Duration = DATEDIFF(MILLISECOND, @StartTime, @EndTime);
            PRINT 'Time taken for DELETE operation: ' + CAST(@Duration AS VARCHAR(20)) + ' milliseconds ' + CAST(@Duration/@Length_of_table AS VARCHAR(20)) + ' lines/millisecond';
            -- reset the index counter
            DBCC CHECKIDENT (inx_platform_app_budfordetailline, RESEED, 0)



            -- *************************************************************************
            -- Refill from the backup table
            -- *************************************************************************
            SET @StartTime = GETDATE();
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
            SET @EndTime = GETDATE();
            PRINT (N'table refilled from backup')
            PRINT 'Time taken for refilling operation: ' + CAST(@Duration AS VARCHAR(20)) + ' milliseconds';

            -- *************************************************************************
            -- Insert sales at the proper granularity, created by the view, in the table
            -- *************************************************************************
            PRINT(N'Start insert')
            INSERT INTO inx_platform_app_budfordetailline (
                volume,
                [value],
                price,
                [year],
                [month],
                currency_zaq,
                detail_date,
                budforline_id,
                scenario_id
            )
            SELECT
                v.volume,
                v.value,
                CASE WHEN v.volume = 0 THEN 0 ELSE ROUND(CAST(v.value AS DECIMAL(18, 2))/CAST(v.volume AS DECIMAL(18, 2)),2) END AS price,
                v.year,
                v.month_number AS month,
                v.curr AS currency_zaq,
                GETDATE() AS detail_date,
                bl.id AS budforline_id,
                @is_sales AS scenario_id
            FROM
                [04_view_budforsales_temporary] AS v
            INNER JOIN
                dbo.inx_platform_app_budforline AS bl ON v.brand_id = bl.brand_id
                AND v.colorgroup_id = bl.color_group_id
                AND v._view_customers_id = bl.customer_id
            WHERE
                bl.brand_id IS NOT NULL
                AND bl.color_group_id IS NOT NULL
                
            PRINT(N'End insert')

        COMMIT TRANSACTION
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE()
        RAISERROR(@ErrMsg, 16, 1)
        --INSERT INTO #Procedurelog VALUES(@ErrMsg);

    END CATCH


END