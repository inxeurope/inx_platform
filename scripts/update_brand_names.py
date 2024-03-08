# Filename: scripts/update_brand_names.py

from inx_platform_app.models import Brand
from django.db.models import Q

def run():
    brands_with_special_chars = Brand.objects.filter(Q(name__contains='[[') | Q(name__contains=']]'))

    count = 0
    for brand in brands_with_special_chars:
        brand.name = brand.name.replace('[[', '[').replace(']]', ']')
        brand.save()
        count += 1

    print(f"Updated {count} brand names.")
