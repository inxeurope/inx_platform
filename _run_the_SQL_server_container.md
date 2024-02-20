# Comand to run the SQL Server docker container

   docker run --cap-add SYS_PTRACE -e 'ACCEPT_EULA=1' -e 'MSSQL_SA_PASSWORD=dellaBiella2!' -e 'MSSQL_PID=Premium' -p 1433:1433 --name AzureSQLEdge -d mcr.microsoft.com/azure-sql-edge