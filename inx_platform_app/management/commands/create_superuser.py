from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create a superuser for development. Marco.zanella@inxeurope.com - dellaBiella2!'

    def handle(self, *args, **options):
        username = 'Marco.zanella'
        email = 'Marco.zanella@inxeurope.com'
        password = 'dellaBiella2!'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS('Superuser created successfully!'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser already exists.'))
