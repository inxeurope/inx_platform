from django.core.management.base import BaseCommand
from inx_platform_app.models import *
from inx_platform_app.utils import *

class Command(BaseCommand):
    help = 'Set BOM Component fert'

    def handle(self, *args, **options):
        
        bom_components = BomComponent.objects.all()
        for component in bom_components:
            # print(component, component.is_fert)
            
            if not component.is_fert:
                if is_fert(component.component_material):
                    print(component, component.is_fert)
                    component.is_fert = True
                    component.save()