# Generated by Django 5.0.6 on 2024-07-08 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0009_alter_swimsplittime_distance'),
    ]

    operations = [
        migrations.AddField(
            model_name='numbercycles',
            name='data',
            field=models.JSONField(db_comment='Данные', default=dict, verbose_name='Данные'),
        ),
        migrations.AddField(
            model_name='pace',
            name='data',
            field=models.JSONField(db_comment='Данные', default=dict, verbose_name='Данные'),
        ),
        migrations.AddField(
            model_name='startdistance',
            name='data',
            field=models.JSONField(db_comment='Данные', default=dict, verbose_name='Данные'),
        ),
        migrations.AddField(
            model_name='underwaterpart',
            name='data',
            field=models.JSONField(db_comment='Данные', default=dict, verbose_name='Данные'),
        ),
    ]