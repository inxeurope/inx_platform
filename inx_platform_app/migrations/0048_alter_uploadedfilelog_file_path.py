from django.conf import settings
from django.db import migrations, models
import inx_platform_app.models

def get_media_root():
    # Get the dynamic path based on the current settings
    return settings.MEDIA_ROOT

class Migration(migrations.Migration):

    dependencies = [
        ('inx_platform_app', '0047_alter_productstatus_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadedfilelog',
            name='file_path',
            field=models.FilePathField(
                blank=True,
                match=r'.*\.(xlsx|XLSX)$',
                null=True,
                path=get_media_root(),
                validators=[inx_platform_app.models.xls_xlsx_file_validator],
            ),
        ),
    ]