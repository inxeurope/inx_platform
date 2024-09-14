-- Remove duplicate products and keep the ones with highest id
WITH CTE_Duplicates AS (
    SELECT 
        [id],
        [number],
        ROW_NUMBER() OVER (PARTITION BY [number] ORDER BY [id] DESC) AS RowNum
    FROM [inx_platform].[dbo].[inx_platform_app_product]
)
DELETE FROM [inx_platform].[dbo].[inx_platform_app_product]
WHERE [id] IN (
    SELECT [id]
    FROM CTE_Duplicates
    WHERE RowNum > 1
);