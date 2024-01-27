from typing import Any
from django.db.models.query import QuerySet
from django.db import connection
from django.utils import timezone
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import models, transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView, CreateView
from inx_platform_members.models import User
from .models import ColorGroup, Division, MadeIn, MajorLabel, InkTechnology, NSFDivision, MarketSegment, MaterialGroup, Packaging, ProductStatus, UnitOfMeasure, ExchangeRate, Scenario, CountryCode, CustomerType
from .models import Fbl5nArrImport, Fbl5nOpenImport, Ke24ImportLine, Ke24Line, ZACODMI9_line, ZACODMI9_import_line, Ke30ImportLine, Ke30Line
from .models import Color, Brand, Product, RateToLT, Customer
from .models import BudForLine, BudForDetailLine
from .models import UploadedFile, StoredProcedure
from .forms import EditMajorLabelForm, EditBrandForm, EditCustomerForm, EditProductForm, EditProcedureForm
from . import dictionaries
from concurrent.futures import ProcessPoolExecutor
import pyodbc
import pandas as pd
import os
import json
from datetime import datetime

def index(request):

    return render(request, "index.html", {})

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
    import_from_SQL_improved(dictionaries.tables_list)
    return render(request, "index.html")

def import_single(request):
    context = {'options': dictionaries.tables_list}
    if request.method == 'POST':
        selected_table = request.POST.get('selected_option', None)
        submit_action = request.POST.get('submit_type')
        if selected_table:
            # filter the list of tuples and leave only the selected one
            filtered_tuple_list = [(t1, t2, t3, t4) for t1, t2, t3, t4 in dictionaries.tables_list if t1 == selected_table]
            if submit_action == 'Import':
                import_from_SQL(filtered_tuple_list)
            if submit_action == 'Clean':
                clean_the_table(filtered_tuple_list)
            return render(request, "import_single.html", context)
    else:
        return render(request, "import_single.html", context)

def import_from_SQL(table_tuples):
    log_messages = []

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
    print()
    print('-'*50)
    print(f'host    :{host}')
    print(f'database:{database}')
    print(f'username:{username}')
    print(f'password:{password}')
    print(f'driver  :{driver}')
    print('-'*50)
    print()
    connection_string = f"DRIVER={driver};SERVER={host};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;Connection Timeout=30;"
    print(connection_string)
    try:        
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Connection Error: {str(e)}")
    # Working to import
    for table_name, field_name, model_class, mapping in table_tuples:
        # Query to get all records of the table
        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)
        records = cursor.fetchall()
        if not records: continue # Skip empty tables
        how_many_records = len(records)
        print(' '*80,'\n','-'*80)
        print('SQL table name:', table_name, '-', how_many_records, "records")
        print(' '*80,'\n','-'*80)
        # Get column names, in a list
        column_names = [column[0] for column in cursor.description]
        
        # This is the field that must me used for sqlapp_id
        # field_index = column_names.index(field_name)
        
        # When the tables have no index, the table will be truncated
        if field_name == None:
            model_class.objects.all().delete()
            print(f"All records from {model_class.__name__} have been deleted")

        # --------------------------------------------------
        # FOREIGN KEYS JOB
        # Here I am building a small list of lists
        # The innner list is built as follows
        # (app_db_column_name, Model)
        # --------------------------------------------------
        # model_fks = []
        # print('model_class', model_class.__name__)
        # for field in model_class._meta.get_fields():
        #     if isinstance(field, models.ForeignKey):
        #         app_db_column_name = field.db_column
        #         if not app_db_column_name: app_db_column_name = field.name + '_id'
        #         model_referenced = [app_db_column_name, field.related_model]
        #         model_fks.append(model_referenced)

        # if model_fks:
        #     print(f"Foreign keys in {model_class.__name__} before modifications")
        #     for item in model_fks:
        #         print(item[0], end=', ')
        #     print(' ')

        # Building model_fks_dict
        # This is a dictionary of foreign keys
        # key: name of the field
        # value: model_class referenced
        model_fks_dict = {}
        for field in model_class._meta.get_fields():
            if isinstance(field, models.ForeignKey):
                app_db_column_name = field.db_column
                # Perchè questo if qui sotto?
                if not app_db_column_name:
                    app_db_column_name = field.name + '_id'
                model_fks_dict.update({app_db_column_name: field.related_model})

        # Looping through all table's records
        record_counter = 0
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
            try:                     
                record_counter, log_messages = save_model(the_class=model_class, the_data=single_record_dict_fields, counter=record_counter, all_records=how_many_records, logs=log_messages)
            except Exception as e:
                print(log_messages)
                print(e)
                    
        print()
    # Close the database connection
    conn.close()

def insert_records(records):
    with transaction.atomic():
        Ke30ImportLine.objects.bulk_create(records)

def process_dataframe_slice(df, field_mapping):
    records = []
    for _, row in df.iterrows():
        record = Ke30ImportLine()
        for pandas_field, model_field in field_mapping.items():
            setattr(record, model_field, row[pandas_field])
        records.append(record)
    insert_records(records)

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

def import_from_SQL_improved(table_tuples):
    # Import from SQL Azure to a dataframe
    # Connect to database
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

    try:
        connection_string = f"DRIVER={driver};SERVER={host};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;Connection Timeout=30;"
        print(connection_string)        
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
    except Exception as e:
        print("SQL database connection failed", e)

    mapping = dictionaries.mapping_Ke30ImportLine

    for table_name, index_field_name, model_class, mapping in table_tuples:
        print("\ntable_name:", table_name)
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, conn)
        # remove unwanted columns
        df = df.filter(items=mapping.keys())
        # rename columns
        df.rename(columns=mapping, inplace=True)
        # remove nan
        df.fillna(0, inplace=True)
        # Make date timezone aware
        for column in df.columns:
            # Check if the column contains datetime values
            if pd.api.types.is_datetime64_any_dtype(df[column]):
                # Make datetime values timezone aware (assuming UTC)
                df[column] = df[column].apply(lambda x: timezone.make_aware(x) if pd.notnull(x) else x)
                # df[column] = df[column].apply(lambda x: x.tz_localize(pytz.UTC) if pd.notnull(x) else x)
                
        # Making the sqlapp_id column, if there is index_field_name
        if not index_field_name == None:
            df['sqlapp_id'] = df[index_field_name].copy()
            df.drop(columns=index_field_name, inplace=True)
        
        if index_field_name == None:
            model_class.objects.all().delete()
            print(f"All records from {model_class.__name__} have been deleted")
        
        # Getting all Foreign keys in a dictionary with their models
        model_fks_dict = {}
        for field in model_class._meta.get_fields():
            if isinstance(field, models.ForeignKey):
                app_db_column_name = field.db_column
                # Perchè questo if qui sotto?
                if not app_db_column_name:
                    app_db_column_name = field.name + '_id'
                model_fks_dict.update({app_db_column_name: field.related_model})

        if not index_field_name == None:
            for column_name, fk_model_class in model_fks_dict.items():
                if column_name in df.columns:
                    df[column_name] = df.apply(lambda row: get_pk_from_sqlapp_id(fk_model_class, row[column_name]), axis=1)
              
        model_instances = []
        print("len df:", len(df))
        counter = 0
        for _, row in df.iterrows():
            if 'sqlapp_id' in df.columns:
                index_value = row['sqlapp_id']
                # the table has an index, if said index was already inserted, skip
                if not model_class.objects.filter(**{'sqlapp_id': index_value}).exists():
                    # Protecting the superuser
                    if 'email' in row and str(row['email']).lower() == 'marco.zanella@inxeurope.com':
                        row['email'] = str(row['email']).lower() + '.sql'
                    model_instance = model_class(**row.to_dict())
                    model_instances.append(model_instance)
            if index_field_name == None:
                model_instance = model_class(**row.to_dict())
                model_instances.append(model_instance)
            counter += 1
            print("\rcounter", counter, "/", len(df), end='')
        model_class.objects.bulk_create(model_instances)
        
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
    
    return render(request, 'index.html', {})

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
        length_of_message = len(message)
        if all_records < 100: soglia = 100
        if all_records >= 100 and all_records <= 1000: soglia = 100
        if all_records >= 100 and all_records > 1000: soglia = 100
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
    
