import os
from datetime import datetime

# Define the date format
date_str = datetime.now().strftime("%Y%m%d")

# Define the commands
export_command = f'sqlpackage /Action:Export /SourceServerName:inx-eugwc-inxdigital-svr.database.windows.net /SourceDatabaseName:INXD_Platform /TargetFile:"db_{date_str}.bacpac" /SourceUser:INXD_Database_admin /SourcePassword:NX{{Pbv2AF'
import_command = f'sqlpackage /Action:Import /TargetConnectionString:"Data Source=localhost;Initial Catalog=inx_platform_{date_str};User ID=sa;Password=dellaBiella2!;TrustServerCertificate=True" /SourceFile:db_{date_str}.bacpac'
change_schema_name_command = f'SqlCmd -S localhost -d inx_platform_{date_str} -U sa -P dellaBiella2! -i Change_schema_name.sql -C'


# Execute the export command
# os.system(export_command)

# Execute the import command
os.system(import_command)
os.system(change_schema_name_command)