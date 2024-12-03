DECLARE @sql NVARCHAR(MAX) = N'';

-- Alter schema for tables
SELECT @sql += 'ALTER SCHEMA dbo TRANSFER db_owner.' + QUOTENAME(TABLE_NAME) + ';'
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'db_owner';

-- Alter schema for views
SELECT @sql += 'ALTER SCHEMA dbo TRANSFER db_owner.' + QUOTENAME(TABLE_NAME) + ';'
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'db_owner';

-- Alter schema for stored procedures
SELECT @sql += 'ALTER SCHEMA dbo TRANSFER db_owner.' + QUOTENAME(ROUTINE_NAME) + ';'
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_SCHEMA = 'db_owner' AND ROUTINE_TYPE = 'PROCEDURE';

EXEC sp_executesql @sql;