from django.db import models
from datetime import time

from swim_graph_utils.constants import (
    PoolLength, SwimLength, INTERMEDIATE_SWIM_LENGTHS
)


class ParsingSession(models.Model):
    "Сессии парсинга"
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания сессии',
        db_comment='Дата создания сессии',
    )
    file_name = models.CharField(
        max_length=256,
        null=False,
        verbose_name='Название файла',
        db_comment='Название файла',
    )
    link_video = models.TextField(
        verbose_name='Ссылка на видео',
        db_comment='Ссылка на видео',
    )
    pool_length = models.CharField(
        max_length=4,
        choices=PoolLength.choices(),
        default=PoolLength.LONG.value,
        verbose_name='Длина бассейна',
        db_comment='Длина бассейна',
    )
    swim_length = models.CharField(
        max_length=5,
        choices=SwimLength.choices(),
        default=SwimLength.ONE_HUNDRED_METERS.value,
        verbose_name='Длина заплыва',
        db_comment='Длина заплыва',
    )

    def __str__(self) -> str:
        return f'Сессия парсинга: {self.file_name} от {self.created}'

    class Meta:
        verbose_name = 'сессию парсинга'
        verbose_name_plural = 'Сессии парсинга'


class ProtocolData(models.Model):
    "Данные об участниках заплывов из стартового и финального протоколов"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    initials = models.CharField(
        max_length=64,
        null=False,
        default='Ошибка при парсинге',
        verbose_name='Фамилия Имя',
        db_comment='Фамилия Имя',
    )
    year_of_birth = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Год рождения',
        db_comment='Год рождения',
    )
    final_category = models.CharField(
        max_length=24,
        null=True,
        blank=True,
        verbose_name='Категория финала',
        db_comment='Категория финала',
    )
    start_position = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Стартовая позиция (№ п.п.)',
        db_comment='Стартовая позиция (№ п.п.)',
    )
    final_position = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Финишная позиция (место)',
        db_comment='Финишная позиция (место)',
    )
    reaction_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Время реакции',
        db_comment='Время реакции',
    )
    result = models.TimeField(
        null=False,
        default=time(0, 0),
        verbose_name="Результат",
        db_comment='Результат',
    )
    points = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Очки',
        db_comment='Очки',
    )

    def __str__(self) -> str:
        return f'{self.initials}: {self.final_position}-е место'

    class Meta:
        verbose_name = 'данные по заплыву'
        verbose_name_plural = 'Данные по заплывам'


class SwimSplitTime(models.Model):
    "Время по участникам на промежуточных дистанциях"
    protocol_data = models.ForeignKey(
        ProtocolData,
        on_delete=models.CASCADE,
        verbose_name='Данные заплыва',
        db_comment='Данные заплыва',
    )
    distance = models.IntegerField(
        null=False,
        verbose_name='Дистанция',
        db_comment='Дистанция',
    )
    split_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Время на промежуточной дистанции',
        db_comment='Время на промежуточной дистанции',
    )

    def __str__(self) -> str:
        return f'{self.distance} м - {self.split_time}'

    class Meta:
        verbose_name = 'Время на промежуточной дистанции'
        verbose_name_plural = 'Время на промежуточных дистанциях'


class StartDistance(models.Model):
    "Настройки для стартого отрезка"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    status = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Статус',
        db_comment='Статус',
    )

    def __str__(self) -> str:
        return f'Стартовый отрезок (статус): {self.status}'

    class Meta:
        verbose_name = 'настройку для статрового отрезка'
        verbose_name_plural = 'Настройки для статрового отрезка'


class AverageSpeed(models.Model):
    "Настройки для средней скорости"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    status = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Статус',
        db_comment='Статус',
    )

    def __str__(self) -> str:
        return f'Средняя скорость (статус): {self.status}'

    class Meta:
        verbose_name = 'настройку для средней скорости'
        verbose_name_plural = 'Настройки для средней скорости'


class NumberCycles(models.Model):
    "Настройки для кол-ва циклов на лучшем отрезке"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    status = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Статус',
        db_comment='Статус',
    )

    def __str__(self) -> str:
        return f'Кол-во циклов на лучшем отрезке (статус): {self.status}'

    class Meta:
        verbose_name = 'настройку для кол-во циклов на лучшем отрезке'
        verbose_name_plural = 'Настройки для кол-ва циклов на лучшем отрезке'


class Pace(models.Model):
    "Настройки для темпа на лучшем отрезке"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    status = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Статус',
        db_comment='Статус',
    )

    def __str__(self) -> str:
        return f'Темп на лучшем отрезке (статус): {self.status}'

    class Meta:
        verbose_name = 'настройку для темпа на лучшем отрезке'
        verbose_name_plural = 'Настройки для темпа на лучшем отрезке'


class SpeedDrop(models.Model):
    "Настройки для падения скорости"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    status = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Статус',
        db_comment='Статус',
    )

    def __str__(self) -> str:
        return f'Падение скорости (статус): {self.status}'

    class Meta:
        verbose_name = 'настройку для падения скорости'
        verbose_name_plural = 'Настройки для падения скорости'


class LeaderGap(models.Model):
    "Настройки для отставания от лидера"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    status = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Статус',
        db_comment='Статус',
    )

    def __str__(self) -> str:
        return f'Отставание от лидера (статус): {self.status}'

    class Meta:
        verbose_name = 'настройку для отставания от лидера'
        verbose_name_plural = 'Настройки для отставания от лидера'


class UnderwaterPart(models.Model):
    "Настройки для подводной части"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    status = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Статус',
        db_comment='Статус',
    )

    def __str__(self) -> str:
        return f'Подводная часть (статус): {self.status}'

    class Meta:
        verbose_name = 'настройку для подводной части'
        verbose_name_plural = 'Настройки для подводной части'


class BestStartReaction(models.Model):
    "Настройки для лучшей стартовой реакции"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    status = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Статус',
        db_comment='Статус',
    )

    def __str__(self) -> str:
        return f'Лучшая стартовая реакция (статус): {self.status}'

    class Meta:
        verbose_name = 'настройку для лучшей стартовой реакции'
        verbose_name_plural = 'Настройки для лучшей стартовой реакции'


class BestStartFinishPercentage(models.Model):
    "Настройки для лучшего процента изменения стартового и финишного отрезков"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    status = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Статус',
        db_comment='Статус',
    )

    def __str__(self) -> str:
        return f'Лучший процент изменения стартового и финишного отрезков (статус): {self.status}'

    class Meta:
        verbose_name = 'настройку для лучшего процента изменения стартового и финишного отрезков'
        verbose_name_plural = 'Настройки для лучшего процента изменения стартового и финишного отрезков'


class HeatMap(models.Model):
    "Настройки для тепловой карты"
    parsing_session = models.ForeignKey(
        ParsingSession,
        on_delete=models.CASCADE,
        verbose_name='Сессия парсинга',
        db_comment='Сессия парсинга',
    )
    status = models.BooleanField(
        default=True,
        null=False,
        verbose_name='Статус',
        db_comment='Статус',
    )

    def __str__(self) -> str:
        return f'Тепловая карта (статус): {self.status}'

    class Meta:
        verbose_name = 'настройку для тепловой карты'
        verbose_name_plural = 'Настройки для тепловой карты'


class ParsingSettings(models.Model):
    "Настройки парсинга"
    setting_name = models.CharField(
        max_length=256,
        null=False,
        verbose_name='Название настройки',
        db_comment='Название настройки парсинга',
    )
    setting_value = models.CharField(
        max_length=256,
        null=False,
        verbose_name='Значение настройки',
        db_comment='Значение настройки парсинга',
    )

    def __str__(self) -> str:
        return f'{self.setting_name}: {self.setting_value}'

    class Meta:
        verbose_name = 'настройку парсинга'
        verbose_name_plural = 'Настройки парсинга'
