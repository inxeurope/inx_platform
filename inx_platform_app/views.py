from collections import defaultdict
from django.db.models import Sum, OuterRef, Subquery, DecimalField, F, Value, Case, When, Count
from django.db.models.functions import Coalesce, Round
from django.db import connection
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponse, Http404, FileResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.admin.models import CHANGE
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import *
from .utils import *
from .forms import *
from .filters import *
from .tasks import file_processor, fetch_euro_exchange_rates
from PIL import Image
from . import dictionaries, import_dictionaries
from decimal import Decimal, ROUND_HALF_UP
from loguru import logger
import binascii
import pyodbc
import math
import pandas as pd
import numpy as np
import os
import io
import time
import shutil
import subprocess
from datetime import datetime
from time import perf_counter
import pprint
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
    
def index(request):
    return render(request, "app_pages/index.html", {})


def forecast(request, customer_id=None, brand_colorgroup_id=None):
    
    months = {
        '1': {'name': 'January', 'abbreviated_name': 'Jan', 'quarter': 'Q1', 'half': 'H1'},
        '2': {'name': 'February', 'abbreviated_name': 'Feb', 'quarter': 'Q1', 'half': 'H1'},
        '3': {'name': 'March', 'abbreviated_name': 'Mar', 'quarter': 'Q1', 'half': 'H1'},
        '4': {'name': 'April', 'abbreviated_name': 'Apr', 'quarter': 'Q2', 'half': 'H1'},
        '5': {'name': 'May', 'abbreviated_name': 'May', 'quarter': 'Q2', 'half': 'H1'},
        '6': {'name': 'June', 'abbreviated_name': 'Jun', 'quarter': 'Q2', 'half': 'H1'},
        '7': {'name': 'July', 'abbreviated_name': 'Jul', 'quarter': 'Q3', 'half': 'H2'},
        '8': {'name': 'August', 'abbreviated_name': 'Aug', 'quarter': 'Q3', 'half': 'H2'},
        '9': {'name': 'September', 'abbreviated_name': 'Sep', 'quarter': 'Q3', 'half': 'H2'},
        '10': {'name': 'October', 'abbreviated_name': 'Oct', 'quarter': 'Q4', 'half': 'H2'},
        '11': {'name': 'November', 'abbreviated_name': 'Nov', 'quarter': 'Q4', 'half': 'H2'},
        '12': {'name': 'December', 'abbreviated_name': 'Dec', 'quarter': 'Q4', 'half': 'H2'},
    }

    c_id = customer_id
    customer = Customer.objects.filter(id=c_id).first()

    current_year = datetime.today().year
    current_month = datetime.today().month
    previous_year = current_year - 1 
    forecast_year = datetime.now().year

    if request.htmx:
        print("This is an htmx request!")
        brand_id = request.GET.get('brand_id')
        budforline_id = request.GET.get('budforline_id')
        print(f"brand_id: {brand_id}, budforline_id: {budforline_id}")
        if brand_id and not budforline_id:
            print(f"brand_id: {brand_id}")
            budforline_colorgroups = BudForLine.objects.filter(customer_id=customer_id, brand_id=brand_id).select_related('color_group').values('id', 'color_group__id', 'color_group__name')
            # brand_selected = get_object_or_404(Brand, pk=brand_id)
            # print(f"Brand selected: {brand_selected.name}")
            return render(request, 'app_pages/forecast_color_groups_partial.html', {'budforline_colorgroups': budforline_colorgroups, 'customer': customer})
        elif budforline_id:
            print(f"You clicked a brand-colorgroup with id: {budforline_id}")
            forecast_data = BudgetForecastDetail.objects.filter(
                budforline_id = budforline_id,
                budforline__customer_id = customer_id,
                year = forecast_year,
                month__gt = current_month,
                scenario__is_forecast = True
            ).select_related(
                'budforline',
                'scenario'
            ).values(
                'id',
                'budforline__brand__name',
                'budforline__color_group__name',
                'year',
                'month',
                'volume',
                'price',
                'value'
            ). order_by('month')
            

            if forecast_data:
                selected_brand = forecast_data[0]['budforline__brand__name']
                color_group = forecast_data[0]['budforline__color_group__name']
                forecast_forms = []
                for entry in forecast_data:
                    form = ForecastForm(initial={
                        'id': entry['id'],
                        'budforline_id': budforline_id,
                        'month': entry['month'],
                        'volume': entry['volume'],
                        'price': entry['price'],
                        'value':entry['value']
                    })
                    forecast_forms.append(form)
            else:
                selected_brand = None
                color_group = None
                forecast_forms = None

            context = {
                'brand_name': selected_brand,
                'color_group_name': color_group,
                'budforline_id': budforline_id,
                'forecast_forms': forecast_forms
            }
            return render(request, "app_pages/forecast_data_partial.html", context)

    else:
        print("This is a REGULAR request")

        # Extract list_of_brands_per_customer
        list_of_brands_of_customer = BudForLine.get_customer_brands(customer_id)
        for c, b in list_of_brands_of_customer:
            logger.info(f"{c.name} {b.name}")
            
        # Get sales of previous year of specific customer
        # All brands and color group.
        # Calculation of total volume and value per customer-brand
        last_year_sales = BudgetForecastDetail_sales.objects.filter(
            budforline__customer_id = customer_id,
            year = previous_year
        ).select_related(
            'budforline',
            'scenario'
        ).values(
            'budforline__brand__name',
            'year',
            'month'
        ).annotate(
            total_volume=Sum('volume'),
            total_value=Sum('value')
        )
        logger.info("last_year_sals queryset was extracted")

        ytd_sales = BudgetForecastDetail_sales.objects.filter(
            budforline__customer_id = customer_id,
            year = current_year,
            month__lte = current_month
        ).select_related(
            'budforline',
            'scenario'
        ).values(
            'budforline__brand__name',
            'year',
            'month'
        ).annotate(
            total_volume=Sum('volume'),
            total_value=Sum('value')
        )
        logger.info("ytd_sales queryset was extracted")

        forecast = BudgetForecastDetail.objects.filter(
            budforline__customer_id = customer_id,
            year = forecast_year,
            month__gt = current_month,
            scenario__is_forecast = True
        ).select_related(
            'budforline',
            'scenario'
        ).values(
            'budforline__brand__name',
            'year',
            'month'
        ).annotate(
            total_volume=Sum('volume'),
            total_value=Sum('value')
        )
        logger.info("forecast was extracted")
        print('FORECAST', '-+'*40)
        for r in forecast:
            print(customer.name, r['budforline__brand__name'], r['year'], r['month'], r['total_volume'], r['total_value'])
        print('-+'*40)


        '''
        Example of the dictionary of dictionaries
        sales_data: {
        'POPFlex': {
                last_year: {
                    1: {'volume': 0, 'price': 0, 'value': 0},
                    2: {'volume': 10, 'price': 10, 'value': 100}
                    .
                    .
                    'brand_total': {'volume': 10, 'price': 10, 'value': 100}

                } ,
                ytd: {
                    1: {'volume': 0, 'price': 0, 'value': 0},
                    2: {'volume': 0, 'price': 0, 'value': 0}
                    .
                    .
                    'brand_total': {'volume': 10, 'price': 10, 'value': 100}
                }
            }
        }
        '''
        # Preparing the data container
        sales_data = {}

        logger.info("Start filling dictionary of dictionaries sales_data")
        logger.info(f"Getting all brands of customer {customer.name}")
        # Loop trhgouh list_of_brands_per_customer
        for the_customer, the_brand in list_of_brands_of_customer:
            brand_name = the_brand.name
            logger.info(f"Working on brand: {brand_name}")
            # If brand is not in the dictionary yet, add it and prepare empty buckets
            if brand_name not in sales_data:
                logger.info(f"Brand {brand_name} was not in the sales_data dict, adding with last_year and ytd empty dict")
                sales_data[brand_name] = {
                    'last_year': {},
                    'ytd': {}
                    }
                logger.info(f"Adding {brand_name} brand_total empty buckets")
                sales_data[brand_name]['last_year'] = {'brand_total': {'value': 0, 'volume': 0, 'price': 0}}
                sales_data[brand_name]['ytd'] = {'brand_total': {'value': 0, 'volume': 0, 'price': 0}}
            
            # Filter data using the budforline id, it's the triplet customer, brand, colorgroup
            # we are filtering and taking only the brand currently in consideration in the loop
            last_year_data = [entry for entry in last_year_sales if entry['budforline__brand__name'] == brand_name]
            ytd_data = [entry for entry in ytd_sales if entry['budforline__brand__name'] == brand_name]
            forecast_data = [entry for entry in forecast if entry['budforline__brand__name'] == brand_name]

            # working on last_year data
            for entry in last_year_data: 
                month = entry['month']
                volume = entry['total_volume']
                value = entry['total_value']
                price = round(value / volume, 2) if volume != 0 else 0
                sales_data[brand_name]['last_year'][month] = {
                    'volume': volume,
                    'price': price,
                    'value': value
                }
                # Calculation of brand totals for last_year
                sales_data[brand_name]['last_year']['brand_total']['volume'] += volume
                sales_data[brand_name]['last_year']['brand_total']['value'] += value
            if sales_data[brand_name]['last_year']['brand_total']['volume'] == 0:
                sales_data[brand_name]['last_year']['brand_total']['price'] = 0
            else:
                sales_data[brand_name]['last_year']['brand_total']['price'] = sales_data[brand_name]['last_year']['brand_total']['value']/sales_data[brand_name]['last_year']['brand_total']['volume']

            # working on ytd data
            for entry in ytd_data:
                month = entry['month']
                volume = entry['total_volume']
                value = entry['total_value']
                price = round(value / volume, 2) if volume != 0 else 0
                sales_data[brand_name]['ytd'][month] = {
                    'volume': volume,
                    'price': price,
                    'value': value
                }
                #Calculation of brand totals for ytd
                sales_data[brand_name]['ytd']['brand_total']['volume'] += volume
                sales_data[brand_name]['ytd']['brand_total']['value'] += value
            if sales_data[brand_name]['ytd']['brand_total']['volume'] == 0:
                sales_data[brand_name]['ytd']['brand_total']['price'] = 0
            else:
                sales_data[brand_name]['ytd']['brand_total']['price'] = sales_data[brand_name]['ytd']['brand_total']['value']/sales_data[brand_name]['ytd']['brand_total']['volume']

            # working on forecast data
            for entry in forecast_data:
                month = entry['month']
                volume = entry['total_volume']
                value = entry['total_value']
                price = round(value / volume, 2) if volume != 0 else 0
                print(f"FCST - {customer.name} - {brand_name} - year {forecast_year} month {month} vol {volume} - val {value}")
                # Months are in the future
                sales_data[brand_name]['ytd'][month] = {
                    'volume': volume,
                    'price': price,
                    'value': value
                }
                #Calculation of brand totals for ytd
                sales_data[brand_name]['ytd']['brand_total']['volume'] += volume
                sales_data[brand_name]['ytd']['brand_total']['value'] += value
            if sales_data[brand_name]['ytd']['brand_total']['volume'] == 0:
                sales_data[brand_name]['ytd']['brand_total']['price'] = 0
            else:
                sales_data[brand_name]['ytd']['brand_total']['price'] = sales_data[brand_name]['ytd']['brand_total']['value']/sales_data[brand_name]['ytd']['brand_total']['volume']

        pprint.pprint(sales_data)


        # Calculating column totals and grand totals
        totals = {
            'last_year': {},
            'ytd': {},
            'ly_grand_totals': {'volume':0, 'value': 0, 'price':0},
            'ytd_grand_totals': {'volume':0, 'value': 0, 'price':0}
            }
        for month_key in months.keys():
            # Making sure month is an integer
            month_key = int(month_key)
            # Calculating last year value and volume totals
            totals['last_year'][month_key] = {
                'volume': sum(sales_data[brand]['last_year'].get(month_key, {}).get('volume', 0) for brand in sales_data),
                'value': sum(sales_data[brand]['last_year'].get(month_key, {}).get('value', 0) for brand in sales_data),
            }
            # Calculating last_year price total of the month (columns)
            totals['last_year'][month_key]['price'] = totals['last_year'][month_key]['value']/totals['last_year'][month_key]['volume'] if totals['last_year'][month_key]['volume'] != 0 else 0
            
            # Calculating ytd value and volume totals
            totals['ytd'][month_key] = {
                'volume': sum(sales_data[brand]['ytd'].get(month_key, {}).get('volume', 0) for brand in sales_data),
                'value': sum(sales_data[brand]['ytd'].get(month_key, {}).get('value', 0) for brand in sales_data),
            }
            # Calculating ytd price totals of the month (columns)
            totals['ytd'][month_key]['price'] = totals['ytd'][month_key]['value']/totals['ytd'][month_key]['volume'] if totals['ytd'][month_key]['volume'] != 0 else 0
            
            # Taking care of the totals of those months that still have to come
            if month_key >= current_month:
                # We inserted forecast, we shold have data
                # totals['ytd'][month_key]['value'] = 0
                # totals['ytd'][month_key]['volume'] = 0
                # totals['ytd'][month_key]['price'] = 0
                pass

            totals['ly_grand_totals']['volume'] += totals['last_year'][month_key]['volume']
            totals['ly_grand_totals']['value'] += totals['last_year'][month_key]['value']
            totals['ytd_grand_totals']['volume'] += totals['ytd'][month_key]['volume']
            totals['ytd_grand_totals']['value'] += totals['ytd'][month_key]['value']
        totals['ly_grand_totals']['price'] = totals['ly_grand_totals']['value']/totals['ly_grand_totals']['volume'] if totals['ly_grand_totals']['volume'] != 0 else 0
        totals['ytd_grand_totals']['price'] = totals['ytd_grand_totals']['value']/totals['ytd_grand_totals']['volume'] if totals['ytd_grand_totals']['volume'] != 0 else 0

        # Removing brands with brand totals that are all zeros
        brands_to_remove = []
        for brand, data in sales_data.items():
            logger.info(f"Working on totals of {brand}")
            last_year_brand_total = data['last_year']['brand_total']
            ytd_brand_total = data['ytd']['brand_total']
            if last_year_brand_total['volume'] == 0 and last_year_brand_total['value'] == 0:
                del sales_data[brand]['last_year']
                logger.info(f"Removing: {brand}['last_year']")
            if ytd_brand_total['volume'] == 0 and ytd_brand_total['value'] == 0:
                del sales_data[brand]['ytd']
                logger.info(f"Removing: {brand}['ytd']")
            if not data.get('last_year') and not data.get('ytd'):
                brands_to_remove.append(brand)
                logger.info(f"Brand {brand} listed for further removal")
        # pprint.pprint(sales_data)
        print('*'*90)
        logger.info("Removing brands with no data")
        for b in brands_to_remove:
            logger.info(f"Brand: {b}")
            del sales_data[b]
        # pprint.pprint('*'*90)
        # pprint.pprint('SALES_DATA')
        # pprint.pprint('*'*90)
        # pprint.pprint(sales_data)
        # pprint.pprint('*'*90)
        # pprint.pprint("TOTALS")
        # pprint.pprint('*'*90)
        # pprint.pprint(totals)
        
    
    # print(type(list_of_brands_of_customer))
    context = {
        'customer': customer,
        'brands_of_customer': list_of_brands_of_customer,
        'sales_data': sales_data,
        'current_year': current_year,
        'current_month': current_month,
        'previous_year': previous_year,
        'months': months,
        'totals': totals
    }

    return render(request, "app_pages/forecast.html", context)


@login_required
def forecast_save(request):
    forecast_year = datetime.now().year
    forecast_month = datetime.now().month
    budget_year = forecast_year + 1
    forecast_scenario = get_object_or_404(Scenario, is_forecast=True)
    budget_scenario = get_object_or_404(Scenario, is_budget=True)
    if request.method == 'POST':
        csrf_token = request.META.get('CSRF_COOKIE', 'Not set')
        print(f"forecast save - csrf token: {csrf_token}")
        form_data = request.POST.copy()
        forecast_budget_id = form_data.get('id')
        form_type = form_data.get('form_type')
        budforline_id = form_data.get('budforline_id', None)

        if form_type == 'forecast':
            # scenario = forecast_scenario
            pass
        elif form_type == 'budget':
            # scenario = budget_scenario
            pass
        elif form_type == 'budget-flat':
            # scenario = budget_scenario
            flat_budget_form = FlatBudgetForm(form_data)
            if flat_budget_form.is_valid():
                print("flat budget form is valid")
                volume = flat_budget_form.cleaned_data['volume']
                price = round(float(flat_budget_form.cleaned_data['price']), 2)
                monthly_volume = volume / 12
                print(budforline_id)
                # Remove budget lines
                BudgetForecastDetail.objects.filter(
                    scenario__is_budget = True,
                    year = budget_year,
                    budforline_id = budforline_id
                ).delete()
                # Inserting new lines
                for m in months:
                    value = monthly_volume * price
                    BudgetForecastDetail.objects.create(
                        budforline_id=budforline_id,
                        scenario=budget_scenario,
                        year=budget_year,
                        month=m,
                        volume=monthly_volume,
                        price=price,
                        value=value
                    )
                messages.success(request, "Flat budget saved successfully")
                

        if forecast_budget_id:
            print(f"forecast_budget_id: {forecast_budget_id}")
            this_instance = get_object_or_404(BudgetForecastDetail, pk=forecast_budget_id)
            old_values = this_instance.__dict__.copy()
            if this_instance:
                if not budforline_id:
                    budforline_id = this_instance.budforline.id
                    form_data['budforline_id'] = budforline_id
            f = ForecastForm(form_data, instance=this_instance)
            old_volume = f['volume'].initial
            new_volume = f['volume'].data
            old_price = f['price'].initial
            new_price = f['price'].data
            print(f"volume: old-{old_volume} new-{new_volume}")
            print(f"price: old-{old_price} new-{new_price}")
            f.budforline_id = budforline_id
        else:
            f = ForecastForm(form_data)

        if f.is_valid():
            the_forecast_budget = f.save(commit=False)
            the_forecast_budget.value = the_forecast_budget.volume * the_forecast_budget.price
            the_forecast_budget.budforline_id = budforline_id
            the_forecast_budget.detail_date = datetime.now() 
            the_forecast_budget.save()
            change_message = []
            for field in f.changed_data:
                if field == 'budforline_id':
                    continue
                old_value = Decimal(old_values[field])
                if f.cleaned_data[field]:
                    new_value = Decimal(f.cleaned_data[field])
                else:
                    new_value = ''
                change_message.append(f'{field}: "{old_value}" -> "{new_value}"')
            # if old_volume != new_volume:
            #     change_message += f'volume changed from {old_volume} to {new_volume}'
            # if old_price != new_price:
            #     change_message += f' price changed from {old_price} to {new_price}'
            create_log_entry(request.user, this_instance, CHANGE, ', '.join(change_message))
            # We want to post a log in LogEntry to keep a trace of what was changed

            messages.success(request, f"{form_type.capitalize()} month {the_forecast_budget.month} volume: {the_forecast_budget.volume}, price: {the_forecast_budget.price}, value: {the_forecast_budget.value} - saved")
        elif form_type == 'budget-flat':
            print('ugo')
        else:
            print("form is not valid")
            print(f"form errors: {f.errors}")
            # print(f)
            return render(request, "app_pages/forecast_data_partial.html", {'form': f})

        # Retrieve all related BudgetForecastDetails instances
        forecast_instances = BudgetForecastDetail.objects.filter(
            budforline_id=budforline_id,
            year=forecast_year,
            month__gt=forecast_month,
            scenario_id=forecast_scenario)
        budget_instances = BudgetForecastDetail.objects.filter(
            budforline_id = budforline_id,
            scenario_id = budget_scenario,
            year = budget_year
        ).order_by('month')
        forecast_forms = [ForecastForm(instance=forecast) for forecast in forecast_instances]
        budget_forms = [ForecastForm(instance=budget) for budget in budget_instances]
        flat_budget_form = ForecastForm()
        context = {
            'form_type': form_type,
            'budforline_id': budforline_id,
            'forecast_forms': forecast_forms,
            'budget_forms': budget_forms,
            'flat_budget_form': flat_budget_form,
            'brand_name': form_data.get('brand_name'),
            'color_group_name': form_data.get('color_group_name')
            # 'customer': the_forecast_budget.budforline.customer
        }
        return render(request, "app_pages/forecast_2_fcst.html", context)

    return HttpResponse("Invalid data", status=400)


@login_required
def budget_flat_save(request):
    budget_year = datetime.now().year + 1
    budget_scenario = get_object_or_404(Scenario, is_budget=True)
    pprint.pprint(request.POST)
    if request.method == 'POST':
        csrf_token = request.META.get('CSRF_COOKIE', 'Not set')
        print(f"budget flat save - csrf token: {csrf_token}")
        form_data = request.POST.copy()
        budforline_id = form_data.get('budforline_id', None)
        # budforline_object = get_object_or_404(BudForLine, pk=budforline_id)
        # customer_id = budforline_object.customer.id
        # brand_id = budforline_object.brand.id
        # color_group_id = budforline_object.color_group.id

        print(f"the budforline_id: {budforline_id}")
        # Remove all budget lines with budforline_id
        records_to_delete = BudgetForecastDetail.objects.filter(budforline_id=budforline_id)
        count, _ = records_to_delete.delete()
        print(f"deleted {count} records")

        # Add lines to budget
        volume = 30000
        price = 24
        volume_per_month = volume / 12
        for m in months:
            BudgetForecastDetail.objects.create(
                budforline_id = budforline_id,
                detail_date = datetime.now().date,
                scenario=budget_scenario,
                year = budget_year,
                month = m,
                volume = volume_per_month,
                price = price,
                value = volume_per_month * price
                )
        pass
    pass


@login_required
def fetch_empty_forecast(request):
    return render(request, "app_pages/forecast_2_fcst_empty_partial.html", {})


@login_required
def forecast_2(request, customer_id=None):
    c_id = customer_id
    customer = Customer.objects.filter(id=c_id).first()

    if request.htmx:
        print("HTMX request")
    else:
        current_year = datetime.now().year
        forecast_year = current_year
        # budget_year = current_year + 1
        current_month = datetime.now().month

        print("Forecast view - standard request")
        list_of_brands_of_customer = BudForLine.get_customer_brands(customer_id)

        # Getting data of ytd and forecast
        ytd_sales = BudgetForecastDetail_sales.objects.filter(
            budforline__customer_id = customer_id,
            year = current_year,
            month__lte = current_month
        ).select_related(
            'budforline',
            'scenario'
        ).values(
            'budforline__brand__name',
            'year',
            'month'
        ).annotate(
            total_volume=Sum('volume'),
            total_value=Sum('value')
        ).order_by('month')
        logger.info("ytd_sales queryset was extracted")
        print('\n'* 2 )
        print("YTD")
        pprint.pprint(ytd_sales)

        forecast = BudgetForecastDetail.objects.filter(
            budforline__customer_id = customer_id,
            year = forecast_year,
            month__gt = current_month,
            scenario__is_forecast = True
        ).select_related(
            'budforline',
            'scenario'
        ).values(
            'budforline__brand__name',
            'year',
            'month'
        ).annotate(
            total_volume=Sum('volume'),
            total_value=Sum('value')
        )
        print('\n'* 2 )
        print("FORECAST")
        pprint.pprint(forecast)
        logger.info("forecast was extracted")
        
        '''
        Example of the dictionary of dictionaries
        sales_data: {
            'POPFlex': {
                    ytd: {
                        1: {'volume': 0, 'price': 0, 'value': 0},
                        2: {'volume': 0, 'price': 0, 'value': 0}
                        .
                        .
                        'brand_total': {'volume': 10, 'price': 10, 'value': 100}
                    }
                },
            'OEM (RD1272)': {
                    ytd: {
                        1: {'volume': 0, 'price': 0, 'value': 0},
                        2: {'volume': 0, 'price': 0, 'value': 0}
                        .
                        .
                        'brand_total': {'volume': 10, 'price': 10, 'value': 100}
                    }
                },

        }
        '''
        ytd_sales_data_dict = {}
        logger.info("Start filling dictionary of dictionaries YTD sales_data")
        logger.info(f"Getting all brands of customer {customer.name}")
        for the_customer, the_brand in list_of_brands_of_customer:
            brand_name = the_brand.name
            logger.info(f"Working on brand: {brand_name}")
            # If brand is not in the dictionary yet, add it and prepare empty buckets
            if brand_name not in ytd_sales_data_dict:
                # logger.info(f"Brand {brand_name} was not in the sales_data dict, adding with last_year and ytd empty dict")
                ytd_sales_data_dict[brand_name] = {
                    'ytd': {}
                    }
                logger.info(f"Adding {brand_name} brand_total empty buckets")
                ytd_sales_data_dict[brand_name]['ytd'] = {'brand_total': {'value': 0, 'volume': 0, 'price': 0}}
            # pprint.pprint("ytd_sales_data_dict")
            # pprint.pprint(ytd_sales_data_dict)
            # Filter data using the budforline id, it's the triplet customer, brand, colorgroup
            # we are filtering and taking only the brand currently in consideration in the loop
            ytd_data = [entry for entry in ytd_sales if entry['budforline__brand__name'] == brand_name]
            forecast_data = [entry for entry in forecast if entry['budforline__brand__name'] == brand_name]

            # working on ytd data
            for entry in ytd_data:
                month = entry['month']
                volume = entry['total_volume']
                value = entry['total_value']
                price = round(value / volume, 2) if volume != 0 else 0
                # logger.info(f"YTD - {customer.name} - {brand_name} - year {datetime.now().year + 1} month {month} vol {volume} - val {value}")
                ytd_sales_data_dict[brand_name]['ytd'][month] = {
                    'volume': volume,
                    'price': price,
                    'value': value
                }
                #Calculation of brand totals for ytd
                ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume'] += volume
                ytd_sales_data_dict[brand_name]['ytd']['brand_total']['value'] += value
            if ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume'] == 0:
                ytd_sales_data_dict[brand_name]['ytd']['brand_total']['price'] = 0
            else:
                ytd_sales_data_dict[brand_name]['ytd']['brand_total']['price'] = ytd_sales_data_dict[brand_name]['ytd']['brand_total']['value']/ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume']

            # working on forecast data
            for entry in forecast_data:
                month = entry['month']
                volume = entry['total_volume']
                value = entry['total_value']
                price = round(value / volume, 2) if volume != 0 else 0
                # logger.info(f"FCST - {customer.name} - {brand_name} - year {datetime.now().year + 1} month {month} vol {volume} - val {value}")
                # Months are in the future
                ytd_sales_data_dict[brand_name]['ytd'][month] = {
                    'volume': volume,
                    'price': price,
                    'value': value
                }
                #Calculation of brand totals for ytd
                ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume'] += volume
                ytd_sales_data_dict[brand_name]['ytd']['brand_total']['value'] += value
            if ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume'] == 0:
                ytd_sales_data_dict[brand_name]['ytd']['brand_total']['price'] = 0
            else:
                ytd_sales_data_dict[brand_name]['ytd']['brand_total']['price'] = ytd_sales_data_dict[brand_name]['ytd']['brand_total']['value']/ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume']
        
        # Calculating column totals and grand totals of YTD
        totals = {
            'ytd': {},
            'ytd_grand_totals': {'volume':0, 'value': 0, 'price':0}
            }
        for month_key in months.keys():
            # Making sure month is an integer
            month_key = int(month_key)

            # Calculating ytd value and volume totals
            totals['ytd'][month_key] = {
                'volume': sum(ytd_sales_data_dict[brand]['ytd'].get(month_key, {}).get('volume', 0) for brand in ytd_sales_data_dict),
                'value': sum(ytd_sales_data_dict[brand]['ytd'].get(month_key, {}).get('value', 0) for brand in ytd_sales_data_dict),
            }
            # Calculating ytd price totals of the month (columns)
            totals['ytd'][month_key]['price'] = totals['ytd'][month_key]['value']/totals['ytd'][month_key]['volume'] if totals['ytd'][month_key]['volume'] != 0 else 0
            
            # Taking care of the totals of those months that still have to come
            if month_key >= datetime.now().month:
                pass

            totals['ytd_grand_totals']['volume'] += totals['ytd'][month_key]['volume']
            totals['ytd_grand_totals']['value'] += totals['ytd'][month_key]['value']
        totals['ytd_grand_totals']['price'] = totals['ytd_grand_totals']['value']/totals['ytd_grand_totals']['volume'] if totals['ytd_grand_totals']['volume'] != 0 else 0
        
        # Removing brands with brand totals that are all zeros
        brands_to_remove = []
        for brand, data in ytd_sales_data_dict.items():
            logger.info(f"Working on totals of {brand}")
            ytd_brand_total = data['ytd']['brand_total']
            if ytd_brand_total['volume'] == 0 and ytd_brand_total['value'] == 0:
                del ytd_sales_data_dict[brand]['ytd']
                logger.info(f"Removing: {brand}['ytd']")
            if not data.get('ytd'):
                brands_to_remove.append(brand)
                logger.info(f"Brand {brand} listed for further removal")
        logger.info("Removing brands with no data")
        for b in brands_to_remove:
            logger.info(f"Brand to delete: {b}")
            del ytd_sales_data_dict[b]

        pprint.pprint(ytd_sales_data_dict)

    context = {
        'customer': customer,
        'brands_of_customer': list_of_brands_of_customer,
        'previous_year': datetime.now().year - 1,
        'current_month': current_month,
        'months': months,
        'sales_data': ytd_sales_data_dict,
        'totals': totals
    }

    return render(request, "app_pages/forecast_2.html", context)


@login_required
def fetch_ytd_sales(request, customer_id=None):
    customer = Customer.objects.filter(id=customer_id).first()
    current_year = datetime.now().year
    forecast_year = current_year
    current_month = datetime.now().month
    list_of_brands_of_customer = BudForLine.get_customer_brands(customer.id)
    logger.info(f"Getting all brands of customer {customer.name}")
    ytd_sales = BudgetForecastDetail_sales.objects.filter(
        budforline__customer_id = customer_id,
        year = current_year,
        month__lte = current_month
    ).select_related(
        'budforline',
        'scenario'
    ).values(
        'budforline__brand__name',
        'year',
        'month'
    ).annotate(
        total_volume=Sum('volume'),
        total_value=Sum('value')
    ).order_by('month')
    forecast = BudgetForecastDetail.objects.filter(
            budforline__customer_id = customer_id,
            year = forecast_year,
            month__gt = current_month,
            scenario__is_forecast = True
        ).select_related(
            'budforline',
            'scenario'
        ).values(
            'budforline__brand__name',
            'year',
            'month'
        ).annotate(
            total_volume=Sum('volume'),
            total_value=Sum('value')
        )
    logger.info("Start filling dictionary of dictionaries YTD sales data and forecast data")

    ytd_sales_data_dict = {}
    for the_customer, the_brand in list_of_brands_of_customer:
        brand_name = the_brand.name
        logger.info(f"Working on brand: {brand_name}")
        # If brand is not in the dictionary yet, add it and prepare empty buckets
        if brand_name not in ytd_sales_data_dict:
            # logger.info(f"Brand {brand_name} was not in the sales_data dict, adding with last_year and ytd empty dict")
            ytd_sales_data_dict[brand_name] = {
                'ytd': {}
                }
            logger.info(f"Adding {brand_name} brand_total empty buckets")
            ytd_sales_data_dict[brand_name]['ytd'] = {'brand_total': {'value': 0, 'volume': 0, 'price': 0}}
        # Filter data using the budforline id, it's the triplet customer, brand, colorgroup
        # we are filtering and taking only the brand currently in consideration in the loop
        ytd_data = [entry for entry in ytd_sales if entry['budforline__brand__name'] == brand_name]
        forecast_data = [entry for entry in forecast if entry['budforline__brand__name'] == brand_name]

        # working on ytd data
        for entry in ytd_data:
            month = entry['month']
            volume = entry['total_volume']
            value = entry['total_value']
            price = round(value / volume, 2) if volume != 0 else 0
            # logger.info(f"YTD - {customer.name} - {brand_name} - year {datetime.now().year + 1} month {month} vol {volume} - val {value}")
            ytd_sales_data_dict[brand_name]['ytd'][month] = {
                'volume': volume,
                'price': price,
                'value': value
            }
            #Calculation of brand totals for ytd
            ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume'] += volume
            ytd_sales_data_dict[brand_name]['ytd']['brand_total']['value'] += value
        if ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume'] == 0:
            ytd_sales_data_dict[brand_name]['ytd']['brand_total']['price'] = 0
        else:
            ytd_sales_data_dict[brand_name]['ytd']['brand_total']['price'] = ytd_sales_data_dict[brand_name]['ytd']['brand_total']['value']/ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume']

        # working on forecast data
        for entry in forecast_data:
            month = entry['month']
            volume = entry['total_volume']
            value = entry['total_value']
            price = round(value / volume, 2) if volume != 0 else 0
            # logger.info(f"FCST - {customer.name} - {brand_name} - year {datetime.now().year + 1} month {month} vol {volume} - val {value}")
            # Months are in the future
            ytd_sales_data_dict[brand_name]['ytd'][month] = {
                'volume': volume,
                'price': price,
                'value': value
            }
            #Calculation of brand totals for ytd
            ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume'] += volume
            ytd_sales_data_dict[brand_name]['ytd']['brand_total']['value'] += value
        if ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume'] == 0:
            ytd_sales_data_dict[brand_name]['ytd']['brand_total']['price'] = 0
        else:
            ytd_sales_data_dict[brand_name]['ytd']['brand_total']['price'] = ytd_sales_data_dict[brand_name]['ytd']['brand_total']['value']/ytd_sales_data_dict[brand_name]['ytd']['brand_total']['volume']
    
    # Calculating column totals and grand totals of YTD
        totals = {
            'ytd': {},
            'ytd_grand_totals': {'volume':0, 'value': 0, 'price':0}
            }
        for month_key in months.keys():
            # Making sure month is an integer
            month_key = int(month_key)

            # Calculating ytd value and volume totals
            totals['ytd'][month_key] = {
                'volume': sum(ytd_sales_data_dict[brand]['ytd'].get(month_key, {}).get('volume', 0) for brand in ytd_sales_data_dict),
                'value': sum(ytd_sales_data_dict[brand]['ytd'].get(month_key, {}).get('value', 0) for brand in ytd_sales_data_dict),
            }
            # Calculating ytd price totals of the month (columns)
            totals['ytd'][month_key]['price'] = totals['ytd'][month_key]['value']/totals['ytd'][month_key]['volume'] if totals['ytd'][month_key]['volume'] != 0 else 0
            
            # Taking care of the totals of those months that still have to come
            if month_key >= datetime.now().month:
                pass

            totals['ytd_grand_totals']['volume'] += totals['ytd'][month_key]['volume']
            totals['ytd_grand_totals']['value'] += totals['ytd'][month_key]['value']
        totals['ytd_grand_totals']['price'] = totals['ytd_grand_totals']['value']/totals['ytd_grand_totals']['volume'] if totals['ytd_grand_totals']['volume'] != 0 else 0
        
        # Removing brands with brand totals that are all zeros
        brands_to_remove = []
        for brand, data in ytd_sales_data_dict.items():
            logger.info(f"Working on totals of {brand}")
            ytd_brand_total = data['ytd']['brand_total']
            if ytd_brand_total['volume'] == 0 and ytd_brand_total['value'] == 0:
                del ytd_sales_data_dict[brand]['ytd']
                logger.info(f"Removing: {brand}['ytd']")
            if not data.get('ytd'):
                brands_to_remove.append(brand)
                logger.info(f"Brand {brand} listed for further removal")
        logger.info("Removing brands with no data")
        for b in brands_to_remove:
            logger.info(f"Brand to delete: {b}")
            del ytd_sales_data_dict[b]
    print("YTD")
    pprint.pprint(ytd_sales_data_dict)
    context = {
        'customer': customer,
        'brands_of_customer': list_of_brands_of_customer,
        'current_month': current_month,
        'months': months,
        'sales_data': ytd_sales_data_dict,
        'totals': totals
    }
    return render(request, "app_pages/forecast_2_ytd_data_partial.html", context)


@login_required
def fetch_bdg_sales(request, customer_id=None):
    print("fetch_bdg_sales started ...")
    customer = Customer.objects.filter(id=customer_id).first()
    current_year = datetime.now().year
    budget_year = current_year + 1
    list_of_brands_of_customer = BudForLine.get_customer_brands(customer.id)
    logger.info(f"Getting all brands of customer {customer.name}")
    bdg_sales = BudgetForecastDetail.objects.filter(
        budforline__customer_id = customer_id,
        year = budget_year,
        scenario__is_budget = True
    ).select_related(
        'budforline',
        'scenario'
    ).values(
        'budforline__brand__name',
        'year',
        'month'
    ).annotate(
        total_volume=Sum('volume'),
        total_value=Sum('value')
    ).order_by('month')
    # pprint.pprint("-----BDG sales")
    # pprint.pprint(bdg_sales)
    logger.info("Start filling dictionary of dictionaries BDG sales data")
    bdg_sales_data_dict = {}
    for the_customer, the_brand in list_of_brands_of_customer:
        brand_name = the_brand.name
        logger.info(f"Working on brand: {brand_name}")
        # If brand is not in the dictionary yet, add it and prepare empty buckets
        if brand_name not in bdg_sales_data_dict:
            logger.info(f"Brand {brand_name} was not in the bdg_sales_data dict,adding bdg empty dict")
            bdg_sales_data_dict[brand_name] = {
                'bdg': {}
                }
            logger.info(f"Adding {brand_name} brand_total empty buckets")
            bdg_sales_data_dict[brand_name]['bdg'] = {'brand_total': {'value': 0, 'volume': 0, 'price': 0}}
        # Filter data using the budforline id, it's the triplet customer, brand, colorgroup
        # we are filtering and taking only the brand currently in consideration in the loop
        bdg_data = [entry for entry in bdg_sales if entry['budforline__brand__name'] == brand_name]
        # working on bdg data
        for entry in bdg_data:
            month = entry['month']
            volume = entry['total_volume']
            value = entry['total_value']
            price = round(value / volume, 2) if volume != 0 else 0
            logger.info(f"BDG - {customer.name} - {brand_name} - year {datetime.now().year + 1} month {month} vol {volume} - val {value}")
            bdg_sales_data_dict[brand_name]['bdg'][month] = {
                'volume': volume,
                'price': price,
                'value': value
            }
            #Calculation of brand totals for bdg
            bdg_sales_data_dict[brand_name]['bdg']['brand_total']['volume'] += volume
            bdg_sales_data_dict[brand_name]['bdg']['brand_total']['value'] += value
        if bdg_sales_data_dict[brand_name]['bdg']['brand_total']['volume'] == 0:
            bdg_sales_data_dict[brand_name]['bdg']['brand_total']['price'] = 0
        else:
            bdg_sales_data_dict[brand_name]['bdg']['brand_total']['price'] = bdg_sales_data_dict[brand_name]['bdg']['brand_total']['value']/bdg_sales_data_dict[brand_name]['bdg']['brand_total']['volume']

        
    # Calculating column totals and grand totals of BDG
        totals = {
            'bdg': {},
            'bdg_grand_totals': {'volume':0, 'value': 0, 'price':0}
            }
        for month_key in months.keys():
            # Making sure month is an integer
            month_key = int(month_key)

            # Calculating ytd value and volume totals
            totals['bdg'][month_key] = {
                'volume': sum(bdg_sales_data_dict[brand]['bdg'].get(month_key, {}).get('volume', 0) for brand in bdg_sales_data_dict),
                'value': sum(bdg_sales_data_dict[brand]['bdg'].get(month_key, {}).get('value', 0) for brand in bdg_sales_data_dict),
            }
            # Calculating ytd price totals of the month (columns)
            totals['bdg'][month_key]['price'] = totals['bdg'][month_key]['value']/totals['bdg'][month_key]['volume'] if totals['bdg'][month_key]['volume'] != 0 else 0
            
            # Taking care of the totals of those months that still have to come
            if month_key >= datetime.now().month:
                pass

            totals['bdg_grand_totals']['volume'] += totals['bdg'][month_key]['volume']
            totals['bdg_grand_totals']['value'] += totals['bdg'][month_key]['value']
        totals['bdg_grand_totals']['price'] = totals['bdg_grand_totals']['value']/totals['bdg_grand_totals']['volume'] if totals['bdg_grand_totals']['volume'] != 0 else 0
        
        # Removing brands with brand totals that are all zeros
        brands_to_remove = []
        for brand, data in bdg_sales_data_dict.items():
            logger.info(f"Working on totals of {brand}")
            bdg_brand_total = data['bdg']['brand_total']
            if bdg_brand_total['volume'] == 0 and bdg_brand_total['value'] == 0:
                del bdg_sales_data_dict[brand]['bdg']
                logger.info(f"Removing: {brand}['bdg']")
            if not data.get('bdg'):
                brands_to_remove.append(brand)
                logger.info(f"Brand {brand} listed for further removal")
        logger.info("Removing brands with no data")
        for b in brands_to_remove:
            logger.info(f"Brand to delete: {b}")
            del bdg_sales_data_dict[b]
    gt_volume = totals['bdg_grand_totals']['volume']
    gt_value = totals['bdg_grand_totals']['value']
    gt_price = totals['bdg_grand_totals']['price']

    context = {
        'customer': customer,
        'brands_of_customer': list_of_brands_of_customer,
        'months': months,
        'budget_data': bdg_sales_data_dict,
        'budget_totals': totals,
        'gt_volume': gt_volume,
        'gt_value': gt_value,
        'gt_price': gt_price
    }
    return render(request, "app_pages/forecast_2_bdg_partial.html", context)


@login_required
def fetch_previous_year_sales(request, customer_id):
    c = get_object_or_404(Customer, pk=customer_id)
    p_year = datetime.now().year - 1

    # Extract list_of_brands_per_customer
    list_of_brands_of_customer = BudForLine.get_customer_brands(customer_id)
        
    # Get sales of previous year of specific customer
    # All brands and color group.
    # Calculation of total volume and value per customer-brand
    last_year_sales = BudgetForecastDetail_sales.objects.filter(
        budforline__customer_id = customer_id,
        year = p_year
    ).select_related(
        'budforline',
        'scenario'
    ).values(
        'budforline__brand__name',
        'year',
        'month'
    ).annotate(
        total_volume=Sum('volume'),
        total_value=Sum('value')
    ).order_by('month')
    logger.info("last_year_sals queryset was extracted")

    last_year_sales_data_dict = {}
    logger.info("Start filling dictionary of dictionaries sales_data")
    logger.info(f"Getting all brands of customer {c.name}")
    for the_customer, the_brand in list_of_brands_of_customer:
        brand_name = the_brand.name
        logger.info(f"Working on brand: {brand_name}")
        # If brand is not in the dictionary yet, add it and prepare empty buckets
        if brand_name not in last_year_sales_data_dict:
            logger.info(f"Brand {brand_name} was not in the sales_data dict, adding with last_year and ytd empty dict")
            last_year_sales_data_dict[brand_name] = {
                'last_year': {}
                }
            logger.info(f"Adding {brand_name} brand_total empty buckets")
            last_year_sales_data_dict[brand_name]['last_year'] = {'brand_total': {'value': 0, 'volume': 0, 'price': 0}}
            
        last_year_data = [entry for entry in last_year_sales if entry['budforline__brand__name'] == brand_name]
        for entry in last_year_data: 
            month = entry['month']
            volume = entry['total_volume']
            value = entry['total_value']
            price = round(value / volume, 2) if volume != 0 else 0
            last_year_sales_data_dict[brand_name]['last_year'][month] = {
                'volume': volume,
                'price': price,
                'value': value
            }
            # Calculation of brand totals for last_year
            last_year_sales_data_dict[brand_name]['last_year']['brand_total']['volume'] += volume
            last_year_sales_data_dict[brand_name]['last_year']['brand_total']['value'] += value
        if last_year_sales_data_dict[brand_name]['last_year']['brand_total']['volume'] == 0:
            last_year_sales_data_dict[brand_name]['last_year']['brand_total']['price'] = 0
        else:
            last_year_sales_data_dict[brand_name]['last_year']['brand_total']['price'] = last_year_sales_data_dict[brand_name]['last_year']['brand_total']['value']/last_year_sales_data_dict[brand_name]['last_year']['brand_total']['volume']
    # Calculating column totals and grand totals
    totals = {
        'last_year': {},
        'ly_grand_totals': {'volume':0, 'value': 0, 'price':0}
        }
    for month_key in months.keys():
        # Making sure month is an integer
        month_key = int(month_key)
        # Calculating last year value and volume totals
        totals['last_year'][month_key] = {
            'volume': sum(last_year_sales_data_dict[brand]['last_year'].get(month_key, {}).get('volume', 0) for brand in last_year_sales_data_dict),
            'value': sum(last_year_sales_data_dict[brand]['last_year'].get(month_key, {}).get('value', 0) for brand in last_year_sales_data_dict),
        }
        # Calculating last_year price total of the month (columns)
        totals['last_year'][month_key]['price'] = totals['last_year'][month_key]['value']/totals['last_year'][month_key]['volume'] if totals['last_year'][month_key]['volume'] != 0 else 0


        totals['ly_grand_totals']['volume'] += totals['last_year'][month_key]['volume']
        totals['ly_grand_totals']['value'] += totals['last_year'][month_key]['value']
    totals['ly_grand_totals']['price'] = totals['ly_grand_totals']['value']/totals['ly_grand_totals']['volume'] if totals['ly_grand_totals']['volume'] != 0 else 0

    # Removing brands with brand totals that are all zeros
    brands_to_remove = []
    for brand, data in last_year_sales_data_dict.items():
        logger.info(f"Working on totals of {brand}")
        last_year_brand_total = data['last_year']['brand_total']
        if last_year_brand_total['volume'] == 0 and last_year_brand_total['value'] == 0:
            del last_year_sales_data_dict[brand]['last_year']
            logger.info(f"Removing: {brand}['last_year']")
        if not data.get('last_year'):
            brands_to_remove.append(brand)
            logger.info(f"Brand {brand} listed for further removal")
    logger.info("Removing brands with no data")
    for b in brands_to_remove:
        logger.info(f"Brand to delete: {b}")
        del last_year_sales_data_dict[b]

    pprint.pprint(last_year_sales_data_dict)

    context = {
        'months': months,
        'customer': c,
        'previous_year': p_year,
        'sales_data': last_year_sales_data_dict,
        'totals': totals
    }
    return render(request, "app_pages/forecast_2_py_data_partial.html", context)


@login_required
def fetch_no_previous_year_sales(request, customer_id):
    c = get_object_or_404(Customer, pk=customer_id)
    p_year = datetime.now().year - 1
    context = {
        'customer': c,
        'previous_year': p_year
    }
    return render(request, "app_pages/forecast_2_py_no_data_partial.html", context)


@login_required
def fetch_cg(request, customer_id, brand_id):
    budforlines = BudForLine.objects.filter(
        customer_id = customer_id,
        brand_id = brand_id
    )
    brand_name = budforlines.first().brand.name
    print(brand_name)
    context = {
        'customer_id': customer_id,
        'brand_id': brand_id,
        'budforlines': budforlines,
        'brand_name': brand_name
    }
    return render(request, "app_pages/forecast_2_cg_fcst_partial.html", context)


@login_required
def fetch_forecast(request, budforline_id):
    logger.info("fetch_forecast view")
    if budforline_id is None:
        budforline_id = request.GET.get('budforline_id')
        logger.info(f"budforline_id {budforline_id} comes from GET")
    else:
        logger.info(f"budforline_id {budforline_id} comes as an argument")
    forecast_year = datetime.now().year
    budget_year = forecast_year + 1
    current_month = datetime.now().month
    logger.info(f"forecast_year: {forecast_year}")
    logger.info(f"budget_year: {budget_year}")
    logger.info(f"current_month: {current_month}")

    budforline_object = get_object_or_404(BudForLine, id=budforline_id)
    if budforline_object:
        brand_name = budforline_object.brand.name
        color_group_name = budforline_object.color_group.name
        logger.info(f"brand_name: {brand_name}")
        logger.info(f"color_group_name: {color_group_name}")

    forecast_lines = BudgetForecastDetail.objects.filter(
        budforline_id = budforline_id,
        scenario__is_forecast = True,
        year = forecast_year,
        month__gt = current_month
    ).order_by('month')
    logger.info(f"There are {len(forecast_lines)} records in forecast with the budforline_id {budforline_id}")
    scenario_forecast = get_object_or_404(Scenario, is_forecast=True)
    logger.info(f"scenario of forecast {scenario_forecast} with id: {scenario_forecast.id}")
    logger.info("forecast was extracted")
    
    budget_lines = BudgetForecastDetail.objects.filter(
        budforline_id = budforline_id,
        scenario__is_budget = True,
        year = budget_year
        # month__gt = current_month
    ).order_by('month')
    logger.info(f"There are {len(budget_lines)} records in budget with the budforline_id {budforline_id}")
    scenario_budget = get_object_or_404(Scenario, is_budget=True)
    logger.info(f"scenario of budget {scenario_budget} with id: {scenario_budget.id}")
    logger.info("budeget was extracted")

    missing_forecast_months = set()
    existing_forecast_months = set(line.month for line in forecast_lines)
    missing_forecast_months = set(range(current_month + 1, 13)) - existing_forecast_months
    logger.info(f"existing forecast months: {existing_forecast_months}")
    logger.info(f"missing forecast months: {missing_forecast_months}")

    # if forecast_lines.count() < 12:
    #     logger.info(f"Forecast months are less than 12 - filling")
    #     existing_forecast_months = set(forecast_lines.values_list('month', flat=True))
    #     logger.info(f"existing forecast months: {existing_forecast_months}")
    #     missing_forecast_months = set(range(1,13)) - existing_forecast_months
    #     logger.info("missing forecast months:", missing_forecast_months)

    forecast_lines = list(forecast_lines)
    if missing_forecast_months:
        for month in missing_forecast_months:
            new_line = BudgetForecastDetail.objects.create(
                budforline_id=budforline_id,
                scenario_id=scenario_forecast.id,
                year=forecast_year,
                month=month,
                volume=0,
                price=0,
                value=0
            )
            forecast_lines.append(new_line)
    forecast_lines.sort(key=lambda x: x.month)


    missing_budget_months = set()
    if budget_lines.count() < 12:
        logger.info("Budget months are less than 12")
        existing_budget_months = set(budget_lines.values_list('month', flat=True))
        logger.info(f"existing forecast months: {existing_budget_months}")
        missing_budget_months = set(range(1, 13)) - existing_budget_months
        logger.info("missing budget months:", missing_budget_months)

    budget_lines = list(budget_lines)
    if missing_budget_months:
        for month in missing_budget_months:
            new_line = BudgetForecastDetail.objects.create(
                budforline_id=budforline_id,
                scenario_id=scenario_budget.id,
                year=budget_year,
                month=month,
                volume=0,
                price=0,
                value=0
            )
            budget_lines.append(new_line)
    budget_lines.sort(key=lambda x: x.month)
    
    forecast_forms = []
    for line in forecast_lines:
        form = ForecastForm(initial={
            'id': line.id,
            'budforline_id': budforline_id,
            'month': line.month,
            'volume': line.volume,
            'price': line.price,
            'value':line.value
        })
        forecast_forms.append(form)
    
    budget_forms = []
    for line in budget_lines:
        form = ForecastForm(initial={
            'id': line.id,
            'budforline_id': budforline_id,
            'month': line.month,
            'volume': line.volume,
            'price': line.price,
            'value':line.value
        })
        budget_forms.append(form)

    flat_budget_form = FlatBudgetForm()

    context = {
        'budforline_id': budforline_id,
        'forecast_lines': forecast_lines,
        'forecast_forms': forecast_forms,
        'budget_forms': budget_forms,
        'flat_budget_form': flat_budget_form,
        'brand_name': brand_name,
        'color_group_name': color_group_name,
        'budget_year': budget_year
    }
    return render(request, "app_pages/forecast_2_fcst.html", context)


@login_required
def loading(request):
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

        are_all_empty = all(file is None for _, file in files_list)
        if are_all_empty:
            return render(request, "app_pages/index.html")

        for file_field, original_file in files_list:
            if original_file is not None:
                original_file_name = original_file.name.lower()
                prefix = file_field.split('_')[0]
                original_file_name = prefix +"_" + user_name + "_" + timestamp + "_" + original_file_name.replace(" ", "_")
                logger.info(f"loading file: {original_file_name}")
                upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")

                match prefix:
                    case 'ke30':
                        file_color = 'blue'
                    case 'ke24':
                        file_color = 'orange'
                    case 'zaq':
                        file_color = 'red'
                    case 'oo':
                        file_color = 'purple'
                    case 'oi':
                        file_color = 'cyan'
                    case 'arr':
                        file_color = 'indigo'
                    case 'pr':
                        file_color = 'azure'
                    case 'boms':
                        file_color = 'yellow'
                    case _:
                        file_color = 'muted'

                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                with open(os.path.join(upload_dir, original_file_name), 'wb+') as destination:
                    # for chunk in ke30_file.chunks():
                    for chunk in original_file.chunks():
                        destination.write(chunk)
                    # here it's done, update the database
                    uploaded_file = UploadedFile(owner=request.user, file_type=prefix, file_path=upload_dir, file_name=original_file_name, file_color=file_color, process_status='NEW')
                    uploaded_file.save()
        return redirect('files-to-import')
    else:
        return render(request, "app_pages/loading_data.html", {})


@login_required
def import_data(request):
    import_from_SQL(dictionaries.tables_list)
    return render(request, "index-inx.html")


def import_single(request):
    context = {'options': dictionaries.tables_list}
    if request.method == 'POST':
        csrf_token = request.META.get('CSRF_COOKIE', 'Not set')
        print(f"import_single - csrf token: {csrf_token}")
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
    

def import_single_table(request):
    context = {'options': dictionaries.tables_list}
    if request.method == 'POST':
        csrf_token = request.META.get('CSRF_COOKIE', 'Not set')
        print(f"import single table - csrf token: {csrf_token}")
        submit_action = request.POST.get('submit_type')
        table_name = request.POST.get('table_name')
        filtered_tuple = [(t1, t2, t3, t4) for t1, t2, t3, t4 in dictionaries.tables_list if t1 == table_name]
        if submit_action == 'Import':
            import_from_SQL(filtered_tuple)
            messages.success(request, f"Import done on {table_name}")
        if submit_action == 'Clean':
            clean_the_table(filtered_tuple)
            messages.success(request, f"Clean done on {filtered_tuple[0][2]}")
        return render(request, "app_pages/import_single_table.html", context)
    else:
        return render(request, "app_pages/import_single_table.html", context)


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
        if table_name == 'BudgetForecastDetails':
            table_name = '_BudForDetails'
        # Query to get all records of the table
        if table_name == '_BudForDetails':
            query = f"SELECT * FROM {table_name} WHERE ScenarioID <> 6"
        else:
            query = f"SELECT * FROM {table_name}"
        msg = "starting to get rows ..."
        print(msg, end="")
        cursor.execute(query)
        records = cursor.fetchall()
        print(f"reading {query} - completed")
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
        df_length = len(df)
        print("Dataframe creation completed")
        
        # Manage the duplication of that user
        if table_name == 'Users': 
            for index, row in df.iterrows():
                if row['email'] == 'marco.zanella@inxeurope.com':
                    df.at[index, 'email'] = 'marco.zanella.sql@inxeurope.com'
                
                if row['email'] == 'stefano.rogora@inxeurope.com':
                    df.at[index, 'email'] = 'stefano.rogora.sql@inxeurope.com'

        # Manage the import of Customer number that comes as 12345.0
        if table_name == 'Customers':
            df['CustomerNumber'] = df['CustomerNumber'].astype(int).astype(str)

        # Trim unnecessary columns
        columns_to_keep = [column for column in df.columns if column in mapping]
        df = df[columns_to_keep]

        # creating a copy of the index column, if there is one
        if not field_name == None:
            df['sqlapp_id'] = df[field_name]
            df.drop(columns=[field_name], inplace=True)
            print("Copy of index column created")
        
        # When the tables have no index, the table will be truncated
        if field_name == None:
            model_class.objects.all().delete()
            print(f"All records from {model_class.__name__} have been deleted")

        # Changing column names
        for sql_column, django_field in mapping.items():
            # Rename the column using the mapping
            if sql_column in df.columns:
                df.rename(columns={sql_column: django_field}, inplace=True)
        print("Applied django column names")

        # Remove np.nan
        df = df.replace(np.nan, None)
        print("Removed np.nan")

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
        # model_fks_dict = {}
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

        print(f"created model FKs dictionary in {round(perf_counter()-t_start, 2):.2f} seconds")

        # Iterating to update FKs IDs
        # Iterate through the DataFrame
        t_start = perf_counter()
        for index, row in df.iterrows():
            print (f"row {index+1}/{df_length}", end="\r")
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
        print(f"Update of FKs done in {round(perf_counter()-t_start, 2):.2f} seconds")
    
        # Removing from df those lines where sqlapp_id are already in the model records
        # Fetch existing sqlapp_id values from the model records
        if 'sqlapp_id' in df.columns:
            print(f"trimming df based on sqlapp_id values, df length={df_length}...", end="")
            existing_ids = set(model_class.objects.values_list('sqlapp_id', flat=True))
            # Filter the DataFrame to exclude rows with existing sqlapp_id values
            df = df[~df['sqlapp_id'].isin(existing_ids)]
            df_length = len(df)
            print ("done")
            print (f"df length after trimming = {df_length}")
        
        # Defining the size of the chunk in rows
        size_of_df_chunk = 300

        # Calculate the number of chunks needed
        num_chunks = math.ceil(df_length / size_of_df_chunk)

        # Iterate over each chunk to insert
        for chunk_index in range(num_chunks):
            start_index = chunk_index * size_of_df_chunk
            end_index = min((chunk_index + 1) * size_of_df_chunk, df_length)
            chunk_df = df.iloc[start_index:end_index]
            len_of_chunk_df = len(chunk_df)

            if df_length > 0:
                try:
                    with transaction.atomic():
                        print("start atomic transaction")
                        instances_to_create = []
                        problematic_rows = []
                        row_counter = 1
                        for row in chunk_df.to_dict(orient='records'):
                            try:
                                instances_to_create.append(model_class(**row))
                                print(f"filling model instances ... {row_counter}/{len_of_chunk_df}", end="\r")
                                row_counter += 1
                            except Exception as ex:
                                problematic_rows.append((row, str(ex)))
                        print()
                        if problematic_rows:
                            print("Problematic Rows:")
                            for idx, (row_data, error_msg) in enumerate(problematic_rows):
                                print(f"Row {idx + 1}: {error_msg}\n{row_data}\n")
                        else:
                            print("no problematic rows")
                        
                        print(f"working on bulk_create - model {model_class.__name__}")
                        print(f"there are {len(instances_to_create)} instances to create in the db")
                        model_class.objects.bulk_create(instances_to_create)
                        print(f"Completed atomic transaction on table {table_name}, chunk: {chunk_index + 1} of {num_chunks}")
                        print()                 
                except Exception as e:
                    print(e)
                    filename = f"error_{chunk_index}of{num_chunks}.xlsx"
                    file_path = f"{settings.MEDIA_ROOT}/{filename}"
                    chunk_df.to_excel(file_path, index=False)
    conn.close() 


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
        csrf_token = request.META.get('CSRF_COOKIE', 'Not set')
        print(f"clean single - csrf token: {csrf_token}")
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
    table_name = model_to_clean._meta.db_table

    with connection.cursor() as cursor:
        cursor.execute(f"DBCC CHECKIDENT ({table_name}, RESEED, 0)")    
    
    print(f"Deleted all fom {model_to_clean}")


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


@login_required
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


@login_required
def files_to_import(request):
    user = request.user
    if request.user.is_superuser == True:
        user_files = UploadedFile.objects.all().filter(process_status='NEW').order_by('-id')
    else:
        user_files = UploadedFile.objects.filter(owner=user)
    return render(request, "app_pages/files_to_import.html", {'user_files': user_files})


@login_required
def imported_files(request, page=0):
    user = request.user
    if user.is_superuser:
        user_files = UploadedFile.objects.all().order_by('-processed_at')
    else:
        user_files = UploadedFile.objects.filter(owner=user).order_by('-processed_at')
    
    items_per_page = 50

    paginator = Paginator(user_files.order_by('-processed_at'), items_per_page)
    # Get the current page from the GET request or in the URL
    if page != 0:
        page_number = page
    else:
        try:
            page_number = request.GET.get('page', 1)
        except (ValueError, TypeError):
            page_number = 1
        
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.get_page(1)



    context = {
        'user_files': page_obj,
        'page_object': page_obj
        }
    return render(request, "app_pages/imported_files.html", context)


def imported_file_log(request, pk):
    log_records = UploadedFileLog.objects.filter(uploaded_file_id=pk).order_by("date")
    context = {
        "log_records": log_records
    }
    return render(request, "app_pages/imported_file_log.html", context)


def start_processing(request, file_id):
    pass


@login_required
def push_file_to_file_processor(request):
    id = request.GET.get("file_id")
    file = get_object_or_404(UploadedFile, pk=id)
    file.process_status = "PROCESSING"
    file.save()
    file_processor.delay(id, request.user.id)
    return redirect("files-to-import")


def delete_this_file_to_import(request, file_id):
    file = get_object_or_404(UploadedFile, id = file_id)
    try:
        file.delete_file()
    except FileNotFoundError as fnf:
        print(fnf)
        file.is_processed = False
        file.save()
    return redirect('files-to-import')


def process_this_file(file):
    file_path = file.file_path + "/" + file.file_name
    log_text = ''
    list_of_sp = []
    if not os.path.exists(file_path):
        # The file does not exists
        log_message = f"data:The file {file_path} is not existing, marking the UploadedFile record as is_processed=True\n\n"
        yield log_message
        log_text += log_message + '\n'
        file.is_processed = True
        file.save()
    else:
        match file.file_type:
            case "ke30":
                convert_dict = import_dictionaries.ke30_converters_dict
                log_message = "data:start reading the Excel file\n\n"
                print(log_message)
                yield log_message
                log_text += log_message + '\n'
                df = file.read_excel_file(file_path, convert_dict)
                log_message = "data:completed reading the Excel file\n\n"
                print(log_message)
                yield log_message
                log_text += log_message + '\n'
                df['Importtimestamp'] = datetime.now()
                df["YearMonth"] = (df['Fiscal Year'].astype(int) * 100 + df['Period'].astype(int)).astype(str)
                # These 2 variable are set for the following action, after the match-case
                model = Ke30ImportLine
                field_mapping = import_dictionaries.ke30_mapping_dict
                list_of_sp =['_ke30_import', '_ke30_import_add_new_customers', '_ke30_import_add_new_products']
            case "ke24":
                convert_dict = import_dictionaries.ke24_converters_dict
                df = file.read_excel_file(file_path, convert_dict)
                df = df.drop(columns=['Industry Code 1'])
                # df['Industry Code 1'] = df['Industry Code 1'].astype(str)               
                model = Ke24ImportLine
                field_mapping = import_dictionaries.ke24_mapping_dict
            case "zaq":
                print("enter zaq section")
                convert_dict = import_dictionaries.zaq_converters_dict
                df = file.read_excel_file(file_path, convert_dict)
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
            case "oo":
                convert_dict = import_dictionaries.oo_converters_dict
                df = file.read_excel_file(file_path, convert_dict)
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
            case "oi" | "arr":
                convert_dict = import_dictionaries.oo_converters_dict
                df = file.read_excel_file(file_path, convert_dict)
                # Removing bottom lines
                print(f"{file.file_type} was {len(df)} lines long")
                uniques = len(df['Document currency'].value_counts())
                df = df.iloc[:-uniques]
                print(f"{file.file_type} is now {len(df)} lines long")
                # Adjusting dates
                df['Document Date'] = df['Document Date'].dt.date
                df['Net due date'] = df['Net due date'].dt.date
                df['Payment date'] = df['Payment date'].dt.date
                df['Arrears after net due date'] = df['Arrears after net due date'].fillna(0).astype(int)
                if file.file_type == "arr":
                    model = Fbl5nArrImport
                    field_mapping = import_dictionaries.arr_mapping_dict
                if file.file_type == "oi":
                    model = Fbl5nOpenImport
                    field_mapping = import_dictionaries.oi_mapping_dict
            case "pr":
                convert_dict = import_dictionaries.pr_converters_dict
                df = file.read_excel_file(file_path)
                model = Price
                field_mapping = import_dictionaries.prl_mapping_dict
        model.objects.all().delete()
        log_message = "data:deleting rows from the db table\n\n"
        yield log_message
        log_text += log_message + '\n'
        df_length = len(df)
        df = df.replace(np.nan, '')
        chunk_size = 500
        chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
        log_message = f"data:based on chunck_size, we got {len(chunks)} chunks for {df_length} total datframe rows\n\n"
        yield log_message
        log_text += log_message + '\n'
        chunk_counter = 0
        for chunk in chunks:
            chunk_counter += 1
            log_message = f"data:processing {chunk_counter}/{len(chunks)}\n\n"
            print(f"processing {chunk_counter}/{len(chunks)}")
            yield log_message
            log_text += log_message + '\n'
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
                    print(f'bulk_create for chunk {chunk_counter} done')
                    instances = []
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                log_message = f"data:working on chunk {chunk_counter} of {len(chunks)}  -  it took {elapsed_time} seconds\n\n"
                yield log_message
                log_text += log_message + '\n'
            except Exception as e:
                # Handle the exception
                log_message = f"data:An error occurred during the transaction: {e}\n\n"
                yield log_message
                log_text += log_message + '\n'
        # All chunks are processed
        print('all chunks processed')
        file.is_processed = True
        file.processed_at = datetime.now()
        # Woring on the stored procedures now
        if list_of_sp:
            print(f'There are {len(list_of_sp)} stored procedures')
            print(list_of_sp)
            with connection.cursor() as curs:
                for index, sp in enumerate(list_of_sp):
                    with transaction.atomic():
                        log_message = f'sp{index}: {sp}'
                        log_text += log_message + '\n'
                        sql_command = f'EXECUTE {sp}'
                        log_message = f"...executing {sp}"
                        log_text += log_message + '\n'
                        print(log_message)
                        curs.execute(sql_command)
                        log_message = f"{sp}...executed"
                        log_text += log_message + '\n'
                        print(log_message)
                        if curs.description:
                            resulting_rows = curs.fetchall()
                            log_message = f'resulting_rows from procedure: {len(resulting_rows)}'
                            print(log_message)
                            log_text += log_message + '\n'
                            result_text=''
                            for row in resulting_rows:
                                row_text = ', '.join(map(str, row))
                                # print(row_text)
                                result_text += row_text + "\n"
                                log_message = result_text
                                log_text += log_message + '\n'
                                yield log_message
                        print("-----------------------------------------------------------")

        # Delete the file
        print(f'deleting ...{file.file_name}')
        if file.delete_file_soft():
            log_message = f"data:File {file.file_name} removed and db updated"
        else:
            log_message = f"data:There is a problem with file name {file.file_name}"
        yield log_message
        log_text += log_message + '\n'
        log_message = f'data:process terminated for file id: {file.id}  filetye: {file.file_type} file_name: {file.file_name} file_path: {file.file_path}\n\n'
        yield log_message
        log_text += log_message + '\n'
        file.log = log_text
        file.save()
        yield 'data:basta\n\n'


@login_required
def customers(request, page=0):
    country_codes = get_cache_country_codes()
    customers = Customer.objects.all().order_by('name')
    sales_team_group = Group.objects.get(name="Sales Team")
    sales_team_members = User.objects.filter(groups=sales_team_group)
    cs_group = Group.objects.get(name="Customer Service")
    cs_reps = User.objects.filter(groups=cs_group)


    if request.method == "POST":
        #collect form data
        form_data = {
                'search_term': request.POST.get('search_term', ''),
                'only_new_customers' : request.POST.get('only_new_customers', ''),
                'activity' :request.POST.get('activity', ''),
                'country_code': request.POST.get('country_code', ''),
                'sales_manager': request.POST.get('sales_manager', ''),
                'customer_service_rep': request.POST.get('customer_service_rep', ''),
                'entries_per_page': request.POST.get('entries_per_page', '20')
            }
    
        request.session['customer_filters'] = form_data

        if "apply_filters" in request.POST:
            customers = apply_filters_to_customers(customers, form_data)

        elif "reset_filters" in request.POST:
            request.session.pop('customer_filters', None)
            form_data = {
                'search_term': '',
                'only_new_customers': '',
                'activity': 'all',
                'country_code': '',
                'sales_manager': '',
                'customer_service_rep': '',
                'entries_per_page': ''
            }
            customers = Customer.objects.all().order_by('name')

    else:
        form_data = request.session.get('customer_filters',{
            'search_term': '',
            'only_new_customers': '',
            'activity': 'all',
            'country_code': '',
            'sales_manager': '',
            'customer_service_rep': '',
            'entries_per_page': '20'
        })
        customers = apply_filters_to_customers(customers, form_data)

    try:
        entries_per_page = int(form_data['entries_per_page'])
    except ValueError:
        entries_per_page = 20
    paginator = Paginator(customers, entries_per_page)
    page_number = request.GET.get('page', 1)
    customers = paginator.get_page(page_number)
    
    context = {
        'country_codes': country_codes,
        'customers': customers,
        'page_object': customers,
        'cs_reps': cs_reps,
        'sales_team_members': sales_team_members,
        'form_data': form_data
    }
    return render(request, "app_pages/customers.html", context)


def apply_filters_to_customers(customers, form_data):
    if form_data['search_term']:
        customers = customers.filter(name__icontains=form_data['search_term'])
    if form_data['only_new_customers']:
        customers = customers.filter(is_new=True)
    if form_data['activity'] != 'all':
        customers = customers.filter(active=(form_data['activity'] == 'active'))
    if form_data['country_code']:
        customers = customers.filter(country__alpha_2=form_data['country_code'])
    if form_data['sales_manager']:
        customers = customers.filter(sales_employee__id=form_data['sales_manager'])
    if form_data['customer_service_rep']:
        customers = customers.filter(customer_service_rep_id=form_data['customer_service_rep'])
    return customers


@login_required
def customers_list_old(request, page=0):
    search_term = request.GET.get('search')
    entries = request.GET.get('entries')
    view_entries = request.GET.get('radios_view')
    
    if 'new_customers' in request.GET:
        only_new_ustomers = request.GET.get('new_customers')
        if only_new_ustomers == 'on':
            only_new_ustomers = True
        else:
            only_new_ustomers = False
        customers = Customer.objects.filter(is_new = only_new_ustomers).order_by('name')
    else:
        only_new_ustomers = False
        customers = Customer.objects.all()

    if search_term:
        customers = customers.filter(
                models.Q(name__icontains=search_term) |
                models.Q(number__icontains=search_term) |
                models.Q(country__alpha_2__icontains=search_term) |
                models.Q(country__official_name_en__icontains=search_term) |
                models.Q(sales_employee__first_name__icontains=search_term) |
                models.Q(sales_employee__last_name__icontains=search_term) |
                models.Q(customer_service_rep__last_name__icontains=search_term) |
                models.Q(customer_service_rep__first_name__icontains=search_term)
                ).order_by('name')
    else:
        customers = customers.order_by('-is_new','name')
    
    if view_entries is not None or view_entries != '':
        if view_entries == 'active':
            customers = customers.filter(active=True)
        elif view_entries == 'inactive':
            customers = customers.filter(active=False)
        else:
            customers = customers    

    if entries is not None:
        try:
            entries = int(entries)
        except ValueError:
            entries = 10
        items_per_page = entries
    else:
        items_per_page = 10

    paginator = Paginator(customers, items_per_page)
    # Get the current page from the GET request or in the URL
    if page != 0:
        page_number = page
    else:
        try:
            page_number = request.GET.get('page', 1)
        except (ValueError, TypeError):
            page_number = 1

    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.get_page(1)

    page_obj.adjusted_elided_pages = paginator.get_elided_page_range(page_number)

    filter_params = {
        'search_term': search_term,
        'entries': entries,
        'only_new': only_new_ustomers
    }

    context = {
        'page_object': page_obj,
        'filter_params': filter_params
    }
    return render(request, "app_pages/customers_list.html", context)


@login_required
def customer_view(request, pk):
    customer = Customer.objects.filter(id=pk).first()

    if request.method == "POST":
        operation = request.POST.get('operation')
        if operation == 'add':

            new_contact = Contact(
                customer = customer,
                first_name = request.POST.get('first_name',),
                middle_name = request.POST.get('middle_name', ''),
                last_name = request.POST.get('last_name', ''),
                job_position = request.POST.get('job_position', ''),
                mobile_number = request.POST.get('mobile_number', ''),
                email = request.POST.get('email', ''),
            )
            new_contact.save()
        elif operation == 'update':
            contact_id = request.POST.get('contact_id')
            contact = get_object_or_404(Contact, pk=contact_id, customer=customer)
            contact.first_name = request.POST.get('first_name')
            contact.middle_name = request.POST.get('middle_name')
            contact.last_name = request.POST.get('last_name')
            contact.job_position = request.POST.get('job_position')
            contact.mobile_number = request.POST.get('mobile_number')
            contact.email = request.POST.get('email')
            contact.save()
        return HttpResponseRedirect(request.path_info)

    # Get Contacts of this customer
    contacts = Contact.objects.filter(customer = customer)

    context = {
        'customer': customer,
        'contacts': contacts
    }
    return render(request, "app_pages/customer_view.html", context)


@login_required
def customer_edit(request, pk):
    c = get_object_or_404(Customer, id=pk)
    # Save is_new here to avoid overwriting when making form.is_valid()
    # for.is_valid would overwrite with False is is_new is not in the 
    # form template, or it is disabled
    is_new_value = c.is_new 
    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance = c)
        if form.is_valid():
            # Check if it's NEW, we consider the edit as approval
            if is_new_value:
                form.instance.approved_by = request.user
                form.instance.approved_on = datetime.today().date()
                form.instance.active = True
                form.instance.is_new = False
            form.save()
            return redirect('customer-view', pk=c.pk)
        else:
            print(form.errors)
    else:
        form = CustomerForm(instance=c)
        form.fields['is_new'].disabled = True
        form.fields['approved_by'].disabled = True
        form.fields['approved_on'].disabled = True

    context = {
        'form': form,
        'customer_is_new': c.is_new,
        'import_note': c.import_note
        }
    return render(request, "app_pages/customer_edit.html", context)


def get_contact_details(request, id):
    if request.method == 'GET':
        try:
            contact = Contact.objects.filter(pk=id).first()
            contact_data = {
                'id': contact.id,
                'first_name': contact.first_name,
                'middle_name': contact.middle_name,
                'last_name': contact.last_name,
                'job_position': contact.job_position,
                'mobile_number': contact.mobile_number,
                'email': contact.email,
            }
            return JsonResponse(contact_data)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest('Contact not found')


@login_required
def products_list(request, page=0):
    search_term = request.GET.get('search')
    entries = request.GET.get('entries') # how many rows to show
    category = request.GET.get('product_category')
    if category == '' or category is None:
        category = 'all'
    status = request.GET.get('product_status_selected')
    if status == '' or status is None:
        status = 'all'
    made_in = request.GET.get('made_in_country_selected')
    if made_in == '' or made_in is None:
        made_in = 'all'

    if search_term:
        products = Product.objects.filter(
                models.Q(name__icontains=search_term) |
                models.Q(number__icontains=search_term) |
                models.Q(brand__name__icontains=search_term) |
                models.Q(made_in__name__icontains=search_term)
                ).order_by('-number')
    else:
        products = Product.objects.all()
    
    if category is not None or category != '':
        if category == 'ink':
            products = products.filter(is_ink=True)
        elif category == 'non_ink':
            products = products.filter(is_ink=False)
        else:
            products = products.order_by('-number')

    products = products.order_by('-is_new', '-number')

    if status is not None and status != 'all':
        products = products.filter(product_status_id=status)


    if made_in is not None and made_in != 'all':
        products = products.filter(made_in=made_in)


    if entries is not None:
        try:
            entries = int(entries)
        except ValueError:
            entries = 10
        items_per_page = entries
    else:
        items_per_page = 10


    paginator = Paginator(products, items_per_page)
    # Get the current page from the GET request or in the URL
    if page != 0:
        page_number = page
    else:
        try:
            page_number = request.GET.get('page', 1)
        except (ValueError, TypeError):
            page_number = 1

    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.get_page(1)


    page_obj.adjusted_elided_pages = paginator.get_elided_page_range(page_number)


    #Get all values of Product Status and Made In Countries
    product_statuses = ProductStatus.objects.all()
    made_in_countries = MadeIn.objects.all()


    filter_params = {
        'search_term': search_term,
        'entries': entries,
        'product_category': category, #ink/non-ink
        'product_status_selected': status,
        'made_in_country_selected': made_in,
    }

    context = {
        'page_object': page_obj,
        'product_statuses_all': product_statuses,
        'made_in_counties_all': made_in_countries,
        'filter_params': filter_params
    }
    return render(request, "app_pages/products_list.html", context)


@login_required
def product_view(request, pk):
    
    product = get_object_or_404(Product, id=pk)
    bom_header_count = BomHeader.objects.filter(product_id=product.id).count()
    bom_headers = BomHeader.objects.filter(product_id = product.id)

    

    if 'page' in request.GET:
        django_filters_page = request.GET.get('page')
        print(f"django_filters_page: {django_filters_page}")
        query_dict = request.GET.copy()
        query_dict.pop('page', None)
        query_dict['return_page'] = django_filters_page
        django_filters_params = query_dict.urlencode()
        print(f"django_filters_params: {django_filters_params}")
    else:
        django_filters_params = request.GET.urlencode()

    context = {
        'product': product,
        'dj_filters_params': django_filters_params,
        'bom_header_count': bom_header_count,
        'bom_headers': bom_headers,
    }
    return render(request, "app_pages/product_view.html", context)


@login_required
def product_edit(request, pk):
    p = get_object_or_404(Product, id=pk)
    django_filters_params = request.GET.urlencode()
    if request.method == 'POST':
        csrf_token = request.META.get('CSRF_COOKIE', 'Not set')
        print(f"product_edit - csrf token: {csrf_token}")
        form = ProductForm(request.POST, instance = p)
        if form.is_valid():
            form.save()
            redirect_url = reverse('product-view', kwargs={'pk': p.pk}) + '?' + django_filters_params
            return redirect(redirect_url)
        else:
            print(form.errors)
    else:
        form = ProductForm(instance=p)
    
    if django_filters_params:
        context = {
            'form': form,
            'product_id': p.id,
            'dj_filters_params': django_filters_params 
            }
    else:
        context = {
            'form': form,
            'product_id': p.id
            }
    return render(request, "app_pages/product_edit.html", context)


@login_required
def brands_list(request, page=0):
    search_term = request.GET.get('search')
    number_of_entries = request.GET.get('number_of_entries',12)
    selected_major_labels = request.GET.get('selected_major_labels')
    selected_ink_technologies = request.GET.getlist('selected_ink_technologies')

    if number_of_entries == '': number_of_entries = 12

    b = Brand.objects.all().order_by('name')

    if search_term:
        b = b.filter(
                models.Q(name__icontains=search_term) |
                models.Q(division__name__icontains=search_term) |
                models.Q(nsf_division__name__icontains=search_term) |
                models.Q(ink_technology__name__icontains=search_term) 
                ).order_by('name')
    else:
        b = b.order_by('name')

    if selected_ink_technologies:
         b = b.filter(ink_technology__name__in=selected_ink_technologies).distinct()

    if selected_major_labels:
        b = b.filter(major_label__name=selected_major_labels).distinct()

    if number_of_entries is not None:
        try:
            number_of_entries = int(number_of_entries)
        except ValueError:
            number_of_entries = 12
        items_per_page = number_of_entries

    paginator = Paginator(b, items_per_page)
     # Get the current page from the GET request or in the URL
    if page != 0:
        page_number = page
    else:
        try:
            page_number = request.GET.get('page', 1)
        except (ValueError, TypeError):
            page_number = 1
    
    try:
        page_obj = paginator.get_page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.get_page(1)

    page_obj.adjusted_elided_pages = paginator.get_elided_page_range(page_number)

    ink_technologies = InkTechnology.objects.all()
    major_labels = MajorLabel.objects.all()

    print("selected_ink_technologies", selected_ink_technologies)
    print("selected_major_labels", selected_major_labels)

    filter_params = {
        'selected_ink_technologies': selected_ink_technologies,
        'selected_major_labels': selected_major_labels
    }

    context = {
        'page_object': page_obj,
        'brands': page_obj,
        'major_labels': major_labels,
        'ink_technologies': ink_technologies,
        'filter_params': filter_params
    }

    return render(request, "app_pages/brands_list.html", context)


@login_required
def brand_view(request, pk):
    b = Brand.objects.filter(id=pk).first()
    context = {
        'brand': b
    }
    return render(request, "app_pages/brand_view.html", context)


@login_required
def brand_edit(request, pk):
    b = get_object_or_404(Brand, id=pk)
    if request.method == 'POST':
        csrf_token = request.META.get('CSRF_COOKIE', 'Not set')
        print(f"brand_edit - csrf token: {csrf_token}")
        form = BrandForm(request.POST, instance = b)
        if form.is_valid():
            form.save()
            return redirect('brand-view', pk=b.pk)
        else:
            print(form.errors)
    else:
        form = BrandForm(instance=b)
    context = {'form': form}
    return render(request, "app_pages/brand_edit.html", context)
    

# For User Management
def create_user(request):
    if request.method == 'POST':
        csrf_token = request.META.get('CSRF_COOKIE', 'Not set')
        print(f"create user - csrf token: {csrf_token}")
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


class UserPasswordChangeView(PasswordChangeView):
  template_name = 'app_pages/password-change.html'
  form_class = UserPasswordChangeForm


# Authentication

class LoginView(LoginView):
  template_name = 'app_pages/sign-in.html'
  form_class = LoginForm


class LoginViewCover(LoginView):
  template_name = 'app_pages/sign-in-cover.html'
  form_class = LoginForm


def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')


@login_required
def products(request):
    
    if request.method == 'GET':
        is_reset_button = request.GET.get('reset')

        if is_reset_button and 'Reset' in is_reset_button:
            return redirect('products')
    
    # products_queryset = Product.objects.select_related(
    #     'color', 'made_in', 'brand', 'packaging', 'product_line', 'product_status', 'approved_by'
    #     ).exclude(product_status__marked_for_deletion = True).annotate(bom_count=Count('bomheader'))
    products_queryset = Product.objects.select_related(
        'color', 'made_in', 'brand', 'packaging', 'product_line', 'product_status', 'approved_by'
        ).annotate(bom_count=Count('bomheader')).order_by('name')
    
    product_filter = ProductFilter(request.GET, products_queryset)
    
    paginator = Paginator(product_filter.qs, 10)
    
    if 'page' in request.GET:
        page_number = request.GET.get('page')
        print(request.GET.get('page'))
    elif 'return_page' in request.GET:
        page_number = request.GET.get('return_page')
    else:
        page_number = 1
    page_obj = paginator.get_page(page_number)

    django_filters_params = request.GET.copy()
    if 'page' in django_filters_params:
        del django_filters_params['page']
        django_filters_params['return_page'] = page_number
    django_filters_params = django_filters_params.urlencode()

    context = {
        'form': product_filter.form,
        'products': page_obj,
        'page_object': page_obj,
        'dj_filters_params': django_filters_params
    }

    return render(request, "app_pages/products.html", context)


@login_required
def sales_forecast_budget(request):
    # Setting time variables
    current_year = datetime.now().year
    forecast_year = current_year
    last_year = current_year - 1
    current_month = datetime.now().month
    budget_year = current_year + 1

    # Missing division string
    missing_division = 'Z missing division'
    # Total string
    total_text = 'ZZ Total'

    if request.method == 'POST':
        csrf_token = request.META.get('CSRF_COOKIE', 'Not set')
        print(f"sbf - csrf token: {csrf_token}")
        form = SalesForecastBudgetFilterForm(request.POST)
        if form.is_valid():
            user_filter = form.cleaned_data['user']
            customer_filter = form.cleaned_data['customer']
            if user_filter and user_filter != 'all':
                user = User.objects.get(id=user_filter)
                # user_email = user.email
            if customer_filter and customer_filter != 'all':
                # customer = Customer.objects.get(id = customer_filter)
                pass
        else:
            user_filter = 'all'
            customer_filter = 'all'
    else:
        form = SalesForecastBudgetFilterForm()
        user_filter = 'all'
        customer_filter = 'all'
        


    # Subquery to get the NSFDivision related to the product's name
    # this is used with last_year, this_year, forecast, budget
    nsf_division_subquery = Product.objects.filter(
        number=OuterRef('material')
    ).values('brand__nsf_division__name')[:1]

    # Subquery to get the exchange rate
    exchange_rate_subquery = EuroExchangeRate.objects.filter(
        currency__alpha_3=OuterRef('curr'),
        year=last_year,
        month=OuterRef('billing_date__month')
    ).values('rate')[:1]

    # If the user is passed we get all managed customer of the user, in a list
    customer_numbers = []
    if user_filter != 'all':
        customer_numbers = Customer.objects.filter(sales_employee=user).values_list('number', flat=True)
    
    # If the customer is appased the customer_numbers only contains the single sap number
    if customer_filter != 'all':
        customer_numbers = Customer.objects.filter(id=customer_filter).values_list('number', flat=True)


    ## Working on Last year
    # Annotate the ZAQCODMI9_line with the NSF division and EUR exchange rates
    # for those lines that are not in EUR
    last_year_annotated_lines = ZAQCODMI9_line.objects.filter(
        billing_date__year=last_year
    ).annotate(
        nsf_division=Subquery(nsf_division_subquery),
        exchange_rate=Coalesce(Subquery(exchange_rate_subquery), Value(1, output_field=DecimalField(max_digits=10, decimal_places=2))),
        adjusted_sales=Round(Case(
            When(curr='EUR', then=F('invoice_sales')),
            default=F('invoice_sales')/F('exchange_rate'),
            output_field=DecimalField(max_digits=20, decimal_places=2)
        ), 2)
    ).values(
        'billing_date', 'nsf_division', 'invoice_qty', 'curr', 'invoice_sales', 'exchange_rate', 'adjusted_sales'
    )

    # If there is a customer_number list, we are filtering on this
    if customer_numbers:
        last_year_annotated_lines = last_year_annotated_lines.filter(sold_to__in=customer_numbers)

    # Transform the queryset in a dictionary that grows automatically
    last_year_sales_data = defaultdict(lambda: {'vol': 0, 'val': 0})
    for line in last_year_annotated_lines:
        nsf_division = line['nsf_division'] or missing_division
        last_year_sales_data[nsf_division]['vol'] += int(line['invoice_qty'])
        last_year_sales_data[nsf_division]['val'] += int(line['adjusted_sales'])

    # Calculate the price per nsf_division
    for nsf_division, data in last_year_sales_data.items():
        data['price'] = (Decimal(data['val']) / Decimal(data['vol'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if data['vol'] != 0 else Decimal('0.00')

    # Calculating the total of last_year
    total_last_year = {'vol': 0, 'val': 0, 'price': Decimal('0.00')}
    for data in last_year_sales_data.values():
        total_last_year['vol'] += data['vol']
        total_last_year['val'] += data['val']
    total_last_year['price'] = (Decimal(total_last_year['val']) / Decimal(total_last_year['vol'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_last_year['vol'] != 0 else Decimal('0.00')
    last_year_sales_data[total_text] = total_last_year

    ## Working on this year
    # Subquery to get the exchange rate
    exchange_rate_subquery = EuroExchangeRate.objects.filter(
        currency__alpha_3=OuterRef('curr'),
        year=current_year,
        month=OuterRef('billing_date__month')
    ).values('rate')[:1]

    # Annotate the ZAQCODMI9_line with the NSF division and EUR exchange rates
    # for those lines that are not in EUR
    this_year_annotated_lines = ZAQCODMI9_line.objects.filter(
        billing_date__year=current_year,
        billing_date__month__lt = current_month
    ).annotate(
        nsf_division=Subquery(nsf_division_subquery),
        exchange_rate=Coalesce(Subquery(exchange_rate_subquery), Value(1, output_field=DecimalField(max_digits=10, decimal_places=2))),
        adjusted_sales=Round(Case(
            When(curr='EUR', then=F('invoice_sales')),
            default=F('invoice_sales')/F('exchange_rate'),
            output_field=DecimalField(max_digits=20, decimal_places=2)
        ), 2)
    ).values(
        'billing_date', 'nsf_division', 'invoice_qty', 'curr', 'invoice_sales', 'exchange_rate', 'adjusted_sales'
    )

    # If there is a customer_number list, we are filtering on this
    if customer_numbers:
        this_year_annotated_lines = this_year_annotated_lines.filter(sold_to__in=customer_numbers)    

    # Transform the queryset into a dictionary
    this_year_sales_data = defaultdict(lambda: {'vol': 0, 'val': 0})
    for line in this_year_annotated_lines:
        nsf_division = line['nsf_division'] or missing_division
        this_year_sales_data[nsf_division]['vol'] += int(line['invoice_qty'])
        this_year_sales_data[nsf_division]['val'] += int(line['adjusted_sales'])

    # Calculate the price per nsf_division
    for nsf_division, data in this_year_sales_data.items():
        data['price'] = (Decimal(data['val']) / Decimal(data['vol'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if data['vol'] != 0 else Decimal('0.00')

    # Calculate total for this year
    total_this_year = {'vol': 0, 'val': 0, 'price': Decimal('0.00')}
    for data in this_year_sales_data.values():
        total_this_year['vol'] += data['vol']
        total_this_year['val'] += data['val']
    total_this_year['price'] = (Decimal(total_this_year['val']) / Decimal(total_this_year['vol'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_this_year['vol'] != 0 else Decimal('0.00')
    this_year_sales_data[total_text] = total_this_year

    # print("Control loop this_year")
    # for l in this_year_sales_data.items():
    #     pprint.pprint(l)
    #     pass
    # print("end of control loop")

    # For the forecast and the budget I need to convert those values where customer currency is not EUR
    # Subquery to get the fixed exchange rate, it will be used below 
    currency_rate_subquery = CurrencyRate.objects.filter(
        currency_id=OuterRef('budforline__customer__currency_id'),
        year=current_year
    ).values('rate')[:1]

    forecast_lines = BudgetForecastDetail.objects.filter(
        scenario__is_forecast=True,
        year=current_year,
        month__gte=current_month
    ).select_related(
        'budforline__brand__nsf_division',
        'budforline__customer__currency'
    ).annotate(
        currency_alpha3=F('budforline__customer__currency__alpha_3'),
        currency_rate=Coalesce(Subquery(currency_rate_subquery), Value(1, output_field=DecimalField(max_digits=10, decimal_places=2))),
        adjusted_value=Case(
            When(budforline__customer__currency__alpha_3='EUR', then=F('value')),
            default=F('value') / F('currency_rate'),
            output_field=DecimalField(max_digits=20, decimal_places=2)
        )
    ).values(
        'budforline__brand__nsf_division__name',
        'volume',
        'adjusted_value'
    )

    if customer_numbers:
        forecast_lines = forecast_lines.filter(budforline__customer__number__in=customer_numbers)

    # Transform the queryset into a dictionary for budget forecast data
    forecast_data = defaultdict(lambda: {'vol': 0, 'val': 0})

    for line in forecast_lines:
        nsf_division = line['budforline__brand__nsf_division__name'] or missing_division
        forecast_data[nsf_division]['vol'] += line['volume']
        forecast_data[nsf_division]['val'] += line['adjusted_value']

    # Calculate the price per nsf_division for budget forecast data
    for nsf_division, data in forecast_data.items():
        data['val'] = int(data['val'])
        if nsf_division is None:
            nsf_division = missing_division       
        data['price'] = (Decimal(data['val']) / Decimal(data['vol'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if data['vol'] != 0 else Decimal('0.00')

    # Calculate total for forecast
    total_forecast = {'vol': 0, 'val': 0, 'price': Decimal('0.00')}
    for data in forecast_data.values():
        total_forecast['vol'] += data['vol']
        total_forecast['val'] += data['val']
    total_forecast['price'] = (Decimal(total_forecast['val']) / Decimal(total_forecast['vol'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_forecast['vol'] != 0 else Decimal('0.00')
    forecast_data[total_text] = total_forecast

    # print("Control loop forecast")
    # for l in forecast_data.items():
    #     pprint.pprint(l)
    # print("end of control loop")

    ## Budget
    # Get the BudgetForecastDetail data aggregated by nsf_division

    currency_rate_subquery = CurrencyRate.objects.filter(
        currency_id=OuterRef('budforline__customer__currency_id'),
        year=budget_year
    ).values('rate')[:1]

    budget_lines = BudgetForecastDetail.objects.filter(
        scenario__is_budget=True,
        year=budget_year
    ).select_related(
        'budforline__brand__nsf_division',
        'budforline__customer__currency'
    ).annotate(
        currency_alpha3=F('budforline__customer__currency__alpha_3'),
        currency_rate=Coalesce(Subquery(currency_rate_subquery), Value(1, output_field=DecimalField(max_digits=10, decimal_places=2))),
        adjusted_value=Case(
            When(budforline__customer__currency__alpha_3='EUR', then=F('value')),
            default=F('value') / F('currency_rate'),
            output_field=DecimalField(max_digits=20, decimal_places=2)
        )
    ).values(
        'budforline__brand__nsf_division__name',
        'volume',
        'adjusted_value'
    )

    if customer_numbers:
        budget_lines = budget_lines.filter(budforline__customer__number__in=customer_numbers)

    # Transform the queryset into a dictionary for budget forecast data
    budget_data = defaultdict(lambda: {'vol': 0, 'val': 0})

    for line in budget_lines:
        nsf_division = line['budforline__brand__nsf_division__name'] or missing_division
        budget_data[nsf_division]['vol'] += line['volume']
        budget_data[nsf_division]['val'] += line['adjusted_value']

    # Calculate the price per nsf_division for budget forecast data
    for nsf_division, data in budget_data.items():
        data['val'] = int(data['val'])
        if nsf_division is None:
            nsf_division = missing_division
        data['price'] = (Decimal(data['val']) / Decimal(data['vol'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if data['vol'] != 0 else Decimal('0.00')

    # Calculate total for budget
    total_budget = {'vol': 0, 'val': 0, 'price': Decimal('0.00')}
    for data in budget_data.values():
        total_budget['vol'] += data['vol']
        total_budget['val'] += data['val']
    total_budget['price'] = (Decimal(total_budget['val']) / Decimal(total_budget['vol'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if total_budget['vol'] != 0 else Decimal('0.00')
    budget_data[total_text] = total_budget

    # Output the budget forecast results to the console
    # print("* BUDGET *")
    # for nsf_division, data in sorted(budget_data.items()):
    #     pass
    #     print(f"NSF Division: {nsf_division}, Volume: {data['vol']}, Value: {data['val']}, Price: {data['price']}")


    ## Combine this year and forecast
    forecast_full_data = defaultdict(lambda: {'vol': 0, 'val': 0})

    # Combine this year's sales data
    for nsf_division, data in this_year_sales_data.items():
        forecast_full_data[nsf_division]['vol'] += data['vol']
        forecast_full_data[nsf_division]['val'] += data['val']
    # pprint.pprint(this_year_sales_data)

    # Combine forecast data
    for nsf_division, data in forecast_data.items():
        forecast_full_data[nsf_division]['vol'] += data['vol']
        forecast_full_data[nsf_division]['val'] += data['val']
    # pprint.pprint(forecast_data)

    # Calculate the combined price per nsf_division
    for nsf_division, data in forecast_full_data.items():
        data['price'] = (Decimal(data['val']) / Decimal(data['vol'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if data['vol'] != 0 else Decimal('0.00')

    # Calculate total for full_forecast
    # The total of the full forecast is already calculated because
    # this_year_sales_data and forecast_data already had the total, so 
    # it was already summed.

    all_nsf_divisions = set(last_year_sales_data.keys()) | set(this_year_sales_data.keys()) | set(forecast_data.keys()) | set(budget_data.keys())
    consolidated_data = []
    for nsf_division in sorted(all_nsf_divisions):
        consolidated_data.append({
            'nsf_division': nsf_division,
            'last': last_year_sales_data.get(nsf_division, {'vol': 0, 'price': 0, 'val': 0}),
            'this': this_year_sales_data.get(nsf_division, {'vol': 0, 'price': 0, 'val': 0}),
            'forecast': forecast_data.get(nsf_division, {'vol': 0, 'price': 0, 'val': 0}),
            'forecast_full': forecast_full_data.get(nsf_division, {'vol': 0, 'price': 0, 'val': 0}),
            'budget': budget_data.get(nsf_division, {'vol': 0, 'price': 0, 'val': 0}),
        })

    current_month_name = months[str(current_month)]['name']
    forecast_month_name = months[str(current_month + 1)]['name']

    # Pushing the datat set in the redis
    cache_key = 'u_all_c_all_sales_forecast_budget_data'
    if user_filter != 'all':
        cache_key = cache_key.replace('u_all', f'u_{user_filter}')
    if customer_filter != 'all':
        cache_key = cache_key.replace('c_all', f'c_{customer_filter}')
    print("cache_key:", cache_key)

    cache.set(cache_key, consolidated_data, timeout=1800)
    # cache.set('sfb_selected_user', user_filter, timeout=None)

    context = {
        'current_month': current_month,
        'current_month_name': current_month_name,
        'forecast_month_name': forecast_month_name,
        'last_year': last_year,
        'current_year': current_year,
        'forecast_year': forecast_year,
        'budget_year': budget_year,
        'missing_division': missing_division,
        'total_text': total_text,
        'consolidated_data': consolidated_data,
        'form': form
    }

    return render(request, 'app_pages/sfb.html', context)


def get_exchange_rates(request):
    print("start the task")
    fetch_euro_exchange_rates.delay()
    return render(request, "app_pages/index.html", {})


# no need for login_required
def format_decimal(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


@login_required
def download_sfb(request):
    current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f'INX_Platform_SFB_{current_date}'
    user_filter = request.GET.get('user', 'all')
    customer_filter = request.GET.get('customer', 'all')
    print(f"user: {user_filter};  customer: {customer_filter}")
    header_line = 'Sales + forecast + Budget (sales manager: all, customer: all)'

    # We had pushed the data in the cach, now here we recover
    cache_key = 'u_all_c_all_sales_forecast_budget_data'
    if user_filter != 'all':
        cache_key = cache_key.replace('u_all', f'u_{user_filter}')
        u = get_object_or_404(User, pk=user_filter)
        if u:
            file_name += f'_{u.first_name}'
            header_line = header_line.replace('sales manager: all', f'sales manager: {u.first_name}')
    if customer_filter != 'all':
        cache_key = cache_key.replace('c_all', f'c_{customer_filter}')
        c = get_object_or_404(Customer, pk=customer_filter)
        if c:
            c_name = c.name.replace(' ', '_')
            file_name += f'_{c_name}'
            header_line = header_line.replace('customer: all', f'customer: {c.name}')
    header_line += f', date:{current_date}'
    
    data = cache.get(cache_key)
    rows = []
    for item in data:
        row = {
            'Division': item['nsf_division'],
            'Last Volume': item['last']['vol'],
            'Last Price': format_decimal(item['last']['price']),
            'Last Value': item['last']['val'],
            'This Volume': item['this']['vol'],
            'This Price': format_decimal(item['this']['price']),
            'This Value': item['this']['val'],
            'Forecast Volume': item['forecast']['vol'],
            'Forecast Price': format_decimal(item['forecast']['price']),
            'Forecast Value': item['forecast']['val'],
            'Forecast Full Volume': item['forecast_full']['vol'],
            'Forecast Full Price': format_decimal(item['forecast_full']['price']),
            'Forecast Full Value': item['forecast_full']['val'],
            'Budget Volume': item['budget']['vol'],
            'Budget Price': format_decimal(item['budget']['price']),
            'Budget Value': item['budget']['val']
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    
    if not data:
        return HttpResponse("No data available to download.", status=404)
    
    with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
        workbook = writer.book
        worksheet = workbook.create_sheet(title='sfb')
        worksheet['A1'] = header_line
        df.to_excel(writer, sheet_name='sfb', startrow=1, index=False)

    with open('output.xlsx', 'rb') as f:
        file_data = f.read()

    response = HttpResponse(file_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheet.sheet')
    response['Content-Disposition'] = f'attachment; filename={file_name}.xlsx'

    return response


def production_requirements(request):
    scenario = Scenario.objects.filter(is_forecast=True).first()
    current_month = datetime.now().month
    if scenario:
        aggregation = BudgetForecastDetail.objects.filter(
            scenario=scenario,
            year=2024,
            month__gt=current_month
        ).values(
            'budforline__brand__name',
            'budforline__brand',
            'budforline__color_group__name',
            'budforline__color_group'
        ).annotate(
            total_volume=Sum('volume')
        ).order_by(
            'budforline__brand__name',
            'color_group__name'
        )
        
        aggregation = aggregation.filter(total_volume__gt=0)
        
        for entry in aggregation:
            brand_id = entry['budforline__brand']
            color_group_id = entry['budforline__color_group']
            active_products = Product.objects.filter(
                brand_id=brand_id,
                color__color_group_id=color_group_id,
                product_status__marked_for_deletion=False,
                is_fert=True
            ).values('number', 'name')
            entry['active_products'] = list(active_products)
        
        context = {
            'forecast_aggregation': aggregation
        }
            
    return render(request, "app_pages/production_requirements.html", context)
    

def fetch_bom_components(request, bom_header_id):
    
    bom_header = get_object_or_404(BomHeader, pk=bom_header_id)
    boms = Bom.objects.filter(bom_header=bom_header).select_related('bom_component').order_by('item_number')
    
    # Calculation of total RMC
    header_base_quantity = bom_header.header_base_quantity
    specific_gravity = Decimal(100) / header_base_quantity
    total_RMC_CZK = Decimal(0)
    total_RMC_EUR = Decimal(0)
    print("len:", len(boms))
    for c in boms:
        # old_value = total_RMC_CZK
        if c.component_base_uom != "EA":
            total_RMC_CZK += c.weighed_price_per_kg_ea_CZK
            total_RMC_EUR += c.weighed_price_per_kg_ea_EUR
        else:
            total_RMC_CZK += c.weighed_price_per_kg_ea_CZK
            total_RMC_EUR += c.weighed_price_per_kg_ea_EUR
        # print("***",c.component_base_uom, old_value,"+", c.weighed_price_per_kg_ea_CZK, " = ", total_RMC_CZK, type(c.weighed_price_per_kg_ea_CZK))
    
    total_RMC_CZK_KG = total_RMC_CZK / 100
    total_RMC_CZK_LT = total_RMC_CZK_KG * specific_gravity
    total_RMC_EUR_KG = total_RMC_EUR / 100
    total_RMC_EUR_LT = total_RMC_EUR_KG * specific_gravity
    
    context = {
        'bom_header': bom_header,
        'bom_components': boms,
        'total_RMC_CZK': total_RMC_CZK,
        'total_RMC_CZK_KG': total_RMC_CZK_KG,
        'total_RMC_CZK_LT': total_RMC_CZK_LT,
        'total_RMC_EUR_KG': total_RMC_EUR_KG,
        'total_RMC_EUR_LT': total_RMC_EUR_LT,
        'total_RMC_EUR': total_RMC_EUR,
        'specific_gravity': specific_gravity
    }
    
    return render(request, "app_pages/bom_components_partial.html", context)


@login_required
def special_marco(request):
    return render(request, "app_pages/_marco.html", {})

@login_required
def special_del_boms(request):
    Bom.objects.all().delete()
    BomHeader.objects.all().delete()
    BomComponent.objects.all().delete()
    mess = 'deleted all !'
    context = {
        'mewssages': mess
    }
    return render(request, "app_pages/_marco.html", context)
    

def fetch_sds_l1_replacements(request, pk):
    c = Customer.objects.filter(id=pk).first()
    try:
        # Get all lines from SDSReplacement with this customer_id and null in language_id and null in product_id
        sds_l1_lines = SDSReplacement.objects.filter(customer = c, language=None, product=None)

    except Http404:
        pass

    context = {
        'sds_l1_lines': sds_l1_lines,
    }
    return render (request, "app_pages/sds_l1_partial.html", context)


def delete_sds_l1_replacement(request, pk):
    sds_l1_replacement = get_object_or_404(SDSReplacement, pk=pk)
    c = sds_l1_replacement.customer
    sds_l1_replacement.delete()
    sds_l1_lines = SDSReplacement.objects.filter(customer=c, language=None, product=None)
    
    context = {
        'sds_l1_lines': sds_l1_lines,
    }
    return render(request, "app_pages/sds_l1_partial.html", context)

def edit_sds_l1_replacement(request, pk):
    sds_replacement = get_object_or_404(SDSReplacement, pk=pk)
    c = sds_replacement.customer
    if request.method == 'POST':
        form = SDSReplacementForm(request.POST, instance = sds_replacement)
        if form.is_valid():
            form.save()
            sds_l1_lines = SDSReplacement.objects.filter(customer = sds_replacement.customer, language=None, product=None)
            context = {
                'sds_l1_lines': sds_l1_lines,
            }
            return render (request, "app_pages/sds_l1_partial.html", context)
        else:
            context = {
                'form': form,
                'sds_replacement': sds_replacement
            }
            return render(request, "app_pages/sds_l1_edit_partial.html", context)
    else:
        form = SDSReplacementForm(instance=sds_replacement)
    context = {
        'customer': c,
        'form': form,
        'sds_replacement': sds_replacement
    }
    return render(request, "app_pages/sds_l1_edit_partial.html", context)

def add_sds_l1_replacement(request, pk):
    c = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = SDSReplacementForm(request.POST)
        if form.is_valid():
            sds_replacement = form.save(commit=False)
            sds_replacement.customer = c
            sds_replacement.save()
            return redirect('fetch-sds-l1-replacements', pk=sds_replacement.customer.id)
    else:
        form = SDSReplacementForm()
    context = {
        'customer': c,
        'form': form,
        'sds_replacement': None
    }
    return render(request, "app_pages/sds_l1_edit_partial.html", context)


def fetch_sds_l2_languages_list(request, pk, added_language_id=None):
    c = get_object_or_404(Customer, pk=pk)
    sds_l2_languages = SDSReplacement.objects.filter(customer=c, product=None).exclude(language=None).values('language_id', 'language__name').distinct()
    context = {
        'customer': c,
        'added_language_id': added_language_id,
        'sds_l2_languages': sds_l2_languages
    }
    return render(request, "app_pages/sds_l2_languages_list.html", context)


def add_sds_l2_language(request, pk):
    c = get_object_or_404(Customer, pk=pk)
    added_language = 'no added language'
    if request.method == 'POST':
        form = SDSL2LanguageForm(request.POST)
        if form.is_valid():
            sds_l2_language = form.save(commit=False)
            sds_l2_language.customer = c
            sds_l2_language.save()
            added_language = form.cleaned_data['language']
            return redirect('fetch-sds-l2-languages-list', pk=c.id, added_language_id=added_language.id)
    else:
        form = SDSL2LanguageForm()
    context = {
        'customer': c,
        'added_language': added_language,
        'form': form
    }
    return render(request, "app_pages/sds_l2_add_language.html", context)


def fetch_sds_l2_replacements(request, customer_id, language_id):
    c = get_object_or_404(Customer, pk=customer_id)
    l = get_object_or_404(Language, pk=language_id)
    sds_l2_replacements = SDSReplacement.objects.filter(customer=c, language=l, product=None)
    context = {
        'customer': c,
        'language': l,
        'sds_l2_replacements': sds_l2_replacements
    }
    return render(request, "app_pages/sds_l2_replacements_list.html", context)


def delete_sds_l2_replacement(request, pk):
    sds_l2_replacement = get_object_or_404(SDSReplacement, pk=pk)
    c = sds_l2_replacement.customer
    l = sds_l2_replacement.language
    if sds_l2_replacement:
        sds_l2_replacement.delete()
    # Check if any replacements left with this language
    sds_l2_replacements_left = len(SDSReplacement.objects.filter(customer=c, language = l))
    # How to return more HTML for more div ids?
    sds_l2_replacements = SDSReplacement.objects.filter(customer=c, language=l, product=None)
    context = {
        'customer': c,
        'language': l,
        'sds_l2_replacements': sds_l2_replacements
    }
    return render(request, "app_pages/sds_l2_replacements_list.html", context)


def edit_sds_l2_replacement(request, pk):
    sds_l2_replacement = get_object_or_404(SDSReplacement, pk=pk)
    c = sds_l2_replacement.customer
    l = sds_l2_replacement.language
    if request.method == 'POST':
        form = SDSReplacementForm(request.POST, instance = sds_l2_replacement)
        if form.is_valid():
            form.save()
            sds_l2_replacements = SDSReplacement.objects.filter(customer=c, language=l, product=None)
            context = {
                'customer': c,
                'language': l,
                'sds_l2_replacements': sds_l2_replacements
            }
            return render (request, "app_pages/sds_l2_replacements_list.html", context)
    else:
        form = SDSReplacementForm(instance=sds_l2_replacement)
    context = {
        'customer': c,
        'language': l,
        'form': form,
        'sds_l2_replacement': sds_l2_replacement
    }
    return render(request, "app_pages/sds_l2_edit_replacement.html", context)


def add_sds_l2_replacement(request, customer_id, language_id):
    c = get_object_or_404(Customer, pk=customer_id)
    l = get_object_or_404(Language, pk=language_id)
    SDSReplacement.objects.create(customer=c, language=l)
    sds_l2_replacements = SDSReplacement.objects.filter(customer=c, language=l, product=None)

    context = {
        'customer': c,
        'language': l,
        'sds_l2_replacements': sds_l2_replacements
    }
    return render(request, "app_pages/sds_l2_replacements_list.html", context)


def fetch_sds_l3_languages_list(request, pk):
    p = get_object_or_404(Product, pk=pk)
    c = p.customer
    sds_l3_languages = SDSReplacement.objects.filter(customer=c, product=p).exclude(language=None).values('language_id', 'language__name').distinct()
    context = {
        'customer': c,
        'product': p,
        'sds_l3_languages': sds_l3_languages
    }
    return render(request, "app_pages/sds_l3_languages_list.html", context)


def fetch_sds_l3_replacements(request, product_id, language_id):
    # Get Language
    l= get_object_or_404(Language, pk=language_id)
    # Get replacements based on product (if product has a customer linked)
    p = get_object_or_404(Product, pk=product_id)
    c = p.customer
    sds_l3_replacements = SDSReplacement.objects.filter(product=p, customer=c, language=l)
    sds_l3_replacements_count = len(sds_l3_replacements)
    sds_rtf_file = SDSRTFFile.objects.filter(product=p, language=l).first()
    if sds_rtf_file:
        sds_rtf_file_exists = True
    else:
        sds_rtf_file_exists = False
    context = {
        'customer': c,
        'product': p,
        'language': l,
        'sds_l3_replacements_count': sds_l3_replacements_count,
        'sds_l3_replacements': sds_l3_replacements,
        'sds_rtf_file': sds_rtf_file,
        'sds_rtf_file_exists': sds_rtf_file_exists
    }
    return render(request, "app_pages/sds_l3_replacements_list.html", context)


def add_sds_l3_replacement(request, customer_id, product_id, language_id):
    p = get_object_or_404(Product, pk=product_id)
    c = get_object_or_404(Customer, pk=customer_id)
    l = get_object_or_404(Language, pk=language_id)
    SDSReplacement.objects.create(customer=c, product=p, language=l)
    sds_l3_replacements = SDSReplacement.objects.filter(customer=c, language=l, product=p)
    sds_l3_replacements_count = len(sds_l3_replacements)

    context = {
        'customer': c,
        'product': p,
        'language': l,
        'sds_l3_replacements': sds_l3_replacements,
        'sds_l3_replacements_count': sds_l3_replacements_count
    }
    return render(request, "app_pages/sds_l3_replacements_list.html", context)


def add_sds_l3_language(request, pk):
    p = get_object_or_404(Product, pk=pk)
    c = p.customer
    if request.method == 'POST':
        form = SDSL2LanguageForm(request.POST)
        if form.is_valid():
            sds_l3_language = form.save(commit=False)
            sds_l3_language.customer = c
            sds_l3_language.product = p
            sds_l3_language.save()
            return redirect('fetch-sds-l3-languages-list', pk=p.id)
    else:
        form = SDSL2LanguageForm()
    context = {
        'customer': c,
        'product': p,
        'form': form
    }
    return render(request, "app_pages/sds_l3_add_language.html", context)


def edit_sds_l3_replacement(request, pk):
    # pk is the id of the replacement record
    sds_l3_replacement = get_object_or_404(SDSReplacement, pk=pk)
    c = sds_l3_replacement.customer
    l = sds_l3_replacement.language
    p = sds_l3_replacement.product
    if request.method == 'POST':
        form = SDSReplacementForm(request.POST, instance = sds_l3_replacement)
        if form.is_valid():
            form.save()
            sds_l3_replacements = SDSReplacement.objects.filter(customer=c, language=l, product=p)
            sds_l3_replacements_count = len(sds_l3_replacements)
            context = {
                'customer': c,
                'product': p,
                'language': l,
                'sds_l3_replacements': sds_l3_replacements,
                'sds_l3_replacements_count': sds_l3_replacements_count
            }
            return render (request, "app_pages/sds_l3_replacements_list.html", context)
    else:
        form = SDSReplacementForm(instance=sds_l3_replacement)
    context = {
        'customer': c,
        'product': p,
        'language': l,
        'form': form,
        'sds_l3_replacement': sds_l3_replacement
    }
    return render(request, "app_pages/sds_l3_edit_replacement.html", context)


def delete_sds_l3_replacement(request, pk):
    # pk is the id of the replacement record
    sds_l3_replacement = get_object_or_404(SDSReplacement, pk=pk)
    c = sds_l3_replacement.customer
    p = sds_l3_replacement.product
    l = sds_l3_replacement.language
    if sds_l3_replacement:
        sds_l3_replacement.delete()

    # How to return more HTML for more div ids?
    sds_l3_replacements = SDSReplacement.objects.filter(customer=c, language=l, product=p)
    sds_l3_replacements_count = len(sds_l3_replacements)
    context = {
        'customer': c,
        'product': p,
        'language': l,
        'sds_l3_replacements': sds_l3_replacements,
        'sds_l3_replacements_count': sds_l3_replacements_count
    }
    return render(request, "app_pages/sds_l3_replacements_list.html", context)


def delete_sds_rtf_file(request, pk):
    sds_rtf_file = get_object_or_404(SDSRTFFile, pk=pk)
    product = sds_rtf_file.product
    language = sds_rtf_file.language
    sds_rtf_file.file.delete(save=False)
    sds_rtf_file.delete()
    return redirect('fetch-sds-l3-replacements', product_id=product.id, language_id=language.id)


def upload_sds_rtf_file(request, product_id, language_id):
    if request.method == 'POST' and request.FILES.get('file'):
        product = get_object_or_404(Product, pk=product_id)
        language = get_object_or_404(Language, pk=language_id)
        file = request.FILES['file']
        file_content = file.read()
        sds_rtf_file, created = SDSRTFFile.objects.get_or_create(product=product, language=language)
        if created:
            sds_rtf_file.file = file
            sds_rtf_file.save()

        return redirect('fetch-sds-l3-replacements', product_id=product.id, language_id=language.id)
    else:
        return redirect('fetch-sds-l3-replacements', product_id=product.id, language_id=language.id)
    

def get_logo_string(logo_path, logo_width_mm):
    print("\tStart working on the customer logo")
    print("\trequested width:", logo_width_mm)
    print(f"\tlogo_path: {logo_path}")
    with open(logo_path, 'rb') as image_file:
        logo_binary = image_file.read()
        logo_hex = binascii.hexlify(logo_binary).decode('ascii')
        print(f"\tlogo_hex: {logo_hex[:50]}...")
    
    with Image.open(logo_path) as image_file:
        image_width, image_height = image_file.size
        aspect_ratio = image_height / image_width
    
    # 1 twip = 1/1440 inch
    # 1 inch = 25.4 mm
    # 1 twip = 1/1440 * 25.4 mm = 0.0176388888888889 mm
    twips_per_mm = 1440 / 25.4
    width_twips = int(logo_width_mm * twips_per_mm)
    height_twips = int(width_twips * aspect_ratio)
    print(f"\tcustomer logo width x height (twips): {width_twips}x{height_twips}")

    logo_rtf = (
        r"{\pict\pngblip\n" +
        f"\n\\picwgoal{width_twips}\\pichgoal{height_twips}\n"
        + logo_hex
        + r"\n}"
    )
    print("\tcustomer logo work finished")
    return logo_rtf, width_twips, height_twips, aspect_ratio


def find_start_index_of_logo(list_of_strings, content):
    print("Searching start index of the logo ... ", end="")
    for i, string_to_find in enumerate(list_of_strings):
        start_index = content.find(string_to_find)
        if start_index != -1:
            print(f"Found string {i} at index {start_index}")
            return start_index
    return -1


def remove_logo_from_rtf(list_of_start_strings, end_string, content, cycles=1):
    working_content = content
    removed = False
    position_of_first_logo_insertion = 0
    loops = 1
    media_root_path = settings.MEDIA_ROOT

    while True:
        print(f"Loop {loops}")
        output_test_file_path = os.path.join(media_root_path, f'removing_logo_loop_{str(loops)}.rtf')
        with open( output_test_file_path, 'w', encoding='utf-8') as file:
            file.write(working_content)
        start_index = find_start_index_of_logo(list_of_start_strings, working_content)
        if start_index == -1:
            print("Logo not found with any of the search strings")
            break
        
        try:
            end_index = working_content.index(end_string, start_index) + len(end_string)
            print(f"start_index: {start_index}, end_index: {end_index}")
            if not removed:
                position_of_first_logo_insertion = start_index
                print(f"----------position_of_first_logo_insertion: {position_of_first_logo_insertion}")
            working_content = working_content[:start_index] + working_content[end_index:]
            removed = True
            loops += 1
        except ValueError:
            print(f"end_string: {end_string} - not found")
            break

    content = working_content

    # try:
    #     start_index = find_start_index_of_logo(list_of_start_strings, content)
    #     print(f"start_index: {start_index}")
    #     if cycles == 1 and start_index != -1:
    #         position_of_first_logo_insertion = start_index
    #         print(f"position_of_first_logo_insertion: {position_of_first_logo_insertion}")
    #         removed = True
    #     elif cycles == 1 and start_index == -1:
    #         position_of_first_logo_insertion = 0
    #     else:
    #         position_of_first_logo_insertion = 0
    #         removed = True
    # except ValueError:
    #     print("Error in finding the start index of the logo")
    #     start_index = -1
    #     if start_index == -1:
    #         removed = False
    
    # if removed:
    #     try:
    #         end_index = content.index(end_string, start_index)
    #         print(f"end_index: {end_index}")
    #         if end_index > start_index:
    #             print("OK")
    #         else:
    #             print("Not OK")
    #         end_index = content.index(end_string) + len(end_string)
    #     except ValueError:
    #         print(f"end_string: {end_string} - not found")
    
    # if start_index != -1 and end_index != -1:
    #     content = content[:start_index] + content[end_index:]
    #     print(f"Logo removed - cycles: {cycles}")
    #     removed = True
    
    # if find_start_index_of_logo(list_of_start_strings, content) != -1:
    #     cycles += 1
    #     print(f"There is another occurrence of the logo. Entering cycle {cycles}")
    #     content, not_used, removed = remove_logo_from_rtf(list_of_start_strings, end_string, content, cycles)
    
    return content, position_of_first_logo_insertion, removed

@login_required
def download_sds_rtf_file(request, pk):
    sds_rtf_file = get_object_or_404(SDSRTFFile, pk=pk)
    p = sds_rtf_file.product
    l = sds_rtf_file.language

    with open(sds_rtf_file.file.path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    # Get all Level 1 replacements
    sds_lev1_replacements = SDSReplacement.objects.filter(customer=p.customer, language=None, product=None)
    # Get all Level 2 replacements
    sds_lev2_replacements = SDSReplacement.objects.filter(customer=p.customer, language=l, product=None)
    # Get all Level 3 replacements
    sds_lev3_replacements = SDSReplacement.objects.filter(customer=p.customer, language=l, product=p)

    if sds_lev1_replacements:
        for r in sds_lev1_replacements:
            file_content = file_content.replace(r.search_for, r.replace_with)
        print("Level 1 replacements done")
    if sds_lev2_replacements:
        for r in sds_lev2_replacements:
            file_content = file_content.replace(r.search_for, r.replace_with)
        print("Level 2 replacements done")
    if sds_lev3_replacements:
        for r in sds_lev3_replacements:
            file_content = file_content.replace(r.search_for, r.replace_with)
        print("Level 3 replacements done")

    # Get the logo image from the customer
    c = p.customer
        
    # Container tags in the RTF file
    logo_box_tags ='{\shp{\*\shpinst\shpleft-15\shptop-1041\shpright1871\shpbottom-33'
    
    inx_logo_start_string = [
        '{\pict{\*\picprop\shplid1037{',
        '{\pict{\*\picprop\shplid1027{',
        '{\pict{\*\picprop\shplid1026{\sp{\sn shapeType}{\sv 75}}{\sp{\sn fFlipH}{\sv 0}}{\sp{\sn fFlipV}{\sv 0}}{\sp{\sn fLine}{\sv 0}}{\sp{\sn wzDescription}{\sv NEW INX LOGO FOR SDS}}'
        ]
    # inx_logo_end_string = '0000000000000000000000000000000000b840ff1fdf86134b9a5bc8bb0000000049454e44ae426082}'
    inx_logo_end_string = '54e44ae426082}'
    
    new_content, index_of_logo_insertion, removed = remove_logo_from_rtf(inx_logo_start_string, inx_logo_end_string, file_content, cycles=1)
    if removed:
        print("INX logo(s) removed")

    current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    basename, ext = os.path.splitext(os.path.basename(sds_rtf_file.file.name))
    new_filename_rtf = f"{basename}_{current_datetime}{ext}"
    new_filename_pdf = f"{basename}_{current_datetime}.pdf"

    if shutil.which('soffice'):
        print("soffice installed")
        # Write RTF data in a temporary file
        temporary_rtf_file_path = os.path.join(settings.MEDIA_ROOT, new_filename_rtf)
        with open(temporary_rtf_file_path, 'w', encoding='utf-8') as temporary_rtf_file:
            temporary_rtf_file.write(new_content)
            print("RTF Write finished")
        command = [
            "soffice",
            "--headless",
            "--convert-to", "pdf",
            temporary_rtf_file_path,
            "--outdir", os.path.dirname(temporary_rtf_file_path)
        ]
        subprocess.run(command, check=True)
        print(f"PDF conversion finished - os.path.dirname(temporary_rtf_file_path): {os.path.dirname(temporary_rtf_file_path)}/{new_filename_pdf}")
        # Removing the temporary RTF file
        os.remove(temporary_rtf_file_path)
        pdf_path = os.path.join(os.path.dirname(temporary_rtf_file_path), new_filename_pdf)
        
        # Operation on the PDF file
        if c.logo:
            logo_path = c.logo.path
            with Image.open(logo_path) as lg:
                logo_width_px, logo_height_px = lg.size
            logo_width_points = c.logo_width_mm * 2.83465
            logo_height_points = logo_width_points * (logo_height_px / logo_width_px)
            logo_left_margin_points = c.logo_left_margin_mm * 2.83465
            logo_baseline_points = c.logo_baseline_mm * 2.83465
            logo_y_position = A4[1] - logo_baseline_points - logo_height_points
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=A4)
            logo = ImageReader(logo_path)
            can.drawImage(logo, logo_left_margin_points, 770, width=logo_width_points, height=logo_height_points)
            can.save()
            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            new_pdf = PdfReader(packet)
            existing_pdf = PdfReader(open(pdf_path, "rb"))
            output = PdfWriter()
            # Add the "new layer" (which is the new pdf) on the existing page
            page = existing_pdf.pages[0]
            page.merge_page(new_pdf.pages[0])
            output.add_page(page)
            # Add the rest of the pages
            for i in range(1, len(existing_pdf.pages)):
                output.add_page(existing_pdf.pages[i])
            # Save the result
            output_stream = open(pdf_path, "wb")
            output.write(output_stream)
            output_stream.close()
        
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        os.remove(pdf_path)
        response = HttpResponse(pdf_content, content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename={new_filename_pdf}'
        return response
    else:
        response = HttpResponse(new_content, content_type="application/rtf")
        response['Content-Disposition'] = f'attachment; filename={new_filename_rtf}'
        return response