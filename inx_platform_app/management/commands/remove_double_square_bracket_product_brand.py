from django.core.management.base import BaseCommand
from inx_platform_app.models import Product, Brand

class Command(BaseCommand):
    help = 'Remove double bracket from product name and brand name'

    def handle(self, *args, **options):
        
        products = Product.objects.all()
        if products:
            for p in products:
                if "[[" in p.name or "]]" in p.name:
                    print()
                    print(p.name, " -> ", end="")
                    p.name = p.name.replace("[[", "[").replace("]]", "]")
                    print(p.name)
                    p.save()
                else:
                    print(".", end="")
        else:
            print("no products")
        
        brands = Brand.objects.all()
        if brands:
            for b in brands:
                if "[[" in b.name or "]]" in b.name:
                    print()
                    print(b.name, " -> ", end="")
                    b.name = b.name.replace("[[", "[").replace("]]", "]")
                    print(b.name)
                    b.save()
                else:
                    print(".", end="")
        else:
            print("no brand")
