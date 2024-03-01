from django.contrib import admin
from .models import ColorGroup, Color, MadeIn, Division, MajorLabel
from .models import InkTechnology, NSFDivision, MarketSegment, MaterialGroup, Industry
from .models import Brand, Packaging, ProductStatus, Product, Customer, Ke30Line, UnitOfMeasure
from .models import ExchangeRate, Scenario, CountryCode, BudForLine, BudForNote, BudForDetailLine
from .models import CustomerType, Fbl5nArrImport, Fbl5nOpenImport, Ke30ImportLine, Ke24ImportLine
from .models import Ke24Line, Order, CustomerNote, ProductLine, RateToLT, StoredProcedure
from .models import ZACODMI9_line, ZACODMI9_import_line, UploadedFile, Price, User, Contact


class ColorGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sqlapp_id']


class MadeInAdmin(admin.ModelAdmin):
    list_display = ['id', 'plant_name', 'plant_number', 'sqlapp_id']


class ColorAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sqlapp_id', 'name_short', 'color_weight', 'hex_value', 'color_number', 'color_group']


class ProductLineAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sqlapp_id']


class DivisionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sap_id', 'sap_name', 'sqlapp_id']


class MajorLabelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sap_id', 'sap_name', 'sqlapp_id']


class InkTechnologyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'short_name', 'ribbon_color', 'sap_id', 'sap_name', 'sqlapp_id']


class NSFDivisionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sap_id', 'sap_name', 'sqlapp_id']


class MarketSegmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sap_id', 'sap_name', 'sqlapp_id']


class MaterialGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sap_id', 'sap_name', 'sqlapp_id']


class PackagingAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class ProductStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sqlapp_id']


class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['id', 'currency']


class ScenarioAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class CountryCodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'iso3166_1_alpha_2', 'official_name_en']


class CustomerTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class BrandAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sap_id', 'sap_name', 'get_division_name', 'get_nsf_division_name']

    def get_division_name(self, obj):
        return obj.division.name

    def get_nsf_division_name(self, obj):
        return obj.nsf_division.name
    
    get_division_name.short_description = 'division_name'
    get_nsf_division_name.short_description = 'nsf_division'


class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'number', 'name', 'get_brand_name']

    def get_brand_name(self, obj):
        return obj.brand.name
    
    get_brand_name.short_description = 'brand_name'


class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'number', 'name', 'get_countrycode']

    def get_countrycode(self, obj):
        return obj.country.iso3166_1_alpha_2
    
    get_countrycode.short_description = 'country'


class RateToLTAdmin(admin.ModelAdmin):
    list_display=['uom', 'rate_to_lt']


class IndustryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class PriceAdmin(admin.ModelAdmin):
    list_display=['id', 'customer_name', 'product_name', 'volume_from', 'volume_to', 'price', 'per', 'UoM', 'currency', 'valid_from', 'valid_to']


class StoredProcedureAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'script']


class ContactAdmin(admin.ModelAdmin):
    list_display = ['title', 'first_name', 'last_name', 'job_position', 'email', 'mobile_number']


admin.site.register(ColorGroup, ColorGroupAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(MadeIn, MadeInAdmin)
admin.site.register(ProductLine, ProductLineAdmin)
admin.site.register(Division, DivisionAdmin)
admin.site.register(MajorLabel, MajorLabelAdmin)
admin.site.register(InkTechnology, InkTechnologyAdmin)
admin.site.register(NSFDivision, NSFDivisionAdmin)
admin.site.register(MarketSegment, MarketSegmentAdmin)
admin.site.register(MaterialGroup, MaterialGroupAdmin)
admin.site.register(Packaging, PackagingAdmin)
admin.site.register(ProductStatus, ProductStatusAdmin)
admin.site.register(UnitOfMeasure, UnitOfMeasureAdmin)
admin.site.register(Industry, IndustryAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(RateToLT, RateToLTAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)
admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(CountryCode, CountryCodeAdmin)
admin.site.register(CustomerType, CustomerTypeAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(BudForLine)
admin.site.register(BudForNote)
admin.site.register(BudForDetailLine)
admin.site.register(Fbl5nArrImport)
admin.site.register(Fbl5nOpenImport)
admin.site.register(Ke30ImportLine)
admin.site.register(Ke30Line)
admin.site.register(Ke24ImportLine)
admin.site.register(Ke24Line)
admin.site.register(ZACODMI9_import_line)
admin.site.register(ZACODMI9_line)
admin.site.register(Order)
admin.site.register(CustomerNote)
admin.site.register(UploadedFile)
admin.site.register(Price, PriceAdmin)
admin.site.register(StoredProcedure, StoredProcedureAdmin)
admin.site.register(User)
admin.site.register(Contact, ContactAdmin)

