import os, sys
from django.db import connection

def check_and_create_views_and_procs(app_folder):
    

    table_names = connection.introspection.table_names()
    if 'inx_platform_app_product' in table_names and 'inx_platform_app_customer' in table_names:
        # Check for views
        print("*"*50)
        print("* VIEWS", end="")
        print(" "*41, "*")
        print("*"*50)
        view_folder = os.path.join(app_folder, 'database_scripts/views')
        view_files = sorted([f[:-4] for f in os.listdir(view_folder) if f.endswith('.sql')])
        print(f"view_files:{view_files}")
        with connection.cursor() as cursor:
            for view_name in view_files:
                sql_statement = f"SELECT * FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME = '{view_name}'"
                print(f"sql_statement: {sql_statement}")
                try:
                    cursor.execute(sql_statement)
                except Exception as e:
                    print("Error executing SQL statement:", e)
                    sys.exit(1)

                if not cursor.fetchone():
                    with open(os.path.join(view_folder, f"{view_name}.sql")) as f:
                        view_sql = f.read()
                    cursor.execute(view_sql)
                    print(f"{view_name} created in the db")
                else:
                    print(f"{view_name} exists")
        print()

        # Check for stored procedures
        print("*"*50)
        print("* PROCS", end="")
        print(" "*41, "*")
        print("*"*50)
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
        print()