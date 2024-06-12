CREATE PROCEDURE [_budgetforecastdetail_fill_sales]
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
            -- Empty the table
            -- *************************************************************************
            DELETE FROM inx_platform_app_budgetforecastdetail_sales
            -- reset the index counter
            DBCC CHECKIDENT (inx_platform_app_budgetforecastdetail_sales, RESEED, 0)

            -- *************************************************************************
            -- Insert sales at the proper granularity, created by the view, in the table
            -- *************************************************************************
            PRINT(N'Start insert')
            INSERT INTO inx_platform_app_budgetforecastdetail_sales (
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
                inx_platform_app_budforline AS bl ON
                v.brand_id = bl.brand_id AND
                v.colorgroup_id = bl.color_group_id AND
                v._view_customers_id = bl.customer_id
            WHERE
                customer_id IS NOT NULL AND
                bl.brand_id IS NOT NULL AND
                bl.color_group_id IS NOT NULL
                
            PRINT(N'End insert')

        COMMIT TRANSACTION
        -- SELECT * FROM inx_platform_app_budgetforecastdetail_sales
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE()
        RAISERROR(@ErrMsg, 16, 1)
        --INSERT INTO #Procedurelog VALUES(@ErrMsg);
    END CATCH

END