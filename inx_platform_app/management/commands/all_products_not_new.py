from django.core.management.base import BaseCommand
from inx_platform_app.models import Product

class Command(BaseCommand):
    help = 'Making all products not new'

    def handle(self, *args, **options):
        products = Product.objects.all()
        for p in products:
            p.is_new = False
        
