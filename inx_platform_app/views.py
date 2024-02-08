from typing import Any
from django.db.models.query import QuerySet
from django.db import connection
from django.utils import timezone
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import models, transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView
from .models import ColorGroup, Division, MadeIn, MajorLabel, InkTechnology, NSFDivision, MarketSegment, MaterialGroup, Packaging, ProductStatus, UnitOfMeasure, ExchangeRate, Scenario, CountryCode, CustomerType
from .models import Fbl5nArrImport, Fbl5nOpenImport, Ke24ImportLine, Ke24Line, ZACODMI9_line, ZACODMI9_import_line, Ke30ImportLine, Ke30Line
from .models import Color, Brand, Product, RateToLT, Customer, User
from .models import BudForLine, BudForDetailLine
from .models import UploadedFile, StoredProcedure
from .forms import EditMajorLabelForm, EditBrandForm, EditCustomerForm, EditProductForm, EditProcedureForm, CustomUserCreationForm, UserPasswordChangeForm, RegistrationForm, LoginForm, UserPasswordResetForm, UserSetPasswordForm
from . import dictionaries
import pyodbc
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from time import perf_counter
import multiprocessing
from sqlalchemy import create_engine

def index(request):
    return render(request, "app_pages/index.html", {})

def index_original(request):
    return render(request, "app_pages/index_original.html", {})

def profile(request):
    return render(request, "app_pages/profile.html", {})

def index_inx(request):
    return render(request, "index-inx.html")

def account_settings(request):
    context = {
        'parent': 'extra',
        'segment': 'settings',
    }
    return render(request, 'app_pages/settings.html', context)

@login_required
def loader(request):
    if request.method == "POST":

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        ke30_file = request.FILES.get('ke30_file')
        ke24_file = request.FILES.get('ke24_file')
        zaq_file = request.FILES.get('zaq_file')
        oo_file = request.FILES.get('oo_file')
        oh_file = request.FILES.get('oh_file')
        oi_file = request.FILES.get('oi_file')
        arr_file = request.FILES.get('arr_file')
        pr_file = request.FILES.get('pr_file')
        boms_file = request.FILES.get('boms_file')

        user_name = request.user.get_snakecase_name()

        files_list = [
            ('ke30_file', ke30_file),
            ('ke24_file', ke24_file),
            ('zaq_file', zaq_file),
            ('oo_file', oo_file),
            ('oh_file', oh_file),
            ('oi_file', oi_file),
            ('arr_file', arr_file),
            ('pr_file', pr_file),
            ('boms_file', boms_file),
        ]

        for file_field, original_file in files_list:
            if original_file is not None:
                original_file_nane = original_file.name.lower()
                prefix = file_field.split('_')[0]
                original_file_nane = prefix +"_" + user_name + "_" + timestamp + "_" + original_file_nane
                upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                with open(os.path.join(upload_dir, original_file_nane), 'wb+') as destination:
                    # for chunk in ke30_file.chunks():
                    for chunk in original_file.chunks():
                        destination.write(chunk)
                    # here it's done, update the database
                    uploaded_file = UploadedFile(owner=request.user, file_type=prefix, file_path=upload_dir, file_name=original_file_nane)
                    uploaded_file.save()
        return redirect('display_files')
    else:
        return render(request, "loader.html", {})

@login_required
def import_data(request):
    import_from_SQL(dictionaries.tables_list)
    return render(request, "index.html")

@login_required
def import_data_improved(request):
    import_from_SQL_improved_2(dictionaries.tables_list)
    return render(request, "index.html")

def import_single(request):
    context = {'options': dictionaries.tables_list}
    if request.method == 'POST':
        submit_action = request.POST.get('submit_type')
        table_name = request.POST.get('table_name')
        filtered_tuple = [(t1, t2, t3, t4) for t1, t2, t3, t4 in dictionaries.tables_list if t1 == table_name]
        if submit_action == 'Import':
            import_from_SQL(filtered_tuple)
            messages.success(request, f"Import done on {table_name}")
        if submit_action == 'Clean':
            clean_the_table(filtered_tuple)
            messages.success(request, f"Clean done on {table_name}")
        return render(request, "import_single.html", context)
    else:
        return render(request, "import_single.html", context)

def import_from_SQL(table_tuples):
    host = os.getenv("DB_SERVER", default=None)
    if  host == None: host = 'localhost'
    database = os.getenv("ORIGINAL_DB_NAME", default=None)
    if database == None: database = 'INXD_Database'
    username = os.getenv("ORIGINAL_DB_USERNAME", default=None)
    if  username == None: username = 'sa'
    password = os.getenv("ORIGINAL_DB_PASSWORD", default=None)
    if password == None: password = "dellaBiella2!"
    driver = os.getenv("DB_DRIVER", None)
    if driver == None: driver = '{ODBC Driver 18 for SQL Server}'
   
    connection_string = f"DRIVER={driver};SERVER={host};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;Connection Timeout=30;"
    # print(connection_string)
    try:        
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Connection Error: {str(e)}")
    # Working to import
    for table_name, field_name, model_class, mapping in table_tuples:
        # Query to get all records of the table
        query = f"SELECT * FROM {table_name}"
        msg = "startint to get rows ..."
        print(msg, end="")
        cursor.execute(query)
        records = cursor.fetchall()
        print("\r", " "* len(msg), end="")
        print(f"completed. {query}")
        if not records:
            print("no rows")
            continue # Skip empty tables
        how_many_records = len(records)
        print(' '*80,'\n','-'*80)
        print('SQL table name:', table_name, '-', how_many_records, "records")
        print('-'*80)
        # Get column names, in a list
        column_names = [column[0] for column in cursor.description]
        
        # Making a Dataframe
        data_dicts = [dict(zip(row.cursor_description, row)) for row in records]
        df = pd.DataFrame(data_dicts)
        df.columns = column_names
        
        if table_name == 'Users':
            for index, row in df.iterrows():
                if row['email'] == 'marco.zanella@inxeurope.com':
                    df.at[index, 'email'] = 'marco.zanella.sql@inxeurope.com'

        # For testing
        # df = df.head(1)

        # Prune unnecessary columns
        columns_to_keep = [column for column in df.columns if column in mapping]
        df = df[columns_to_keep]

        # creating a copy of the index column, if there is one
        if not field_name == None:
            df['sqlapp_id'] = df[field_name]
            df.drop(columns=[field_name], inplace=True)
        
        # When the tables have no index, the table will be truncated
        if field_name == None:
            model_class.objects.all().delete()
            print(f"All records from {model_class.__name__} have been deleted")

        # Changing column names
        for sql_column, django_field in mapping.items():
            # Rename the column using the mapping
            if sql_column in df.columns:
                df.rename(columns={sql_column: django_field}, inplace=True)

        # Remove np.nan
        df = df.replace(np.nan, None)

        # Iterate through the model_class fields and detect data types
        for field in model_class._meta.get_fields():
            field_name = field.name
            if field_name in model_class._meta.fields_map: continue
            if field_name in df.columns:
                if isinstance(field, models.IntegerField):
                    df[field_name] = df[field_name].fillna(0)
                    df[field_name] = df[field_name].astype(int)
                elif isinstance(field, models.FloatField):
                    df[field_name] = df[field_name].fillna(0)
                    df[field_name] = df[field_name].astype(float)
                elif isinstance(field, models.DateTimeField):
                    df[field_name] = pd.to_datetime(df[field_name], errors='coerce')
                elif isinstance(field, models.CharField):
                    df[field_name] = df[field_name].fillna('')
                    df[field_name] = df[field_name].astype(str)

        df.to_excel("customers_beforeFK.xlsx")

        # --------------------------------------------------
        # FOREIGN KEYS JOB
        # Here I am building a small list of lists
        # The innner list is built as follows
        # (app_db_column_name, Model)
        # --------------------------------------------------

        # Building model_fks_dict
        # This is a dictionary of foreign keys
        # key: name of the field
        # value: model_class referenced
        model_fks_dict = {}
        other_model_fks_dict = {}
        t_start = perf_counter()
        for field in model_class._meta.get_fields():
            if isinstance(field, models.ForeignKey):
                app_db_column_name = field.db_column
                # Perchè questo if qui sotto?
                if not app_db_column_name:
                    app_db_column_name = field.name + '_id'
                # model_fks_dict.update({app_db_column_name: field.related_model})
                #----------
                related_model = field.related_model
                related_objects = related_model.objects.all()
                related_df = pd.DataFrame(list(related_objects.values()))
                # Store the DataFrame in model_fks_dict
                other_model_fks_dict[app_db_column_name] = (related_model, related_df)
                # ------------

        if model_fks_dict: pass
        if other_model_fks_dict:
            print(f"FK fields of table {table_name}")
            # for fk in other_model_fks_dict.items():
            #     print(f"-{fk}")
        print(f"created model FKs dictionary in {round(perf_counter()-t_start, 2):.2f} seconds")

        # Iterating to update FKs IDs
        # Iterate through the DataFrame
        t_start = perf_counter()
        for index, row in df.iterrows():
            print (f"row {index+1}/{len(df)}", end="\r")
            for sql_column, django_field in mapping.items():
                if (sql_column == 'ID' and django_field == 'ID') or sql_column == django_field:
                    continue
                # --------------
                if django_field in other_model_fks_dict:
                    related_model, related_df = other_model_fks_dict[django_field]
                    # Get the SQL column value
                    sql_column_value = row[django_field]

                    # Look up the related model instance by sqlapp_id in the DataFrame
                    matching_rows = related_df.loc[related_df['sqlapp_id'] == sql_column_value]

                    if not matching_rows.empty:
                        # Get the first matching instance (if there is one)
                        found_results = True
                        related_instance = matching_rows.iloc[0]
                    else:
                        found_results = False

                    if found_results:
                        if not related_instance.empty:
                            # Update the DataFrame column with the related model's ID
                            df.at[index, django_field] = related_instance.id
                    else:
                        df.at[index, django_field] = None
                    # -------------
                '''
                # Check if the column is in the model_fks_dict
                if django_field in model_fks_dict:
                    # Get the related model
                    related_model = model_fks_dict[django_field]
                    
                    # Check if the SQL column has a corresponding value in the DataFrame row
                    if django_field in row.index and not pd.isnull(row[django_field]):
                        # Get the SQL column value (names are already changed to django, so use django names)
                        sql_column_value = row[django_field] 
                        # Look up the related model instance by sqlapp_id
                        related_instance = related_model.objects.filter(sqlapp_id=sql_column_value).first()
                        if related_instance:
                            # Update the DataFrame column with the related model's ID
                            df.at[index, django_field] = related_instance.id
                        else:
                            # Handle cases where there is no related instance found
                            pass
                        '''
        print(f"Update of FKs done in {round(perf_counter()-t_start, 2):.2f} seconds")
        df.to_excel("customers_afterFK.xlsx")
        try:
            with transaction.atomic():
                print("start atomic transaction")
                instances_to_create = []
                problematic_rows = []
                # df.to_excel("customers.xlsx")
                for row in df.to_dict(orient='records'):
                    try:
                        instances_to_create.append(model_class(**row))
                    except Exception as ex:
                        problematic_rows.append((row, str(ex)))
                if problematic_rows:
                    print("Problematic Rows:")
                    for idx, (row_data, error_msg) in enumerate(problematic_rows):
                        print(f"Row {idx + 1}: {error_msg}\n{row_data}\n")
                else:
                    print("no problematic rows")
                # instances_to_create = [model_class(**row) for row in df.to_dict(orient='records')]
                print(f"insances_to_create - model {model_class.__name__}")
                model_class.objects.bulk_create(instances_to_create)
                print(f"SUCCESS importing {table_name}")                 
        except Exception as e:
            print(e)
        conn.close()
        # Dataframe ---------------   

        """
        # Looping through all table's records
        record_counter = 0
        records_to_insert = [] # List to collect all records to be insterted
        for record in records:
            sqlapp_id = None
            # Off the record, we make a dictionary
            # field_name: field_value
            record_dict = dict(zip(column_names, record))
            # Here we get the value of what should be the index
            if not field_name == None:
                sqlapp_id = record_dict[field_name]

            # Create a dictionary of field values to be saved in the model
            # looping through the mapping
            # This modifies some field name
            single_record_dict_fields = {}
            for sql_column, django_field in mapping.items():
                value = record_dict.get(sql_column)
                if value is not None:
                    try:
                        if type(value) == datetime:
                            value = timezone.make_aware(value)
                    except ValueError:
                        value = None
                    single_record_dict_fields[django_field] = value

            # --------------------------------------------------
            # Now there is dict that I could save in the app db
            # becasue there are django field names,
            # but I need first to adapt reference ids
            # --------------------------------------------------
            # For those fields that are foreign keys, I need to search in the
            # referenced table what is the id (in django)
            # and replace it in the dictionary that I am going to save below
            # --------------------------------------------------
            # Loop single_record_dict_fields and detect which fileds are FK
            
            # First, I need to take the first element of all lists in model_fks,
            # and make a list out of it
            # Ths list contains the name of the fields that are FKsu                
            for sql_table_field in single_record_dict_fields:
                # if model_fks_dict and sql_table_field in model_fks_dict:
                if sql_table_field in model_fks_dict:
                    # get 'value' from the dictionary
                    related_model = model_fks_dict[sql_table_field]
                    record_found = related_model.objects.filter(sqlapp_id=single_record_dict_fields[sql_table_field]).first()
                    if record_found == None:
                        print(f'related_model: {related_model.__name__}')
                        print('single_record_dict_fields')
                        for key, value in single_record_dict_fields.items():
                            print(f'{key}: {value}')
                        
                    # print(f'record_found.id: {record_found.id}')
                    single_record_dict_fields[sql_table_field] = record_found.id
                    record_found = None
            
            if field_name != None:
                single_record_dict_fields['sqlapp_id'] = sqlapp_id
                single_record_dict_fields.pop(field_name)
            
            # Prepping for bulk_create
            model_instance = model_class(**single_record_dict_fields)
            records_to_insert.append(model_instance)
            record_counter += 1
            if record_counter % 1000 == 0:
                print(f"{record_counter}/{how_many_records}")

        try:
            with transaction.atomic():
                model_class.objects.bulk_create(records_to_insert)                     
            # record_counter, log_messages = save_model(the_class=model_class, the_data=single_record_dict_fields, counter=record_counter, all_records=how_many_records, logs=log_messages)
        except Exception as e:
            print(e)
           
    # Close the database connection
    conn.close()
    """ 



def get_pk_from_sqlapp_id(model_class, sqlapp_id_value):
    # print("model_class:", model_class.__name__, "\n input sqlapp_id_value:", sqlapp_id_value, end='')
    try:
        instance = model_class.objects.get(sqlapp_id=sqlapp_id_value)
        # print("\t returned pk value:", instance.pk)
        return instance.pk
    except model_class.DoesNotExist:
        # Handle the case where the instance is not found
        # print("instance not found")
        return None


@login_required
def clean_single(request):
    context = {'options': dictionaries.tables_list}
    if request.method == 'POST':
        selected_table = request.POST.get('selected_option', None)
        if selected_table:
            # filter the list of tuples and leave only the selected one
            filtered_tuple_list = [(t1, t2, t3, t4) for t1, t2, t3, t4 in dictionaries.tables_list if t1 == selected_table]
            clean_the_table(filtered_tuple_list)
            return render(request, "clean_single.html", context)
    else:
        return render(request, "clean_single.html", context)


def clean_the_table(tuple_list):
    # Take the name of the model from the tuple passed as argument
    model_to_clean = tuple_list[0][2]
    model_to_clean.objects.all().delete()


@login_required
def clean_db(request):

    list_of_table_names = [table[0] for table in dictionaries.tables_list]
    list_of_table_names.reverse()

    model_list = []
    for table in list_of_table_names:
        for item in dictionaries.tables_list:
            if table == item[0]: model_list.append(item[2])
    
    for model in model_list:
        if not model == User:
            model.objects.all().delete()
    
    return render(request, 'index-inx.html', {})


def save_model(the_class, the_data, counter, all_records, logs=None):
    if the_class.__name__ == 'User':
        if the_data['email'] == 'marco.zanella@inxeurope.com':
            if the_data['first_name'] == 'Marco':
                the_data['email'] = "old_marco_zanella@inxeurope.com"
                the_data['first_name'] = "First"
                the_data['last_name'] = "Last"
            elif the_data['first_name'] == 'New':
                the_data['email'] = "new_business@inxeurope.com"
                the_data['first_name'] = "New"
                the_data['last_name'] = "Business"

    if 'sqlapp_id' in the_data:
        sql_app_to_find = the_data.get('sqlapp_id')
        rec_exists = the_class.objects.filter(sqlapp_id=sql_app_to_find)
        if not rec_exists:
            model_item = the_class(**the_data)
        else:
            model_item = None
    else:
        model_item = the_class(**the_data)
    if model_item:
        model_item.save()
        counter += 1
        message = f"saved ... {str(counter).zfill(6)} / {str(all_records).zfill(6)}"
        soglia =100
        if all_records < soglia:
            # print(" " * length_of_message, end="\r")
            print(message, end="\r")
            # print(message)
        if counter % soglia == 0:
            # print(" " * length_of_message, end="\r")
            print(message, end="\r")
            # print(message)
        if counter == all_records:
            # print(" " * length_of_message, end="\r")
            print(message, end="\r")
            # print(message)

        logs.append(f"Imported {the_class.__name__} - {counter}/{all_records}")
    else:
        print(50*' ', end='\r')
        print(f'skipping sqlapp_id {sql_app_to_find}', end='\r')
    return counter, logs

def display_files(request):
    user = request.user
    user_files = UploadedFile.objects.filter(owner=user)
    
    return render(request, "display_files.html", {'user_files': user_files})

def start_processing(request, file_id):
    # This is used to run a method in UploadedFile class
    # Method is called start_processing
    file = get_object_or_404(UploadedFile, id = file_id)
    file.start_processing()
    return redirect('display_files')

def delete_file(request, file_id):
    file = get_object_or_404(UploadedFile, id = file_id)
    file.delete_file()
    return redirect('display_files')

@login_required
def list_customers(request, page=0):
    customers = Customer.objects.all().order_by('name')
    items_per_page = 52
    paginator = Paginator(customers, items_per_page)

    # Get the current page from the GET request or in the URL
    if page != 0:
        page_number = page
    else:
        try:
            page_number = request.GET.get('page', 1)
        except (ValueError, TypeError):
            page_number = 1

    # Making a set of records for the page
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.get_page(1)

    #Get the total number of pages
    num_pages = paginator.num_pages
    print('There are', num_pages, 'pages')
    page_obj.adjusted_elided_pages = paginator.get_elided_page_range(page_number)
    # page_obj.adjusted_elided_pages_list = list(page_obj.adjusted_elided_pages)
    
    for customer in page_obj:
        country_iso = customer.country.iso3166_1_alpha_2.lower()
        customer.flag_path = f"flags/{country_iso}.svg"

    context = {'customers_page': page_obj}
    
    return render(request, "list_customers.html", context)

def edit_dictionary(request, dictionary_name):
    print(dictionary_name)
    dict_path = os.path.join(settings.MEDIA_ROOT, "dictionaries")
    path_dict_converting = f"{dict_path}/{dictionary_name}_converting.json"
    path_dict_renaming = f"{dict_path}/{dictionary_name}_renaming.json"

    if request.method == 'POST':
        if 'submit_button' in request.POST:
            button_value = request.POST['submit_button']
            if button_value == 'form_converting':
                data_converting = {}
                for key, value in request.POST.items():
                    if key.startswith('data_converting'):
                        key_name = key[len('data_converting['):-1]
                        data_converting[key_name] = value
                with open(path_dict_converting, 'w') as file_converting:
                    json.dump(data_converting, file_converting)

            if button_value == 'form_renaming':
                data_renaming = {}
                for key, value in request.POST.items():
                    if key.startswith('data_renaming'):
                        key_name = key[len('data_renaming['):-1]
                        data_renaming[key_name] = value
                with open(path_dict_renaming, 'w') as file_renaming:
                    json.dump(data_renaming, file_renaming)

    with open(path_dict_converting, 'r') as file_converting:
        data_converting = json.load(file_converting)

    with open(path_dict_renaming, 'r') as file_renaming:
        data_renaming = json.load(file_renaming)
    
    return render(request, "edit_dictionary.html", {'dictionary_name': dictionary_name, 'data_converting': data_converting, 'data_renaming': data_renaming})

def dictionary_add_key(request, dictionary_name):
    key_name = request.GET.get('key_name', '')
    if key_name:
        # Add the key to the dictionary and update the JSON file
        # You can use a similar approach as in the update_dictionary view
        return JsonResponse({'message': 'Key added successfully'})
    return JsonResponse({'message': 'Key not added'})

def dictionary_delete_key(request, dictionary_name):
    print('delete dictionary key on the dictionary: ', dictionary_name)
    key_name = request.GET.get('key_name', '')
    if key_name:
        # Add the key to the dictionary and update the JSON file
        # You can use a similar approach as in the update_dictionary view
        return JsonResponse({'message': 'Key deleted successfully'})
    return JsonResponse({'message': 'Key not deleted'})

@method_decorator(login_required, name='dispatch')
class BrandListView(ListView):
    model = Brand
    paginate_by = 24
    template_name = "brand_list.html"
    context_object_name = "brands"

@method_decorator(login_required, name='dispatch')
class BrandEditView(UpdateView):
    model = Brand
    form_class = EditBrandForm
    template_name = "brand_edit.html"
    success_url = "/brands/"

    def get_object(self, queryset=None):
        id = self.kwargs.get('id', None)
        return get_object_or_404(Brand, id=id)

@method_decorator(login_required, name='dispatch')
class CustomerListView(ListView):
    model=Customer
    paginate_by=24
    template_name = "customer_list.html"
    context_object_name = "customers"

    def get_queryset(self) -> QuerySet[Any]:
        query = self.request.GET.get('search')
        reset_pressed = 'reset' in self.request.GET
        if query and not reset_pressed:
            return Customer.objects.filter(
                models.Q(name__icontains=query) |
                models.Q(number__icontains=query) |
                models.Q(country__iso3166_1_alpha_2__icontains=query) |
                models.Q(country__official_name_en__icontains=query) |
                models.Q(sales_employee__first_name__icontains=query) |
                models.Q(sales_employee__last_name__icontains=query)
                ).order_by('name')
        else:
            return Customer.objects.all().order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reset_pressed'] = 'reset' in self.request.GET
        return context

@method_decorator(login_required, name='dispatch')
class CustomerEditView(UpdateView):
    model = Customer
    form_class = EditCustomerForm
    template_name = "customer_edit.html"
    success_url = "/customers/"

    def get_object(self, queryset=None):
        id = self.kwargs.get('id', None)
        return get_object_or_404(Customer, id=id)

@method_decorator(login_required, name='dispatch')
class ProductListView(ListView):
    model=Product
    paginate_by=24
    template_name = "product_list.html"
    context_object_name = "products"

    def get_queryset(self) -> QuerySet[Any]:
        query = self.request.GET.get('search')
        queryset = Product.objects.all().order_by('name')
        reset_pressed = 'reset' in self.request.GET
        if query and not reset_pressed:
            queryset = Product.objects.filter(
                models.Q(name__icontains=query) |
                models.Q(number__icontains=query) |
                models.Q(color__name__icontains=query) |
                models.Q(made_in__name__icontains=query) |
                models.Q(brand__name__icontains=query) |
                models.Q(packaging__name__icontains=query) |
                models.Q(product_line__name__icontains=query) |
                models.Q(product_status__name__icontains=query)
                ).order_by('name')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reset_pressed'] = 'reset' in self.request.GET
        return context

@method_decorator(login_required, name='dispatch')
class ProductEditView(UpdateView):
    model = Product
    form_class = EditProductForm
    template_name = "product_edit.html"
    success_url = "/products/"

    def get_object(self, queryset=None):
        id = self.kwargs.get('id', None)
        return get_object_or_404(Product, id=id)

@method_decorator(login_required, name='dispatch')
class MajorLabelListView(ListView):
    model = MajorLabel
    paginate_by = 10
    template_name = "major_label_list.html"
    context_object_name = "major_labels"

@method_decorator(login_required, name='dispatch')
class MajorLabelEditView(UpdateView):
    model = MajorLabel
    form_class = EditMajorLabelForm
    template_name = "major_label_edit.html"
    success_url = "/major/"

    def get_object(self, queryset=None):
        id = self.kwargs.get('id', None)
        return get_object_or_404(MajorLabel, id=id)

@method_decorator(login_required, name='dispatch')
class MajorLabelCreateView(CreateView):
    model = MajorLabel
    form_class = EditMajorLabelForm
    template_name = "major_label_create.html"
    success_url = "/major/"

@method_decorator(login_required, name='dispatch')
class StoredProcedureListView(ListView):
    model = StoredProcedure
    template_name = 'stored_procedures/list.html'
    context_object_name = 'procedures'

@method_decorator(login_required, name='dispatch')
class StoredProcedureUpdateView(UpdateView):
    model = StoredProcedure
    form_class = EditProcedureForm
    template_name = 'stored_procedures/update.html'
    success_url = reverse_lazy('procedure_list')

def push_and_execute(request, pk):
    procedure = get_object_or_404(StoredProcedure, pk=pk)
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM information_schema.routines WHERE routine_name = '{procedure.name}'")
        exists = cursor.fetchone()[0]
    
    if exists:
        # If it exists, drop the existing stored procedure
        with connection.cursor() as cursor:
            cursor.execute(f"DROP PROCEDURE {procedure.name}")
            
    with connection.cursor() as cursor:
        cursor.execute(procedure.script)
        cursor.execute(f"EXEC {cursor.name}")

    return redirect('procedure_list')
    

# For User Management
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a success page or any other desired page after successful user creation
            return redirect('index')
    else:
        form = CustomUserCreationForm()

    return render(request, 'authenticate/create_user.html', {'form': form})

def login_user(request):
    if request.method == "POST":
        email = request.POST["login_email"]
        password = request.POST["login_password"]
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, ('You were successfully logged in'))
            # Check if there is a 'next' parameter in the URL
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('index')
        else:
            messages.success(request, ("There was an error loggin in ..."))
            return redirect('login')
    else:
        return render (request, 'authenticate/login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request, ("You were logged out"))
    return redirect('index')

class UserListView(ListView):
    model = User
    template_name = "list_users.html"
    context_object_name = "users"

class UserUpdateView(UpdateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'edit_user.html'
    success_url = reverse_lazy('list_users')

class UserPasswordChangeView(PasswordChangeView):
  template_name = 'app_pages/password-change.html'
  form_class = UserPasswordChangeForm


# Interface
def accordion(request):
    context = {
        'parent': 'interface',
        'segment': 'accordion',
    }
    return render(request, 'app_pages/accordion.html', context)

def blank_page(request):
    context = {
        'parent': 'interface',
        'segment': 'blank_page',
    }
    return render(request, 'app_pages/blank.html', context)

def badges(request):
    context = {
        'parent': 'interface',
        'segment': 'badges',
    }
    return render(request, 'app_pages/badges.html', context)

def buttons(request):
    context = {
        'parent': 'interface',
        'segment': 'buttons',
    }
    return render(request, 'app_pages/buttons.html', context)

# Cards
def sample_cards(request):
    context = {
        'parent': 'interface',
        'segment': 'sample_cards',
    }
    return render(request, 'app_pages/cards.html', context)

def card_actions(request):
    context = {
        'parent': 'interface',
        'segment': 'card_actions',
    }
    return render(request, 'app_pages/card-actions.html', context)

def cards_masonry(request):
    context = {
        'parent': 'interface',
        'segment': 'cards_masonry',
    }
    return render(request, 'app_pages/cards-masonry.html', context)

def colors(request):
    context = {
        'parent': 'interface',
        'segment': 'colors',
    }
    return render(request, 'app_pages/colors.html', context)

def data_grid(request):
    context = {
        'parent': 'interface',
        'segment': 'data_grid',
    }
    return render(request, 'app_pages/datagrid.html', context)

def datatables(request):
    context = {
        'parent': 'interface',
        'segment': 'datatables',
    }
    return render(request, 'app_pages/datatables.html', context)

def dropdowns(request):
    context = {
        'parent': 'interface',
        'segment': 'dropdowns',
    }
    return render(request, 'app_pages/dropdowns.html', context)

def modals(request):
    context = {
        'parent': 'interface',
        'segment': 'modals',
    }
    return render(request, 'app_pages/modals.html', context)

def maps(request):
    context = {
        'parent': 'interface',
        'segment': 'maps',
    }
    return render(request, 'app_pages/maps.html', context)

def map_fullsize(request):
    context = {
        'parent': 'interface',
        'segment': 'map_fullsize',
    }
    return render(request, 'app_pages/map-fullsize.html', context)

def vector_maps(request):
    context = {
        'parent': 'interface',
        'segment': 'vector_maps',
    }
    return render(request, 'app_pages/maps-vector.html', context)

def navigation(request):
    context = {
        'parent': 'interface',
        'segment': 'navigation',
    }
    return render(request, 'app_pages/navigation.html', context)

def charts(request):
    context = {
        'parent': 'interface',
        'segment': 'charts',
    }
    return render(request, 'app_pages/charts.html', context)

def pagination(request):
    context = {
        'parent': 'interface',
        'segment': 'pagination',
    }
    return render(request, 'app_pages/pagination.html', context)

def placeholder(request):
    context = {
        'parent': 'interface',
        'segment': 'placeholder',
    }
    return render(request, 'app_pages/placeholder.html', context)

def steps(request):
    context = {
        'parent': 'interface',
        'segment': 'steps',
    }
    return render(request, 'app_pages/steps.html', context)

def stars_rating(request):
    context = {
        'parent': 'interface',
        'segment': 'stars_rating',
    }
    return render(request, 'app_pages/stars-rating.html', context)

def tabs(request):
    context = {
        'parent': 'interface',
        'segment': 'tabs',
    }
    return render(request, 'app_pages/tabs.html', context)

def tables(request):
    context = {
        'parent': 'interface',
        'segment': 'tables',
    }
    return render(request, 'app_pages/tables.html', context)

def inxd_customers(request):
    customers = Customer.objects.all()
    context = {
        'parent': 'interface',
        'segment': 'inxd_customers',
        'customers': customers
    }
    return render(request, 'app_pages/inxd_customers.html', context)

def carousel(request):
    context = {
        'parent': 'interface',
        'segment': 'carousel',
    }
    return render(request, 'app_pages/carousel.html', context)

def lists(request):
    context = {
        'parent': 'interface',
        'segment': 'lists',
    }
    return render(request, 'app_pages/lists.html', context)

def typography(request):
    context = {
        'parent': 'interface',
        'segment': 'typography',
    }
    return render(request, 'app_pages/typography.html', context)

def offcanvas(request):
    context = {
        'parent': 'interface',
        'segment': 'offcanvas',
    }
    return render(request, 'app_pages/offcanvas.html', context)

def markdown(request):
    context = {
        'parent': 'interface',
        'segment': 'markdown',
    }
    return render(request, 'app_pages/markdown.html', context)

def dropzone(request):
    context = {
        'parent': 'interface',
        'segment': 'dropzone',
    }
    return render(request, 'app_pages/dropzone.html', context)

def lightbox(request):
    context = {
        'parent': 'interface',
        'segment': 'lightbox',
    }
    return render(request, 'app_pages/lightbox.html', context)

def tinymce(request):
    context = {
        'parent': 'interface',
        'segment': 'tinymce',
    }
    return render(request, 'app_pages/tinymce.html', context)

def inline_player(request):
    context = {
        'parent': 'interface',
        'segment': 'inline_player',
    }
    return render(request, 'app_pages/inline-player.html', context)


# Authentication
class RegistrationView(CreateView):
  template_name = 'app_pages/sign-up.html'
  form_class = RegistrationForm
  success_url = '/accounts/login/'

class LoginView(LoginView):
  template_name = 'app_pages/sign-in.html'
  form_class = LoginForm

class LoginViewIllustrator(LoginView):
  template_name = 'app_pages/sign-in-illustration.html'
  form_class = LoginForm

class LoginViewCover(LoginView):
  template_name = 'app_pages/sign-in-cover.html'
  form_class = LoginForm

def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')

def login_link(request):
    return render(request, 'app_pages/sign-in-link.html')

class PasswordReset(PasswordResetView):
  template_name = 'app_pages/forgot-password.html'
  form_class = UserPasswordResetForm

class UserPasswordResetConfirmView(PasswordResetConfirmView):
  template_name = 'app_pages/password-reset-confirm.html'
  form_class = UserSetPasswordForm

class UserPasswordChangeView(PasswordChangeView):
  template_name = 'app_pages/password-change.html'
  form_class = UserPasswordChangeForm

def terms_service(request):
    return render(request, 'app_pages/terms-of-service.html')

def lock_screen(request):
    return render(request, 'app_pages/auth-lock.html')

# Error and maintenance
def error_404(request):
    return render(request, 'app_pages/error-404.html')

def error_500(request):
    return render(request, 'app_pages/error-500.html')

def maintenance(request):
    return render(request, 'app_pages/error-maintenance.html')


def form_elements(request):
    context = {
        'parent': '',
        'segment': 'form_elements',
    }
    return render(request, 'app_pages/form-elements.html', context)

# Extra
def empty_page(request):
    context = {
        'parent': 'extra',
        'segment': 'empty_page',
    }
    return render(request, 'app_pages/empty.html', context)

def cookie_banner(request):
    context = {
        'parent': 'extra',
        'segment': 'cookie_banner',
    }
    return render(request, 'app_pages/cookie-banner.html', context)

def activity(request):
    context = {
        'parent': 'extra',
        'segment': 'activity',
    }
    return render(request, 'app_pages/activity.html', context)

def gallery(request):
    context = {
        'parent': 'extra',
        'segment': 'gallery',
    }
    return render(request, 'app_pages/gallery.html', context)

def invoice(request):
    context = {
        'parent': 'extra',
        'segment': 'invoice',
    }
    return render(request, 'app_pages/invoice.html', context)

def search_results(request):
    context = {
        'parent': 'extra',
        'segment': 'search_results',
    }
    return render(request, 'app_pages/search-results.html', context)

def pricing_cards(request):
    context = {
        'parent': 'extra',
        'segment': 'pricing_cards',
    }
    return render(request, 'app_pages/pricing.html', context)

def pricing_table(request):
    context = {
        'parent': 'extra',
        'segment': 'pricing_table',
    }
    return render(request, 'app_pages/pricing-table.html', context)

def faq(request):
    context = {
        'parent': 'extra',
        'segment': 'faq',
    }
    return render(request, 'app_pages/faq.html', context)

def users(request):
    context = {
        'parent': 'extra',
        'segment': 'users',
    }
    return render(request, 'app_pages/users.html', context)

def license(request):
    context = {
        'parent': 'extra',
        'segment': 'license',
    }
    return render(request, 'app_pages/license.html', context)

def logs(request):
    context = {
        'parent': 'extra',
        'segment': 'logs',
    }
    return render(request, 'app_pages/logs.html', context)

def music(request):
    context = {
        'parent': 'extra',
        'segment': 'music',
    }
    return render(request, 'app_pages/music.html', context)

def photogrid(request):
    context = {
        'parent': 'extra',
        'segment': 'photogrid',
    }
    return render(request, 'app_pages/photogrid.html', context)

def tasks(request):
    context = {
        'parent': 'extra',
        'segment': 'tasks',
    }
    return render(request, 'app_pages/tasks.html', context)

def uptime(request):
    context = {
        'parent': 'extra',
        'segment': 'uptime',
    }
    return render(request, 'app_pages/uptime.html', context)

def widgets(request):
    context = {
        'parent': 'extra',
        'segment': 'widgets',
    }
    return render(request, 'app_pages/widgets.html', context)

def wizard(request):
    context = {
        'parent': 'extra',
        'segment': 'widgets',
    }
    return render(request, 'app_pages/wizard.html', context)

def settings(request):
    context = {
        'parent': 'extra',
        'segment': 'settings',
    }
    return render(request, 'app_pages/settings.html', context)

def settings_plan(request):
    context = {
        'parent': 'extra',
        'segment': 'settings',
    }
    return render(request, 'app_pages/settings-plan.html', context)

def trial_ended(request):
    context = {
        'parent': 'extra',
        'segment': 'trial_ended',
    }
    return render(request, 'app_pages/trial-ended.html', context)

def job_listing(request):
    context = {
        'parent': 'extra',
        'segment': 'job_listing',
    }
    return render(request, 'app_pages/job-listing.html', context)

def page_loader(request):
    context = {
        'parent': 'extra',
        'segment': 'page_loader',
    }
    return render(request, 'app_pages/page-loader.html', context)

# Layout
def layout_horizontal(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_horizontal',
    }
    return render(request, 'app_pages/layout-horizontal.html', context)

def layout_boxed(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_boxed',
    }
    return render(request, 'app_pages/layout-boxed.html', context)

def layout_vertical(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_vertical',
    }
    return render(request, 'app_pages/layout-vertical.html', context)

def layout_vertical_transparent(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_vertical_transparent',
    }
    return render(request, 'app_pages/layout-vertical-transparent.html', context)

def layout_vertical_right(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_vertical_right',
    }
    return render(request, 'app_pages/layout-vertical-right.html', context)

def layout_condensed(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_condensed',
    }
    return render(request, 'app_pages/layout-condensed.html', context)

def layout_combined(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_combined',
    }
    return render(request, 'app_pages/layout-combo.html', context)

def layout_navbar_dark(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_navbar_dark',
    }
    return render(request, 'app_pages/layout-navbar-dark.html', context)

def layout_navbar_sticky(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_navbar_sticky',
    }
    return render(request, 'app_pages/layout-navbar-sticky.html', context)

def layout_navbar_overlap(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_navbar_overlap',
    }
    return render(request, 'app_pages/layout-navbar-overlap.html', context)

def layout_rtl(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_rtl',
    }
    return render(request, 'app_pages/layout-rtl.html', context)

def layout_fluid(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_fluid',
    }
    return render(request, 'app_pages/layout-fluid.html', context)

def layout_fluid_vertical(request):
    context = {
        'parent': 'layout',
        'segment': 'layout_fluid_vertical',
    }
    return render(request, 'app_pages/layout-fluid-vertical.html', context)

def changelog(request):
    return render(request, 'app_pages/changelog.html')

def profile(request):
    return render(request, 'app_pages/profile.html')

def icons(request):

    context = {
        'parent': '',
        'segment': 'icons',
    }
    return render(request, 'app_pages/icons.html', context)



