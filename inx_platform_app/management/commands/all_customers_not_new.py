from django.core.management.base import BaseCommand
from inx_platform_app.models import Customer

class Command(BaseCommand):
    help = 'Making all products not new'

    def handle(self, *args, **options):
        customers = Customer.objects.all()
        for c in customers:
            print(c.name, c.is_new, end='')
            c.is_new = False
            c.save()
            print(c.is_new)
        
