from django.core.management.base import BaseCommand
from inx_platform_app.models import InkTechnology

class Command(BaseCommand):
    help = 'Setting Ink technology colors and short names'

    def handle(self, *args, **options):
        print(self.help)
        ink_technologies = InkTechnology.objects.all()
        for i_t in ink_technologies:
            print(i_t.name, " ", end = "")
            match i_t.name:
                case 'Liquid Laminate':
                    i_t.short_name = 'LL'
                    i_t.ribbon_color = 'azure-lt'
                case 'Not an ink':
                    i_t.short_name = 'Nai'
                    i_t.ribbon_color = 'muted'
                case 'Toner':
                    i_t.short_name = 'Toner'
                    i_t.ribbon_color = 'cyan-lt'
                case 'Ebeam':
                    i_t.short_name = 'EB'
                    i_t.ribbon_color = 'green'
                case 'Eco Solvent':
                    i_t.short_name = 'ESolv'
                    i_t.ribbon_color = 'purple-lt'
                case 'Mild Solvent':
                    i_t.short_name = 'MSolv'
                    i_t.ribbon_color = 'purple'
                case 'Water-based dye-sub':
                    i_t.short_name = 'Dyesub'
                    i_t.ribbon_color = 'yellow'
                case 'True Solvent':
                    i_t.short_name = 'TSolv'
                    i_t.ribbon_color = 'red'
                case 'Bio Solvent':
                    i_t.short_name = 'Bio'
                    i_t.ribbon_color = 'lime'
                case 'UVCurable':
                    i_t.short_name = 'UV'
                    i_t.ribbon_color = 'teal'
                case 'Water-based':
                    i_t.short_name = 'WB'
                    i_t.ribbon_color = 'azure'
                case 'Adhesion Promoter':
                    i_t.short_name = 'AP'
                    i_t.ribbon_color = 'muted-lt'
                case _:
                    i_t.short_name = 'NAI'
                    i_t.ribbon_color = 'muted'
            print(i_t.short_name, i_t.ribbon_color)
            i_t.save()
