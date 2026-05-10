from django.conf import settings
from django.db import models


class Project(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Resource(models.Model):
    TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('link', 'Link'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='resources',
    )
    title = models.CharField(max_length=255)
    authors = models.CharField(max_length=500, blank=True)
    year = models.IntegerField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='link')
    file_path = models.FileField(upload_to='papers/', null=True, blank=True)
    url = models.URLField(blank=True)
    annotation = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, through='ResourceTag', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ResourceTag(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('resource', 'tag')


class Summary(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='summaries',
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class Citation(models.Model):
    summary = models.ForeignKey(
        Summary,
        on_delete=models.CASCADE,
        related_name='citations',
    )
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='citations',
    )

    class Meta:
        unique_together = ('summary', 'resource')


class ComparisonTable(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='comparisons',
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class Subscription(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
    )
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES, default='free')
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user} ({self.plan})'
