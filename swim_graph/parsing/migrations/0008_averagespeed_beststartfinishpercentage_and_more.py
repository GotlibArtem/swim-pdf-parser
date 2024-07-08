# Generated by Django 5.0.6 on 2024-07-06 15:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parsing', '0007_auto_add_default_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='AverageSpeed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_comment='Статус', default=True, verbose_name='Статус')),
                ('parsing_session', models.ForeignKey(db_comment='Сессия парсинга', on_delete=django.db.models.deletion.CASCADE, to='parsing.parsingsession', verbose_name='Сессия парсинга')),
            ],
            options={
                'verbose_name': 'настройку для средней скорости',
                'verbose_name_plural': 'Настройки для средней скорости',
            },
        ),
        migrations.CreateModel(
            name='BestStartFinishPercentage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_comment='Статус', default=True, verbose_name='Статус')),
                ('parsing_session', models.ForeignKey(db_comment='Сессия парсинга', on_delete=django.db.models.deletion.CASCADE, to='parsing.parsingsession', verbose_name='Сессия парсинга')),
            ],
            options={
                'verbose_name': 'настройку для лучшего процента изменения стартового и финишного отрезков',
                'verbose_name_plural': 'Настройки для лучшего процента изменения стартового и финишного отрезков',
            },
        ),
        migrations.CreateModel(
            name='BestStartReaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_comment='Статус', default=True, verbose_name='Статус')),
                ('parsing_session', models.ForeignKey(db_comment='Сессия парсинга', on_delete=django.db.models.deletion.CASCADE, to='parsing.parsingsession', verbose_name='Сессия парсинга')),
            ],
            options={
                'verbose_name': 'настройку для лучшей стартовой реакции',
                'verbose_name_plural': 'Настройки для лучшей стартовой реакции',
            },
        ),
        migrations.CreateModel(
            name='HeatMap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_comment='Статус', default=True, verbose_name='Статус')),
                ('parsing_session', models.ForeignKey(db_comment='Сессия парсинга', on_delete=django.db.models.deletion.CASCADE, to='parsing.parsingsession', verbose_name='Сессия парсинга')),
            ],
            options={
                'verbose_name': 'настройку для тепловой карты',
                'verbose_name_plural': 'Настройки для тепловой карты',
            },
        ),
        migrations.CreateModel(
            name='LeaderGap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_comment='Статус', default=True, verbose_name='Статус')),
                ('parsing_session', models.ForeignKey(db_comment='Сессия парсинга', on_delete=django.db.models.deletion.CASCADE, to='parsing.parsingsession', verbose_name='Сессия парсинга')),
            ],
            options={
                'verbose_name': 'настройку для отставания от лидера',
                'verbose_name_plural': 'Настройки для отставания от лидера',
            },
        ),
        migrations.CreateModel(
            name='NumberCycles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_comment='Статус', default=True, verbose_name='Статус')),
                ('parsing_session', models.ForeignKey(db_comment='Сессия парсинга', on_delete=django.db.models.deletion.CASCADE, to='parsing.parsingsession', verbose_name='Сессия парсинга')),
            ],
            options={
                'verbose_name': 'настройку для кол-во циклов на лучшем отрезке',
                'verbose_name_plural': 'Настройки для кол-ва циклов на лучшем отрезке',
            },
        ),
        migrations.CreateModel(
            name='Pace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_comment='Статус', default=True, verbose_name='Статус')),
                ('parsing_session', models.ForeignKey(db_comment='Сессия парсинга', on_delete=django.db.models.deletion.CASCADE, to='parsing.parsingsession', verbose_name='Сессия парсинга')),
            ],
            options={
                'verbose_name': 'настройку для темпа на лучшем отрезке',
                'verbose_name_plural': 'Настройки для темпа на лучшем отрезке',
            },
        ),
        migrations.CreateModel(
            name='SpeedDrop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_comment='Статус', default=True, verbose_name='Статус')),
                ('parsing_session', models.ForeignKey(db_comment='Сессия парсинга', on_delete=django.db.models.deletion.CASCADE, to='parsing.parsingsession', verbose_name='Сессия парсинга')),
            ],
            options={
                'verbose_name': 'настройку для падения скорости',
                'verbose_name_plural': 'Настройки для падения скорости',
            },
        ),
        migrations.CreateModel(
            name='StartDistance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_comment='Статус', default=True, verbose_name='Статус')),
                ('parsing_session', models.ForeignKey(db_comment='Сессия парсинга', on_delete=django.db.models.deletion.CASCADE, to='parsing.parsingsession', verbose_name='Сессия парсинга')),
            ],
            options={
                'verbose_name': 'настройку для статрового отрезка',
                'verbose_name_plural': 'Настройки для статрового отрезка',
            },
        ),
        migrations.CreateModel(
            name='UnderwaterPart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(db_comment='Статус', default=True, verbose_name='Статус')),
                ('parsing_session', models.ForeignKey(db_comment='Сессия парсинга', on_delete=django.db.models.deletion.CASCADE, to='parsing.parsingsession', verbose_name='Сессия парсинга')),
            ],
            options={
                'verbose_name': 'настройку для подводной части',
                'verbose_name_plural': 'Настройки для подводной части',
            },
        ),
        migrations.DeleteModel(
            name='Indicators',
        ),
    ]
