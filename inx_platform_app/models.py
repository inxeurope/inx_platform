import os
import time
from datetime import datetime
import pandas as pd
import numpy as np
import django
from django.apps import apps
from django.db import models, transaction
from django.core.validators import RegexValidator
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from . import import_dictionaries
from django.core.exceptions import ValidationError


# Field validators
def xls_xlsx_file_validator(value):
    ext = os.path.splitext(value.name)[1]  # Get file extension
    valid_extensions = ['.xlsx', '.XLSX']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Only .xlsx and .XLSX files are allowed.')
#--------------------------------------------- End of validators


# ----------------------------------------------------------
# The following classes are for managing a custom User model
# ----------------------------------------------------------
class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("You have not provided a valid email address")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)
    
    def get_all_users(self):
        return self.get_queryset().all()


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(blank=True, default='', unique=True)
    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    mobile_number = models.CharField(max_length=100, null=True, blank=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    sqlapp_id = models.IntegerField(default=0, null=True)

    photo = models.CharField(default='', max_length=255, blank=True, null=True)    

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def get_full_name(self):
        strings =[self.first_name, self.last_name]
        return ' '.join(strings)
    
    def get_short_name(self):
        return self.first_name or self.email
    
    def get_snakecase_name(self):
        strings =[self.first_name.replace(" ", "_").lower(), self.last_name.lower()]
        return '_'.join(strings)
    
    @classmethod
    def get_all_users(cls):
        return cls.objects.all()

# -----------------------------------------------------
# Models with no Foreign Keys
# -----------------------------------------------------

class ProductLine(models.Model):
    name = models.CharField(max_length=50, blank=True)
    sqlapp_id = models.IntegerField(default=0)

    def __str__(self):
        return_value = f"{self.name}"
        return return_value


class ColorGroup(models.Model):
    name = models.CharField(max_length=50)
    sqlapp_id = models.IntegerField(default=0)

    def __str__(self):
        return_value = f"{self.name}"
        return return_value


class MadeIn(models.Model):
    name = models.CharField(max_length=10)
    plant_name = models.CharField(max_length=40)
    plant_number = models.CharField(max_length=4) # example 8800
    sqlapp_id = models.IntegerField(default=0)

    def __str__(self):
        return_value = f"{self.name}"
        return return_value


class Division(models.Model):
    name = models.CharField(max_length=40)
    sap_id = models.CharField(max_length=10, blank=True, null=True)
    sap_name = models.CharField(max_length=50, blank=True, null=True)
    sqlapp_id = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class MajorLabel(models.Model):
    name = models.CharField(max_length=40)
    sap_id = models.CharField(max_length=10, null=True, blank=True)
    sap_name = models.CharField(max_length=50, null=True, blank=True)
    sqlapp_id = models.IntegerField(default=0, null=True, blank=True)
    svg_logo = models.TextField(blank=True)

    def __str__(self):
        return self.name


class InkTechnology(models.Model):
    name = models.CharField(max_length=40, null=True, blank=True)
    short_name = models.CharField(max_length = 10, null=True, blank=True)
    sap_id = models.CharField(max_length=10, null=True, blank=True)
    sap_name = models.CharField(max_length=50, null=True, blank=True)
    sqlapp_id = models.IntegerField(default=0, null=True, blank=True)
    ribbon_color = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


class NSFDivision(models.Model):
    name = models.CharField(max_length=40)
    sap_id = models.CharField(max_length=10)
    sap_name = models.CharField(max_length=50)
    sqlapp_id = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class MarketSegment(models.Model):
    name = models.CharField(max_length=40)
    sap_id = models.CharField(max_length=10)
    sap_name = models.CharField(max_length=50)
    sqlapp_id = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class MaterialGroup(models.Model):
    name = models.CharField(max_length=40)
    sap_id = models.CharField(max_length=10)
    sap_name = models.CharField(max_length=50)
    sqlapp_id = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Packaging(models.Model):
    name = models.CharField(max_length=20)
    # the following field is superseded by the table RateToLT, which combines Packaging ID
    # and UoM ID (if I am selling -440ML as EA)
    rate_to_lt = models.IntegerField(default=1) 
    sold_in_lt = models.BooleanField(default=True)
    sqlapp_id = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class ProductStatus(models.Model):
    name = models.CharField(max_length=50)
    color_r = models.IntegerField(null=True)
    color_g = models.IntegerField(null=True)
    color_b = models.IntegerField(null=True)
    color_a = models.IntegerField(null=True)
    sqlapp_id = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.name


class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=15)
    sqlapp_id = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.name


class ExchangeRate(models.Model):
    currency = models.CharField(max_length=3)
    year = models.IntegerField()
    rate = models.FloatField()
    sqlapp_id = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.currency + self.year


class Scenario(models.Model):
    name = models.CharField(max_length=100, blank=True)
    is_sales = models.BooleanField(default=False, null=True)
    sqlapp_id = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.name


class CountryCode(models.Model):
    class Meta:
        ordering = ['alpha_2']

    country_id = models.IntegerField(default=0)
    alpha_3 = models.CharField(max_length=3, null=True)
    alpha_2 = models.CharField(max_length=2, null=True)
    intermediate_region_code = models.IntegerField(null=True)
    intermediate_region_name = models.CharField(max_length=255, null=True)
    iso4217_currency_name = models.CharField(max_length=255, null=True)
    iso4217_currency_numeric_code = models.IntegerField(default=0, null=True)
    iso4217_currency_alphabetic_code = models.CharField(max_length=7, null=True)
    iso4217_currency_minor_unit = models.IntegerField(default=0, null=True)
    iso4217_currency_country_name = models.CharField(max_length=255, null=True)
    uniterm_english_short = models.CharField(max_length=255, null=True)
    uniterm_english_formal = models.CharField(max_length=255, null=True)
    region_code = models.IntegerField(default=0, null=True)
    region_name = models.CharField(max_length=255, null=True)
    sub_region_code = models.IntegerField(default=0, null=True)
    sub_region_name = models.CharField(max_length=255, null=True)
    continent = models.CharField(max_length=255, null=True)
    global_name = models.CharField(max_length=255, null=True)
    capital = models.CharField(max_length=255, null=True)
    official_name_en = models.CharField(max_length=255, null=True)
    cldr_display_name = models.CharField(max_length=255, null=True)
    sqlapp_id = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.official_name_en


class CustomerType(models.Model):
    name = models.CharField(max_length=20)
    sqlapp_id = models.IntegerField(default=0, null=True)
    
    def __str__(self):
        return self.name


class Industry(models.Model):
    # Industry defines if a Customer is a Distributor or an OEM or other values
    name = models.CharField(max_length=30)
    sap_id = models.CharField(max_length=20, blank=True)
    sap_name = models.CharField(max_length=40, blank=True)
    sqlapp_id = models.IntegerField(default=0, null=True)

    class Meta:
        verbose_name = 'Industry'
        verbose_name_plural = 'Industries'
    
    def __str__(self):
        return self.name


class PaymentTerm(models.Model):
    name=models.CharField(max_length=255)
    days_term = models.SmallIntegerField(null=True)

# -----------------------------------------------------
# Models with no FK and no index
# -----------------------------------------------------

class Fbl5nArrImport(models.Model):
    document_date = models.DateField()
    net_due_date = models.DateField()
    arrears = models.IntegerField()
    amount_in_doc_currency = models.FloatField(null=True)
    doc_currency = models.CharField(max_length=5)
    doc_type = models.CharField(max_length=3)
    customer_number = models.IntegerField()
    doc_number = models.CharField(max_length=50)
    invoice_number = models.CharField(max_length=20)
    payment_terms = models.CharField(max_length=5)
    invoice_reference = models.CharField(max_length=30)
    payment_date = models.DateField()
    deb_cred = models.CharField(max_length=1, null=True)

    def __str__(self):
        return_value = f"ID:{self.id}, Document date: {self.document_date}, Customer number: {self.customer_number}"
        return return_value


class Fbl5nOpenImport(models.Model):
    document_date = models.DateField()
    net_due_date = models.DateField()
    arrears = models.IntegerField()
    amount_in_doc_currency = models.FloatField(null=True)
    doc_currency = models.CharField(max_length=5)
    doc_type = models.CharField(max_length=3)
    customer_number = models.IntegerField()
    doc_number = models.CharField(max_length=50)
    invoice_number = models.CharField(max_length=20)
    payment_terms = models.CharField(max_length=5)
    invoice_reference = models.CharField(max_length=30)
    payment_date = models.DateField()
    deb_cred = models.CharField(max_length=5, null=True)

    def __str__(self):
        return_value = f"ID:{self.id}, Document date: {self.document_date}, Customer number: {self.customer_number}"
        return return_value


class Ke24ImportLine(models.Model):
    currency = models.CharField(max_length=3, null=True) 
    currency_type = models.CharField(max_length=3, null=True) 
    record_type = models.CharField(max_length=2, null=True) 
    year_month = models.CharField(max_length=7, null=True) 
    document_number = models.CharField(max_length=20, null=True) 
    item_number = models.CharField(max_length=20, null=True) 
    created_on = models.DateField(null=True) 
    reference_document = models.CharField(max_length=10, null=True) 
    referenceitem_no = models.CharField(max_length=6, null=True) 
    created_by = models.CharField(max_length=10, null=True) 
    company_code = models.CharField(max_length=4, null=True) 
    sender_cost_center = models.CharField(max_length=20, null=True) 
    cost_element = models.CharField(max_length=20, null=True) 
    currency_key = models.CharField(max_length=3, null=True) 
    sales_quantity = models.FloatField(null=True) 
    unit_sales_quantity = models.CharField(max_length=4, null=True) 
    year_week = models.CharField(max_length=10, null=True) 
    product = models.CharField(max_length=30, null=True) 
    industry_code_1 = models.CharField(max_length=4, null=True) 
    industry = models.CharField(max_length=4, null=True) 
    posting_date = models.DateField(null=True) 
    sales_district = models.CharField(max_length=6, null=True) 
    reference_org_unit = models.CharField(max_length=10, null=True) 
    log_system_source = models.CharField(max_length=10, null=True) 
    reference_transaction = models.CharField(max_length=6, null=True) 
    point_of_valuation = models.CharField(max_length=10, null=True) 
    revenue = models.FloatField(null=True) 
    invoice_date = models.DateField(null=True) 
    billing_type = models.CharField(max_length=10, null=True) 
    year = models.IntegerField(null=True) 
    business_area = models.CharField(max_length=10, null=True) 
    customer_Hierarchy_01 = models.CharField(max_length=5, null=True) 
    customer_hierarchy_02 = models.CharField(max_length=5, null=True) 
    customer_hierarchy_03 = models.CharField(max_length=5, null=True) 
    customer_hierarchy_04 = models.CharField(max_length=5, null=True) 
    customer_hierarchy_05 = models.CharField(max_length=5, null=True) 
    origin = models.CharField(max_length=10, null=True) 
    hierarchy_assignment = models.IntegerField(null=True) 
    annual_rebates = models.FloatField(null=True) 
    sales_order = models.CharField(max_length=20, null=True)
    customer_group = models.CharField(max_length=5, null=True) 
    sales_order_item = models.IntegerField(null=True) 
    customer = models.CharField(max_length=10, null=True) 
    controlling_area = models.CharField(max_length=3, null=True) 
    price_group = models.CharField(max_length=2, blank=True, null=True) 
    material_pricing_group = models.CharField(max_length=4, null=True) 
    cost_object = models.CharField(max_length=10, null=True) 
    customer_account_assignment_group = models.CharField(max_length=2, null=True) 
    ship_to_party = models.CharField(max_length=10, null=True) 
    exchange_rate = models.FloatField(null=True) 
    country = models.CharField(max_length=2, null=True) 
    client = models.CharField(max_length=3, null=True) 
    material_group = models.CharField(max_length=4, null=True) 
    quantityDiscount = models.FloatField(null=True) 
    market_segment = models.CharField(max_length=3, null=True) 
    color = models.CharField(max_length=3, null=True) 
    major_label = models.CharField(max_length=3, null=True) 
    brand_name = models.CharField(max_length=3, null=True) 
    color_group = models.CharField(max_length=5, null=True) 
    profitability_segment_no = models.CharField(max_length=10, null=True) 
    partner_prof_segment = models.CharField(max_length=5, null=True) 
    part_sub_number = models.CharField(max_length=1, null=True) 
    sub_number = models.CharField(max_length=1, null=True) 
    period = models.IntegerField(null=True) 
    plan_act_indicator = models.IntegerField(null=True) 
    partner_profit_center = models.CharField(max_length=4, null=True) 
    dye_ink = models.CharField(max_length=5, null=True) 
    profit_center = models.CharField(max_length=5, null=True) 
    product_hierarchy = models.CharField(max_length=12, null=True) 
    sender_business_process = models.CharField(max_length=5, null=True) 
    WBS_element = models.CharField(max_length=5, null=True) 
    currency_of_record = models.CharField(max_length=3, null=True) 
    order = models.CharField(max_length=12, null=True) 
    update_status = models.CharField(max_length=5, null=True) 
    division = models.CharField(max_length=2, null=True) 
    canceled_document = models.CharField(max_length=10, null=True) 
    canceled_document_item = models.CharField(max_length=5, null=True) 
    time_created = models.CharField(max_length=20, null=True) 
    date = models.DateField(null=True)
    time = models.TimeField(null=True)
    version = models.CharField(max_length=5, null=True) 
    sales_org = models.CharField(max_length=4, null=True) 
    sales_employee = models.CharField(max_length=3, null=True) 
    distribution_channel = models.CharField(max_length=2, null=True) 
    cost_of_sales = models.FloatField(null=True) 
    inplant_depreciation = models.FloatField(null=True) 
    freight_charges = models.FloatField(null=True) 
    mts_input_var = models.FloatField(null=True) 
    mts_input_priveVar = models.FloatField(null=True) 
    mts_lotsize_var = models.FloatField(null=True) 
    mto_fix_freight_cost = models.FloatField(null=True) 
    mto_fix_material_cost = models.FloatField(null=True) 
    mto_variable_material_cost = models.FloatField(null=True) 
    mto_fix_overhead_cost = models.FloatField(null=True) 
    mto_variable_overhead_cost = models.FloatField(null=True) 
    mto_fix_production_cost = models.FloatField(null=True) 
    mts_output_price_var = models.FloatField(null=True) 
    mto_variable_production_cost = models.FloatField(null=True) 
    inplant_other_expenses = models.FloatField(null=True) 
    inplant_payroll = models.FloatField(null=True) 
    mts_quantity_var = models.FloatField(null=True) 
    mts_remaining_var = models.FloatField(null=True) 
    mts_res_usage_var = models.FloatField(null=True) 
    mts_fix_freight_cost = models.FloatField(null=True) 
    mts_fix_material_cost = models.FloatField(null=True) 
    mts_variable_material_cost = models.FloatField(null=True) 
    mts_fix_overhead_cost = models.FloatField(null=True) 
    mts_varialble_overhead_cost = models.FloatField(null=True) 
    mts_fix_production_cost = models.FloatField(null=True) 
    mts_variable_production_cost = models.FloatField(null=True) 
    goods_issue_date = models.DateField(null=True) 
    plant = models.CharField(max_length=4, null=True) 
    national_account_manager = models.CharField(max_length=10, null=True) 
    product_line = models.CharField(max_length=2, null=True) 
    vp_sales = models.CharField(max_length=4, null=True) 
    product_line_sales_manager = models.CharField(max_length=4, null=True) 
    field_sales_manager = models.CharField(max_length=4, null=True)
    import_timestamp = models.DateTimeField(auto_now_add=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)


class Ke24Line(models.Model):
    currency = models.CharField(max_length=3, null=True) 
    currency_type = models.CharField(max_length=3, null=True) 
    record_type = models.CharField(max_length=2, null=True) 
    year_month = models.CharField(max_length=7, null=True) 
    document_number = models.CharField(max_length=20, null=True) 
    item_number = models.CharField(max_length=20, null=True) 
    created_on = models.DateField(null=True) 
    reference_document = models.CharField(max_length=10, null=True) 
    referenceitem_no = models.CharField(max_length=6, null=True) 
    created_by = models.CharField(max_length=10, null=True) 
    company_code = models.CharField(max_length=4, null=True) 
    sender_cost_center = models.CharField(max_length=20, null=True) 
    cost_element = models.CharField(max_length=20, null=True) 
    currency_key = models.CharField(max_length=3, null=True) 
    sales_quantity = models.FloatField(null=True) 
    unit_sales_quantity = models.CharField(max_length=4, null=True) 
    year_week = models.CharField(max_length=10, null=True) 
    product = models.CharField(max_length=30, null=True) 
    industry_code_1 = models.CharField(max_length=40, null=True) 
    industry = models.CharField(max_length=4, null=True) 
    posting_date = models.DateField(null=True) 
    sales_district = models.CharField(max_length=6, null=True) 
    reference_org_unit = models.CharField(max_length=10, null=True) 
    log_system_source = models.CharField(max_length=10, null=True) 
    reference_transaction = models.CharField(max_length=6, null=True) 
    point_of_valuation = models.CharField(max_length=10, null=True) 
    revenue = models.FloatField(null=True) 
    invoice_date = models.DateField(null=True) 
    billing_type = models.CharField(max_length=10, null=True) 
    year = models.IntegerField(null=True) 
    business_area = models.CharField(max_length=10, null=True) 
    customer_Hierarchy_01 = models.CharField(max_length=5, null=True) 
    customer_hierarchy_02 = models.CharField(max_length=5, null=True) 
    customer_hierarchy_03 = models.CharField(max_length=5, null=True) 
    customer_hierarchy_04 = models.CharField(max_length=5, null=True) 
    customer_hierarchy_05 = models.CharField(max_length=5, null=True) 
    origin = models.CharField(max_length=10, null=True) 
    hierarchy_assignment = models.IntegerField(null=True) 
    annual_rebates = models.FloatField(null=True) 
    sales_order = models.CharField(max_length=20, null=True)
    customer_group = models.CharField(max_length=5, null=True) 
    sales_order_item = models.IntegerField(null=True) 
    customer = models.CharField(max_length=10, null=True) 
    controlling_area = models.CharField(max_length=3, null=True) 
    price_group = models.CharField(max_length=20, null=True) 
    material_pricing_group = models.CharField(max_length=4, null=True) 
    cost_object = models.CharField(max_length=10, null=True) 
    customer_account_assignment_group = models.CharField(max_length=2, null=True) 
    ship_to_party = models.CharField(max_length=10, null=True) 
    exchange_rate = models.FloatField(null=True) 
    country = models.CharField(max_length=2, null=True) 
    client = models.CharField(max_length=3, null=True) 
    material_group = models.CharField(max_length=4, null=True) 
    quantityDiscount = models.FloatField(null=True) 
    market_segment = models.CharField(max_length=3, null=True) 
    color = models.CharField(max_length=3, null=True) 
    major_label = models.CharField(max_length=3, null=True) 
    brand_name = models.CharField(max_length=3, null=True) 
    color_group = models.CharField(max_length=5, null=True) 
    profitability_segment_no = models.CharField(max_length=10, null=True) 
    partner_prof_segment = models.CharField(max_length=5, null=True) 
    part_sub_number = models.CharField(max_length=1, null=True) 
    sub_number = models.CharField(max_length=1, null=True) 
    period = models.IntegerField(null=True) 
    plan_act_indicator = models.IntegerField(null=True) 
    partner_profit_center = models.CharField(max_length=4, null=True) 
    dye_ink = models.CharField(max_length=5, null=True) 
    profit_center = models.CharField(max_length=5, null=True) 
    product_hierarchy = models.CharField(max_length=12, null=True) 
    sender_business_process = models.CharField(max_length=5, null=True) 
    WBS_element = models.CharField(max_length=5, null=True) 
    currency_of_record = models.CharField(max_length=3, null=True) 
    order = models.CharField(max_length=12, null=True) 
    update_status = models.CharField(max_length=5, null=True) 
    division = models.CharField(max_length=2, null=True) 
    canceled_document = models.CharField(max_length=10, null=True) 
    canceled_document_item = models.CharField(max_length=5, null=True) 
    time_created = models.CharField(max_length=20, null=True) 
    # date = models.DateTimeField(null=True)
    date = models.DateField(null=True)
    time = models.TimeField(null=True)
    version = models.CharField(max_length=5, null=True) 
    sales_org = models.CharField(max_length=4, null=True) 
    sales_employee = models.CharField(max_length=3, null=True) 
    distribution_channel = models.CharField(max_length=2, null=True) 
    cost_of_sales = models.FloatField(null=True) 
    inplant_depreciation = models.FloatField(null=True) 
    freight_charges = models.FloatField(null=True) 
    mts_input_var = models.FloatField(null=True) 
    mts_input_priveVar = models.FloatField(null=True) 
    mts_lotsize_var = models.FloatField(null=True) 
    mto_fix_freight_cost = models.FloatField(null=True) 
    mto_fix_material_cost = models.FloatField(null=True) 
    mto_variable_material_cost = models.FloatField(null=True) 
    mto_fix_overhead_cost = models.FloatField(null=True) 
    mto_variable_overhead_cost = models.FloatField(null=True) 
    mto_fix_production_cost = models.FloatField(null=True) 
    mts_output_price_var = models.FloatField(null=True) 
    mto_variable_production_cost = models.FloatField(null=True) 
    inplant_other_expenses = models.FloatField(null=True) 
    inplant_payroll = models.FloatField(null=True) 
    mts_quantity_var = models.FloatField(null=True) 
    mts_remaining_var = models.FloatField(null=True) 
    mts_res_usage_var = models.FloatField(null=True) 
    mts_fix_freight_cost = models.FloatField(null=True) 
    mts_fix_material_cost = models.FloatField(null=True) 
    mts_variable_material_cost = models.FloatField(null=True) 
    mts_fix_overhead_cost = models.FloatField(null=True) 
    mts_varialble_overhead_cost = models.FloatField(null=True) 
    mts_fix_production_cost = models.FloatField(null=True) 
    mts_variable_production_cost = models.FloatField(null=True) 
    goods_issue_date = models.DateField(null=True) 
    plant = models.CharField(max_length=4, null=True) 
    national_account_manager = models.CharField(max_length=10, null=True) 
    product_line = models.CharField(max_length=2, null=True) 
    vp_sales = models.CharField(max_length=4, null=True) 
    product_line_sales_manager = models.CharField(max_length=4, null=True) 
    field_sales_manager = models.CharField(max_length=4, null=True)
    import_timestamp = models.DateTimeField(auto_now_add=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)


class ZAQCODMI9_line(models.Model):
    billing_date = models.DateField() 
    material = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    sold_to = models.FloatField() 
    name = models.CharField(max_length=255)
    billing_doc = models.FloatField() 
    invoice_qty = models.FloatField() 
    UoM = models.CharField(max_length=10)
    unit_price = models.FloatField() 
    invoice_sales = models.FloatField() 
    curr = models.CharField(max_length=3)
    batch = models.CharField(max_length=30)
    gm_perc = models.FloatField() 
    prof = models.FloatField() 
    ptrm = models.CharField(max_length=5)
    curr_1 = models.CharField(max_length=3)
    cost = models.FloatField() 
    can = models.CharField(max_length=10)
    bill = models.CharField(max_length=5)
    item = models.CharField(max_length=5)
    tax_amount = models.CharField(max_length=20)
    curr_2 = models.CharField(max_length=3)
    dv = models.CharField(max_length=5)
    shpt = models.FloatField() 
    sales_doc = models.CharField(max_length=20)
    import_date = models.CharField(max_length=25)


class ZAQCODMI9_import_line(models.Model):
    billing_date = models.DateField() 
    material = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    sold_to = models.FloatField() 
    name = models.CharField(max_length=255)
    billing_doc = models.FloatField() 
    invoice_qty = models.FloatField() 
    UoM = models.CharField(max_length=10)
    unit_price = models.FloatField() 
    invoice_sales = models.FloatField() 
    curr = models.CharField(max_length=3)
    batch = models.CharField(max_length=30)
    gm_perc = models.FloatField() 
    prof = models.FloatField() 
    ptrm = models.CharField(max_length=5)
    curr_1 = models.CharField(max_length=3)
    cost = models.FloatField() 
    can = models.CharField(max_length=10)
    bill = models.CharField(max_length=5)
    item = models.CharField(max_length=5)
    tax_amount = models.CharField(max_length=20)
    curr_2 = models.CharField(max_length=3)
    dv = models.CharField(max_length=5)
    shpt = models.FloatField() 
    sales_doc = models.CharField(max_length=20)
    import_date = models.DateTimeField(auto_now_add=True, null=True)
    import_timestamp = models.DateTimeField(auto_now_add=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)


class Ke30Line(models.Model):
    currency = models.CharField(max_length=3, null=True)
    month = models.CharField(max_length=2, null=True)
    year = models.CharField(max_length=4, null=True)
    year_month = models.CharField(max_length=6, null=True)
    fake_date = models.DateField(null=True)
    customer_number = models.CharField(max_length=20, null=True)
    customer_name = models.CharField(max_length=200, null=True)
    sap_country = models.CharField(max_length=255, null=True)
    sap_sales_district = models.CharField(max_length=255, null=True)
    sap_sales_employee = models.CharField(max_length=100, null=True)
    customer_account_group = models.CharField(max_length=40, null=True)
    ship_to_party_number = models.CharField(max_length=20, null=True)
    ship_to_party_name = models.CharField(max_length=255, null=True)
    product_number = models.CharField(max_length=100, null=True)
    product_name = models.CharField(max_length=255, null=True)
    sap_brand = models.CharField(max_length=255, null=True)
    sap_major_label = models.CharField(max_length=255, null=True)
    sap_division = models.CharField(max_length=255, null=True)
    sap_material_group = models.CharField(max_length=255, null=True)
    sap_market_segment = models.CharField(max_length=255, null=True)
    sap_industry = models.CharField(max_length=255, null=True)
    sap_color = models.CharField(max_length=255, null=True)
    sap_product_line = models.CharField(max_length=255, null=True)
    sap_profit_center = models.CharField(max_length=50, null=True)
    sap_UOM = models.CharField(max_length=10, null=True)
    quantity = models.FloatField(null=True)
    unit_sales_quantity = models.CharField(max_length=255, null=True)
    net_sales = models.FloatField(null=True)
    rebates = models.FloatField(null=True)
    gross_sales = models.FloatField(null=True)
    rmc_costs = models.FloatField(null=True)
    conversion_costs = models.FloatField(null=True)
    other_costs = models.FloatField(null=True)
    total_costs = models.FloatField(null=True)
    gross_margin = models.FloatField(null=True)
    gross_margin_perc = models.FloatField(null=True)
    margin_perc_actual = models.FloatField(null=True)
    contribution_margin_actual = models.FloatField(null=True)
    contribution_margin_perc_actual = models.FloatField(null=True)
    net_sales_unit_actual = models.FloatField(null=True)
    cost_unit_actual = models.FloatField(null=True)
    disc_claim_adj_actual = models.FloatField(null=True)
    import_timestamp = models.DateTimeField(auto_now_add=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return self.id


class Ke30ImportLine(models.Model):
    period_year = models.CharField(max_length=20)
    period_year_1 = models.CharField(max_length=255)
    customer = models.CharField(max_length=255) 
    sales_qty_actual = models.FloatField()
    field_sales_manager = models.CharField(max_length=255)
    field_sales_mgr_1 = models.CharField(max_length=255)
    customer_1 = models.CharField(max_length=255) 
    product = models.CharField(max_length=255) 
    product_1 = models.CharField(max_length=255) 
    unit_sales_quantity = models.CharField(max_length=255) 
    net_sales_actual = models.FloatField()
    rebate_actual = models.FloatField()
    gross_sales_actual = models.FloatField()
    rmc_actual = models.FloatField()
    conversion_actual = models.FloatField()
    other_cost_actual = models.FloatField()
    total_cost_actual = models.FloatField()
    gross_margin_actual = models.FloatField()
    margin_perc_actual = models.FloatField()
    contribution_margin_actual = models.FloatField()
    contribution_margin_perc_actual = models.FloatField()
    net_sales_unit_actual = models.FloatField()
    cost_unit_actual = models.FloatField()
    customer_hierarchy_01 = models.CharField(max_length=255)
    customer_hier_01 = models.CharField(max_length=255)
    disc_claim_adj_actual = models.FloatField()
    material_group = models.CharField(max_length=255)
    material_group_1 = models.CharField(max_length=255)
    product_hierarchy = models.CharField(max_length=255)
    prod_hierarchy = models.CharField(max_length=255)
    color = models.CharField(max_length=255)
    color_1 = models.CharField(max_length=255)
    product_line = models.CharField(max_length=255)
    product_line_1 = models.CharField(max_length=255)
    vp_sales = models.CharField(max_length=255)
    cust_acct_Assg_group = models.CharField(max_length=255)
    cust_acct_Assg_grp = models.CharField(max_length=255)
    profit_center = models.CharField(max_length=255)
    profit_center_1 = models.CharField(max_length=255)
    currency = models.CharField(max_length=255)
    unit_of_measure = models.CharField(max_length=255)
    market_segment = models.CharField(max_length=255)
    market_segment_1 = models.CharField(max_length=255)
    major_label = models.CharField(max_length=255)
    major_label_1 = models.CharField(max_length=255)
    national_account_manager = models.CharField(max_length=255)
    national_account_manager_1 = models.CharField(max_length=255)
    fiscal_year = models.CharField(max_length=255)
    fiscal_year_1 = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    country_1 = models.CharField(max_length=255)
    sales_employee = models.CharField(max_length=255)
    sales_employee_1 = models.CharField(max_length=255)
    sales_district = models.CharField(max_length=255)
    sales_district_1 = models.CharField(max_length=255)
    color_group = models.CharField(max_length=255)
    color_group_1 = models.CharField(max_length=255)
    material_pricing_grp = models.CharField(max_length=255)
    mat_pricing_grp = models.CharField(max_length=255)
    price_group = models.CharField(max_length=255)
    price_group_1 = models.CharField(max_length=255)
    industry = models.CharField(max_length=255)
    industry_1 = models.CharField(max_length=255)
    brand_name = models.CharField(max_length=255)
    brand_name_1 = models.CharField(max_length=255)
    period = models.CharField(max_length=255)
    period_1 = models.CharField(max_length=255)
    division = models.CharField(max_length=255)
    division_1 = models.CharField(max_length=255)
    ship_to_party = models.CharField(max_length=255)
    ship_to_party_1 = models.CharField(max_length=255)
    import_timestamp = models.DateTimeField(auto_now_add=True, null=True)
    year_month = models.IntegerField()
    owner = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
    
    def __str__(self):
        string_to_return = f"{self.year_month} {self.customer} {self.product} qty:{self.sales_qty_actual}"
        return string_to_return


class Order(models.Model):
    customer_number = models.FloatField(null=True)
    customer_name = models.CharField(max_length=100)
    ship_to = models.FloatField(null=True)
    country = models.CharField(max_length=10)
    plant = models.CharField(max_length=8)
    sales_order_number = models.CharField(max_length=50)
    store_location =models.CharField(max_length=5)
    item_line_number = models.IntegerField(default=0)
    order_type = models.CharField(max_length=8)
    sales_order_date = models.DateField(null=True)
    requested_date = models.DateField(null=True)
    partial_shipment_date = models.DateField(null=True)
    days_late = models.IntegerField(null=True)
    product_number = models.CharField(max_length=20)
    product_name = models.CharField(max_length=100)
    qty_ordered = models.IntegerField(null=True)
    qty_ordered_unit = models.CharField(max_length=4)
    qty_open = models.IntegerField(null=True)
    qty_open_unit =  models.CharField(max_length=4)
    qty_partial_shipped = models.IntegerField(null=True)
    qty_partial_shipped_unit = models.CharField(max_length=4)
    customer_po_number = models.CharField(max_length=60)
    lead_time = models.IntegerField(null=True)
    import_date = models.DateField(null=True)
    line_type = models.CharField(max_length=20)
    delivery_number = models.IntegerField(null=True)
    delivery_date = models.DateField(null=True)
    invoice_number = models.IntegerField(null=True)
    invoice_date = models.DateField(null=True)
    document_currency = models.CharField(max_length=20)
    qty_invoiced = models.IntegerField(null=True)
    qty_invoiced_unit = models.CharField(max_length=4)
    value_invoiced = models.FloatField(null=True)
    import_timestamp = models.DateTimeField(auto_now_add=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self) -> str:
        return_tring = self.invoice_number or "" + " " + self.customer_name or ""
        return return_tring

# -----------------------------------------------------
# Models with Foreign Keys
# -----------------------------------------------------

class Color(models.Model):
    name = models.CharField(max_length=30)
    color_weight = models.IntegerField(default=0, null=True)
    hex_value = models.CharField(max_length=7, null=True)
    name_short = models.CharField(max_length=3, null=True)
    color_number = models.CharField(max_length=10, null=True)
    color_group = models.ForeignKey(ColorGroup, on_delete=models.PROTECT) # PROTECT avoid deletion if there are refrenced object
    sqlapp_id = models.IntegerField(default=0, null=True)

    def __str__(self):
        return_value = f"{self.name}"
        return return_value


class Brand(models.Model):
    name = models.CharField(max_length=50)
    sap_name = models.CharField(max_length=30, null=True, blank=True)
    sap_id = models.CharField(max_length=10, null=True, blank=True)
    no_budget = models.BooleanField(default=False)
    has_colors = models.BooleanField(default=False)
    division = models.ForeignKey(Division, on_delete=models.PROTECT)
    major_label = models.ForeignKey(MajorLabel, on_delete=models.PROTECT)
    ink_technology = models.ForeignKey(InkTechnology, on_delete=models.PROTECT)
    nsf_division = models.ForeignKey(NSFDivision, on_delete=models.PROTECT)
    market_segment = models.ForeignKey(MarketSegment, on_delete=models.PROTECT)
    material_group = models.ForeignKey(MaterialGroup, on_delete=models.PROTECT)
    sqlapp_id = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=100)
    number = models.CharField(max_length=30)
    is_ink = models.BooleanField(default = True)
    import_note = models.CharField(max_length=255, null=True, blank=True)
    import_status = models.CharField(max_length=255, null=True, blank=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, null=True, blank=True)
    made_in = models.ForeignKey(MadeIn, on_delete=models.PROTECT, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, null=True, blank=True)
    packaging = models.ForeignKey(Packaging, on_delete=models.PROTECT, null=True, blank=True)
    product_line = models.ForeignKey(ProductLine, on_delete=models.PROTECT, null=True, blank=True)
    product_status = models.ForeignKey(ProductStatus, on_delete=models.PROTECT, null=True, blank=True)
    sqlapp_id = models.IntegerField(default=0, null=True)
    is_new = models.BooleanField(default=True)
    approved_on = models.DateField(null=True)
    approved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return_value = f"{self.number}, {self.name}"
        return return_value


class RateToLT(models.Model):
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    packaging = models.ForeignKey(Packaging, on_delete=models.PROTECT)
    rate_to_lt = models.FloatField()
    sqlapp_id = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.uom + self.packaging


class ShippingPolicy(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)


class Customer(models.Model):
    class Meta:
        ordering = ['name']

    number = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=10, null=True, blank=True)
    active = models.BooleanField(default=False, null=True)
    insurance = models.BooleanField(default=False, null=True)
    insurance_value = models.IntegerField(null=True, blank=True, default=0)
    credit_limit = models.IntegerField(null=True, blank=True, default=0)
    vat = models.CharField(max_length=30, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    approved_by_old = models.CharField(max_length=255, null=True, blank=True)
    approved_on =  models.DateTimeField(auto_now_add=True, null=True)
    import_note = models.CharField(max_length=255, null=True, blank=True)
    import_status = models.CharField(max_length=255, null=True, blank=True)
    sqlapp_id = models.IntegerField(default=0, null=True, blank=True)
    sales_employee = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sales_manager', null=True)
    customer_type = models.ForeignKey(CustomerType, on_delete=models.PROTECT, blank=True, null=True)
    industry = models.ForeignKey(Industry, on_delete=models.PROTECT, blank=True, null=True)
    country = models.ForeignKey(CountryCode, on_delete=models.PROTECT, null=True)
    is_new = models.BooleanField(default=True)
    approved_on = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='approved_by', blank=True, null=True)
    customer_service_rep = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_policy = models.ForeignKey(ShippingPolicy, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return_value = f"{self.name}"
        return return_value


class ShippingAddress(models.Model):
    name = models.CharField(max_length=250, null=True)
    street_name = models.CharField(max_length=250, null=True)
    street_number = models.CharField(max_length=250, null=True)
    zip_code = models.CharField(max_length=250, null=True)
    city = models.CharField(max_length=250, null=True)
    country = models.ForeignKey(CountryCode, on_delete=models.SET_NULL,null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)


class CustomerNote(models.Model):
    note = models.TextField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    note_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_by_notes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='updated_by_notes',null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.customer.name} - {self.created_at} - {self.note}"


class BudForLine(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT)
    color_group = models.ForeignKey(ColorGroup, on_delete=models.PROTECT)
    sqlapp_id = models.IntegerField(default=0, null=True)


class BudForNote(models.Model):
    note = models.CharField(max_length=255)
    note_date = models.DateTimeField(auto_now=True)
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT)
    bud_for_id = models.ForeignKey(BudForLine, on_delete=models.PROTECT)
    sqlapp_id = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.note
    

class BudForDetailLine(models.Model):
    volume = models.IntegerField(null=True, default=0)
    price = models.FloatField(null=True, default=0)
    value = models.IntegerField(null=True, default=0)
    budforline = models.ForeignKey(BudForLine, on_delete=models.PROTECT)
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT)
    year = models.IntegerField()
    month = models.IntegerField(default=0)
    currency_zaq = models.CharField(max_length=3)
    detail_date = models.DateField(default='2024-01-01')
    sqlapp_id = models.IntegerField(default=0, null=True)
    
    def __str__(self):
        return_string = f"BudForDetail line - bud_for_id:{self.budforline.id} - scenario: {self.scenario.id}"
        return return_string


class BudForDetail_Abstract(models.Model):
    '''
    This is an abstract class and can be used to create other models that will inherit
    all fields
    '''
    budforline = models.ForeignKey(BudForLine, on_delete=models.PROTECT)
    scenario = models.ForeignKey(Scenario, on_delete= models.PROTECT)
    year = models.IntegerField(null=True, default=0)
    month = models.IntegerField(null=True, default=0)
    volume = models.IntegerField(null=True, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value = models.IntegerField(null=True, default=0)
    currency_zaq = models.CharField(max_length=3)
    detail_date = models.DateField(default='2024-01-01')
    sqlapp_id = models.IntegerField(default=0, null=True)

    class Meta:
        abstract = True
        
    
class BudgetForecastDetail(BudForDetail_Abstract):
    class Meta:
        verbose_name = 'Budget Forecast Detail'
        verbose_name_plural = 'Budget Forecast Details'

    def __str__(self):
        return_string = f"BudgetForcastDetail line - bud_for_id:{self.budforline.id} - scenario: {self.scenario.id}"
        return return_string


class BudgetForecastDetail_sales(BudForDetail_Abstract):
    class Meta:
        verbose_name = 'Budget Forecast, Sales'
        verbose_name_plural = 'Budget Forcast, Sales'

    def __str__(self):
        return_string = f"BudgetForcastDetail_sales line - bud_for_id:{self.budforline.id} - scenario: {self.scenario.id}"
        return return_string


class Price(models.Model):
    sales_org = models.CharField(max_length=10, null=True)
    customer_number = models.CharField(max_length=10, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True)
    product_number = models.CharField(max_length=10, blank=True, null=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True)
    price = models.FloatField(default=0)
    per = models.IntegerField(default=0)
    UoM = models.CharField(max_length=10)
    volume_from = models.IntegerField(default=0)
    volume_to = models.IntegerField(default=0)
    valid_from = models.DateField()
    valid_to = models.DateField()
    currency = models.CharField(max_length=5)
    import_timestamp = models.DateTimeField(auto_now_add=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True)


class UploadedFile(models.Model):
    STATUS_CHOICES = (
        ('NEW', 'new'),
        ('PROCESSING', 'processing'),
        ('PROCESSED', 'processed'),
        ('ERROR', 'error'),
    )
    file_name = models.CharField(max_length=255, blank=True)
    file_path = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=20, blank=True)
    file_color = models.CharField(max_length=20, null=True, default='blue')
    created_at = models.DateTimeField(auto_now=True, null=True)
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(blank=True, null=True)
    process_status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='NEW')
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    log = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        value = self.file_path + self.file_name + ' ' + self.owner.email + ' ' + self.created_at.strftime("%Y/%m/%d, %H:%M:%S")
        return value

    
    def process_chunk(self, chunk, model, field_mapping, index, no_of_chunks):
        apps.ready()
        print (f'Prcessing of chunk {index}/{no_of_chunks} started ...')
        for index, row in chunk.iterrows():
            instance = model()
            for field, column_name in field_mapping.items():
                setattr(instance, field, row[column_name])
            instance.save()


    def start_processing(self):
        file_path = self.file_path + "/" + self.file_name
        if not os.path.exists(file_path):
            # The file does not exists
            log_message = f"The file {file_path} is not existing, marking the UploadedFile record as is_processed=True"
            print(log_message)
            yield log_message
            self.is_processed = True
            self.save()
        else:
            django.setup()
            match self.file_type:
                case "ke30":
                    convert_dict = import_dictionaries.ke30_converters_dict
                    log_message = "start reading the Excel file"
                    print(log_message)
                    yield log_message
                    df = self.read_excel_file(file_path, convert_dict)
                    log_message = "completed reading the Excel file"
                    print(log_message)
                    yield log_message
                    df_length = len(df)
                    df['Importtimestamp'] = datetime.now()
                    df["YearMonth"] = (df['Fiscal Year'].astype(int) * 100 + df['Period'].astype(int)).astype(str)
                    # These 2 variable are set for the following action, after the match-case
                    model = Ke30ImportLine
                    field_mapping = import_dictionaries.ke30_mapping_dict
                case "ke24":
                    convert_dict = import_dictionaries.ke24_converters_dict
                    df = self.read_excel_file(file_path, convert_dict)
                    df = df.drop(columns=['Industry Code 1'])
                    # df['Industry Code 1'] = df['Industry Code 1'].astype(str)               
                    model = Ke24ImportLine
                    field_mapping = import_dictionaries.ke24_mapping_dict
                case "zaq":
                    convert_dict = import_dictionaries.zaq_converters_dict
                    df = self.read_excel_file(file_path, convert_dict)
                    df["Billing date"] = df['Billing date'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
                    # This Excel file has the totals,at teh bottom, that must be removed
                    # The number of rows may vary depending on the number of currencies and UoMs mentioned
                    unique_uom = df['UoM'].nunique()
                    unique_curr = df['Curr.'].nunique()
                    rows_to_remove = max(unique_curr, unique_uom)
                    df = df.head(len(df) - rows_to_remove) 
                    model = ZACODMI9_import_line
                    field_mapping = import_dictionaries.zaq_mapping_dict
                case "oo":
                    convert_dict = import_dictionaries.oo_converters_dict
                    df = self.read_excel_file(file_path, convert_dict)
                    # Setting these records as "Open Orders"
                    df['LineType'] = 'OO'
                    # Trimming the bottom
                    print(f"it was {len(df)}")
                    uniques = len(df['Unit'].value_counts())
                    df = df.iloc[:-uniques]
                    print(f"it is {len(df)}")
                    # Filtering out rows where Plant is null
                    df = df[df["Plant"].notnull()]
                    # Adjusting dates
                    df["Order Date"] = df['Order Date'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
                    df["Req. dt"] = df['Req. dt'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
                    df["PL. GI Dt"] = df['PL. GI Dt'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
                    # sometimes Customer number is null - assign a value
                    df['Sold-to'] = df['Sold-to'].fillna(df['Ship-to'])
                    df['Sold-to'] = np.where(df['Sold-to'] == '', df['Ship-to'], df['Sold-to'])
                    model = Order
                    field_mapping = import_dictionaries.oo_mapping_dict
                case "oi" | "arr":
                    convert_dict = import_dictionaries.oo_converters_dict
                    df = self.read_excel_file(file_path, convert_dict)
                    # Removing bottom lines
                    print(f"{self.file_type} was {len(df)} lines long")
                    uniques = len(df['Document currency'].value_counts())
                    df = df.iloc[:-uniques]
                    print(f"{self.file_type} is now {len(df)} lines long")
                    # Adjusting dates
                    df['Document Date'] = df['Document Date'].dt.date
                    df['Net due date'] = df['Net due date'].dt.date
                    df['Payment date'] = df['Payment date'].dt.date
                    df['Arrears after net due date'] = df['Arrears after net due date'].fillna(0).astype(int)
                    if self.file_type == "arr":
                        model = Fbl5nArrImport
                        field_mapping = import_dictionaries.arr_mapping_dict
                    if self.file_type == "oi":
                        model = Fbl5nOpenImport
                        field_mapping = import_dictionaries.oi_mapping_dict
                case "pr":
                    convert_dict = import_dictionaries.pr_converters_dict
                    df = self.read_excel_file(file_path)
                    model = Price
                    field_mapping = import_dictionaries.pr_mapping_dict

            start_time = time.perf_counter()
            model.objects.all().delete()
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            log_message = f"deletion {model._meta.model_name} took {elapsed_time} seconds"
            print(log_message)
            yield log_message

            # check how long is the dataframe
            df_length = len(df)
            df = df.replace(np.nan, '')
            chunk_size = 150
            chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

            log_message = f"Chunk size {chunk_size}"
            print(log_message)
            yield log_message
            log_message = f"based on chnuck_size we got {len(chunks)} chunks for {df_length} rows"
            print(log_message)
            yield log_message

            chunk_counter = 0
            for chunk in chunks:
                chunk_counter += 1
                log_message = f"processing {chunk_counter}/{len(chunks)}"
                print(log_message)
                yield log_message
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
                        instances = []
                    end_time = time.perf_counter()
                    elapsed_time = end_time - start_time
                    log_message = f" ... work on chunk {chunk_counter} of {len(chunks)} took {elapsed_time} seconds"
                    print(log_message)
                    yield log_message
                    self.is_processed = True
                    self.processed_at = datetime.now()
                except Exception as e:
                    # Handle the exception
                    log_message = f"An error occurred during the transaction: {e}"
                    print(log_message)
                    yield log_message
            # Delete the file
            self.delete_file()
            log_message = f'process terminated for file id: {self.id}  filetye: {self.file_type} file_name: {self.file_name} file_path: {self.file_path}'
            print(log_message)
            yield log_message
            print (f'processed the file id: {self.id}  filetye: {self.file_type} file_name: {self.file_name} file_path: {self.file_path}')
            print("processing terminated in the model")


    def delete_file_soft(self):
        full_file_name = os.path.join(settings.MEDIA_ROOT, self.file_path, self.file_name)
        if os.path.exists(full_file_name):
            os.remove(full_file_name)
            self.is_processed = True
            self.save()
            return True
        else:
            return False


    def delete_file(self):
        full_file_name = os.path.join(settings.MEDIA_ROOT, self.file_path, self.file_name)
        now =  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if os.path.exists(full_file_name):
            os.remove(full_file_name)
            # Mark as is_processed=True
            self.is_processed = True
            self.save()
        else:
            self.log = f"On {now} this file was asked for deletion, but the file was not there, therefore we set the is_processed property as True, so it won't show up in the list of files to be processed"
            self.is_processed = True
            self.save()

            
        
    def read_excel_file(self, file_path, conversion_dict):
        df = pd.read_excel(file_path, thousands='.', decimal=',', dtype=conversion_dict, parse_dates=True)
        df = df.replace(np.nan, '')
        return df


class UploadedFileLog(models.Model):
    class Meta:
        ordering = ['-date']

    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    file_path = models.FilePathField(path=settings.MEDIA_ROOT, match=r'.*\.(xlsx|XLSX)$', validators=[xls_xlsx_file_validator], null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)
    log_text = models.TextField(null=True, blank=True)


class Contact(models.Model):
    TITLE_CHOICES = [
        ('NO_TITLE', ''),
        ('MR', 'Mr.'),
        ('MRS', 'Mrs.'),
        ('MS', 'Ms.'),
        ('DR', 'Dr.'),
        ('PROF', 'Prof.'),
    ]
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,18}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    first_name = models.CharField(max_length=255, null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    job_position = models.CharField(max_length=255, null=True, blank=True)
    mobile_number = models.CharField(validators=[phone_regex], max_length=20, blank=True)
    email = models.EmailField(max_length=254, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=10, choices=TITLE_CHOICES, default='NO_TITLE')

    class Meta:
        ordering = ["last_name"]

    def get_full_name(self):
        full_name = f"{self.first_name} {self.middle_name[0].capitalize()} {self.last_name}"
        return full_name
    

class Fert(models.Model):
    number = models.CharField(max_length=6, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    nsf_division = models.ForeignKey(NSFDivision, on_delete=models.SET_NULL, null=True, blank=True)
    market_segment = models.ForeignKey(MarketSegment, on_delete=models.SET_NULL, null=True, blank=True)
    material_group = models.ForeignKey(MaterialGroup, on_delete=models.SET_NULL, null=True, blank=True)
    major_label = models.ForeignKey(MajorLabel, on_delete=models.SET_NULL, null=True, blank=True)
    ink_technology = models.ForeignKey(InkTechnology, on_delete=models.SET_NULL, null=True, blank=True)
    is_active =  models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_on = models.DateTimeField()

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return self.number
    
    def get_fert_and_brand(self):
        return_string = self.number + self.brand.name
        return return_string
    