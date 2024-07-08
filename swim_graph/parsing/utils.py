from datetime import datetime, timedelta, time
from typing import List, Dict
import re
import pandas as pd
import pdfplumber
import plotly.graph_objects as go

from swim_graph_utils.constants import (
    ParsingKeywords, SwimLength, INTERMEDIATE_SWIM_LENGTHS
)
from .models import (
    ProtocolData, ParsingSession, SwimSplitTime, ParsingSettings
)


class SwimParser:
    "Класс для парсинга стартового и финального протоколов"

    def __init__(self):
        self.parse_results = {
            'file_name': None,
            'swim_length': None,
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

    def parse_pdf(self, file) -> List[str]:
        """
        Парсит указанный PDF файл и
        возвращает извлеченные данные в виде списка строк.

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

    def process_start_list(self, data: List[str]) -> None:
        """
        Обрабатывает данные стартового протокола и
        сохраняет их в переменную parse_results.

        :param data: Список строк, извлеченных из PDF файла.
        """
        final_category = None

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

    def process_results(self, data: List[str]) -> None:
        """
        Обрабатывает данные финального протокола и
        сохраняет их в переменную parse_results.

        :param data: Список строк, извлеченных из PDF файла.
        """
        initials = None
        year_of_birth = None
        final_category = None
        last_final_position = 0

        for line in data:
            if self.contains_keyword(line, ParsingKeywords.FINAL_KEYWORDS):
                final_category = line
            elif any(keyword in line for keyword in INTERMEDIATE_SWIM_LENGTHS) and final_category:
                swim_times = self.parse_split_times(line)
                self.update_participant(initials, year_of_birth, swim_times)
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
                    'result': self.parse_time(parts[-2]),
                    'points': self.convert_to_int(parts[-1]),
                }
                self.update_participant(initials, year_of_birth, updates)

                last_final_position = final_position

    def update_participant(self, initials: str, year_of_birth: int, updates: Dict[str, any]) -> None:
        """
        Находит участника по значениям initials и year_of_birth и
        обновляет указанные ключи.

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

    def parse_split_times(self,
                          input_str: str) -> Dict[str, List[Dict[str, any]]]:
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

            # Найти все совпадения для паттерна
            matches = pattern.finditer(input_str)
            positions = [match.start() for match in matches]

            # Добавить конец строки как позицию для последнего сегмента
            positions.append(len(input_str))

            for i in range(len(positions) - 1):
                segment = input_str[positions[i]:positions[i+1]].strip()
                distance, time_segment = segment.split(':', 1)
                # Извлекаем второе значение времени
                time_values = time_segment.strip().split()
                if len(time_values) > 1:
                    key = distance.strip().replace('m', '')
                    split_times.append({'distance': int(key), 'split_time': self.parse_time(time_values[1].strip())})

            split_times = sorted(split_times, key=lambda x: x['distance'])

            return {'split_times': split_times}
        except (ValueError, TypeError) as error:
            print(f"Ошибка при парсинге времени заплыва: {error}")
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

    def contains_keyword(self, line: str, keywords: list) -> bool:
        """
        Проверяет, содержит ли строка одно из ключевых слов.

        :param line: Строка для проверки.
        :param keywords: Список ключевых слов.
        :return: True, если одно из ключевых слов найдено в строке,
        иначе False.
        """
        return any(re.search(r'\b' + re.escape(keyword) + r'\b', line) for keyword in keywords)

    def clean_line(self, line: str, substrings_to_remove: list) -> str:
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
            print(f"Ошибка при преобразовании строки в число: {error}")
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
            return self.parse_time(time_reaction)
        except (ValueError, TypeError) as error:
            print(f"Ошибка при преобразовании времени реакции: {error}")
            return None

    def parse_time(self, time_str: str) -> time:
        """
        Преобразует строку времени в объект time.

        :param time_str: строка времени в форматах
        minute:second.millisecond или second.millisecond
        :return: объект time
        """
        try:
            if ':' in time_str:
                # minute:second.millisecond
                minute, rest = time_str.split(':')
                second, millisecond = rest.split('.')
            else:
                # second.millisecond
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


def save_parse_data(protocol_data: Dict, session: ParsingSession) -> None:
    """
    Сохраняет спарсенные данные по протоколам в ProtocolData и SwimSplitTime.

    :param protocol_data: Спарсенные данные из протоколов.
    :param session: Сессия парсинга.
    """
    protocol_fields = [field.name for field in ProtocolData._meta.get_fields()]

    # Сортировка участников по полю final_position
    sorted_participants = sorted(
        protocol_data['participants'],
        key=lambda x: x['final_position'] if x['final_position'] is not None else float('inf')
    )
    # Кол-во участников для сохранения
    max_number_participants = int(get_setting_value('Number_participants'))

    for participant_data in sorted_participants:
        if (participant_data['result'] and
                participant_data['final_position'] is not None and
                participant_data['final_position'] <= max_number_participants):
            participant_data['parsing_session'] = session
            filtered_data = {key: value for key, value in participant_data.items() if key in protocol_fields}

            protocol_entry = ProtocolData.objects.create(**filtered_data)

            split_times_data = participant_data.get('split_times', [])

            split_times = [
                SwimSplitTime(protocol_data=protocol_entry, **split_time)
                for split_time in split_times_data
            ]

            SwimSplitTime.objects.bulk_create(split_times)


def get_setting_value(setting_name: str) -> str:
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


class ChartGenerator:
    def __init__(self, session, protocol_data):
        self.session = session
        self.protocol_data = protocol_data

    def generate_heat_map(self):
        """
        Создает и возвращает тепловую карту для протокола данных.

        :return:
            str: HTML-код для отображения тепловой карты.
        """
        participants = sorted(self.protocol_data, key=lambda x: x.start_position)

        data = []
        row_labels = []
        col_labels = set()

        # Получить все уникальные промежуточные дистанции или использовать swim_length и result
        for participant in participants:
            split_times = participant.swimsplittime_set.all()
            if not split_times:
                col_labels.add(int(self.session.swim_length.replace('m', '')))
                break
            for split in split_times:
                distance = split.distance
                col_labels.add(distance)

        col_labels = sorted(col_labels)

        # Создать строки данных для каждого пловца
        for participant in participants:
            row_labels.append(participant.initials)
            split_times = participant.swimsplittime_set.all()
            if not split_times:
                total_seconds = participant.result.minute * 60 + participant.result.second + participant.result.microsecond / 1e6
                row = {int(self.session.swim_length.replace('m', '')): total_seconds}
            else:
                row = {split.distance: split.split_time.minute * 60 + split.split_time.second + split.split_time.microsecond / 1e6 for split in split_times}

            # Заполнить отсутствующие значения None
            row_data = [row.get(dist, None) for dist in col_labels]
            data.append(row_data)

        # Развернуть данные для корректного отображения
        data = list(map(list, zip(*data)))

        # Создание меток промежутков
        col_labels_with_ranges = []
        previous_dist = 0
        for dist in col_labels:
            col_labels_with_ranges.append(f"{previous_dist}-{dist}м")
            previous_dist = dist

        # Создание тепловой карты
        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=row_labels,  # Участники по оси x
            y=col_labels_with_ranges,  # Промежуточные дистанции по оси y
            colorscale='YlGnBu',
            text=[[f"{val:.2f}" if val is not None else "" for val in row] for row in data],
            hoverinfo="text"
        ))

        fig.update_layout(
            xaxis_nticks=36,
            yaxis=dict(title='Дистанция (м)'),
        )

        config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToAdd': ['toImage', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetViews', 'toImage', 'toggleSpikelines']
        }

        heat_map = fig.to_html(full_html=False, config=config)

        return heat_map

    def generate_average_speed_table(self) -> str:
        """
        Генерирует HTML код для таблицы средней скорости.
        """
        participants = sorted(self.protocol_data, key=lambda x: x.start_position)
        distances = sorted({split.distance for participant in participants for split in participant.swimsplittime_set.all()})

        data = []
        pool_length = int(self.session.pool_length.replace('m', ''))
        row_labels = [f"{dist - pool_length if i > 0 else 0}-{dist}м, м/сек" for i, dist in enumerate(distances)] or [f"0-{self.session.swim_length.replace('m', '')}м, м/сек"]
        col_labels = [participant.initials for participant in participants]

        # Собираем данные для каждой дистанции или используем swim_length и result
        for dist in distances or [int(self.session.swim_length.replace('m', ''))]:
            row = []
            for participant in participants:
                split_time = participant.swimsplittime_set.filter(distance=dist).first()
                if split_time:
                    total_seconds = split_time.split_time.minute * 60 + split_time.split_time.second + split_time.split_time.microsecond / 1e6
                    speed = pool_length / total_seconds  # Используем дистанцию вместо pool_length
                elif not split_time and participant.result:
                    total_seconds = participant.result.minute * 60 + participant.result.second + participant.result.microsecond / 1e6
                    speed = pool_length / total_seconds
                else:
                    speed = None
                row.append(f"{speed:.3f}" if speed is not None else "")
            data.append(row)

        # Генерируем HTML таблицы
        table_html = "<div class='table-responsive'> <table id='speed-table' class='table table-bordered table-hover'><thead><tr><th></th>"
        for col in col_labels:
            table_html += f"<th>{col}</th>"
        table_html += "</tr></thead><tbody class='text-center align-middle'>"

        for i, row in enumerate(data):
            table_html += f"<tr><td>{row_labels[i]}</td>"
            for cell in row:
                table_html += f"<td>{cell}</td>"
            table_html += "</tr>"

        table_html += "</tbody></table> </div>"

        return table_html


    def generate_average_speed_chart(self) -> str:
        """
        Генерирует HTML код для столбчатой диаграммы средней скорости.
        """
        participants = sorted(self.protocol_data, key=lambda x: x.start_position)
        distances = sorted({split.distance for participant in participants for split in participant.swimsplittime_set.all()}) or [int(self.session.swim_length.replace('m', ''))]

        pool_length = int(self.session.pool_length.replace('m', ''))
        col_labels = [participant.initials for participant in participants]

        speed_data = {dist: [] for dist in distances}
        
        for participant in participants:
            for dist in distances:
                split_time = participant.swimsplittime_set.filter(distance=dist).first()
                if split_time:
                    total_seconds = split_time.split_time.minute * 60 + split_time.split_time.second + split_time.split_time.microsecond / 1e6
                    speed = pool_length / total_seconds  # Используем дистанцию вместо pool_length
                elif not split_time and participant.result:
                    total_seconds = participant.result.minute * 60 + participant.result.second + participant.result.microsecond / 1e6
                    speed = pool_length / total_seconds
                else:
                    speed = None
                speed_data[dist].append(speed)
        
        fig = go.Figure()

        bar_width = 0.2
        colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black', 'orange', 'purple', 'pink', 'brown', 'grey', 'lime', 'olive', 'navy', 'teal']
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
            width=2000,
            height=500
        )

        speed_chart = fig.to_html(full_html=False)

        return speed_chart


    def generate_speed_drop_table(self) -> str:
        """
        Генерирует HTML код для таблицы падения скорости.
        """
        participants = sorted(self.protocol_data, key=lambda x: x.start_position)
        distances = sorted({split.distance for participant in participants for split in participant.swimsplittime_set.all()})

        data = []
        pool_length = int(self.session.pool_length.replace('m', ''))
        row_labels = [f"{dist - pool_length if i > 0 else 0}-{dist}м, %" for i, dist in enumerate(distances)]
        col_labels = [participant.initials for participant in participants]

        # Создаем словарь для хранения скоростей по каждой дистанции для каждого участника
        speed_data = {participant.initials: [] for participant in participants}

        for participant in participants:
            for dist in distances:
                split_time = participant.swimsplittime_set.filter(distance=dist).first()
                if split_time:
                    total_seconds = split_time.split_time.minute * 60 + split_time.split_time.second + split_time.split_time.microsecond / 1e6
                    speed = pool_length / total_seconds
                    speed_data[participant.initials].append(speed)
                else:
                    speed_data[participant.initials].append(None)

        # Создаем таблицу падения скорости
        for dist_index, dist in enumerate(distances):
            row = []
            for participant in participants:
                initial_speed = speed_data[participant.initials][0]
                current_speed = speed_data[participant.initials][dist_index]
                if initial_speed and current_speed:
                    speed_drop = (current_speed / initial_speed) * 100
                elif dist_index == 0:
                    speed_drop = 100.0  # Первая дистанция всегда 100%
                else:
                    speed_drop = None
                row.append(speed_drop)
            data.append(row)

        table_html = "<div class='table-responsive'><table id='speed-table' class='table table-bordered table-hover'><thead><tr><th></th>"
        for col in col_labels:
            table_html += f"<th>{col}</th>"
        table_html += "</tr></thead><tbody class='text-center align-middle'>"

        for i, row in enumerate(data):
            table_html += f"<tr><td>{row_labels[i]}</td>"
            for cell in row:
                table_html += f"<td>{cell:.2f}</td>" if cell is not None else "<td></td>"
            table_html += "</tr>"

        table_html += "</tbody></table></div>"

        return table_html

    def generate_leader_gap_table(self) -> str:
        """
        Генерирует HTML код для таблицы отставания от лидера.
        """
        participants = sorted(self.protocol_data, key=lambda x: x.start_position)
        leader = next((p for p in participants if p.final_position == 1), None)

        if not leader:
            raise ValueError("Лидер не найден")

        distances = sorted({split.distance for participant in participants for split in participant.swimsplittime_set.all()}) or [int(self.session.swim_length.replace('m', ''))]
        
        # Получаем времена лидера для всех дистанций
        leader_times = {split.distance: split.split_time.minute * 60 + split.split_time.second + split.split_time.microsecond / 1e6 for split in leader.swimsplittime_set.all()}
        if not leader_times:
            leader_times = {int(self.session.swim_length.replace('m', '')): leader.result.minute * 60 + leader.result.second + leader.result.microsecond / 1e6}
        
        data = []
        pool_length = int(self.session.pool_length.replace('m', ''))
        row_labels = [f"{dist - pool_length if i > 0 else 0}-{dist}м" for i, dist in enumerate(distances)] or [f"0-{self.session.swim_length}м"]
        col_labels = [participant.initials for participant in participants]

        for dist in distances:
            row = []
            leader_time = leader_times.get(dist, 0)
            for participant in participants:
                if participant.final_position == 1:
                    row.append(0.0)  # Для лидера всегда 0
                else:
                    split_time = participant.swimsplittime_set.filter(distance=dist).first()
                    if split_time:
                        total_seconds = split_time.split_time.minute * 60 + split_time.split_time.second + split_time.split_time.microsecond / 1e6
                        gap = total_seconds - leader_time
                    elif not split_time and participant.result:
                        total_seconds = participant.result.minute * 60 + participant.result.second + participant.result.microsecond / 1e6
                        gap = total_seconds - leader_time
                    else:
                        gap = None
                    row.append(gap)
            data.append(row)

        table_html = "<div class='table-responsive'><table id='speed-table' class='table table-bordered table-hover'><thead><tr><th></th>"
        for col in col_labels:
            table_html += f"<th>{col}</th>"
        table_html += "</tr></thead><tbody class='text-center align-middle'>"

        for i, row in enumerate(data):
            table_html += f"<tr><td>{row_labels[i]}</td>"
            for cell in row:
                table_html += f"<td>{cell:.2f}</td>" if cell is not None else "<td></td>"
            table_html += "</tr>"

        table_html += "</tbody></table></div>"

        return table_html


    def generate_best_start_reaction_table(self) -> str:
        """
        Генерирует HTML код для таблицы лучшей стартовой реакции.
        """
        participants = sorted(self.protocol_data, key=lambda x: x.start_position)

        data = []
        col_labels = [participant.initials for participant in participants]

        # Собираем данные для лучшей стартовой реакции
        for participant in participants:
            if participant.reaction_time:
                total_seconds = participant.reaction_time.minute * 60 + participant.reaction_time.second + participant.reaction_time.microsecond / 1e6
            else:
                total_seconds = None
            data.append(total_seconds)

        # Создаем метку строки
        row_labels = ['Лучшая стартовая реакция, сек']

        # Генерируем HTML таблицы
        table_html = "<div class='table-responsive'> <table id='speed-table' class='table table-bordered table-hover'><thead><tr><th></th>"
        for col in col_labels:
            table_html += f"<th>{col}</th>"
        table_html += "</tr></thead><tbody class='text-center align-middle'>"

        table_html += f"<tr><td>{row_labels[0]}</td>"
        for cell in data:
            table_html += f"<td>{cell:.2f}</td>" if cell is not None else "<td>-</td>"
        table_html += "</tr>"

        table_html += "</tbody></table> </div>"

        return table_html

    def generate_best_start_reaction_chart(self) -> str:
        """
        Генерирует HTML код для столбчатой диаграммы лучшей стартовой реакции.
        """
        participants = sorted(self.protocol_data, key=lambda x: x.start_position)

        col_labels = [participant.initials for participant in participants]
        reaction_times = [participant.reaction_time.minute * 60 + participant.reaction_time.second + participant.reaction_time.microsecond / 1e6 if participant.reaction_time else 0 for participant in participants]

        fig = go.Figure(data=[go.Bar(
            x=col_labels,
            y=reaction_times,
            name='Стартовая реакция (сек)',
            marker_color='blue'
        )])

        fig.update_layout(
            xaxis_tickangle=-45,
            yaxis_title='Стартовая реакция (сек)',
            width=900,
            height=500
        )

        start_reaction_chart = fig.to_html(full_html=False)

        return start_reaction_chart

    def generate_start_finish_difference_table(self) -> str:
        """
        Генерирует HTML код для таблицы лучшего процента изменения стартового и финишного отрезков.
        """
        participants = sorted(self.protocol_data, key=lambda x: x.start_position)

        row_labels = ["% изменения стартового и финишного отрезков, с"]
        col_labels = [participant.initials for participant in participants]

        data = []
        for participant in participants:
            split_times = sorted(participant.swimsplittime_set.all(), key=lambda x: x.distance)
            if split_times:
                start_time = split_times[0].split_time
                end_time = split_times[-1].split_time
                start_seconds = start_time.minute * 60 + start_time.second + start_time.microsecond / 1e6
                end_seconds = end_time.minute * 60 + end_time.second + end_time.microsecond / 1e6
                time_difference = end_seconds - start_seconds
                data.append(f"{time_difference:.2f}")
            else:
                data.append("")

        # Генерируем HTML таблицы
        table_html = "<div class='table-responsive'> <table id='speed-table' class='table table-bordered table-hover'><thead><tr><th></th>"
        for col in col_labels:
            table_html += f"<th>{col}</th>"
        table_html += "</tr></thead><tbody class='text-center align-middle'>"

        table_html += f"<tr><td>{row_labels[0]}</td>"
        for cell in data:
            table_html += f"<td>{cell}</td>"
        table_html += "</tr>"

        table_html += "</tbody></table> </div>"

        return table_html

    def generate_start_finish_difference_chart(self) -> str:
        """
        Генерирует HTML код для столбчатой диаграммы лучшего процента изменения стартового и финишного отрезков.
        """
        participants = sorted(self.protocol_data, key=lambda x: x.start_position)

        col_labels = [participant.initials for participant in participants]
        data = []

        for participant in participants:
            split_times = sorted(participant.swimsplittime_set.all(), key=lambda x: x.distance)
            if split_times:
                start_time = split_times[0].split_time
                end_time = split_times[-1].split_time
                start_seconds = start_time.minute * 60 + start_time.second + start_time.microsecond / 1e6
                end_seconds = end_time.minute * 60 + end_time.second + end_time.microsecond / 1e6
                time_difference = end_seconds - start_seconds
                data.append(time_difference)
            else:
                data.append(0)

        fig = go.Figure(data=[go.Bar(
            x=col_labels,
            y=data,
            marker_color='purple',
            text=[f"{val:.2f}" for val in data]
        )])

        fig.update_layout(
            yaxis=dict(title='Процент изменения (%)'),
            width=900,
            height=500
        )

        start_finish_difference_chart = fig.to_html(full_html=False)

        return start_finish_difference_chart
