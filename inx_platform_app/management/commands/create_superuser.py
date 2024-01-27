from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

class Command(BaseCommand):
    help = 'Create a superuser for development. Marco.zanella@inxeurope.com - dellaBiella2!'

    def handle(self, *args, **options):
        # username = 'Marco.zanella'
        email = 'Marco.zanella@inxeurope.com'
        password = 'dellaBiella2!'

        User = get_user_model()

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email, password)
            self.stdout.write(self.style.SUCCESS('Superuser created successfully!'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser already exists.'))
