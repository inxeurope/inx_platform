DECLARE @ViewExists INT;
SET @ViewExists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.VIEWS 
    WHERE TABLE_NAME = '01_view_customers'
);
IF @ViewExists = 0
BEGIN
    DECLARE @CreateViewSql NVARCHAR(MAX);
    SET @CreateViewSql = N'
        CREATE VIEW [dbo].[01_view_customers] AS
        SELECT
            c.*,
            cc.id as country_id_from_view,
            cc.iso3166_1_alpha_2 as country_iso_alpha2,
            cc.iso3166_1_alpha_3 as country_iso_alpha3,
            cc.official_name_en as country_name,
            u.first_name + '' '' + u.last_name as sales_manager
        FROM inx_platform_app_customer c
        LEFT JOIN inx_platform_app_countrycode cc ON cc.id = c.country_id
        LEFT JOIN inx_platform_app_user u ON u.id = c.sales_employee_id
        ';
    EXEC sp_executesql @CreateViewSql;
END
