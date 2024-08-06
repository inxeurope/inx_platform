from django.core.management.base import BaseCommand
from inx_platform_app.models import *

class Command(BaseCommand):
    help = 'Making all products not new'

    def handle(self, *args, **options):
        
        Bom.objects.all().delete()
        BomComponent.objects.all().delete()
        BomHeader.objects.all().delete()
        Product.objects.filter(id__gt = 2537).delete()
        