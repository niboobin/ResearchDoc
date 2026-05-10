from django import template
from django.template.defaultfilters import timesince
from django.utils import timezone

register = template.Library()


@register.filter
def time_ago(value):
    if not value:
        return ''
    now = timezone.now()
    delta = (now - value).total_seconds()
    if delta < 60:
        return 'just now'
    return timesince(value).split(',')[0].strip() + ' ago'
