#!/bin/bash

# Define variables
SOURCE_SERVER="inx-eugwc-inxdigital-svr.database.windows.net"
SOURCE_DATABASE="INXD_Platform"
SOURCE_USER="INXD_Database_admin"
SOURCE_PASSWORD="NX{Pbv2AF"
TARGET_FILE="db_$(date +%Y%m%d).bacpac"

LOCAL_DATABASE="inx_platform_$(date +%Y%m%d)"
LOCAL_CONNECTION_STRING="Data Source=localhost;Initial Catalog=$LOCAL_DATABASE;User ID=sa;Password=dellaBiella2!;TrustServerCertificate=True"
SQL_SCRIPT="change_schema_name_to_dbo.sql"

# Step 1: Export the database to a .bacpac file
echo "Exporting database from Azure SQL to $TARGET_FILE..."
sqlpackage /Action:Export \
  /SourceServerName:$SOURCE_SERVER \
  /SourceDatabaseName:$SOURCE_DATABASE \
  /TargetFile:"$TARGET_FILE" \
  /SourceUser:$SOURCE_USER \
  /SourcePassword:$SOURCE_PASSWORD

if [ $? -ne 0 ]; then
  echo "Failed to export the database."
  exit 1
fi

# Step 2: Import the .bacpac file into the local SQL Server
echo "Importing $TARGET_FILE into local SQL Server as $LOCAL_DATABASE..."
sqlpackage /Action:Import \
  /TargetConnectionString:"$LOCAL_CONNECTION_STRING" \
  /SourceFile:"$TARGET_FILE"

if [ $? -ne 0 ]; then
  echo "Failed to import the database locally."
  exit 1
fi

# Step 3: Execute the SQL script on the local database
echo "Executing SQL script $SQL_SCRIPT on the local database..."
SqlCmd -S localhost -d $LOCAL_DATABASE -U sa -P dellaBiella2! -i "$SQL_SCRIPT" -C

if [ $? -ne 0 ]; then
  echo "Failed to execute the SQL script."
  exit 1
fi

echo "All steps completed successfully."