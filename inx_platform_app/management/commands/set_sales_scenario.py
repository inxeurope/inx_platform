from django.core.management.base import BaseCommand
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from inx_platform_app.models import Scenario

class Command(BaseCommand):
    help = 'Set Sales scenario with is_sales = True'

    def handle(self, *args, **options):
        try:
            s = Scenario.objects.get(name='Sales')
            s.is_sales = True
            s.save()
            self.stdout.write(self.style.SUCCESS(f'Scenario updated successfully!'))
        except MultipleObjectsReturned as multiple:
            self.stdout.write(self.style.ERROR(f'Multiple object returned, no action has been taken!'))
            return
        except ObjectDoesNotExist as not_exists:
            self.stdout.write(self.style.ERROR(f'No Scenario contains "Sales" in the name column'))
            return
        

