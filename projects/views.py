import re
from datetime import datetime
from itertools import chain

import bleach
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    Citation,
    ComparisonTable,
    Project,
    Resource,
    ResourceTag,
    Summary,
    Tag,
)


def _greeting(now=None):
    h = (now or timezone.localtime()).hour
    if h < 12:
        return 'Good morning'
    if h < 18:
        return 'Good afternoon'
    return 'Good evening'


def _word_count(html):
    text = re.sub(r'<[^>]+>', ' ', html or '')
    return len(text.split())

ALLOWED_TAGS = [
    'p', 'h1', 'h2', 'h3', 'h4',
    'strong', 'em', 'u', 's',
    'ul', 'ol', 'li',
    'blockquote', 'code', 'pre', 'br',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'span',
]
ALLOWED_ATTRS = {'*': ['class', 'data-citation-id']}
_DANGEROUS_BLOCK = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.IGNORECASE | re.DOTALL)


def sanitize_html(raw: str) -> str:
    raw = _DANGEROUS_BLOCK.sub('', raw or '')
    return bleach.clean(raw, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def _parse_tags(raw: str):
    return [t.strip() for t in (raw or '').split(',') if t.strip()]


_LANDING_FEATURES = [
    {
        'title': 'Research projects',
        'body': 'Self-contained workspaces — group resources, summaries, and tables under a clear focus area.',
        'icon': '<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/></svg>',
    },
    {
        'title': 'Resource library',
        'body': 'Upload PDFs or link articles. Track authors, year, venue, and your own annotations.',
        'icon': '<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z M14 3v6h6 M8 13h8 M8 17h6"/></svg>',
    },
    {
        'title': 'Structured writing',
        'body': 'Compose summaries with inline citation chips that link straight back to the source paper.',
        'icon': '<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16 3 21 8 8 21H3v-5z"/></svg>',
    },
    {
        'title': 'Comparison tables',
        'body': 'Side-by-side product and method comparisons with custom rows, columns, and rich content cells.',
        'icon': '<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18 M3 16h18 M9 4v16 M15 4v16"/></svg>',
    },
    {
        'title': 'Full-text search',
        'body': 'Search every project, resource, and summary at once. Filter by type, date, or project.',
        'icon': '<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path stroke-linecap="round" stroke-linejoin="round" d="m21 21-4.3-4.3"/></svg>',
    },
    {
        'title': 'AI summaries',
        'body': 'One-click structured annotations: argument, methodology, findings, limitations. Edit before saving.',
        'icon': '<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2 2M16 16l2 2M18 6l-2 2M8 16l-2 2"/></svg>',
    },
]

_LANDING_STEPS = [
    {
        'n': '01', 'title': 'Create project', 'body': 'Define a focus area and invite collaborators.',
        'icon': '<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/></svg>',
    },
    {
        'n': '02', 'title': 'Upload sources', 'body': 'Drop PDFs and paste links. Metadata auto-fills.',
        'icon': '<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M17 8l-5-5-5 5 M12 3v12"/></svg>',
    },
    {
        'n': '03', 'title': 'Generate summaries', 'body': 'AI extracts argument, methodology, findings.',
        'icon': '<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2 2M16 16l2 2M18 6l-2 2M8 16l-2 2"/></svg>',
    },
    {
        'n': '04', 'title': 'Write & cite', 'body': 'Draft with inline citations and comparison tables.',
        'icon': '<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16 3 21 8 8 21H3v-5z"/></svg>',
    },
]

_LANDING_SOURCES = [
    {'title': 'Switch Transformer: Scaling to Trillion Parameter Mod…', 'authors': 'Fedus et al.', 'year': 2022},
    {'title': 'GShard: Scaling Giant Models with Conditional Comput…', 'authors': 'Lepikhin et al.', 'year': 2021},
    {'title': 'Mixtral of Experts — Technical Report', 'authors': 'Mistral AI', 'year': 2024},
    {'title': 'ST-MoE: Designing Stable and Transferable Sparse Exp…', 'authors': 'Zoph et al.', 'year': 2022},
]


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html', {
        'full_width': True,
        'features': _LANDING_FEATURES,
        'steps': _LANDING_STEPS,
        'landing_sources': _LANDING_SOURCES,
    })


@login_required
def dashboard(request):
    projects_qs = Project.objects.filter(user=request.user)
    resources_qs = Resource.objects.filter(project__user=request.user)
    summaries_qs = Summary.objects.filter(project__user=request.user)
    comparisons_qs = ComparisonTable.objects.filter(project__user=request.user)

    project_count = projects_qs.count()
    resource_count = resources_qs.count()
    summary_count = summaries_qs.count()
    citation_count = Citation.objects.filter(summary__project__user=request.user).count()
    word_count = sum(_word_count(s.body) for s in summaries_qs.only('body'))

    recent_projects = []
    for p in projects_qs[:4]:
        rcount = p.resources.count()
        scount = p.summaries.count()
        progress = min(100, int((scount / rcount) * 100)) if rcount else 0
        recent_projects.append({
            'project': p,
            'resources': rcount,
            'summaries': scount,
            'progress': progress,
        })

    activity = []
    for r in resources_qs.order_by('-created_at')[:3]:
        activity.append({'kind': 'resource', 'object': r, 'when': r.created_at})
    for s in summaries_qs.order_by('-updated_at')[:3]:
        activity.append({'kind': 'summary', 'object': s, 'when': s.updated_at})
    for c in comparisons_qs.order_by('-created_at')[:2]:
        activity.append({'kind': 'comparison', 'object': c, 'when': c.created_at})
    activity.sort(key=lambda a: a['when'], reverse=True)
    activity = activity[:6]

    ai_queue = list(resources_qs.filter(annotation='').order_by('-created_at')[:5])

    return render(request, 'dashboard.html', {
        'greeting': _greeting(),
        'project_count': project_count,
        'resource_count': resource_count,
        'summary_count': summary_count,
        'citation_count': citation_count,
        'word_count': word_count,
        'recent_projects': recent_projects,
        'activity': activity,
        'ai_queue': ai_queue,
    })


@login_required
def project_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return render(request, 'projects/form.html', {
                'errors': ['Title is required.'],
                'form_title': '',
                'form_description': request.POST.get('description', ''),
            })
        project = Project.objects.create(
            user=request.user,
            title=title,
            description=request.POST.get('description', ''),
        )
        messages.success(request, f'Project &ldquo;{project.title}&rdquo; created.')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'projects/form.html', {})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    return render(request, 'projects/detail.html', {
        'project': project,
        'resources': project.resources.all(),
        'summaries': project.summaries.all(),
        'comparisons': project.comparisons.all(),
    })


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return render(request, 'projects/form.html', {
                'project': project,
                'errors': ['Title is required.'],
                'form_title': '',
                'form_description': request.POST.get('description', project.description),
            })
        project.title = title
        project.description = request.POST.get('description', project.description)
        project.save()
        messages.success(request, 'Project updated.')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'projects/form.html', {
        'project': project,
        'form_title': project.title,
        'form_description': project.description,
    })


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == 'POST':
        title = project.title
        project.delete()
        messages.success(request, f'Project &ldquo;{title}&rdquo; deleted.')
        return redirect('dashboard')
    return render(request, 'projects/confirm_delete.html', {
        'project': project,
        'resource_count': project.resources.count(),
        'summary_count': project.summaries.count(),
        'comparison_count': project.comparisons.count(),
    })


def _save_resource_tags(resource, raw_tags):
    names = _parse_tags(raw_tags)
    ResourceTag.objects.filter(resource=resource).delete()
    for name in names:
        tag, _ = Tag.objects.get_or_create(name=name)
        ResourceTag.objects.get_or_create(resource=resource, tag=tag)


def _resource_form_ctx(project, resource=None, post=None):
    """Build form context dict from a resource (edit) or POST (validation re-render)."""
    if post is not None:
        return {
            'project': project,
            'resource': resource,
            'form_type': post.get('type', 'link'),
            'form_title': post.get('title', ''),
            'form_authors': post.get('authors', ''),
            'form_year': post.get('year', ''),
            'form_url': post.get('url', ''),
            'form_annotation': post.get('annotation', ''),
            'form_tags': post.get('tags', ''),
        }
    if resource is not None:
        return {
            'project': project,
            'resource': resource,
            'form_type': resource.type,
            'form_title': resource.title,
            'form_authors': resource.authors,
            'form_year': resource.year or '',
            'form_url': resource.url,
            'form_annotation': resource.annotation,
            'form_tags': ', '.join(resource.tags.values_list('name', flat=True)),
        }
    return {'project': project, 'form_type': 'link'}


def _parse_year(raw):
    raw = (raw or '').strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


@login_required
def resource_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            ctx = _resource_form_ctx(project, post=request.POST)
            ctx['errors'] = ['Title is required.']
            return render(request, 'resources/form.html', ctx)
        rtype = request.POST.get('type', 'link')
        resource = Resource.objects.create(
            project=project,
            title=title,
            authors=request.POST.get('authors', ''),
            year=_parse_year(request.POST.get('year')),
            type=rtype,
            url=request.POST.get('url', '') if rtype == 'link' else '',
            annotation=request.POST.get('annotation', ''),
            file_path=request.FILES.get('file_path') if rtype == 'pdf' else None,
        )
        _save_resource_tags(resource, request.POST.get('tags', ''))
        messages.success(request, f'Resource &ldquo;{resource.title}&rdquo; added.')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'resources/form.html', _resource_form_ctx(project))


@login_required
def resource_edit(request, pk):
    resource = get_object_or_404(Resource, pk=pk, project__user=request.user)
    project = resource.project
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            ctx = _resource_form_ctx(project, resource=resource, post=request.POST)
            ctx['errors'] = ['Title is required.']
            return render(request, 'resources/form.html', ctx)
        resource.title = title
        resource.authors = request.POST.get('authors', '')
        resource.year = _parse_year(request.POST.get('year'))
        resource.type = request.POST.get('type', resource.type)
        resource.url = request.POST.get('url', '') if resource.type == 'link' else ''
        resource.annotation = request.POST.get('annotation', '')
        if resource.type == 'pdf' and request.FILES.get('file_path'):
            resource.file_path = request.FILES['file_path']
        resource.save()
        _save_resource_tags(resource, request.POST.get('tags', ''))
        messages.success(request, 'Resource updated.')
        return redirect('project_detail', pk=project.pk)
    return render(request, 'resources/form.html', _resource_form_ctx(project, resource=resource))


@login_required
def resource_delete(request, pk):
    resource = get_object_or_404(Resource, pk=pk, project__user=request.user)
    if request.method == 'POST':
        project_pk = resource.project.pk
        title = resource.title
        resource.delete()
        messages.success(request, f'Resource &ldquo;{title}&rdquo; deleted.')
        return redirect('project_detail', pk=project_pk)
    return render(request, 'resources/confirm_delete.html', {
        'resource': resource,
        'citation_count': resource.citations.count(),
    })


@login_required
def summary_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    summary = Summary.objects.create(
        project=project,
        title=request.POST.get('title', 'Untitled Summary') if request.method == 'POST' else 'Untitled Summary',
        body='',
    )
    return redirect('summary_edit', pk=summary.pk)


@login_required
def summary_edit(request, pk):
    summary = get_object_or_404(Summary, pk=pk, project__user=request.user)
    if request.method == 'POST':
        summary.title = request.POST.get('title', summary.title).strip() or summary.title
        summary.body = sanitize_html(request.POST.get('body', ''))
        summary.save()

        citation_ids = {
            int(rid) for rid in request.POST.getlist('citation_ids[]') if rid.isdigit()
        }
        valid_ids = set(
            Resource.objects.filter(
                pk__in=citation_ids, project__user=request.user
            ).values_list('pk', flat=True)
        )
        existing = set(
            Citation.objects.filter(summary=summary).values_list('resource_id', flat=True)
        )
        Citation.objects.filter(summary=summary, resource_id__in=existing - valid_ids).delete()
        for rid in valid_ids - existing:
            Citation.objects.create(summary=summary, resource_id=rid)
        messages.success(request, 'Summary saved.')
        return redirect('summary_edit', pk=summary.pk)

    resources = summary.project.resources.all()
    cited_ids = set(Citation.objects.filter(summary=summary).values_list('resource_id', flat=True))
    return render(request, 'summaries/edit.html', {
        'summary': summary,
        'resources': resources,
        'cited_ids': cited_ids,
    })


@login_required
def summary_delete(request, pk):
    summary = get_object_or_404(Summary, pk=pk, project__user=request.user)
    if request.method == 'POST':
        project_pk = summary.project.pk
        title = summary.title
        summary.delete()
        messages.success(request, f'Summary &ldquo;{title}&rdquo; deleted.')
        return redirect('project_detail', pk=project_pk)
    return render(request, 'summaries/confirm_delete.html', {
        'summary': summary,
        'citation_count': summary.citations.count(),
    })


@login_required
def comparison_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, user=request.user)
    comparison = ComparisonTable.objects.create(
        project=project,
        title=request.POST.get('title', 'Untitled Comparison') if request.method == 'POST' else 'Untitled Comparison',
        body='',
    )
    return redirect('comparison_edit', pk=comparison.pk)


@login_required
def comparison_edit(request, pk):
    comparison = get_object_or_404(ComparisonTable, pk=pk, project__user=request.user)
    if request.method == 'POST':
        comparison.title = request.POST.get('title', comparison.title).strip() or comparison.title
        comparison.body = sanitize_html(request.POST.get('body', ''))
        comparison.save()
        messages.success(request, 'Comparison saved.')
        return redirect('comparison_edit', pk=comparison.pk)
    return render(request, 'comparisons/edit.html', {'comparison': comparison})


@login_required
def comparison_delete(request, pk):
    comparison = get_object_or_404(ComparisonTable, pk=pk, project__user=request.user)
    if request.method == 'POST':
        project_pk = comparison.project.pk
        title = comparison.title
        comparison.delete()
        messages.success(request, f'Comparison &ldquo;{title}&rdquo; deleted.')
        return redirect('project_detail', pk=project_pk)
    return render(request, 'comparisons/confirm_delete.html', {'comparison': comparison})


@login_required
def search(request):
    q = (request.GET.get('q') or '').strip()
    active = request.GET.get('type') or 'all'

    counts = {'projects': 0, 'resources': 0, 'summaries': 0, 'comparisons': 0}
    projects = resources = summaries = comparisons = []

    if q:
        projects_qs = Project.objects.filter(user=request.user).filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )
        resources_qs = Resource.objects.filter(project__user=request.user).filter(
            Q(title__icontains=q) | Q(authors__icontains=q) | Q(annotation__icontains=q)
        ).select_related('project')
        summaries_qs = Summary.objects.filter(project__user=request.user).filter(
            Q(title__icontains=q) | Q(body__icontains=q)
        ).select_related('project')
        comparisons_qs = ComparisonTable.objects.filter(project__user=request.user).filter(
            Q(title__icontains=q) | Q(body__icontains=q)
        ).select_related('project')

        counts = {
            'projects': projects_qs.count(),
            'resources': resources_qs.count(),
            'summaries': summaries_qs.count(),
            'comparisons': comparisons_qs.count(),
        }

        if active in ('all', 'projects'):
            projects = list(projects_qs[:50])
        if active in ('all', 'resources'):
            resources = list(resources_qs[:50])
        if active in ('all', 'summaries'):
            summaries = list(summaries_qs[:50])
        if active in ('all', 'comparisons'):
            comparisons = list(comparisons_qs[:50])

    total = sum(counts.values())

    return render(request, 'search.html', {
        'q': q,
        'active': active,
        'counts': counts,
        'total': total,
        'projects': projects,
        'resources': resources,
        'summaries': summaries,
        'comparisons': comparisons,
    })
