from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
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

    path("loader/", views.loader, name="loader"),
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

    path("get_contact_details/<int:id>", views.get_contact_details, name="get-contact-details"),

    path("products/", views.products, name="products"),
    path("products_list/", views.products_list, name="products-list"),
    path("product_view/<int:pk>", views.product_view, name="product-view"),
    path("product_edit/<int:pk>", views.product_edit, name="product-edit"),

    path("brands_list/", views.brands_list, name="brands-list"),
    path("brand_view/<int:pk>", views.brand_view, name="brand-view"),
    path("brand_edit/<int:pk>", views.brand_edit, name="brand-edit"),
    

    # Authentication
    path('accounts/login/', views.LoginView.as_view(), name='login'),
    # path('accounts/login-illustration/', views.LoginViewIllustrator.as_view(), name='login_illustration'),
    # path('accounts/login-cover/', views.LoginViewCover.as_view(), name='login_cover'),
    path('accounts/logout/', views.logout_view, name='logout'),

    path('accounts/password-change/', views.UserPasswordChangeView.as_view(), name='change_password'),
    path('accounts/password-change-done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='app_pages/password-change-done.html'
    ), name="password_change_done" ),


]

