from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("loader/", views.loader,name="loader"),
    
    path("import_data/", views.import_data, name='import_data'),
    path("import_single/", views.import_single, name='import_single'),
    
    path("clean_db/", views.clean_db, name='clean_db'),
    path("clean_single/", views.clean_single, name='clean_single'),
    
    path("display_files/", views.display_files, name='display_files'),
    path('start_processing/<int:file_id>/', views.start_processing, name='start_processing'),
    path('delete_file/<int:file_id>/', views.delete_file, name='delete_file'),
    
    path("import_settings/<str:dictionary_name>", views.edit_dictionary, name="edit_dictionary"),
    path("dictionary_add_key/<str:dictionary_name>", views.dictionary_add_key, name='dictionary_add_key'),
    path("dictionary_delete_key/<str:dictionary_name>", views.dictionary_delete_key, name='dictionary_delete_key'),
    
    path("customers/", views.CustomerListView.as_view(), name="customers"),
    path("customers/edit/<int:id>", views.CustomerEditView.as_view(), name="customer-edit"),
    
    path("products/", views.ProductListView.as_view(), name="products"),
    path("products/edit/<int:id>", views.ProductEditView.as_view(), name="product-edit"),

    path("brands/", views.BrandListView.as_view(), name="brands"),
    path("brand/edit/<int:id>", views.BrandEditView.as_view(), name="brand-edit"),
    
    path("major/", views.MajorLabelListView.as_view(), name="major"),
    path("major/add", views.MajorLabelCreateView.as_view(), name="major-add"),
    path("major/edit/<int:id>", views.MajorLabelEditView.as_view(), name="major-edit"),

    path('procedures/', views.StoredProcedureListView.as_view(), name='procedure_list'),
    path('procedure/<int:pk>/', views.StoredProcedureUpdateView.as_view(), name='procedure_update'),
    path('procedure/<int:pk>/push_and_execute/', views.push_and_execute, name='push_and_execute'),

]

