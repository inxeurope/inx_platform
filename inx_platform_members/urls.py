from django.urls import path
from . import views

urlpatterns = [
    path('login_user', views.login_user, name="login"),
    path('logout_user', views.logout_user, name="logout"),
    path('create_user',views.create_user, name='create_user'),
    path('list_users', views.UserListView.as_view(), name="list_users"),
    path('edit_user/<int:pk>/', views.UserUpdateView.as_view(), name='edit_user'),
]