from django import template

register = template.Library()

@register.filter
def replace_dash_for_underscore(value):
    return value.replace("-","_")