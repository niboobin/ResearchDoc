import re

from django import template
from django.template.defaultfilters import timesince
from django.utils import timezone
from django.utils.html import escape, strip_tags
from django.utils.safestring import mark_safe

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


@register.filter
def highlight(text, query):
    """Wrap query matches in <mark> for emphasis. Escapes the source text."""
    if not text:
        return ''
    text = strip_tags(str(text))
    if not query:
        return mark_safe(escape(text))
    terms = [re.escape(t) for t in query.split() if t.strip()]
    if not terms:
        return mark_safe(escape(text))
    pattern = re.compile(r'(' + '|'.join(terms) + r')', re.IGNORECASE)
    out = []
    for chunk in pattern.split(escape(text)):
        if pattern.fullmatch(chunk):
            out.append(f'<mark class="bg-[#0d9488]/30 text-[#5eead4] rounded px-0.5">{chunk}</mark>')
        else:
            out.append(chunk)
    return mark_safe(''.join(out))


@register.filter
def snippet(text, query, length=180):
    """
    Return a short snippet from text — centred around the first query match if any.
    HTML is stripped from the source.
    """
    if not text:
        return ''
    body = strip_tags(str(text)).strip()
    if not body:
        return ''
    if not query:
        return body[:length] + ('…' if len(body) > length else '')
    terms = [t for t in query.split() if t.strip()]
    if not terms:
        return body[:length] + ('…' if len(body) > length else '')
    lower = body.lower()
    first = -1
    for term in terms:
        idx = lower.find(term.lower())
        if idx != -1 and (first == -1 or idx < first):
            first = idx
    if first == -1:
        return body[:length] + ('…' if len(body) > length else '')
    start = max(0, first - length // 3)
    end = min(len(body), start + length)
    out = body[start:end]
    if start > 0:
        out = '… ' + out
    if end < len(body):
        out = out + ' …'
    return out
