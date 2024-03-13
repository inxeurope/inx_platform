from django.core.management.base import BaseCommand
from inx_platform_app.models import Customer

class Command(BaseCommand):
    help = 'Making all products not new'

    def handle(self, *args, **options):
        customers = Customer.objects.all()
        for c in customers:
            c.is_new = False
        
