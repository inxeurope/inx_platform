from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from inx_platform_app.models import *
import re

class Command(BaseCommand):
    help = 'do Products'

    def is_number_starting_with_digit(self, product):
        return bool(re.match(r'^[0-9]', product.number))

    def handle(self, *args, **options):
        
        products = Product.objects.all()
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
        

        for p in products:
            if self.is_number_starting_with_digit(p):
                p.is_ink = True
            else:
                p.is_ink = False
            p.save()

        
            if any(substring in p.name for substring in light_substrings):
                # this is  light   
                print(f"{p.name}", end = "")
                if "CYAN" in p.name or "Cyan" in p.name:
                    p.color = lc
                    p.save()
                    print(f"  {p.color.name}")
                if "MAGENTA" in p.name or "Magenta" in p.name:
                    p.color = lm
                    p.save()
                    print(f"  {p.color.name}")
                if "YELLOW" in p.name or "Yellow" in p.name:
                    p.color = ly
                    p.save()
                    print(f"  {p.color.name}")
                if "BLACK" in p.name or "Black" in p.name:
                    p.color = lk
                    p.save()
                    print(f"  {p.color.name}")
                if "GREY" in p.name or "Grey" in p.name:
                    p.color = lgy
                    p.save()
                    print(f"  {p.color.name}")
            else:
                print(f"{p.name}", end = "")
                if "CYAN" in p.name or "Cyan" in p.name:
                    p.color = c
                    p.save()
                    print(f"  {p.color.name}")
                if "MAGENTA" in p.name or "Magenta" in p.name:
                    p.color = m
                    p.save()
                    print(f"  {p.color.name}")
                if "YELLOW" in p.name or "Yellow" in p.name:
                    p.color = y
                    p.save()
                    print(f"  {p.color.name}")
                if "BLACK" in p.name or "Black" in p.name:
                    p.color = k
                    p.save()
                    print(f"  {p.color.name}")
                if "WHITE" in p.name or "White" in p.name:
                    p.color = w
                    p.save()
                    print(f"  {p.color.name}")
                if "CLEANER" in p.name or "Cleaner" in p.name:
                    p.color = cleaner
                    p.save()
                    print(f"  {p.color.name}")
                if "FLUSH" in p.name or "Flush" in p.name:
                    p.color = ff
                    p.save()
                    print(f"  {p.color.name}")
                if "ORANGE" in p.name or "Orange" in p.name:
                    p.color = ora
                    p.save()
                    print(f"  {p.color.name}")
                if "GREEN" in p.name or "Green" in p.name:
                    p.color = gr
                    p.save()
                    print(f"  {p.color.name}")
                if "BLUE" in p.name or "Blue" in p.name:
                    p.color = bl
                    p.save()
                    print(f"  {p.color.name}")
                if "RED" in p.name or "Red" in p.name:
                    p.color = r
                    p.save()
                    print(f"  {p.color.name}")
                if "VIOLET" in p.name or "Violet" in p.name:
                    p.color = gr
                    p.save()
                    print(f"  {p.color.name}")
    
   