from django.urls import path
from . import views

urlpatterns = [
    path('sse/', views.index, name='sse'),
    path('stream/', views.sse_stream, name='sse_stream')
]