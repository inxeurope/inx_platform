# Transfer of the prod db to local server

To transport the db from Production to locl db, we need to fix a schema name issue. The Production server is set with default schema name *db_owner*, while the development server has a default schema name *dbo*

## Phase 1
The first operation to perform is to export a Data-tier from the Production server either with Azure Data Studio or SSMS, creating a *.bacpac* file

### Exporting a data tier application (.bacpac)
Use this command, it takes long time to complete

    sqlpackage /Action:Export /SourceServerName:inx-eugwc-inxdigital-svr.database.windows.net /SourceDatabaseName:INXD_Database /TargetFile:db_20241015.bacpac /SourceUser:INXD_Database_admin /SourcePassword:NX{Pbv2AF

If sqlpackage is not istalled, use this command
    
    dotnet tool install -g microsoft.sqlpackage

## Phase 2
### Importing a data tier locally
The following operation is to import the Data-tier Application (file .bacpac) in the local DB server either with Azure Data Studio or SSMS, creating a *.bacpac* file.
Use this command

    sqlpackage /Action:Import /TargetServerName:localhost /TargetDatabaseName:inx_platform_20241015 /SourceFile:<path-to-your-file.bacpac> /TargetUser:sa /TargetPassword:dellaBiella2!


## Phase 3
At this point, all Table, Views and Store procedures will be in the local sever, but with the wrong schema name. We need to change schema name. To do so, we have to execute the following SQL statement to compile SQL statements for changing schema names on tables

    DECLARE @sql NVARCHAR(MAX) = '';

    SELECT @sql += 'ALTER SCHEMA dbo TRANSFER db_owner.' + QUOTENAME(TABLE_NAME) + ';' + CHAR(13)
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'db_owner';
    PRINT(@sql);
    EXEC sp_executesql @sql

Store procedure will have the same schema name mistake and they also need to be changed. Use this script

    DECLARE @sql NVARCHAR(MAX) = '';
    
    SELECT @sql += 'ALTER SCHEMA dbo TRANSFER db_owner.' + QUOTENAME(ROUTINE_NAME) + ';' + CHAR(13)
    FROM INFORMATION_SCHEMA.ROUTINES
    WHERE ROUTINE_SCHEMA = 'db_owner' AND ROUTINE_TYPE = 'PROCEDURE';
    PRINT(@sql);
    EXEC sp_executesql @sql;


## Optional in a single script
Use this script

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


 ## Conclusion
 After these phases, we have complete the transition to the local db server. It is possible to launch the django app

     python manage.py runserver_plus 0.0.0.0:21013

