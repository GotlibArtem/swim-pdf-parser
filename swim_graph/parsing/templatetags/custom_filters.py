from django import template

register = template.Library()

@register.filter
def time_format(value):
    if value:
        return value.strftime('%M:%S.%f')[:-4]
    return '-'


@register.filter
def concat_strings(str1, str2):
    return f"{str1}{str2}"


@register.filter
def get_item(dictionary, key):
    value = dictionary.get(str(key))
    if not value:
        return ""
    return value
