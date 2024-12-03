# clear_country_codes_cache.py
from django.core.management.base import BaseCommand
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Clears the country_codes cache'

    def handle(self, *args, **kwargs):
        cache.delete('country_codes')
        self.stdout.write(self.style.SUCCESS('Successfully cleared country_codes cache'))
