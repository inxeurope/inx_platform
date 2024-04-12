import os
from django.conf import settings
from django.db import connection

def check_and_create_views_and_procs(app_folder):
    # Check for views
    view_folder = os.path.join(app_folder, 'database_scripts/views')
    view_files = [f[:-4] for f in os.listdir(view_folder) if f.endswith('.sql')]
    with connection.cursor() as cursor:
        for view_name in view_files:
            cursor.execute(f"SELECT * FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME = '{view_name}'")
            if not cursor.fetchone():
                with open(os.path.join(view_folder, f"{view_name}.sql")) as f:
                    view_sql = f.read()
                cursor.execute(view_sql)
                print(f"{view_name} created in the db")
            else:
                print(f"{view_name} exists")

    # Check for stored procedures
    proc_folder = os.path.join(app_folder, 'database_scripts/stored_procedures')
    proc_files = [f[:-4] for f in os.listdir(proc_folder) if f.endswith('.sql')]
    with connection.cursor() as cursor:
        for proc_name in proc_files:
            cursor.execute(f"SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[{proc_name}]') AND type in (N'P', N'PC')")
            if not cursor.fetchone():
                with open(os.path.join(proc_folder, f"{proc_name}.sql")) as f:
                    proc_sql = f.read()
                cursor.execute(proc_sql)
                print(f"{proc_name} created in the db")
            else:
                print(f"{proc_name} exists")