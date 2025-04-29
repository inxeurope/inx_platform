from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'customers', views.CustomerViewSet)
router.register(r'color_groups', views.ColorGroupViewSet)
router.register(r'colors', views.ColorViewSet)
router.register(r'market_segments', views.MarketSegmentViewSet)
router.register(r'divisions', views.DivisionViewSet)
router.register(r'currencies', views.CurrencyViewSet)
router.register(r'currency_rates', views.CurrencyRateViewSet)
router.register(r'product_lines', views.ProductLineViewSet)
router.register(r'major_labels', views.MajorLabelViewSet)
router.register(r'ink_technologies', views.InkTechnologyViewSet)
router.register(r'brands', views.BrandViewSet)
router.register(r'nsf_divisions', views.NSFDivisionViewSet)
router.register(r'material_groups', views.MaterialGroupViewSet)
router.register(r'unit_of_measure', views.UnitOfMeasureViewSet)
router.register(r'packagings', views.PackagingViewSet)
router.register(r'packaging_rate_to_lts', views.PackagingRateToLiterViewSet)
router.register(r'product_statuses', views.ProductStatusViewSet)
router.register(r'exchange_rates', views.ExchangeRateViewSet)
router.register(r'scenarios', views.ScenarioViewSet)
router.register(r'country_codes', views.CountryCodeViewSet)
router.register(r'customer_types', views.CustomerTypeViewSet)
router.register(r'industries', views.IndustryViewSet)
router.register(r'rate_to_lts', views.RateToLTViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'ke30', views.Ke30ViewSet)
router.register(r'zaq', views.ZaqViewSet)
router.register(r'budforlines', views.BudForLineViewSet)
router.register(r'budgetforecastdetail', views.BudgetForecastDetailViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path("", views.index, name="index"),
    path("forecast_2/<int:customer_id>/", views.forecast_2, name="forecast-2"),
    path("forecast_2/fetch_previous_years_sales/<int:customer_id>/", views.fetch_previous_year_sales, name="fetch-py-sales"),
    path("forecast_2/fetch_ytd_sales/<int:customer_id>", views.fetch_ytd_sales, name="fetch-ytd-sales"),
    path("forecast_2/fetch_bdg_sales/<int:customer_id>", views.fetch_bdg_sales, name="fetch-bdg-sales"),
    path("forecast_2/fetch_no_previous_years_sales/<int:customer_id>/", views.fetch_no_previous_year_sales, name="fetch-no-py-sales"),
    path("forecast_2/fetch_cg_forecast_data/<int:customer_id>/<int:brand_id>", views.fetch_cg, name="fetch-cg-forecast"),
    path("forecast_2/fetch_forecast/<int:budforline_id>", views.fetch_forecast, name="fetch-forecast"),
    path("forecast_2/fetch_empty_forecast/", views.fetch_empty_forecast, name="fetch-empty-forecast-area"),
    path("forecast/save/", views.forecast_save, name="forecast-save"),
    path("budget/save/", views.forecast_save, name="budget-save"),
    # path("budget/flat_save/", views.budget_flat_save, name="flat-budget-save"),
    path("budget/flat_save/", views.forecast_save, name="flat-budget-save"),

    # path("test/<int:customer_id>", views.fetch_bdg_sales, name="test"),
    
    path("sfb/", views.sales_forecast_budget, name="sales-forecast-budget"),
    path("download_sfb", views.download_sfb, name="download-sfb"),

    path("get_exchange_rates", views.get_exchange_rates, name="get-exchange-rates"),

    path("loading", views.loading, name="loading"),

    path("import_data/", views.import_data, name='import_data'),
    path("import_single_table/", views.import_single_table, name='import-single-table'),
    
    path("clean_db/", views.clean_db, name='clean_db'),
    path("clean_single/", views.clean_single, name='clean_single'),
    
    path("imported_files/", views.imported_files, name='imported-files'),
    path("imported_file_log/<int:pk>", views.imported_file_log, name='imported-file-log'),
    path("files_to_import/", views.files_to_import, name='files-to-import'),
    path("push_file_to_file_processor", views.push_file_to_file_processor, name="push-file-to-file-processor"),
   
    path('start_processing/<int:file_id>/', views.start_processing, name='start-processing'),
    path('delete_this_file_to_import/<int:file_id>/', views.delete_this_file_to_import, name='delete-this-file-to-import'),
    
    path("customers/", views.customers, name="customers"),
    path("customer_view/<int:pk>", views.customer_view, name="customer-view"),
    path("customer_edit/<int:pk>", views.customer_edit, name="customer-edit"),

    path("fetch_sds_l1_replacements/<int:pk>", views.fetch_sds_l1_replacements, name="fetch-sds-l1-replacements"),
    path("delete_sds_l1_replacement/<int:pk>", views.delete_sds_l1_replacement, name="delete-sds-l1-replacement"),
    path("edit_sds_l1_replacement/<int:pk>", views.edit_sds_l1_replacement, name="edit-sds-l1-replacement"),
    path("add_sds_l1_replacement/<int:pk>", views.add_sds_l1_replacement, name="add-sds-l1-replacement"),

    path("fetch_sds_l2_languages_list/<int:pk>", views.fetch_sds_l2_languages_list, name="fetch-sds-l2-languages-list"),
    path("fetch_sds_l2_languages_list/<int:pk>/<int:added_language_id>", views.fetch_sds_l2_languages_list, name="fetch-sds-l2-languages-list"),
    path("add_sds_l2_language/<int:pk>", views.add_sds_l2_language, name="add-sds-l2-language"),

    path("fetch_sds_l2_replacements/<int:customer_id>/<int:language_id>", views.fetch_sds_l2_replacements, name="fetch-sds-l2-replacements"),
    path("delete_sds_l2_replacement/<int:pk>", views.delete_sds_l2_replacement, name="delete-sds-l2-replacement"),
    path("edit_sds_l2_replacement/<int:pk>", views.edit_sds_l2_replacement, name="edit-sds-l2-replacement"),
    path("add_sds_l2_replacement/<int:customer_id>/<int:language_id>", views.add_sds_l2_replacement, name="add-sds-l2-replacement"),
    
    path("fetch_sds_l3_languages_list/<int:pk>", views.fetch_sds_l3_languages_list, name="fetch-sds-l3-languages-list"),
    # In the following path, pk is the Product ID, from it we derive Customer ID
    path("add_sds_l3_language/<int:pk>", views.add_sds_l3_language, name="add-sds-l3-language"),

    path("fetch_sds_l3_replacements/<int:product_id>/<int:language_id>", views.fetch_sds_l3_replacements, name="fetch-sds-l3-replacements"),
    path("edit_sds_l3_replacement/<int:pk>", views.edit_sds_l3_replacement, name="edit-sds-l3-replacement"),
    path("delete_sds_l3_replacement/<int:pk>", views.delete_sds_l3_replacement, name="delete-sds-l3-replacement"),
    path("add_sds_l3_replacement/<int:customer_id>/<int:product_id>/<int:language_id>", views.add_sds_l3_replacement, name="add-sds-l3-replacement"),

    path("fetch_sds_l3_replacements/<int:product_id>/<int:language_id>/", views.fetch_sds_l3_replacements, name="fetch-sds-l3-replacements"),
    path("delete_sds_rtf_file/<int:pk>/", views.delete_sds_rtf_file, name="delete-sds-rtf-file"),
    path("upload_sds_rtf_file/<int:product_id>/<int:language_id>/", views.upload_sds_rtf_file, name="upload-sds-rtf-file"),
     path("download_sds_rtf_file/<int:pk>/", views.download_sds_rtf_file, name="download-sds-rtf-file"),
     path("download_cleaned_rtf_file/<int:pk>/", views.download_cleaned_rtf_file, name="download-cleaned-rtf-file"),

    path("get_contact_details/<int:id>", views.get_contact_details, name="get-contact-details"),

    path("products/", views.products, name="products"),
    path("products_list/", views.products_list, name="products-list"),
    path("product_view/<int:pk>", views.product_view, name="product-view"),
    path("product_edit/<int:pk>", views.product_edit, name="product-edit"),
    path('fetch_bom_components/<int:bom_header_id>/', views.fetch_bom_components, name='fetch-bom-components'),

    path("brands_list/", views.brands_list, name="brands-list"),
    path("brand_view/<int:pk>", views.brand_view, name="brand-view"),
    path("brand_edit/<int:pk>", views.brand_edit, name="brand-edit"),
    
    path("production_requirements/", views.production_requirements, name="production-requirements"),
    

    # Authentication
    path('accounts/login/', views.LoginView.as_view(), name='login'),
    # path('accounts/login-illustration/', views.LoginViewIllustrator.as_view(), name='login_illustration'),
    # path('accounts/login-cover/', views.LoginViewCover.as_view(), name='login_cover'),
    path('accounts/logout/', views.logout_view, name='logout'),

    path('accounts/password-change/', views.UserPasswordChangeView.as_view(), name='change_password'),
    path('accounts/password-change-done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='app_pages/password-change-done.html'
    ), name="password_change_done" ),
    
    path('_marco/', views.special_marco, name="marco"),
    path('_marco/del_bom/', views.special_del_boms, name="del-bom")


]

