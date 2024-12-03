CREATE PROCEDURE [_budfordetailline_delete_sales]
AS
BEGIN
    -- Get sales id from Scenario
    DECLARE @sales AS INT
    SELECT @sales = id FROM inx_platform_app_scenario WHERE is_sales = 1
    PRINT(@sales)
    SELECT id, name FROM inx_platform_app_scenario WHERE is_sales = 1
    DELETE FROM inx_platform_app_budfordetailline WHERE scenario_id = @sales
END