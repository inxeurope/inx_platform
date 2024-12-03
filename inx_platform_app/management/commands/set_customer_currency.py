from django.core.management.base import BaseCommand
from inx_platform_app.models import *

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        try:
            # Get the Currency record where alpha_3='USD'
            usd_currency = Currency.objects.get(alpha_3='USD')
            eur_currency = Currency.objects.get(alpha_3='EUR')
            
            # Get the customers whose country's alpha_2 is 'US'
            us_customers = Customer.objects.filter(country__alpha_2='US')
            eu_customers = Customer.objects.exclude(country__alpha_2='US')
            
            # Update the currency for these customers
            updated_count_us = us_customers.update(currency=usd_currency)
            updated_count_eu = eu_customers.update(currency=eur_currency)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count_us} customers to USD currency.'))
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count_eu} customers to EUR currency.'))
        except Currency.DoesNotExist:
            self.stdout.write(self.style.ERROR('Currency with alpha_3="USD" does not exist.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
