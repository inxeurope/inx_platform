from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

class Command(BaseCommand):
    help = 'Create a superuser for development. Marco.zanella@inxeurope.com - dellaBiella2!'

    def handle(self, *args, **options):
        # username = 'Marco.zanella'
        email_marco = 'Marco.zanella@inxeurope.com'
        password_marco = 'dellaBiella2!'
        first_name_marco = "Marco Valentino"
        last_name_marco = "Zanella"

        email_stefano = "Stefano.rogora@inxeurope.com"
        password_stefano = "dellaBiella2!"
        first_name_stefano = "Stefano"
        last_name_stefano = "Rogora"

        User = get_user_model()

        if not User.objects.filter(email=email_marco).exists():
            User.objects.create_superuser(email_marco, password_marco, first_name=first_name_marco, last_name=last_name_marco)
            self.stdout.write(self.style.SUCCESS(f'Superuser {email_marco} created successfully!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Superuser {email_marco} already exists.'))

        if not User.objects.filter(email=email_stefano).exists():
            User.objects.create_superuser(email_stefano, password_stefano, first_name=first_name_stefano, last_name=last_name_stefano)
            self.stdout.write(self.style.SUCCESS(f'Superuser {email_stefano} created successfully!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Superuser {email_stefano} already exists.'))
