from celery import shared_task, current_task
from django.utils import timezone
from celery.utils.log import get_task_logger
from django.shortcuts import get_object_or_404
from django.db import connection, transaction
from django.db.models import Max
from django.contrib.admin.models import ADDITION, CHANGE
from .models import (
    User,
    UploadedFile,
    UploadedFileLog,
    Ke24ImportLine,
    Ke30ImportLine,
    ZAQCODMI9_import_line,
    Order,
    Fbl5nArrImport,
    Fbl5nOpenImport,
    Price,
    Product,
    ProductStatus,
    BomComponent,
    BomHeader,
    Bom,
    EuroExchangeRate,
    Currency
)
from .utils import (
    is_fert,
    create_log_entry
)
from . import import_dictionaries
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
import numpy as np
import time
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime


# app = Celery('core_app', broker='redis://localhost:6379/0')
celery_logger = get_task_logger(__name__)


@shared_task
def file_processor(id_of_UploadedFile, user_id):
    bom_work = False
    # Get celery task id
    celery_task_id = current_task.request.id

    # Get the UploadedFile record via the id
    uploaded_file_record = get_object_or_404(UploadedFile, pk=id_of_UploadedFile)
    user = get_object_or_404(User, pk=user_id)
    if not uploaded_file_record:
        celery_logger.error(f"No UploadedFile record with id: {id_of_UploadedFile}")
        return
    if not os.path.exists(uploaded_file_record.file_path + "/" + uploaded_file_record.file_name):
        celery_logger.error("File does not exist.")
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
            df = read_this_file(uploaded_file_record,user, import_dictionaries.ke24_converters_dict, celery_task_id)
            if not df.empty:
                df = df.drop(columns=['Industry Code 1'])               
                model = Ke24ImportLine
                field_mapping = import_dictionaries.ke24_mapping_dict
                list_of_sp =[]
            else:
                celery_logger.error(f"file could not be read - {uploaded_file_record}")
                return
        case "zaq":
            df = read_this_file(uploaded_file_record,user, import_dictionaries.zaq_converters_dict, celery_task_id)
            if not df.empty:
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
            df = read_this_file(uploaded_file_record,user, import_dictionaries.oo_converters_dict, celery_task_id)
            if not df.empty:
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
                list_of_sp =[]
            else:
                celery_logger.error(f"file could not be read - {uploaded_file_record}")
                return
        case "oi" | "arr":
            df = read_this_file(uploaded_file_record,user, import_dictionaries.oo_converters_dict, celery_task_id)
            if not df.empty:
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
                list_of_sp =[]
            else:
                celery_logger.error(f"file could not be read - {uploaded_file_record}")
                return
        case "pr":
            df = read_this_file(uploaded_file_record, user, import_dictionaries.pr_converters_dict, celery_task_id)
            if not df.empty:
                model = Price
                field_mapping = import_dictionaries.prl_mapping_dict
                list_of_sp =[]
            else:
                celery_logger.error(f"file could not be read - {uploaded_file_record}")
                return
        case "boms":
            bom_work = True
            celery_logger.info("About to start reading")
            df = read_this_file(uploaded_file_record, user, import_dictionaries.boms_converters_dict, celery_task_id)
            # start tasks
            if not df.empty:
                # Start task of Materials
                df['Finished Material'].replace('', np.nan, inplace=True)
                df.dropna(subset=['Finished Material'], inplace=True)
                df = df[df['Plant'] == '8800']
                # Adding new products or updating current ones
                unique_materials = df['Finished Material'].unique()
                material_counter = 0
                # get the marked for deletion product status
                mark_for_del = get_object_or_404(ProductStatus, marked_for_deletion = True)
                for material in unique_materials:
                    material_counter += 1
                    description = df.loc[df['Finished Material'] == material, 'Finished Material Desc'].values[0]
                    # created is True if the product has to be created
                    product, created = Product.objects.get_or_create(number=material)
                    if created:
                        product.name = description
                        product.is_new = True
                        if is_fert(material):
                            product.is_fert = True
                        product.save()
                        logmessage = f'Product imported by importing BOMs file: {product.id} {product.name}'
                        create_log_entry(user, product, ADDITION, logmessage)
                        post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, logmessage)
                    else:
                        if is_fert(material):
                            product.is_fert = True
                            product.save()
                        if product.name != description:
                            old_value = product.name
                            product.name = description
                            product.save()
                            logmessage = f'Product name changed by importing BOMs from {old_value} to {description}'
                            create_log_entry(user,product, CHANGE, logmessage)
                            post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, logmessage)
                    if product.name.startswith('+'):
                        product.product_status = mark_for_del
                        product.save()
                    if material_counter % 200 == 0:
                        celery_logger.info(f"materials: {material_counter}/{len(unique_materials)}")
                log_mess = "Materials completed"
                celery_logger.info(log_mess)
                post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, log_mess)
                # Adding new component or updating current ones
                # Count unique bom_component_sap_num values
                unique_component_count = df['Component Material'].nunique()
                log_mess = f"Unique component materials count: {unique_component_count}"
                celery_logger.info(log_mess)
                post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, log_mess)
                component_counter = 0
                for bom_component_sap_num in df['Component Material'].unique():
                    component_counter += 1
                    bom_comp_description = df.loc[df['Component Material'] == bom_component_sap_num, 'Component Material Desc'].values[0]
                    bom_comp_base_uom = df.loc[df['Component Material'] == bom_component_sap_num, 'Comp Base UoM'].values[0]
                    bom_component, created = BomComponent.objects.get_or_create(component_material=bom_component_sap_num)
                    if created:
                        # This component does not exixts in the BomComponent records
                        bom_component.component_material_description = bom_comp_description
                        bom_component.component_base_uom = bom_comp_base_uom
                        # Check if this component may be a fert
                        if is_fert(bom_component.component_material):
                            bom_component.is_fert = True
                        bom_component.save()
                        logmessage = f'BOM component imported by importing BOMs file: {bom_component.id} {bom_component.component_material} {bom_component.component_material_description}'
                        create_log_entry(user, bom_component, ADDITION, logmessage)
                        post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, logmessage)
                    else:
                        # This component already exixts in the BomComponent records
                        if bom_component.component_material_description != bom_comp_description:
                            old_value = bom_component.component_material_description
                            bom_component.component_material_description = bom_comp_description
                            bom_component.save()
                            logmessage = f'BOM component desc changed by importing BOMs from {old_value} to {bom_comp_description}'
                            create_log_entry(user,bom_component, CHANGE, logmessage)
                            post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, logmessage)
                    if component_counter % 200 == 0:
                        celery_logger.info(f"BOM Component: {component_counter}/{unique_component_count}")
                log_mess = "BOM Component review is completed"
                celery_logger.info(log_mess)
                post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, log_mess)

                # Working on BOM Headers
                unique_headers = df.drop_duplicates(subset=['Finished Material', 'Finished Material Desc', 'Alt BOM'])
                # only keeping those columns
                unique_headers = unique_headers.loc[:, ['Finished Material', 'Finished Material Desc', 'Alt BOM', 'Header Base Qty', 'Hdr Base Qty UoM']]
                finished_material_numbers_list = list(unique_headers['Finished Material'].unique())
                celery_logger.info(f"BOMHeaders - unique heders: {len(unique_headers)}")
                all_unique_headers = len(unique_headers)
                log_mess = f"len of unique_headers: {all_unique_headers}"
                celery_logger.info(log_mess)
                post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, log_mess)
                count_of_unique_headers = 0
                
                for index, header in unique_headers.iterrows():
                    count_of_unique_headers += 1
                    product_number = header['Finished Material']
                    alt_bom = header['Alt BOM']
                    header_base_quantity = header['Header Base Qty']
                    header_base_quantity_uom = header['Hdr Base Qty UoM']
                    product = get_object_or_404(Product, number=product_number)
                    if product:
                        bom_header, created = BomHeader.objects.get_or_create(
                            product = product,
                            alt_bom = alt_bom,
                            defaults={
                                'header_base_quantity': header_base_quantity,
                                'header_base_quantity_uom': header_base_quantity_uom
                            }
                        )
                        if created:
                            logmessage = f'BOM header created for {bom_header.product.number} {bom_header.product.name} alt_bom: {alt_bom}'
                            create_log_entry(user, bom_header, ADDITION, logmessage)
                            post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, logmessage)
                        else:
                            logmessage = f'BOM header changed for {bom_header.product.number} {bom_header.product.name} alt_bom: {alt_bom}'
                            create_log_entry(user, bom_header, CHANGE, logmessage)
                    if count_of_unique_headers % 200 == 0:
                        celery_logger.info(f"BOM headers: {count_of_unique_headers}/{all_unique_headers}")
                celery_logger.info("Finished inserting/editing BOM headers")
                
                # products = BomHeader.objects.values('product').distinct()
                filtered_bom_headers = BomHeader.objects.filter(product__number__in=finished_material_numbers_list)
                # Instead of looping through all BomHeader, we shoudl onbly loop on those in teh filtered_bom_headers
                products = filtered_bom_headers.values('product').distinct()
                celery_logger.info(f"Start checking on BOMHeaders and AltBOMs to try setting is_active; Products under review: {len(products)}")
                for product_data in products:
                    product_id = product_data['product']
                    product = Product.objects.get(id=product_id)
                    alt_bom_values = BomHeader.objects.filter(product=product).values_list('alt_bom', flat=True).distinct()
                    alt_bom_list = list(alt_bom_values)                    
                    if '1' in alt_bom_list:
                        bh = BomHeader.objects.filter(product=product, alt_bom='1').first()
                        bh.is_active = True
                        bh.save()
                        # print(f"Product: {product.name}, AltBOMs: {alt_bom_list} - set is_active to True")
                    elif len(alt_bom_list) == 1:
                        alt_bom_value = alt_bom_list[0]
                        bh = BomHeader.objects.filter(product=product, alt_bom=alt_bom_value).first()
                        bh.is_active=True
                        bh.save()
                    elif 'RM' in alt_bom_list:
                        bh = BomHeader.objects.filter(product=product, alt_bom='RM').first()
                        bh.is_active = True
                        bh.save()
                celery_logger.info("Finished checking on BOMHeaders and AltBOMs")
                
                
                
                # for _, header in unique_headers.iterrows():
                #     count_of_unique_headers += 1
                #     product_number = header['Finished Material']
                #     alt_bom = header['Alt BOM']
                #     header_base_quantity = header['Header Base Qty']
                #     header_base_quantity_uom = header['Hdr Base Qty UoM']
                #     product = get_object_or_404(Product, number = product_number)
                #     if product:
                #         header_base_quantity = float(header_base_quantity)
                #         header_base_quantity_uom = str(header_base_quantity_uom).strip()
                #         bom_header, created = BomHeader.objects.get_or_create(
                #             product=product,
                #             alt_bom=alt_bom,
                #             defaults={
                #                 'header_base_quantity': header_base_quantity,
                #                 'header_base_quantity_uom': header_base_quantity_uom
                #             }
                #         )
                #         if created:
                #             logmessage = f'BOM header created for {bom_header.product.number} {bom_header.product.name} alt_bom: {alt_bom}'
                #             create_log_entry(user, bom_header, ADDITION, logmessage)
                #             post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, logmessage)
                #         else:
                #             logmessage = f'BOM header changed for {bom_header.product.number} {bom_header.product.name} alt_bom: {alt_bom}'
                #             create_log_entry(user, bom_header, CHANGE, logmessage)
                #             # post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, logmessage)
                #     if count_of_unique_headers % 100 == 0:
                #         celery_logger.info(f"BOM headers: {count_of_unique_headers}/{all_unique_headers}")
                        
                        
                        
                log_mess = "Bom headers job completed"
                celery_logger.info(log_mess)
                post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, log_mess)
                # Finished working on BOM headers
                # Start working on BOMs
                # slice the file
                bom_chunk_size = 3000
                df_chunks = slice_dataframe(df, bom_chunk_size)
                log_mess = f"Total number of bom_chunks: {len(df_chunks)}"
                celery_logger.info(log_mess)
                post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, log_mess)
                chunk_counter = 0
                number_of_chunks = len(df_chunks)
                for df_chunk in df_chunks:
                    chunk_counter += 1
                    chunk_dict = df_chunk.to_dict(orient='records')
                    process_the_bom_slice_task.delay(chunk_dict, user.id, chunk_counter, number_of_chunks, uploaded_file_record.id, celery_task_id)
                uploaded_file_record.is_processed = True
                uploaded_file_record.processed_at = timezone.make_aware(datetime.now())

            else:
                print("error reading the file")
            pass
    # celery_logger.info(f"model: {model}")
    
    ####################################################################################
    # Start inserting
    ####################################################################################
    if not bom_work:
        model.objects.all().delete()
        post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"deleting rows from {model._meta.model_name}")
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
        post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, "All chuncks are processed")
        uploaded_file_record.is_processed = True
        uploaded_file_record.processed_at = timezone.make_aware(datetime.now())
        # Working on the stored procedures now
        if list_of_sp:
            post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, f"There are {len(list_of_sp)} stored procedures. {list_of_sp}")
            with connection.cursor() as curs:
                for index, sp in enumerate(list_of_sp):
                    with transaction.atomic():
                        sql_command = f"EXECUTE {sp}"
                        try:
                            curs.execute(sql_command)
                        except Exception as e:
                            message = f"Error during execution of {sp}. {e}" 
                            post_a_log_message(uploaded_file_record.id, user_id, celery_task_id, message, "error")
                            return
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


def post_a_log_message(id_of_UploadedFile, user_id, celery_task_id, message, level="info"):
    uploaded_file_record = get_object_or_404(UploadedFile, pk=id_of_UploadedFile)
    user = get_object_or_404(User, pk=user_id)
    UploadedFileLog.objects.create(
        uploaded_file = uploaded_file_record,
        user = user,
        file_path = uploaded_file_record.file_path,
        file_name = uploaded_file_record.file_name,
        celery_task_id = celery_task_id,
        log_text = message
    )
    # if level == "info":
    #     celery_logger.info(message)
    # else:
    #     celery_logger.error(message)


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
def fetch_euro_exchange_rates():

    # Get the latest year from the EuroExchangeRate model
    latest_year_subquery = EuroExchangeRate.objects.aggregate(latest_year=Max('year'))
    latest_year = latest_year_subquery['latest_year']

    # Get the latest month for the latest year
    if latest_year is not None:
        latest_month_subquery = EuroExchangeRate.objects.filter(year=latest_year).aggregate(latest_month=Max('month'))
        latest_month = latest_month_subquery['latest_month']
    else:
        latest_month = None

    celery_logger.info(f'latest_year {latest_year}')
    celery_logger.info(f'latest_month {latest_month}')


    if latest_year is None or latest_month is None:
        start_date = datetime(2000, 1, 1)  # If no data exists, start from a default early date
    else:
        start_date = datetime(latest_year, latest_month, 1)



    url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml'
    response = requests.get(url)
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        celery_logger.info(f"root:{root}")
        namespaces = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
                      '': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}

        celery_logger.info(f"namespaces: {namespaces}")

        valid_currency_codes = set(Currency.objects.values_list('alpha_3', flat=True))
        rates_data = {}
        for cube in root.findall('.//Cube[@time]', namespaces):
            date_str = cube.attrib['time']
            date = datetime.strptime(date_str, '%Y-%m-%d')

            # Skip dates before the start_date
            if date < start_date:
                continue

            year, month = date.year, date.month

            for rate in cube.findall('.//Cube[@currency]', namespaces):
                currency_code = rate.attrib['currency']
                if currency_code not in valid_currency_codes:
                    continue
                
                exchange_rate = Decimal(rate.attrib['rate']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                # Initialize nested dictionaries if not already present
                if year not in rates_data:
                    rates_data[year] = {}
                if month not in rates_data[year]:
                    rates_data[year][month] = {}
                if currency_code not in rates_data[year][month]:
                    rates_data[year][month][currency_code] = {'sum': 0, 'count': 0}

                print(f"year: {year} month: {month} currency: {currency_code}; exchange rate: {exchange_rate}")
                rates_data[year][month][currency_code]['sum'] += exchange_rate
                rates_data[year][month][currency_code]['count'] += 1

        for year in rates_data:
            for month in rates_data[year]:
                for currency_code in rates_data[year][month]:
                    total_sum = rates_data[year][month][currency_code]['sum']
                    count = rates_data[year][month][currency_code]['count']
                    average_rate = total_sum / count if count else 0

                    try:
                        currency = Currency.objects.get(alpha_3=currency_code)
                        EuroExchangeRate.objects.update_or_create(
                            currency=currency,
                            year=year,
                            month=month,
                            defaults={'rate': average_rate}
                        )
                        celery_logger.info(f"{year}-{month}-{currency_code}-avg: {average_rate}")
                    except Currency.DoesNotExist:
                        celery_logger.warning(f"Currency with code {currency_code} does not exist.")
                        continue
        celery_logger.info("EUR exchange rates update completed")
    else:
        celery_logger.info(f"Failed to fetch data: {response.status_code}")


def get_latest_exchange_rate(currency):
    
    latest_year = EuroExchangeRate.objects.filter(currency=currency).aggregate(latest_year=Max('year'))['latest_year']
    if latest_year:
        latest_month = EuroExchangeRate.objects.filter(currency=currency, year=latest_year).aggregate(latest_month=Max('month'))['latest_month']
        
        # Fetch the exchange rate for the latest year and month
        exchange_rate = EuroExchangeRate.objects.filter(
            currency=currency,
            year=latest_year,
            month=latest_month
        ).first()

        return exchange_rate.rate if exchange_rate else None
    return None


@shared_task
def process_the_bom_slice_task(chunk_dict, user_id, counter, all_chunks, id_of_uploaded_file, celery_task_id):
    stamp = f"{counter}/{all_chunks}"
    log_mess = f"task id {celery_task_id} - process_the_bom_slice_task started - {stamp}"
    celery_logger.warning(log_mess)
    post_a_log_message(id_of_uploaded_file, user_id, celery_task_id, log_mess)
    df = pd.DataFrame(chunk_dict)
    len_df = len(df)
    user = get_object_or_404(User, pk=user_id)
    # Getting the latest exchange rate
    czk_currency = get_object_or_404(Currency, alpha_3='CZK')
    latest_exchange_rate = get_latest_exchange_rate(czk_currency)
    celery_logger.info(f"latest czk exchange rate: {latest_exchange_rate}")

    # Start working on BOMs
    # Adding or updating Bom records
    slice_row = 0
    for _, row in df.iterrows():
        slice_row += 1
        product_number = row['Finished Material']
        alt_bom = row['Alt BOM']
        item_number = row['Item Number']
        component_material = row['Component Material']
        component_quantity = row['Comp Qty']
        component_uom_in_bom = row['Comp UoM in BOM']
        component_base_uom = row['Comp Base UoM']
        price_unit = row['Price Unit']
        standard_price_per_unit = Decimal(row['Std Pr Per Unit/Comp'])
        standard_price_per_unit_EUR = standard_price_per_unit / latest_exchange_rate

        product = get_object_or_404(Product, number=product_number)
        bom_header = get_object_or_404(BomHeader, product=product, alt_bom=alt_bom)
        bom_component = get_object_or_404(BomComponent, component_material=component_material)

        bom, created = Bom.objects.update_or_create(
            bom_header=bom_header,
            bom_component=bom_component,
            defaults={
                'item_number': item_number,
                'component_quantity': component_quantity,
                'component_uom_in_bom': component_uom_in_bom,
                'component_base_uom': component_base_uom,
                'price_unit': price_unit,
                'standard_price_per_unit': standard_price_per_unit,
                'standard_price_per_unit_EUR': standard_price_per_unit_EUR
            }
        )
        if slice_row % 250 == 00:
            celery_logger.warning(f"process {stamp}: {slice_row}/{len_df}")
        if created:
            logmessage = f'BOM record created for {bom_header.product.number} {bom_header.product.name} component: {bom_component.component_material}'
            create_log_entry(user, bom, ADDITION, logmessage)
            post_a_log_message(id_of_uploaded_file, user_id, celery_task_id, logmessage)
        else:
            logmessage = f'BOM record updated for {bom_header.product.number} {bom_header.product.name} component: {bom_component.component_material}'
            create_log_entry(user, bom, CHANGE, logmessage)
    # Finished working on Boms
    log_mess = f"task id {celery_task_id} - process_the_bom_slice_task finished - {stamp}"
    celery_logger.warning(log_mess)
    post_a_log_message(id_of_uploaded_file, user_id, celery_task_id, log_mess)


def slice_dataframe(dataframe, chunk_size):
    chunks = [dataframe.iloc[i:i + chunk_size] for i in range(0, dataframe.shape[0], chunk_size)]
    return chunks