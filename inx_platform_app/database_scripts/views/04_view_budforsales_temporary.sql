DECLARE @ViewExists INT;
SET @ViewExists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.VIEWS 
    WHERE TABLE_NAME = '04_view_budforsales_temporary'
);
IF @ViewExists = 0
BEGIN
    DECLARE @CreateViewSql NVARCHAR(MAX);
    SET @CreateViewSql = N'
        CREATE VIEW [04_view_budforsales_temporary] AS
        SELECT
            _view_customers_id,
            _view_customers_number,
            _view_customers_name,
            [year],
            month_number,
            brand_id,
            brand_name,
            colorgroup_id,
            colorgroup_name,
            SUM(invoice_qty) as volume,
            curr,
            SUM(invoice_sales) as value,
            ''sales'' as [scenario]
        FROM [03_view_zaq]
        WHERE [year] >= YEAR(GETDATE()) - 2
        GROUP BY
            _view_customers_id,
            _view_customers_number,
            _view_customers_name,
            [year],
            [month_number],
            curr,
            brand_id,
            brand_name,
            colorgroup_id,
            colorgroup_name
    ';
    EXEC sp_executesql @CreateViewSql;
END



