from django.contrib import admin
from . import models


@admin.register(models.ParsingSession)
class ParsingSessionAdmin(admin.ModelAdmin):
    "Описание модели Сессии парсинга"
    list_display = (
        'id', 'created', 'file_name',
        'link_video', 'pool_length', 'swim_length'
    )
    search_fields = ('created', 'file_name')
    list_filter = ('created', 'pool_length', 'swim_length')
    readonly_fields = ['created']
    fieldsets = (
        (None, {
            'fields': (
                'file_name', 'link_video', 'pool_length', 'swim_length',
            )
        }),
        ('Время создания', {
            'fields': ('created',)
        }),
    )


@admin.register(models.ProtocolData)
class ProtocolDataAdmin(admin.ModelAdmin):
    """
    Описание модели Данные об участниках заплывов
    из стартового и финального протоколов
    """
    list_display = (
        'parsing_session', 'initials', 'year_of_birth', 'final_category',
        'start_position', 'final_position', 'formatted_reaction_time',
        'formatted_result', 'points'
    )
    search_fields = ('initials', 'year_of_birth', 'final_category')
    list_filter = ['final_position']

    def formatted_reaction_time(self, obj):
        return self.format_time(obj.reaction_time)
    formatted_reaction_time.short_description = 'Время реакции'

    def formatted_result(self, obj):
        return self.format_time(obj.result)
    formatted_result.short_description = 'Результат'

    def format_time(self, time_field):
        if time_field:
            return time_field.strftime('%M:%S.%f')[:-4]
        return None


@admin.register(models.SwimSplitTime)
class SwimSplitTimeAdmin(admin.ModelAdmin):
    """
    Описание модели Время по участникам на промежуточных дистанциях
    """
    list_display = (
        'protocol_data', 'distance', 'formatted_split_time'
    )
    search_fields = ('protocol_data', 'distance')

    def formatted_split_time(self, obj):
        return self.format_time(obj.split_time)
    formatted_split_time.short_description = 'Время на промежуточной дистанции'

    def format_time(self, time_field):
        if time_field:
            return time_field.strftime('%M:%S.%f')[:-4]
        return None


@admin.register(models.ParsingSettings)
class ParsingSettingsAdmin(admin.ModelAdmin):
    """
    Описание модели Настройки парсинга
    """
    list_display = ('setting_name', 'setting_value')
    search_fields = ('setting_name',)


@admin.register(models.StartDistance)
class StartDistanceAdmin(admin.ModelAdmin):
    list_display = ('parsing_session', 'status')
    search_fields = ('parsing_session__file_name',)
    list_filter = ('status',)


@admin.register(models.AverageSpeed)
class AverageSpeedAdmin(admin.ModelAdmin):
    list_display = ('parsing_session', 'status')
    search_fields = ('parsing_session__file_name',)
    list_filter = ('status',)


@admin.register(models.NumberCycles)
class NumberCyclesAdmin(admin.ModelAdmin):
    list_display = ('parsing_session', 'status')
    search_fields = ('parsing_session__file_name',)
    list_filter = ('status',)


@admin.register(models.Pace)
class PaceAdmin(admin.ModelAdmin):
    list_display = ('parsing_session', 'status')
    search_fields = ('parsing_session__file_name',)
    list_filter = ('status',)


@admin.register(models.SpeedDrop)
class SpeedDropAdmin(admin.ModelAdmin):
    list_display = ('parsing_session', 'status')
    search_fields = ('parsing_session__file_name',)
    list_filter = ('status',)


@admin.register(models.LeaderGap)
class LeaderGapAdmin(admin.ModelAdmin):
    list_display = ('parsing_session', 'status')
    search_fields = ('parsing_session__file_name',)
    list_filter = ('status',)


@admin.register(models.UnderwaterPart)
class UnderwaterPartAdmin(admin.ModelAdmin):
    list_display = ('parsing_session', 'status')
    search_fields = ('parsing_session__file_name',)
    list_filter = ('status',)


@admin.register(models.BestStartReaction)
class BestStartReactionAdmin(admin.ModelAdmin):
    list_display = ('parsing_session', 'status')
    search_fields = ('parsing_session__file_name',)
    list_filter = ('status',)


@admin.register(models.BestStartFinishPercentage)
class BestStartFinishPercentageAdmin(admin.ModelAdmin):
    list_display = ('parsing_session', 'status')
    search_fields = ('parsing_session__file_name',)
    list_filter = ('status',)


@admin.register(models.HeatMap)
class HeatMapAdmin(admin.ModelAdmin):
    list_display = ('parsing_session', 'status')
    search_fields = ('parsing_session__file_name',)
    list_filter = ('status',)
