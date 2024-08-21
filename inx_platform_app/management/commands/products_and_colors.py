from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from inx_platform_app.models import *
from inx_platform_app.utils import *
from datetime import datetime
import re

class Command(BaseCommand):
    help = 'work on Products'

    def is_number_starting_with_digit(self, product):
        return bool(re.match(r'^[0-9]', product.number))

    def handle(self, *args, **options):
        
        products = Product.objects.filter(is_new=True)
        light_substrings = ['LT.', 'LIGHT', 'Lt.', 'Light']
        lc = get_object_or_404(Color, name="Light Cyan")
        lm = get_object_or_404(Color, name="Light Magenta")
        ly = get_object_or_404(Color, name="Light Yellow")
        lk = get_object_or_404(Color, name="Light Black")
        lgy = get_object_or_404(Color, name="Light Grey")
        c = get_object_or_404(Color, name="Cyan")
        m = get_object_or_404(Color, name="Magenta")
        y = get_object_or_404(Color, name="Yellow")
        k = get_object_or_404(Color, name="Black")
        w = get_object_or_404(Color, name="White")
        ora = get_object_or_404(Color, name="Orange")
        gr = get_object_or_404(Color, name="Green")
        r = get_object_or_404(Color, name="Red")
        bl = get_object_or_404(Color, name="Blue")
        v = get_object_or_404(Color, name="Violet")
        
        cleaner = get_object_or_404(Color, name="Cleaner")
        ff = get_object_or_404(Color, name="Flushing Fluid")

        disc_brand = get_object_or_404(Brand, name="*")
        disc_packaging= get_object_or_404(Packaging, name="*")

        mark_for_del = get_object_or_404(ProductStatus, marked_for_deletion = True)

        
        for p in products:
            if self.is_number_starting_with_digit(p):
                p.is_ink = True
            else:
                p.is_ink = False
            p.save()

            if is_fert(p.number):
                p.is_fert = True
                p.brand = disc_brand
            else:
                p.is_fert = False
                if p.is_ink == True:
                    p.brand = disc_brand
                    p.packaging = disc_packaging
                    p.product_status = mark_for_del
            p.save()

            if any(substring in p.name for substring in light_substrings):
                # this is  light   
                print(f"{p.name}", end = "")
                if "CYAN" in p.name or "Cyan" in p.name:
                    p.color = lc
                    print(f"  {p.color.name}")
                if "MAGENTA" in p.name or "Magenta" in p.name:
                    p.color = lm
                    print(f"  {p.color.name}")
                if "YELLOW" in p.name or "Yellow" in p.name:
                    p.color = ly
                    print(f"  {p.color.name}")
                if "BLACK" in p.name or "Black" in p.name:
                    p.color = lk
                    print(f"  {p.color.name}")
                if "GREY" in p.name or "Grey" in p.name:
                    p.color = lgy
                    print(f"  {p.color.name}")
                p.save()
            else:
                print(f"{p.name}", end = "")
                if "CYAN" in p.name or "Cyan" in p.name:
                    p.color = c
                    print(f"  {p.color.name}")
                if "MAGENTA" in p.name or "Magenta" in p.name:
                    p.color = m
                    print(f"  {p.color.name}")
                if "YELLOW" in p.name or "Yellow" in p.name:
                    p.color = y
                    print(f"  {p.color.name}")
                if "BLACK" in p.name or "Black" in p.name:
                    p.color = k
                    print(f"  {p.color.name}")
                if "WHITE" in p.name or "White" in p.name:
                    p.color = w
                    print(f"  {p.color.name}")
                if "CLEANER" in p.name or "Cleaner" in p.name:
                    p.color = cleaner
                    print(f"  {p.color.name}")
                if "FLUSH" in p.name or "Flush" in p.name:
                    p.color = ff
                    print(f"  {p.color.name}")
                if "ORANGE" in p.name or "Orange" in p.name:
                    p.color = ora
                    print(f"  {p.color.name}")
                if "GREEN" in p.name or "Green" in p.name:
                    p.color = gr
                    print(f"  {p.color.name}")
                if "BLUE" in p.name or "Blue" in p.name:
                    p.color = bl
                    print(f"  {p.color.name}")
                if "RED" in p.name or "Red" in p.name:
                    p.color = r
                    print(f"  {p.color.name}")
                if "VIOLET" in p.name or "Violet" in p.name:
                    p.color = v
                    print(f"  {p.color.name}")
                p.save()
            p.approved_by = get_object_or_404(User, email = "Stefano.Rogora@inxeurope.com")
            p.approved_on = datetime.now()
            p.save()
        
    
   