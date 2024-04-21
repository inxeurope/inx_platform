CREATE PROCEDURE [_truncate_table_budfordetailline_w_FK]
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Temporary table to store foreign key constraints
    CREATE TABLE #FKConstraints (
        FKName NVARCHAR(128),
        FKSchema NVARCHAR(128),
        FKTable NVARCHAR(128),
        FKColumn NVARCHAR(128),
        PKSchema NVARCHAR(128),
        PKTable NVARCHAR(128),
        PKColumn NVARCHAR(128)
    );

    -- Insert foreign key constraints referencing the table into the temporary table
    INSERT INTO #FKConstraints
    SELECT 
        fk.name AS FKName,
        OBJECT_SCHEMA_NAME(fk.parent_object_id) AS FKSchema,
        OBJECT_NAME(fk.parent_object_id) AS FKTable,
        COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS FKColumn,
        OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS PKSchema,
        OBJECT_NAME(fk.referenced_object_id) AS PKTable,
        COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS PKColumn
    FROM 
        sys.foreign_keys fk
    INNER JOIN 
        sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
    INNER JOIN 
        sys.tables t ON fkc.referenced_object_id = t.object_id
    WHERE 
        OBJECT_NAME(fkc.parent_object_id) = 'inx_platform_app_budfordetailline';

    -- Drop foreign key constraints
    DECLARE @sql NVARCHAR(MAX);
    DECLARE cur CURSOR LOCAL FAST_FORWARD FOR
    SELECT 
        'ALTER TABLE [' + FKSchema + '].[' + FKTable + '] DROP CONSTRAINT ' + FKName
    FROM 
        #FKConstraints;

    OPEN cur;
    FETCH NEXT FROM cur INTO @sql;
    WHILE @@FETCH_STATUS = 0
    BEGIN
        EXEC(@sql);
        FETCH NEXT FROM cur INTO @sql;
    END;

    CLOSE cur;
    DEALLOCATE cur;

    -- Truncate the table
    TRUNCATE TABLE inx_platform_app_budfordetailline;

    -- Recreate foreign key constraints
    DECLARE cur_fk CURSOR LOCAL FAST_FORWARD FOR
    SELECT 
        'ALTER TABLE [' + FKSchema + '].[' + FKTable + '] ADD CONSTRAINT ' + FKName + ' FOREIGN KEY (' + FKColumn + ') REFERENCES [' + PKSchema + '].[' + PKTable + '](' + PKColumn + ');'
    FROM 
        #FKConstraints;

    OPEN cur_fk;
    FETCH NEXT FROM cur_fk INTO @sql;
    WHILE @@FETCH_STATUS = 0
    BEGIN
        EXEC(@sql);
        FETCH NEXT FROM cur_fk INTO @sql;
    END;

    CLOSE cur_fk;
    DEALLOCATE cur_fk;

    -- Drop temporary table
    DROP TABLE #FKConstraints;
END;