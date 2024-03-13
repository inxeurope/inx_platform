from django.core.management.base import BaseCommand
from inx_platform_app.models import Product, Customer

class Command(BaseCommand):
    help = 'Removing proeducts 1689777-05LT asn 1689778-05LT and removing customer 39916'

    def handle(self, *args, **options):
        product_numbers=['1689777-05LT', '1689778-05LT']
        products = Product.objects.filter(number__in=product_numbers)
        if products:
            for p in products:
                print(f'product {p.name} found')
                p.delete()
        
        customers = Customer.objects.filter(number='39916')
        if customers:
            for c in customers:
                print(f'customer {c.name} found')
                c.delete()
