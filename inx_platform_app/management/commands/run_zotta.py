from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Executes the __zotta stored procedure in SQL Server'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("EXEC __zotta")
            results = cursor.fetchall()
            for result in results:
                self.stdout.write(self.style.SUCCESS(f'Result: {result}'))
            self.stdout.write(self.style.SUCCESS('Successfully executed __zotta'))
