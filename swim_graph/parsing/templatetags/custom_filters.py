from django import template

register = template.Library()

@register.filter
def time_format(value):
    if value:
        return value.strftime('%M:%S.%f')[:-4]
    return '-'
