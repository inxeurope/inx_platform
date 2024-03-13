from django.core.management.base import BaseCommand
from inx_platform_app.models import Product

class Command(BaseCommand):
    help = 'Removing proeducts 1689777-05LT asn 1689778-05LT and removing customer 39916'

    def handle(self, *args, **options):
        
        products = Product.objects.all()
        if products:
            for p in products:
                p.name = p.name.replace("[[", "[").replace("]]", "]")
                p.save()
