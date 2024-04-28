from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Drop and create stored procedures and views'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if the stored procedure exists and drop it if it does
            cursor.execute("IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = '_drop_all_views_and_sprocs') DROP PROCEDURE _drop_all_views_and_sprocs")
            
            # Create a new stored procedure with the provided script
            cursor.execute("""
                CREATE PROCEDURE _drop_all_views_and_sprocs AS
                BEGIN
                    DROP PROCEDURE [_budfordetailline_delete_sales];
                    DROP PROCEDURE [_budfordetailline_fill_sales];
                    DROP PROCEDURE [_budforline_add_triplets];
                    DROP PROCEDURE [_ke30_import];
                    DROP PROCEDURE [_ke30_import_add_new_customers];
                    DROP PROCEDURE [_ke30_import_add_new_products];
                    DROP PROCEDURE [_zaq_import];
                    DROP VIEW [01_view_customers];
                    DROP VIEW [02_view_products];
                    DROP VIEW [03_view_zaq];
                    DROP VIEW [04_view_budforsales_temporary];
                END
            """)

            # Execute the created stored procedure
            cursor.execute("EXEC _drop_all_views_and_sprocs")
        
        self.stdout.write(self.style.SUCCESS('Stored procedures and views dropped and created successfully'))
