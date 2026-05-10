from django.contrib import admin

from .models import (
    Citation,
    ComparisonTable,
    Project,
    Resource,
    ResourceTag,
    Subscription,
    Summary,
    Tag,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at', 'updated_at']
    search_fields = ['title', 'description', 'user__username', 'user__email']
    list_filter = ['created_at']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'type', 'year', 'created_at']
    search_fields = ['title', 'authors', 'annotation']
    list_filter = ['type', 'year']


@admin.register(ResourceTag)
class ResourceTagAdmin(admin.ModelAdmin):
    list_display = ['resource', 'tag']
    search_fields = ['resource__title', 'tag__name']


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'created_at', 'updated_at']
    search_fields = ['title', 'body']


@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = ['summary', 'resource']
    search_fields = ['summary__title', 'resource__title']


@admin.register(ComparisonTable)
class ComparisonTableAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'created_at']
    search_fields = ['title']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'is_archived', 'created_at']
    list_filter = ['plan', 'is_archived']
    search_fields = ['user__username', 'user__email']
    actions = ['archive_subscriptions']

    @admin.action(description='Archive selected subscriptions')
    def archive_subscriptions(self, request, queryset):
        updated = queryset.update(is_archived=True)
        self.message_user(request, f'{updated} subscription(s) archived.')
