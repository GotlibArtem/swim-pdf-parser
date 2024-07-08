from django import forms
from .models import ParsingSession
from swim_graph_utils import constants


class UploadFileForm(forms.Form):
    "Форма для загрузки файлов."
    link_video = forms.URLField(
        label='Укажите ссылку на видео:',
        required=True,
        widget=forms.URLInput(
            attrs={'class': 'form-control border-primary'}
        )
    )
    start_list_file = forms.FileField(
        label='Загрузите стартовый протокол:',
        required=True,
        widget=forms.ClearableFileInput(
            attrs={'class': 'form-control-file'}
        )
    )
    results_file = forms.FileField(
        label='Загрузите финальный протокол:',
        required=True,
        widget=forms.ClearableFileInput(
            attrs={'class': 'form-control-file'}
        )
    )


class ReportSetupForm(forms.Form):
    "Форма настройки отчета"
    file_name = forms.CharField(
        max_length=256,
        label='Название отчета:',
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control border-primary'}
        )
    )
    swim_length = forms.ChoiceField(
        choices=constants.SwimLength.choices(),
        label='Длина заплыва:',
        required=True,
        widget=forms.Select(
            attrs={'class': 'form-control border-primary'}
        )
    )
    pool_length = forms.ChoiceField(
        choices=constants.PoolLength.choices(),
        label='Метраж бассейна:',
        required=True,
        widget=forms.Select(
            attrs={'class': 'form-control border-primary'}
        )
    )

    # 1. Стартовый отрезок
    status_start_distance = forms.BooleanField(
        required=False,
        label='Включать в отчет',
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input',
                   'role': 'switch'}
            )
    )

    # 2. Средняя скорость каждые 25/50 м
    status_average_speed = forms.BooleanField(
        required=False,
        label='Включать в отчет',
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input',
                   'role': 'switch'}
            )
    )

    # 3. Количество циклов на лучшем отрезке
    status_number_cycles = forms.BooleanField(
        required=False,
        label='Включать в отчет',
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input',
                   'role': 'switch'}
            )
    )

    # 4. Темп на лучшем отрезке
    status_pace = forms.BooleanField(
        required=False,
        label='Включать в отчет',
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input',
                   'role': 'switch'}
            )
    )

    # 5. Падение скорости каждые 25/50 м
    status_speed_drop = forms.BooleanField(
        required=False,
        label='Включать в отчет',
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input',
                   'role': 'switch'}
            )
    )

    # 6. Отставание от лидера каждые 25/50 м
    status_leader_gap = forms.BooleanField(
        required=False,
        label='Включать в отчет',
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input',
                   'role': 'switch'}
            )
    )

    # 7. Подводная часть
    status_underwater_part = forms.BooleanField(
        required=False,
        label='Включать в отчет',
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input',
                   'role': 'switch'}
            )
    )

    # 8. Лучшая стартовая реакция
    status_best_start_reaction = forms.BooleanField(
        required=False,
        label='Включать в отчет',
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input',
                   'role': 'switch'}
            )
    )

    # 9. Лучший процент изменения стартового и финишного отрезков
    status_best_start_finish_percentage = forms.BooleanField(
        required=False,
        label='Включать в отчет',
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input',
                   'role': 'switch'}
            )
    )

    # 10. Тепловая карта
    status_heat_map = forms.BooleanField(
        required=False,
        label='Включать в отчет',
        initial=True,
        widget=forms.CheckboxInput(
            attrs={'class': 'form-check-input',
                   'role': 'switch'}
            )
    )
