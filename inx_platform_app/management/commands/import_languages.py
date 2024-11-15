from django.conf import settings
import os
import json
from django.core.management.base import BaseCommand
from inx_platform_app.models import Language

class Command(BaseCommand):
    help = 'Import languages from JSON file'

    def handle(self, *args, **kwargs):
        # Load JSON file
        json_file_path = os.path.join(settings.BASE_DIR, 'languages', 'iso_639-1.json')
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Iterate and create Language instances
        for code, details in data.items():
            Language.objects.update_or_create(
                iso_639_1=code,
                defaults={
                    'iso_639_2': details.get('639-2'),
                    'family': details.get('family'),
                    'name': details.get('name'),
                    'native_name': details.get('nativeName'),
                    'wiki_url': details.get('wikiUrl'),
                }
            )
        self.stdout.write(self.style.SUCCESS('Languages imported successfully'))