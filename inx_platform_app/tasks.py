from celery import Celery, shared_task, current_task
from django.utils import timezone
from celery.utils.log import get_task_logger
from django.shortcuts import get_object_or_404
from django.db import connection
from .models import *
from . import dictionaries, import_dictionaries
import pandas as pd
import time
import os
from loguru import logger as django_logger


# app = Celery('core_app', broker='redis://localhost:6379/0')
celery_logger = get_task_logger(__name__)


@shared_task
def file_processor(id_of_UploadedFile, user_id):
    # Get celery task id
    celery_task_id = current_task.request.id

    # Get the UploadedFile record via the id
    uploaded_file_record = get_object_or_404(UploadedFile, pk=id_of_UploadedFile)
    user = get_object_or_404(User, pk=user_id)
    if not uploaded_file_record:
        celery_logger.error(f"No UploadedFile record with id: {id_of_UploadedFile}")
        return
    if not os.path.exists(uploaded_file_record.file_path + "/" + uploaded_file_record.file_name):
        celery_logger.error(f"File does not exist.")
        return
    
    celery_logger.info(
        f"the file {uploaded_file_record.file_path + '/' + uploaded_file_record.file_name} has been found is ready to process"
        )
    
    # Create the first log line in the log table
    post_a_log_message(id_of_UploadedFile, user_id, celery_task_id, f"process {celery_task_id} started")

    # What type is the file
    # Preparing variables according to file_type
    match uploaded_file_record.file_type:
        case "ke30":
            df = read_this_file(uploaded_file_record, user, import_dictionaries.ke30_converters_dict, celery_task_id)
            if not df.empty:
                df['Importtimestamp'] = datetime.now()
                df["YearMonth"] = (df['Fiscal Year'].astype(int) * 100 + df['Period'].astype(int)).astype(str)
                # These 2 variable are set for the following action, after the match-case
                model = Ke30ImportLine
                field_mapping = import_dictionaries.ke30_mapping_dict
                list_of_sp =['_ke30_import', '_ke30_import_add_new_customers', '_ke30_import_add_new_products']
            else:
                celery_logger.error(f"file could not be read - {uploaded_file_record}")
                return
        case "ke24":
            result = read_this_file(uploaded_file_record,user, import_dictionaries.ke24_converters_dict, celery_task_id)
            if not result == False:
                df = df.drop(columns=['Industry Code 1'])               
                model = Ke24ImportLine
                field_mapping = import_dictionaries.ke24_mapping_dict
            else:
                celery_logger.error(f"file could not be read - {uploaded_file_record}")
                return
        case "zaq":
            result = read_this_file(uploaded_file_record,user, import_dictionaries.zaq_converters_dict, celery_task_id)
            if not result == False:
                df["Billing date"] = df['Billing date'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
                # This Excel file has the totals,at teh bottom, that must be removed
                # The number of rows may vary depending on the number of currencies and UoMs mentioned
                unique_uom = df['UoM'].nunique()
                unique_curr = df['Curr.'].nunique()
                rows_to_remove = max(unique_curr, unique_uom)
                df = df.head(len(df) - rows_to_remove) 
                model = ZAQCODMI9_import_line
                field_mapping = import_dictionaries.zaq_mapping_dict
                # Store procedure are importing from import table to full table
                # Then deleting sales from budfordetailline
                # Then backing up budfordetailline
                # Then filling in again sales from zaq with proper granularity
                list_of_sp = ['_zaq_import', '_budforline_add_triplets', '_budgetforecastdetail_fill_sales']
            else:
                celery_logger.error(f"file could not be read - {uploaded_file_record}")
                return
        case "oo":
            result = read_this_file(uploaded_file_record,user, import_dictionaries.oo_converters_dict, celery_task_id)
            if not result == False:
                df['LineType'] = 'OO'
                print(f"it was {len(df)}")
                uniques = len(df['Unit'].value_counts())
                df = df.iloc[:-uniques]
                print(f"it is {len(df)}")
                df = df[df["Plant"].notnull()]
                df["Order Date"] = df['Order Date'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
                df["Req. dt"] = df['Req. dt'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
                df["PL. GI Dt"] = df['PL. GI Dt'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
                df['Sold-to'] = df['Sold-to'].fillna(df['Ship-to'])
                df['Sold-to'] = np.where(df['Sold-to'] == '', df['Ship-to'], df['Sold-to'])
                model = Order
                field_mapping = import_dictionaries.oo_mapping_dict
            else:
                celery_logger.error(f"file could not be read - {uploaded_file_record}")
                return
        case "oi" | "arr":
            result = read_this_file(uploaded_file_record,user, import_dictionaries.oo_converters_dict, celery_task_id)
            if not result == False:
                uniques = len(df['Document currency'].value_counts())
                df = df.iloc[:-uniques]
                print(f"{uploaded_file_record.file_type} is now {len(df)} lines long")
                # Adjusting dates
                df['Document Date'] = df['Document Date'].dt.date
                df['Net due date'] = df['Net due date'].dt.date
                df['Payment date'] = df['Payment date'].dt.date
                df['Arrears after net due date'] = df['Arrears after net due date'].fillna(0).astype(int)
                if uploaded_file_record.file_type == "arr":
                    model = Fbl5nArrImport
                    field_mapping = import_dictionaries.arr_mapping_dict
                if uploaded_file_record.file_type == "oi":
                    model = Fbl5nOpenImport
                    field_mapping = import_dictionaries.oi_mapping_dict
            else:
                celery_logger.error(f"file could not be read - {uploaded_file_record}")
                return
        case "pr":
            result = read_this_file(uploaded_file_record,user, import_dictionaries.pr_converters_dict, celery_task_id)
            if not result == False:
                model = Price
                field_mapping = import_dictionaries.prl_mapping_dict
            else:
                celery_logger.error(f"file could not be read - {uploaded_file_record}")
                return
    celery_logger.info(f"model: {model}")
    
    ####################################################################################
    # Start inserting
    ####################################################################################
    model.objects.all().delete()
    post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"deleting rows from {model._meta.model_name}")
    df_length = len(df)
    df = df.replace(np.nan, '')
    chunk_size = 500
    chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
    chunk_counter = 0
    for chunk in chunks:
        chunk_counter += 1
        post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"processing ... {chunk_counter}/{len(chunks)}")
        try:
            start_time = time.perf_counter()
            # List to hold model instances
            instances = []
            for index, row in chunk.iterrows():
                instance = model()
                for field, column_name in field_mapping.items():
                    setattr(instance, field, row[column_name])
                instances.append(instance)
            with transaction.atomic():
                model.objects.bulk_create(instances)
                post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f'bulk_create for chunk {chunk_counter} done')
                instances = [] # resetting
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"working on chunk {chunk_counter} of {len(chunks)}  -  it took {elapsed_time} seconds")
        except Exception as e:
            # Handle the exception
            post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"An error occurred during the transaction: {e}")
    # All chunks are processed
    post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"All chuncks are processed")
    uploaded_file_record.is_processed = True
    uploaded_file_record.processed_at = timezone.make_aware(datetime.now())
    # Working on the stored procedures now
    if list_of_sp:
        post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"There are {len(list_of_sp)} stored procedures. {list_of_sp}")
        with connection.cursor() as curs:
            for index, sp in enumerate(list_of_sp):
                with transaction.atomic():
                    sql_command = f"EXECUTE {sp}"
                    curs.execute(sql_command)
                    if curs.description:
                        resulting_rows = curs.fetchall()
                        post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"resulting rows from sp {sp}.")
                        for row in resulting_rows:
                            row_text = ', '.join(map(str, row))
                            post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, row_text)
    # Delete the file
    post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"deleting ... {uploaded_file_record.file_name}")
    if uploaded_file_record.delete_file_soft():
        post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"File {uploaded_file_record.file_name} removed and db updated")
    else:
        log_message = f"There is a problem with file name {uploaded_file_record.file_name} - 'process terminated for file id: {uploaded_file_record.id}  filetye: {uploaded_file_record.file_type} file_name: {uploaded_file_record.file_name} file_path: {uploaded_file_record.file_path}"
        post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, log_message)
    log_message = f'process terminated for file id: {uploaded_file_record.id}  filetye: {uploaded_file_record.file_type} file_name: {uploaded_file_record.file_name} file_path: {uploaded_file_record.file_path}'
    post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, log_message)
    uploaded_file_record.save()

def post_a_log_message(id_of_UploadedFile, user_id, celery_task_id, message):
    uploaded_file_record = get_object_or_404(UploadedFile, pk=id_of_UploadedFile)
    user = get_object_or_404(User, pk=user_id)
    log = UploadedFileLog.objects.create(
        uploaded_file = uploaded_file_record,
        user = user,
        file_path = uploaded_file_record.file_path,
        file_name = uploaded_file_record.file_name,
        celery_task_id = celery_task_id,
        log_text = message
    )
    celery_logger.info(message)


def read_this_file(the_file, user, conversion_dictionary, celery_task_id):
    user_id = user.id
    uploaded_file_id = the_file.id
    full_file_name = the_file.file_path + "/" + the_file.file_name
    post_a_log_message(uploaded_file_id, user_id, celery_task_id, f"start reading {full_file_name}")
    df = the_file.read_excel_file(full_file_name, conversion_dictionary)
    if not df.empty:
        post_a_log_message(uploaded_file_id, user_id, celery_task_id, f"completed reading Excel file {full_file_name}")
        return df
    else:
        return False



@shared_task
def ticker_task(pippo):
    for iteration in range(3):
        time.sleep(7)
        celery_logger.info("ticker_task: tick!")
    return "ticker_task completed"

@shared_task
def very_long_task():
    for number in range(50):
        time.sleep(.3)
        celery_logger.info(f"number: {number}")
    return"task 50x completed!"

