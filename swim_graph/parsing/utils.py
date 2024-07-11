"""Parsing Utilities"""
from datetime import time
import re
from typing import Any, Dict, List, Optional
import pdfplumber
import plotly.graph_objects as go
from django.contrib import messages
from django.http import HttpRequest

from swim_graph_utils.constants import (
    ParsingKeywords, PoolLength, SwimLength,
    INTERMEDIATE_SWIM_LENGTHS
)
from .models import (
    ProtocolData, ParsingSession, SwimSplitTime,
    ParsingSettings, StartDistance, NumberCycles,
    Pace, UnderwaterPart
)


class SwimParser:
    """Класс для парсинга стартового и финального протоколов."""

    def __init__(self):
        self.parse_results = {
            'file_name': None,
            'swim_length': None,
            'pool_length': None,
            'participants': []
        }
        self.participant_template = {
            'initials': None,
            'year_of_birth': None,
            'final_category': None,
            'start_position': None,
            'final_position': None,
            'reaction_time': None,
            'result': None,
            'points': None,
            'split_times': []
        }

    def parse_pdf(self, file: Any) -> List[str]:
        """
        Парсит указанный PDF файл и возвращает извлеченные данные в виде списка строк.

        :param file: Загруженный PDF файл.
        :return: Список извлеченных строк.
        """
        lines = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.split("\n"))
        return lines

    def process_start_list(self, request: HttpRequest, data: List[str]) -> bool:
        """
        Обрабатывает данные стартового протокола и сохраняет их в переменную parse_results.

        :param data: Список строк, извлеченных из PDF файла.
        """
        final_category = None

        if not any(keyword in ' '.join(data) for keyword in ['Стартовый протокол', 'Startlist']):
            messages.error(
                request,
                'Убедитесь, что загрузили стартовый протокол!',
                extra_tags='warning'
            )
            return False

        for line in data:
            if self.contains_keyword(line, ParsingKeywords.FILE_NAME_KEYWORDS):
                if self.parse_results['file_name'] is None:
                    self.parse_results['file_name'] = self.get_file_name(line)
                if self.parse_results['swim_length'] is None:
                    self.parse_results['swim_length'] = self.get_swim_length(line)
            elif self.contains_keyword(line, ParsingKeywords.FINAL_KEYWORDS):
                self.participant_template = {
                    key: None for key in self.participant_template
                }
                final_category = line
                self.participant_template['final_category'] = final_category
            elif final_category and line and len(line) > 15:
                line = self.clean_line(line, ParsingKeywords.RANKS_KEYWORDS)
                parts = line.split()

                position = self.convert_to_int(parts[0])
                if position is not None:
                    initials = f"{parts[1]} {parts[2]}".title()
                    year_of_birth = self.convert_to_int(parts[3])
                else:
                    initials = f"{parts[0]} {parts[1]}".title()
                    year_of_birth = self.convert_to_int(parts[2])

                self.participant_template['start_position'] = position
                self.participant_template['initials'] = initials
                self.participant_template['year_of_birth'] = year_of_birth
                self.participant_template['split_times'] = []
                self.parse_results['participants'].append(self.participant_template.copy())

        return True

    def process_results(self, request: HttpRequest, data: List[str]) -> bool:
        """
        Обрабатывает данные финального протокола и сохраняет их в переменную parse_results.

        :param data: Список строк, извлеченных из PDF файла.
        """
        if not any(keyword in ' '.join(data) for keyword in ['Результаты', 'Results']):
            messages.error(
                request,
                'Убедитесь, что загрузили финальный протокол!',
                extra_tags='warning'
            )
            return False

        initials = None
        year_of_birth = None
        final_category = None
        last_final_position = 0
        distances = set()

        for line in data:
            if self.contains_keyword(line, ParsingKeywords.FINAL_KEYWORDS):
                final_category = line
            elif any(keyword in line for keyword in INTERMEDIATE_SWIM_LENGTHS) and final_category:
                swim_times = self.parse_split_times(line)
                self.update_participant(initials, year_of_birth, swim_times)
                distances.update([split['distance'] for split in swim_times.get('split_times', [])])
            elif final_category and line and len(line) > 15:
                line = self.clean_line(line, ParsingKeywords.RANKS_KEYWORDS)
                parts = line.split()
                if parts[-1] in ['A', 'B', 'R', 'Q']:
                    parts = parts[:-1]

                final_position = self.convert_to_int(parts[0].replace('.', ''))
                if final_position is not None:
                    initials = f"{parts[1]} {parts[2]}".title()
                    year_of_birth = self.convert_to_int(parts[3])
                else:
                    final_position = last_final_position + 1
                    initials = f"{parts[0]} {parts[1]}".title()
                    year_of_birth = self.convert_to_int(parts[2])

                updates = {
                    'final_position': final_position,
                    'reaction_time': self.convert_time_reaction(parts[-3]),
                    'result': parse_time(parts[-2]),
                    'points': self.convert_to_int(parts[-1]),
                }
                self.update_participant(initials, year_of_birth, updates)

                last_final_position = final_position

        self.parse_results['pool_length'] = (
            PoolLength.SHORT.value if 25 in distances
            else PoolLength.LONG.value
        )
        return True

    def update_participant(
            self, initials: str,
            year_of_birth: int,
            updates: Dict[str, any]
        ) -> None:
        """
        Находит участника по значениям initials и year_of_birth и обновляет указанные ключи.

        :param initials: Инициалы участника.
        :param year_of_birth: Год рождения участника.
        :param updates: Словарь с ключами и значениями, которые нужно обновить.
        """
        if not updates:
            return
        for participant in self.parse_results['participants']:
            if (participant['initials'] == initials and
                    participant['year_of_birth'] == year_of_birth):
                for key, value in updates.items():
                    if key == 'split_times':
                        if not participant['split_times']:
                            participant['split_times'] = []
                        participant['split_times'].extend(value)
                    else:
                        participant[key] = value
                break

    def parse_split_times(self, input_str: str) -> Dict[str, List[Dict[str, any]]]:
        """
        Парсит строку с результатами заплывов и возвращает словарь с данными.
        Извлекает только второе значение времени для каждого ключа
        (например, result_50m, result_100m).

        :param input_str: строка с результатами заплывов
        :return: словарь с данными заплывов
        """
        try:
            split_times = []
            pattern = re.compile(r'(' + '|'.join(INTERMEDIATE_SWIM_LENGTHS) + r')')

            matches = pattern.finditer(input_str)
            positions = [match.start() for match in matches]
            positions.append(len(input_str))

            for i in range(len(positions) - 1):
                segment = input_str[positions[i]:positions[i+1]].strip()
                distance, time_segment = segment.split(':', 1)
                # Извлекаем второе значение времени
                time_values = time_segment.strip().split()
                if len(time_values) > 1:
                    key = distance.strip().replace('m', '')
                    split_times.append(
                        {'distance': int(key),
                         'split_time': parse_time(time_values[1].strip())}
                    )
            split_times = sorted(split_times, key=lambda x: x['distance'])

            return {'split_times': split_times}

        except (ValueError, TypeError) as error:
            return {'split_times': []}

    def get_file_name(self, line: str) -> str:
        """
        Парсит название файла из строки.

        :param line: Строка для парсинга.
        :return: Название файла.
        """
        line = ' '.join(line.split()[2:])
        line = re.sub(r'\(.*?\)', '', line)
        line_parts = line.split()
        if len(line_parts) > 1:
            line_parts.pop()

        file_name = ' '.join(line_parts).strip()

        return file_name

    def get_swim_length(self, line: str) -> str:
        """
        Парсит длину заплыва из строки.

        :param line: Строка для парсинга.
        :return: Длина заплыва.
        """
        distance_pattern = re.compile(r'\b\d+m\b')
        match = distance_pattern.search(line)
        if match:
            distance = match.group()
            for length in SwimLength:
                if length.value == distance:
                    return length.value

        return None

    def contains_keyword(self, line: str, keywords: List[str]) -> bool:
        """
        Проверяет, содержит ли строка одно из ключевых слов.

        :param line: Строка для проверки.
        :param keywords: Список ключевых слов.
        :return: True, если одно из ключевых слов найдено в строке,
        иначе False.
        """
        return any(re.search(r'\b' + re.escape(keyword) + r'\b', line) for keyword in keywords)

    def clean_line(self, line: str, substrings_to_remove: List[str]) -> str:
        """
        Удаляет из строки определенные подстроки.

        :param line: Исходная строка.
        :param substrings_to_remove: Список подстрок для удаления.
        :return: Очищенная строка.
        """
        for substring in substrings_to_remove:
            line = line.replace(substring, '')
        return line

    def convert_to_int(self, value: str) -> int:
        """
        Преобразовывает строку в число.

        :param value: Строка в виде числа.
        :rerutn: Число.
        """
        try:
            return int(value)
        except (ValueError, TypeError) as error:
            return None

    def convert_time_reaction(self, time_reaction: str) -> time:
        """
        Преобразовывает строки со временем реакции в число.

        :param time_reaction: Время реакции в исходном формате.
        :return: Время реакции.
        """
        try:
            time_reaction = time_reaction.replace(',', '.')
            time_reaction = time_reaction.replace('+', '')
            return parse_time(time_reaction)
        except (ValueError, TypeError) as error:
            return None


class ChartGenerator:
    """Класс для генерации диаграмм."""

    def __init__(self, session: ParsingSession, participants: List[ProtocolData]) -> None:
        self.session = session
        self.participants = participants

    def generate_average_speed_chart(self) -> str:
        """
        Генерирует HTML код для столбчатой диаграммы средней скорости.
        """
        distances = sorted({
            split.distance
            for participant in self.participants
            for split in participant.swimsplittime_set.all()
        }) or [int(self.session.swim_length.replace('m', ''))]

        col_labels = [participant.initials for participant in self.participants]
        speed_data = {dist: [] for dist in distances}

        for participant in self.participants:
            for dist in distances:
                speed = self._calculate_speed(participant, dist)
                speed_data[dist].append(speed)

        fig = go.Figure()

        bar_width = 0.2
        colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black',
                  'orange', 'purple', 'pink', 'brown', 'grey', 'lime', 'olive',
                  'navy', 'teal']
        for i, dist in enumerate(distances):
            speeds = speed_data[dist]
            fig.add_trace(go.Bar(
                x=col_labels,
                y=speeds,
                name=f'ср. скорость {distances[i-1] if i > 0 else 0}-{dist}м, м/сек',
                marker_color=colors[i % len(colors)],
                width=bar_width
            ))

        fig.update_layout(
            barmode='group',
            xaxis_tickangle=-45,
            yaxis_title='Скорость (м/сек)',
            legend_title='Дистанции',
        )

        average_speed_chart = fig.to_html(
            full_html=False,
            config={
                'displayModeBar': False,
                'displaylogo': False,
                'modeBarButtonsToAdd': ['toImage', 'zoomIn2d', 'zoomOut2d', 'autoScale2d']
            }
        )

        return average_speed_chart

    def generate_number_cycles_chart(self) -> str:
        """
        Генерирует HTML код для столбчатой диаграммы количества циклов на лучшем отрезке.
        """
        col_labels = [participant.initials for participant in self.participants]

        number_cycles_data = NumberCycles.objects.filter(parsing_session=self.session).first()
        values = self._get_number_cycles_data(self.participants, number_cycles_data)

        fig = go.Figure(data=[go.Bar(
            name='Кол-во циклов на лучшем отрезке',
            x=col_labels,
            y=values,
            marker_color='blue'
        )])

        fig.update_layout(
            yaxis_title='Кол-во циклов',
            barmode='group'
        )

        number_cycles_chart = fig.to_html(
            full_html=False,
            config={
                'displayModeBar': False,
                'displaylogo': False,
                'modeBarButtonsToAdd': ['toImage', 'zoomIn2d', 'zoomOut2d', 'autoScale2d']
            }
        )

        return number_cycles_chart

    def generate_underwater_part_chart(self) -> str:
        """
        Генерирует HTML код для столбчатой диаграммы подводной части.
        """
        col_labels = [participant.initials for participant in self.participants]

        underwater_parts_data = UnderwaterPart.objects.filter(parsing_session=self.session)
        data = self._get_underwater_parts_data(self.participants, underwater_parts_data)

        fig = go.Figure(data=[go.Bar(
            x=col_labels,
            y=data,
            name='Подводная часть (м)',
            marker_color='green'
        )])

        fig.update_layout(
            xaxis_tickangle=-45,
            yaxis_title='Подводная часть (м)',
        )

        underwater_part_chart = fig.to_html(
            full_html=False,
            config={
                'displayModeBar': False,
                'displaylogo': False,
                'modeBarButtonsToAdd': ['toImage', 'zoomIn2d', 'zoomOut2d', 'autoScale2d']
            }
        )

        return underwater_part_chart

    def generate_best_start_reaction_chart(self) -> str:
        """
        Генерирует HTML код для столбчатой диаграммы лучшей стартовой реакции.
        """
        col_labels = [participant.initials for participant in self.participants]
        reaction_times = [self._get_total_seconds(participant.reaction_time)
                          if participant.reaction_time else 0
                          for participant in self.participants]

        fig = go.Figure(data=[go.Bar(
            x=col_labels,
            y=reaction_times,
            name='Стартовая реакция (сек)',
            marker_color='blue'
        )])

        fig.update_layout(
            xaxis_tickangle=-45,
            yaxis_title='Стартовая реакция (сек)',
        )

        best_start_reaction_chart = fig.to_html(
            full_html=False,
            config={
                'displayModeBar': False,
                'displaylogo': False,
                'modeBarButtonsToAdd': ['toImage', 'zoomIn2d', 'zoomOut2d', 'autoScale2d']
            }
        )

        return best_start_reaction_chart

    def generate_start_finish_difference_chart(self) -> str:
        """
        Генерирует HTML код для столбчатой диаграммы
        лучшего процента изменения стартового и финишного отрезков.
        """
        col_labels = [participant.initials for participant in self.participants]
        data = self._get_start_finish_difference_data(self.participants)

        fig = go.Figure(data=[go.Bar(
            x=col_labels,
            y=data,
            marker_color='purple',
            text=[f"{val:.2f}" for val in data]
        )])

        fig.update_layout(
            yaxis={"title": 'Процент изменения (%)'},
        )

        start_finish_difference_chart = fig.to_html(
            full_html=False,
            config={
                'displayModeBar': False,
                'displaylogo': False,
                'modeBarButtonsToAdd': ['toImage', 'zoomIn2d', 'zoomOut2d', 'autoScale2d']
            }
        )

        return start_finish_difference_chart

    def generate_heat_map_chart(self) -> str:
        """
        Создает и возвращает тепловую карту для протокола данных.

        :return: HTML-код для отображения тепловой карты.
        """
        data = []
        row_labels = []
        col_labels = set()

        for participant in self.participants:
            split_times = participant.swimsplittime_set.all()
            if not split_times:
                col_labels.add(int(self.session.swim_length.replace('m', '')))
                break
            for split in split_times:
                distance = split.distance
                col_labels.add(distance)

        col_labels = sorted(col_labels)

        for participant in self.participants:
            row_labels.append(participant.initials)
            split_times = participant.swimsplittime_set.all()
            if not split_times:
                total_seconds = self._get_total_seconds(participant.result)
                row = {
                    int(self.session.swim_length.replace('m', '')): total_seconds
                }
            else:
                row = {
                    split.distance:
                        self._get_total_seconds(split.split_time) for split in split_times
                }

            row_data = [row.get(dist, None) for dist in col_labels]
            data.append(row_data)

        data = list(map(list, zip(*data)))

        col_labels_with_ranges = []
        previous_dist = 0
        for dist in col_labels:
            col_labels_with_ranges.append(f"{previous_dist}-{dist}м")
            previous_dist = dist

        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=row_labels,
            y=col_labels_with_ranges,
            colorscale='YlGnBu',
            text=[[f"{val:.2f}" if val is not None else "" for val in row] for row in data],
            hoverinfo="text"
        ))

        fig.update_layout(
            xaxis_nticks=36,
            yaxis={'title': 'Дистанция (м)'},
        )

        heat_map_chart = fig.to_html(
            full_html=False,
            config={
                'displayModeBar': False,
                'displaylogo': False,
                'modeBarButtonsToAdd': ['toImage', 'zoomIn2d', 'zoomOut2d', 'autoScale2d']
            }
        )

        return heat_map_chart

    def _get_total_seconds(self, time_obj: Optional[time]) -> float:
        """
        Возвращает общее количество секунд для объекта времени.

        :param time_obj: Объект времени.
        :return: Общее количество секунд.
        """
        if time_obj:
            return time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1e6
        return 0.0

    def _calculate_speed(self, participant: ProtocolData, distance: int) -> Optional[float]:
        """
        Рассчитывает скорость для участника на определенной дистанции.

        :param participant: Данные участника.
        :param distance: Дистанция.
        :return: Скорость (м/сек).
        """
        pool_length = int(self.session.pool_length.replace('m', ''))
        split_time = participant.swimsplittime_set.filter(distance=distance).first()
        if split_time:
            total_seconds = self._get_total_seconds(split_time.split_time)
            return pool_length / total_seconds
        if participant.result:
            total_seconds = self._get_total_seconds(participant.result)
            return pool_length / total_seconds
        return None

    def _get_start_finish_difference_data(self, participants: List[ProtocolData]) -> List[float]:
        """
        Получает данные для разницы времени между стартом и финишем.

        :param participants: Список участников.
        :return: Список разниц во времени (сек).
        """
        data = []
        for participant in participants:
            split_times = sorted(participant.swimsplittime_set.all(), key=lambda x: x.distance)
            if split_times:
                start_time = split_times[0].split_time
                end_time = split_times[-1].split_time
                start_seconds = self._get_total_seconds(start_time)
                end_seconds = self._get_total_seconds(end_time)
                time_difference = end_seconds - start_seconds
                data.append(time_difference)
            else:
                data.append(0)
        return data

    def _get_number_cycles_data(
            self, participants: List[ProtocolData], number_cycles_data: Optional[NumberCycles]
        ) -> List[int]:
        """
        Получает данные для количества циклов.

        :param participants: Список участников.
        :param number_cycles_data: Данные о количестве циклов.
        :return: Список значений количества циклов.
        """
        if not number_cycles_data:
            return [0] * len(participants)

        data = number_cycles_data.data
        return [int(data.get(str(participant.id), 0))
                if data.get(str(participant.id)) else 0
                for participant in participants]

    def _get_underwater_parts_data(
            self, participants: List[ProtocolData], underwater_parts_data: List[UnderwaterPart]
        ) -> List[float]:
        """
        Получает данные для подводной части.

        :param participants: Список участников.
        :param underwater_parts_data: Данные о подводной части.
        :return: Список значений подводной части.
        """
        underwater_parts = {}
        for part in underwater_parts_data:
            underwater_parts.update(part.data)

        data = []
        for participant in participants:
            participant_id = str(participant.id)
            if participant_id in underwater_parts:
                value = underwater_parts[participant_id]
                if value:
                    try:
                        value = float(value)
                    except ValueError:
                        value = 0
                else:
                    value = 0
                data.append(value)
            else:
                data.append(0)

        return data


class TableGenerator:
    """Класс для генерации таблиц."""

    def __init__(self, session, participants):
        self.session = session
        self.participants = participants

    def generate_average_speed_table(self) -> str:
        """
        Генерирует HTML код для таблицы средней скорости.

        :return: HTML код таблицы.
        """
        distances = sorted({
            split.distance
            for participant in self.participants
            for split in participant.swimsplittime_set.all()
        })

        row_labels = [
            f"{dist - int(self.session.pool_length.replace('m', '')) if i > 0 else 0}-{dist}м, м/сек"
            for i, dist in enumerate(distances)
        ] or [f"0-{self.session.swim_length.replace('m', '')}м, м/сек"]
        col_labels = [participant.initials for participant in self.participants]
        data = self._get_speed_data(self.participants, distances)

        average_speed_table = self._generate_table_html(row_labels, col_labels, data)

        return average_speed_table

    def generate_speed_drop_table(self) -> str:
        """
        Генерирует HTML код для таблицы падения скорости.

        :return: HTML код таблицы.
        """
        distances = sorted({
            split.distance
            for participant in self.participants
            for split in participant.swimsplittime_set.all()
        })

        row_labels = [
            f"{dist - int(self.session.pool_length.replace('m', '')) if i > 0 else 0}-{dist}м, %"
            for i, dist in enumerate(distances)
        ]
        col_labels = [participant.initials for participant in self.participants]
        data = self._get_speed_drop_data(self.participants, distances)

        speed_drop_table = self._generate_table_html(row_labels, col_labels, data)

        return speed_drop_table

    def generate_leader_gap_table(self) -> str:
        """
        Генерирует HTML код для таблицы отставания от лидера.

        :return: HTML код таблицы.
        """
        leader = next((p for p in self.participants if p.final_position == 1), None)

        if not leader:
            raise ValueError("Лидер не найден")

        distances = sorted({
            split.distance
            for participant in self.participants
            for split in participant.swimsplittime_set.all()
        }) or [int(self.session.swim_length.replace('m', ''))]

        row_labels = [
            f"{dist - int(self.session.pool_length.replace('m', '')) if i > 0 else 0}-{dist}м"
            for i, dist in enumerate(distances)
        ] or [f"0-{self.session.swim_length}м"]
        col_labels = [participant.initials for participant in self.participants]
        data = self._get_leader_gap_data(self.participants, distances, leader)

        leader_gap_table = self._generate_table_html(row_labels, col_labels, data)

        return leader_gap_table

    def generate_best_start_reaction_table(self) -> str:
        """
        Генерирует HTML код для таблицы лучшей стартовой реакции.

        :return: HTML код таблицы.
        """
        col_labels = [participant.initials for participant in self.participants]
        data = [
            self._get_total_seconds(participant.reaction_time)
            if participant.reaction_time else '-'
            for participant in self.participants
        ]
        row_labels = ['Лучшая стартовая реакция, сек']

        best_start_reaction_table = self._generate_table_html(row_labels, col_labels, [data])

        return best_start_reaction_table

    def generate_start_finish_difference_table(self) -> str:
        """
        Генерирует HTML код для таблицы лучшего процента изменения стартового и финишного отрезков.

        :return: HTML код таблицы.
        """
        row_labels = ["% изменения стартового и финишного отрезков, с"]
        col_labels = [participant.initials for participant in self.participants]

        data = self._get_start_finish_difference_data(self.participants)

        start_finish_difference_table = self._generate_table_html(row_labels, col_labels, [data])

        return start_finish_difference_table

    def generate_start_distance_table(self) -> str:
        """
        Генерирует HTML код для таблицы стартового отрезка 0-15.

        :return: HTML код таблицы.
        """
        col_labels = [participant.initials for participant in self.participants]
        row_labels = ['Стартовый отрезок 0-15, сек']

        start_distance_data = StartDistance.objects.filter(parsing_session=self.session).first()
        data = self._get_start_distance_data(self.participants, start_distance_data)

        start_distance_table = self._generate_table_html(row_labels, col_labels, data)

        return start_distance_table


    def generate_pace_table(self) -> str:
        """
        Генерирует HTML код для таблицы темпа в циклах на минуту на лучшем отрезке.

        :return: HTML код таблицы.
        """
        col_labels = [participant.initials for participant in self.participants]

        number_cycles_data = NumberCycles.objects.filter(parsing_session=self.session).first()
        pace_data = Pace.objects.filter(parsing_session=self.session).first()

        data = self._get_pace_data(self.participants, number_cycles_data, pace_data)
        row_labels = ['Темп ц/мин на лучшем отрезке']

        pace_table = self._generate_table_html(row_labels, col_labels, [data])

        return pace_table

    def generate_underwater_part_table(self) -> str:
        """
        Генерирует HTML код для таблицы подводной части.

        :return: HTML код таблицы.
        """
        row_labels = ["Подводная часть, м"]
        col_labels = [participant.initials for participant in self.participants]

        underwater_parts_data = UnderwaterPart.objects.filter(parsing_session=self.session)
        data = self._get_underwater_parts_data(self.participants, underwater_parts_data)

        underwater_part_table = self._generate_table_html(row_labels, col_labels, [data])
        return underwater_part_table

    def _generate_table_html(
            self, row_labels: List[str], col_labels: List[str], data: List[List[Any]]
        ) -> str:
        """
        Генерирует HTML код для таблицы.

        :param row_labels: Список меток строк.
        :param col_labels: Список меток колонок.
        :param data: Список списков данных для таблицы.
        :return: HTML код таблицы.
        """
        table_html = "<div class='table-responsive'> <table id='report-table'" \
                     "class='table table-bordered table-hover'><thead><tr><th></th>"
        for col in col_labels:
            table_html += f"<th>{col}</th>"
        table_html += "</tr></thead> <tbody class='text-center align-middle'>"

        for i, row in enumerate(data):
            table_html += f"<tr><td>{row_labels[i]}</td>"
            for cell in row:
                if cell is not None:
                    try:
                        cell = float(cell)
                        table_html += f"<td>{cell:.2f}</td>"
                    except ValueError:
                        table_html += f"<td>{cell}</td>"
                else:
                    table_html += "<td></td>"
            table_html += "</tr>"

        table_html += "</tbody></table></div>"

        return table_html

    def _get_total_seconds(self, time_obj: Optional[time]) -> float:
        """
        Возвращает общее количество секунд для объекта времени.

        :param time_obj: Объект времени.
        :return: Общее количество секунд.
        """
        if time_obj:
            return time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1e6
        return 0.0

    def _get_speed_data(
            self, participants: List[ProtocolData], distances: List[int]
        ) -> List[List[Optional[float]]]:
        """
        Получает данные о скорости для каждого участника и каждой дистанции.

        :param participants: Список участников.
        :param distances: Список дистанций.
        :return: Данные о скорости.
        """
        data = []
        pool_length = int(self.session.pool_length.replace('m', ''))
        for dist in distances or [int(self.session.swim_length.replace('m', ''))]:
            row = []
            for participant in participants:
                split_time = participant.swimsplittime_set.filter(distance=dist).first()
                if split_time:
                    total_seconds = self._get_total_seconds(split_time.split_time)
                    speed = pool_length / total_seconds
                elif not split_time and participant.result:
                    total_seconds = self._get_total_seconds(participant.result)
                    speed = pool_length / total_seconds
                else:
                    speed = None
                row.append(speed)
            data.append(row)
        return data

    def _get_speed_drop_data(
            self, participants: List[ProtocolData], distances: List[int]
        ) -> List[List[Optional[float]]]:
        """
        Получает данные о падении скорости для каждого участника и каждой дистанции.

        :param participants: Список участников.
        :param distances: Список дистанций.
        :return: Данные о падении скорости.
        """
        speed_data = {participant.initials: [] for participant in participants}
        pool_length = int(self.session.pool_length.replace('m', ''))

        for participant in participants:
            for dist in distances:
                split_time = participant.swimsplittime_set.filter(distance=dist).first()
                if split_time:
                    total_seconds = self._get_total_seconds(split_time.split_time)
                    speed = pool_length / total_seconds
                    speed_data[participant.initials].append(speed)
                else:
                    speed_data[participant.initials].append('-')

        data = []
        for dist_index, dist in enumerate(distances):
            row = []
            for participant in participants:
                initial_speed = speed_data[participant.initials][0]
                current_speed = speed_data[participant.initials][dist_index]
                if initial_speed and current_speed:
                    speed_drop = (current_speed / initial_speed) * 100
                elif dist_index == 0:
                    # Первая дистанция всегда 100%
                    speed_drop = 100.0
                else:
                    speed_drop = None
                row.append(speed_drop)
            data.append(row)

        return data

    def _get_leader_gap_data(
            self, participants: List[ProtocolData], distances: List[int], leader: ProtocolData
        ) -> List[List[Optional[float]]]:
        """
        Получает данные об отставании от лидера для каждого участника и каждой дистанции.

        :param participants: Список участников.
        :param distances: Список дистанций.
        :param leader: Лидер гонки.
        :return: Данные об отставании от лидера.
        """
        leader_times = {split.distance:
                            self._get_total_seconds(split.split_time)
                            for split in leader.swimsplittime_set.all()}
        if not leader_times:
            leader_times = {int(self.session.swim_length.replace('m', '')):
                                self._get_total_seconds(leader.result)}

        data = []
        for dist in distances:
            row = []
            leader_time = leader_times.get(dist, 0)
            for participant in participants:
                if participant.final_position == 1:
                    row.append(0.0)
                else:
                    split_time = participant.swimsplittime_set.filter(distance=dist).first()
                    if split_time:
                        total_seconds = self._get_total_seconds(split_time.split_time)
                        gap = total_seconds - leader_time
                    elif not split_time and participant.result:
                        total_seconds = self._get_total_seconds(participant.result)
                        gap = total_seconds - leader_time
                    else:
                        gap = None
                    row.append(gap)
            data.append(row)
        return data

    def _get_start_finish_difference_data(self, participants: List[ProtocolData]) -> List[float]:
        """
        Получает данные для разницы времени между стартом и финишем.

        :param participants: Список участников.
        :return: Список разниц во времени (сек).
        """
        data = []
        for participant in participants:
            split_times = sorted(participant.swimsplittime_set.all(), key=lambda x: x.distance)
            if split_times:
                start_time = split_times[0].split_time
                end_time = split_times[-1].split_time
                start_seconds = self._get_total_seconds(start_time)
                end_seconds = self._get_total_seconds(end_time)
                time_difference = end_seconds - start_seconds
                data.append(time_difference)
            else:
                data.append(0)
        return data

    def _get_start_distance_data(
            self, participants: List[ProtocolData], start_distance_data: Optional[StartDistance]
        ) -> List[List[str]]:
        """
        Получает данные для стартового отрезка 0-15.

        :param participants: Список участников.
        :param start_distance_data: Данные о стартовом отрезке.
        :return: Данные о стартовом отрезке.
        """
        if not start_distance_data:
            return [[]]

        data = start_distance_data.data
        return [[data.get(str(participant.id), '') for participant in participants]]

    def _get_pace_data(
            self, participants: List[ProtocolData],
            number_cycles_data: Optional[NumberCycles], pace_data: Optional[Pace]
        ) -> List[str]:
        """
        Получает данные для темпа.

        :param participants: Список участников.
        :param number_cycles_data: Данные о количестве циклов.
        :param pace_data: Данные о темпе.
        :return: Данные о темпе.
        """
        if not (number_cycles_data and pace_data):
            return [""] * len(participants)

        cycles = number_cycles_data.data
        paces = pace_data.data

        values = []
        for participant in participants:
            participant_id = str(participant.id)
            if participant_id in cycles and participant_id in paces:
                try:
                    cycle_count = int(cycles[participant_id])
                    pace_value = parse_time(paces[participant_id])
                    if pace_value is not None:
                        pace_in_seconds = self._get_total_seconds(pace_value)
                        pace_per_minute = (cycle_count / pace_in_seconds) * 60
                        values.append(f"{pace_per_minute:.2f}")
                    else:
                        values.append("-")
                except (ValueError, ZeroDivisionError):
                    values.append("-")
            else:
                values.append("-")
        return values

    def _get_underwater_parts_data(
            self, participants: List[ProtocolData], underwater_parts_data: List[UnderwaterPart]
        ) -> List[str]:
        """
        Получает данные для подводной части.

        :param participants: Список участников.
        :param underwater_parts_data: Данные о подводной части.
        :return: Данные о подводной части.
        """
        underwater_parts = {}
        for part in underwater_parts_data:
            underwater_parts.update(part.data)

        data = []
        for participant in participants:
            participant_id = str(participant.id)
            if participant_id in underwater_parts:
                value = underwater_parts[participant_id]
                data.append(f"{value}")
            else:
                data.append("")

        return data


def parse_time(time_str: str) -> Optional[time]:
    """
    Преобразует строку времени в объект time.

    :param time_str: строка времени в форматах minute:second.millisecond или second.millisecond.
    :return: объект time.
    """
    try:
        if ':' in time_str:
            minute, rest = time_str.split(':')
            second, millisecond = rest.split('.')
        else:
            minute = 0
            second, millisecond = time_str.split('.')

        minute = int(minute)
        second = int(second)
        millisecond = int(millisecond)

        return time(minute=minute, second=second, microsecond=millisecond * 10000)
    except ValueError as error:
        print(f"Ошибка при преобразовании значения времени: {error}, {time_str}")
        return None


def save_raw_data(data: List[str], output_path: str) -> None:
    """
    Сохраняет сырые данные в текстовый файл.

    :param data: Список строк для сохранения.
    :param output_path: Путь к выходному текстовому файлу.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in data:
            f.write(line + '\n')


def save_parse_data(protocol_data: Dict[str, Any], session: ParsingSession) -> None:
    """
    Сохраняет спарсенные данные по протоколам в ProtocolData и SwimSplitTime.

    :param protocol_data: Спарсенные данные из протоколов.
    :param session: Сессия парсинга.
    """
    protocol_fields = [field.name for field in ProtocolData._meta.get_fields()]

    sorted_participants = sorted(
        protocol_data['participants'],
        key=lambda x: x['final_position'] if x['final_position'] is not None else float('inf')
    )

    max_number_participants = int(get_setting_value('Number_participants'))

    for participant_data in sorted_participants:
        if (participant_data['result'] and
                participant_data['final_position'] is not None and
                participant_data['final_position'] <= max_number_participants):
            participant_data['parsing_session'] = session
            filtered_data = {
                key: value for key, value in participant_data.items()if key in protocol_fields
            }

            protocol_entry = ProtocolData.objects.create(**filtered_data)

            split_times_data = participant_data.get('split_times', [])
            split_times = [
                SwimSplitTime(protocol_data=protocol_entry, **split_time)
                for split_time in split_times_data
            ]

            SwimSplitTime.objects.bulk_create(split_times)


def get_setting_value(setting_name: str) -> Optional[str]:
    """
    Возвращает значение настройки по её имени.

    :param setting_name: Название настройки.
    :return: Значение настройки или None, если настройка не найдена.
    """
    try:
        setting = ParsingSettings.objects.get(setting_name=setting_name)
        return setting.setting_value
    except ParsingSettings.DoesNotExist:
        return None
