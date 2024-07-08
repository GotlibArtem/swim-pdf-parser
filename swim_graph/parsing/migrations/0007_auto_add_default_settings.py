from django.db import migrations

def add_default_settings(apps, schema_editor):
    ParsingSettings = apps.get_model('parsing', 'ParsingSettings')
    ParsingSettings.objects.create(setting_name='Number_participants', setting_value='20')

class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0006_parsingsettings_alter_swimsplittime_protocol_data'),
    ]

    operations = [
        migrations.RunPython(add_default_settings),
    ]
