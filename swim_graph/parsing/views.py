from django.http import HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from .forms import UploadFileForm, ReportSetupForm
from .utils import (
    save_parse_data, get_setting_value,
    SwimParser, ChartGenerator
    )
from . import models


# Маппинг моделей и полей формы
SETTINGS_MAPPING = {
    models.StartDistance: 'status_start_distance',
    models.AverageSpeed: 'status_average_speed',
    models.NumberCycles: 'status_number_cycles',
    models.Pace: 'status_pace',
    models.SpeedDrop: 'status_speed_drop',
    models.LeaderGap: 'status_leader_gap',
    models.UnderwaterPart: 'status_underwater_part',
    models.BestStartReaction: 'status_best_start_reaction',
    models.BestStartFinishPercentage: 'status_best_start_finish_percentage',
    models.HeatMap: 'status_heat_map',
}


def upload_file_view(request):
    """
    Отображает форму для загрузки файлов и обрабатывает загруженные файлы.
    """
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            link_video = request.POST.get('link_video')
            start_list_file = request.FILES.get('start_list_file')
            results_file = request.FILES.get('results_file')

            # Проверка на наличие файлов
            if not start_list_file or not results_file:
                return HttpResponse("Файлы не загружены. Пожалуйста, загрузите оба файла.")

            # Парсинг файлов
            parser = SwimParser()
            start_list_data = parser.parse_pdf(start_list_file)
            results_data = parser.parse_pdf(results_file)

            # Обработка данных
            parser.process_start_list(start_list_data)
            parser.process_results(results_data)

            # Сохранение сессии парсинга и их результатов в базу данных
            session = models.ParsingSession.objects.create(
                file_name=parser.parse_results['file_name'],
                link_video=link_video,
                swim_length=parser.parse_results['swim_length']
            )
            save_parse_data(parser.parse_results, session)

            return redirect('report_setup', session_id=session.id)
        else:
            print("Form is not valid:", form.errors)
    else:
        form = UploadFileForm()

    return render(request, 'parsing/upload.html', {'form': form})


def report_setup_view(request, session_id):
    """
    Отображает форму для настройки таблиц/графиков отчета.
    """

    session = get_object_or_404(models.ParsingSession, id=session_id)
    participants = session.protocoldata_set.order_by('final_category', 'start_position')

    if request.method == 'POST':
        form = ReportSetupForm(request.POST)
        if form.is_valid():
            session.file_name = form.cleaned_data['file_name']
            session.pool_length = form.cleaned_data['pool_length']
            session.swim_length = form.cleaned_data['swim_length']
            session.save()

            # Сохранение статусов моделей
            for model, form_field in SETTINGS_MAPPING.items():
                status = form.cleaned_data[form_field]
                data = {}
                data_field_prefix = f"{form_field}_data_"
                for participant in participants:
                    field_name = f"{data_field_prefix}{participant.id}"
                    if field_name in request.POST:
                        data[str(participant.id)] = request.POST[field_name]

                if hasattr(model, 'data'):
                    model.objects.update_or_create(
                        parsing_session=session,
                        defaults={'status': status, 'data': data}
                    )
                else:
                    model.objects.update_or_create(
                        parsing_session=session,
                        defaults={'status': status}
                    )

        return redirect('session_results', session_id=session_id)
    else:
        initial_data = {
            'file_name': session.file_name,
            'swim_length': session.swim_length,
            'pool_length': session.pool_length,
        }
        form = ReportSetupForm(initial=initial_data)


    return render(
        request,
        'parsing/report_setup.html',
        {'form': form,
         'session': session,
         'participants': participants}
    )


def sessions_list_view(request):
    """
    Отображает список всех сессий парсинга.
    """
    reports = models.ParsingSession.objects.all().order_by('-created')

    search_term = ''
    # Поиск по наименованию отчета, длине заплыва и метражу бассейна
    if 'search' in request.GET:
        search_term = request.GET['search']
        reports = (reports.filter(file_name__icontains=search_term) |
                   reports.filter(swim_length__icontains=search_term) |
                   reports.filter(pool_length__icontains=search_term))

    # Пагинация
    paginator = Paginator(reports, 8)
    page = request.GET.get('page')
    sessions = paginator.get_page(page)
    get_dict_copy = request.GET.copy()
    params = get_dict_copy.pop('page', True) and get_dict_copy.urlencode()

    return render(
        request,
        'parsing/session_list.html',
        {
            'sessions': sessions,
            'params': params,
            'search_term': search_term,
        }
    )


def session_results_view(request, session_id):
    """
    Отображает результаты парсинга для указанной сессии.
    """
    num_participants = int(get_setting_value('Number_participants'))
    session = models.ParsingSession.objects.get(id=session_id)
    protocol_data = models.ProtocolData.objects.filter(parsing_session=session).order_by('final_position').prefetch_related('swimsplittime_set')
    protocol_data = list(protocol_data[:num_participants])

    active_settings = {}
    for model, form_field in SETTINGS_MAPPING.items():
        active_settings[form_field] = model.objects.filter(parsing_session=session, status=True).exists()

    session_charts = ChartGenerator(session, protocol_data)

    charts = {
        'start_distance_table': session_charts.generate_start_distance_table() if active_settings.get('status_start_distance') else None,
        'average_speed_chart': session_charts.generate_average_speed_chart() if active_settings.get('status_average_speed') else None,
        'average_speed_table': session_charts.generate_average_speed_table() if active_settings.get('status_average_speed') else None,
        'number_cycles_chart': session_charts.generate_number_cycles_chart() if active_settings.get('status_number_cycles') else None,
        'pace_table': session_charts.generate_pace_table() if active_settings.get('status_pace') and active_settings.get('status_number_cycles') else None,
        'speed_drop_table': session_charts.generate_speed_drop_table() if active_settings.get('status_speed_drop') else None,
        'leader_gap_table': session_charts.generate_leader_gap_table() if active_settings.get('status_leader_gap') else None,
        'underwater_part_table': session_charts.generate_underwater_part_table() if active_settings.get('status_underwater_part') else None,
        'underwater_part_chart': session_charts.generate_underwater_part_chart() if active_settings.get('status_underwater_part') else None,
        'start_reaction_table': session_charts.generate_best_start_reaction_table() if active_settings.get('status_best_start_reaction') else None,
        'start_reaction_chart': session_charts.generate_best_start_reaction_chart() if active_settings.get('status_best_start_reaction') else None,
        'start_finish_difference_table': session_charts.generate_start_finish_difference_table() if active_settings.get('status_best_start_finish_percentage') else None,
        'start_finish_difference_chart': session_charts.generate_start_finish_difference_chart() if active_settings.get('status_best_start_finish_percentage') else None,
        'heat_map': session_charts.generate_heat_map() if active_settings.get('status_heat_map') else None,
    }

    return render(
        request,
        'parsing/results.html',
        {
            'session': session,
            'protocol_data': protocol_data,
            'active_settings': active_settings,
            'charts': charts
        }
    )
