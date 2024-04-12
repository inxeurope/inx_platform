from django.apps import AppConfig
from django.db import connection
import os, inspect

class InxPlatformAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inx_platform_app"

    def ready(self):
        from .utils import check_and_create_views_and_procs
        app_folder = os.path.dirname(__file__)
        check_and_create_views_and_procs(app_folder)