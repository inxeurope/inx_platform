from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from inx_platform_app.views import import_from_SQL
from inx_platform_app import dictionaries

class Command(BaseCommand):
    help = 'Runs multiple Django management commands'

    def handle(self, *args, **options):
        try:
            call_command('create_superuser')
            import_from_SQL(dictionaries.tables_list)
            call_command('set_sales_scenario')
            call_command('all_products_not_new')
            call_command('all_customers_not_new')
            call_command('ink_technologies_colors_and_short_names')
            call_command('remove_double_square_bracket_product_brand')
            self.stdout.write(self.style.SUCCESS('All commands executed successfully'))
        except Exception as e:
            raise CommandError('Error executing commands: {}'.format(str(e)))
