import os
import sys
import calendar
import json
from datetime import datetime
from django.db import connection
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from .models import (CountryCode, Color, User)


quarters = {1: 'Q1', 2: 'Q1', 3: 'Q1', 4: 'Q2', 5: 'Q2', 6: 'Q2', 7: 'Q3', 8: 'Q3', 9: 'Q3', 10: 'Q4', 11: 'Q4', 12: 'Q4'}
halves = {1: 'H1', 2: 'H1', 3: 'H1', 4: 'H1', 5: 'H1', 6: 'H1', 7: 'H2', 8: 'H2', 9: 'H2', 10: 'H2', 11: 'H2', 12: 'H2'}
months = {
    str(i): {
        'name': calendar.month_name[i],
        'abbreviated_name': calendar.month_abbr[i],
        'quarter': quarters[i],
        'half': halves[i]
    } for i in range(1, 13)
}

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
                # print(f"sql_statement: {sql_statement}")
                try:
                    cursor.execute(sql_statement)
                except Exception as e:
                    print("Error executing SQL statement:", e)
                    sys.exit(1)
                if not cursor.fetchone():
                    print(f"there is not {view_name}", end = "")
                    with open(os.path.join(view_folder, f"{view_name}.sql")) as f:
                        view_sql = f.read()
                    try:
                        cursor.execute(view_sql)
                    except Exception as e:
                        print("Error executing SQL statement:", e)
                        sys.exit(1)
                    # cursor.execute(view_sql)
                    print(f" -> {view_name} CREATED in the db")
                else:
                    print(f"{view_name} exists")
                    pass
        print()

        # Check for stored procedures
        print("*"*50)
        print("* PROCS", end="")
        print(" "*41, "*")
        print("*"*50)
        proc_folder = os.path.join(app_folder, 'database_scripts/stored_procedures')
        proc_files = [f[:-4] for f in os.listdir(proc_folder) if f.endswith('.sql')]
        print(proc_files)
        with connection.cursor() as cursor:
            for proc_name in proc_files:
                sql_statement = f"SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[{proc_name}]') AND type in (N'P', N'PC')"
                try:
                    # print(sql_statement)
                    cursor.execute(sql_statement)
                except Exception as e:
                    print("Error executing SQL statement:", e)
                    sys.exit(2)
                # cursor.execute(sql_statement)
                if not cursor.fetchone():
                    print(f"there is not {proc_name}", end = "")
                    with open(os.path.join(proc_folder, f"{proc_name}.sql")) as f:
                        proc_sql = f.read()
                        try:
                            cursor.execute(proc_sql)
                        except Exception as e:
                            print("Error executing SQL statement:", e)
                            sys.exit(1)
                        print(f" -> {proc_name} CREATED in the db")
                else:
                    print(f"{proc_name} exists")
        print()

def get_cache_country_codes():
    country_codes = cache.get('country_codes')
    if not country_codes:
        country_codes = list(CountryCode.objects.values('alpha_2', 'official_name_en').order_by('official_name_en'))
        country_codes.insert(0, {'alpha_2': '', 'official_name_en': 'All'})
        cache.set('country_codes', json.dumps(country_codes), timeout=172800) # cahche 48 hours
    else:
        country_codes = json.loads(country_codes)
    return country_codes

def create_log_entry(user, obj, action_flag, change_message):
    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.id,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=change_message
    )

def is_fert(s):
    if '-' in s or '.' in s:
        return False
    
    if len(s) != 7:
        return False

    try:
        int(s)
        return True
    except ValueError:
        return False
    
def assign_color(product):
    if not product:
        return
    # Strings that identify light colors
    light_substrings = ['LT.', 'LIGHT', 'Lt.', 'Light']
    lc = get_object_or_404(Color, name="Light Cyan")
    lm = get_object_or_404(Color, name="Light Magenta")
    ly = get_object_or_404(Color, name="Light Yellow")
    lk = get_object_or_404(Color, name="Light Black")
    lgy = get_object_or_404(Color, name="Light Grey")
    c = get_object_or_404(Color, name="Cyan")
    m = get_object_or_404(Color, name="Magenta")
    y = get_object_or_404(Color, name="Yellow")
    k = get_object_or_404(Color, name="Black")
    w = get_object_or_404(Color, name="White")
    ora = get_object_or_404(Color, name="Orange")
    gr = get_object_or_404(Color, name="Green")
    r = get_object_or_404(Color, name="Red")
    bl = get_object_or_404(Color, name="Blue")
    v = get_object_or_404(Color, name="Violet")
    cleaner = get_object_or_404(Color, name="Cleaner")
    ff = get_object_or_404(Color, name="Flushing Fluid")

    if any(substring in product.name for substring in light_substrings):
        # this is  light   
        # print(f"{product.name}", end = "")
        if "CYAN" in product.name or "Cyan" in product.name:
            product.color = lc
        if "MAGENTA" in product.name or "Magenta" in product.name:
            product.color = lm
        if "YELLOW" in product.name or "Yellow" in product.name:
            product.color = ly
        if "BLACK" in product.name or "Black" in product.name:
            product.color = lk
        if "GREY" in product.name or "Grey" in product.name:
            product.color = lgy
    else:
        if "CYAN" in product.name or "Cyan" in product.name:
            product.color = c
        if "MAGENTA" in product.name or "Magenta" in product.name:
            product.color = m
        if "YELLOW" in product.name or "Yellow" in product.name:
            product.color = y
        if "BLACK" in product.name or "Black" in product.name:
            product.color = k
        if "WHITE" in product.name or "White" in product.name:
            product.color = w
        if "CLEANER" in product.name or "Cleaner" in product.name:
            product.color = cleaner
        if "FLUSH" in product.name or "Flush" in product.name:
            product.color = ff
        if "ORANGE" in product.name or "Orange" in product.name:
            product.color = ora
        if "GREEN" in product.name or "Green" in product.name:
            product.color = gr
        if "BLUE" in product.name or "Blue" in product.name:
            product.color = bl
        if "RED" in product.name or "Red" in product.name:
            product.color = r
        if "VIOLET" in product.name or "Violet" in product.name:
            product.color = v
    product.approved_by = get_object_or_404(User, email = "Marco.zanella@inxeurope.com")
    product.approved_on = datetime.now()
    product.save()
                
    pass