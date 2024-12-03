CREATE PROCEDURE [_drop_all_tables]
AS
BEGIN
    SET NOCOUNT ON;

DECLARE @ForeignKeyName NVARCHAR(128)
DECLARE @ParentTableObjectID INT
DECLARE @ReferencedTableObjectID INT

-- Declare and open the cursor
DECLARE foreign_key_cursor CURSOR FOR
SELECT f.name, f.parent_object_id, f.referenced_object_id
FROM sys.foreign_keys f

	OPEN foreign_key_cursor

	-- Fetch and print each @ForeignKeyName
	FETCH NEXT FROM foreign_key_cursor INTO @ForeignKeyName, @ParentTableObjectID, @ReferencedTableObjectID
	WHILE @@FETCH_STATUS = 0
	BEGIN
		PRINT('ForeignKeyName: ' + @ForeignKeyName)
		PRINT('ParentTableObjectID: ' + CONVERT(NVARCHAR, @ParentTableObjectID))
		PRINT('ReferencedTableObjectID: ' + CONVERT(NVARCHAR, @ReferencedTableObjectID))

		DECLARE @DropForeignKeyStatement NVARCHAR(255)
		SET @DropForeignKeyStatement = 'ALTER TABLE ' + OBJECT_SCHEMA_NAME(@ParentTableObjectID) + '.' + OBJECT_NAME(@ParentTableObjectID) + ' DROP CONSTRAINT ' + @ForeignKeyName
		PRINT('@DropForeignKeyStatement: ' + @DropForeignKeyStatement)
		EXEC sp_executesql @DropForeignKeyStatement
		FETCH NEXT FROM foreign_key_cursor INTO @ForeignKeyName, @ParentTableObjectID, @ReferencedTableObjectID
	END

	-- Close and deallocate the cursor
	CLOSE foreign_key_cursor
	DEALLOCATE foreign_key_cursor

	-- Drop tables

	DECLARE @TableName NVARCHAR(128)
	DECLARE table_cursor CURSOR FOR
	SELECT table_name
	FROM information_schema.tables
	WHERE table_type = 'BASE TABLE'

	OPEN table_cursor
	FETCH NEXT FROM table_cursor INTO @TableName

	WHILE @@FETCH_STATUS = 0
	BEGIN
		DECLARE @SqlStatement NVARCHAR(500)
		SET @SqlStatement = 'DROP TABLE ' + @TableName
		EXEC sp_executesql @SqlStatement

		FETCH NEXT FROM table_cursor INTO @TableName
	END

	CLOSE table_cursor
	DEALLOCATE table_cursor

END


