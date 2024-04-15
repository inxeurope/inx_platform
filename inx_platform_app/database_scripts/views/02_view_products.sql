DECLARE @ViewExists INT;
SET @ViewExists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.VIEWS 
    WHERE TABLE_NAME = '_view_products'
);
IF @ViewExists = 0
BEGIN
    DECLARE @CreateViewSql NVARCHAR(MAX);
    SET @CreateViewSql = N'
        CREATE VIEW [dbo].[02_view_products] AS
        SELECT
            p.id,
            p.number,
            p.name,
            p.made_in_id,
            mi.name as made_in_name,
            p.is_ink,
            p.brand_id,
            b.name as brand_name,
            ml.name as major_label_name,
            nsf.id as nsf_division_id,
            nsf.name as nsf_division_name,
            d.id as division_id,
            d.name as division_name,
            it.id as ink_technology_id,
            it.name as ink_technology_name,
            ms.id as market_segment_id,
            ms.name as market_segment_name,
            mg.id as material_group_id,
            mg.name as material_group_name,
            p.color_id as color_id,
            c.name as color_name,
            cg.id as colorgroup_id,
            cg.name as colorgroup_name,
            p.product_line_id,
            p.product_status_id,
            p.approved_by_id,
            p.approved_on,
            p.is_new
        FROM inx_platform_app_product p
        LEFT JOIN inx_platform_app_brand b ON b.id = p.brand_id
        LEFT JOIN inx_platform_app_nsfdivision nsf ON nsf.id = b.nsf_division_id
        LEFT JOIN inx_platform_app_inktechnology it ON it.id = b.ink_technology_id
        LEFT JOIN inx_platform_app_majorlabel ml ON ml.id = b.major_label_id
        LEFT JOIN inx_platform_app_marketsegment ms ON ms.id = b.market_segment_id
        LEFT JOIN inx_platform_app_materialgroup mg ON mg.id = b.material_group_id
        LEFT JOIN inx_platform_app_color c ON c.id = p.color_id
        LEFT JOIN inx_platform_app_colorgroup cg ON cg.id = c.color_group_id
        LEFT JOIN inx_platform_app_madein mi ON mi.id = p.made_in_id
        LEFT JOIN inx_platform_app_division d ON d.id = b.division_id
        WHERE p.brand_id IS NOT NULL AND cg.id IS NOT NULL
    ';
    EXEC sp_executesql @CreateViewSql;

END
