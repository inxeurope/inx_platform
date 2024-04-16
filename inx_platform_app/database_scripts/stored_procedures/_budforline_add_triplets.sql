CREATE PROCEDURE [_budforline_add_triplets]
AS
BEGIN
    SET NOCOUNT ON
    -- This procedure adds triplets (customer_id, brand_id, colorgroup_id) to the budforline table
    -- If any of brand_id, colorgroup_id or customer_id is null none of thsoe tripets will be added as the insert will fail
    INSERT INTO inx_platform_app_budforline (sqlapp_id, brand_id, color_group_id, customer_id)
    SELECT 
        NULL as sqlapp_id,
        t.brand_id,
        t.colorgroup_id as color_group_id,
        t._view_customers_id as customer_id
    FROM 
        [dbo].[04_view_budforsales_temporary] t
    WHERE NOT EXISTS (
        -- This subquery checks for the existence of the triplets in the inx_platform_app_budforline table
        SELECT 1
        FROM inx_platform_app_budforline b
        WHERE 
            b.brand_id = t.brand_id
            AND b.color_group_id = t.colorgroup_id
            AND b.customer_id = t._view_customers_id
    )
    GROUP BY 
        t._view_customers_id, 
        t.brand_id, 
        t.colorgroup_id;
END