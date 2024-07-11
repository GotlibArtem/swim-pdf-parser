"""swim_graph Constants"""
from enum import Enum


class PoolLength(Enum):
    "Длины бассейнов"

    SHORT = '25m'
    LONG = '50m'

    @classmethod
    def choices(cls):
        return [(key.value, key.value) for key in cls]


class SwimLength(Enum):
    "Длины заплывов"

    FIFTY_METERS = '50m'
    ONE_HUNDRED_METERS = '100m'
    TWO_HUNDRED_METERS = '200m'
    FOUR_HUNDRED_METERS = '400m'

    @classmethod
    def choices(cls):
        return [(key.value, key.value) for key in cls]


class ParsingKeywords():
    "Ключевые слова для замен в парсинге"

    FILE_NAME_KEYWORDS = (
        'Дистанция',
        'Event'
    )

    FINAL_KEYWORDS = (
        'Финал',
        'Полуфинал',
        'Резервные заявки',
        'Заплыв',
        'Heat',
        'Место Фамилия, Имя г/р Команда R.T. Результат Очки',
        'Rank RT Time Pts'
    )

    RANKS_KEYWORDS = (
        'РМЮмсмк',
        'РСмс',
        'змс',
        'мсмк',
        'кмс',
        'мс',
        'I',
        'II',
        'III'
    )


# Промежуточные дистанции
INTERMEDIATE_SWIM_LENGTHS = (
    '25m',
    '50m',
    '75m',
    '100m',
    '125m',
    '150m',
    '175m',
    '200m',
    '225m',
    '250m',
    '275m',
    '300m',
    '325m',
    '350m',
    '375m',
    '400m',
)
