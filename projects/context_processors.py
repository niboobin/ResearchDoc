from .models import Project


def user_projects(request):
    if request.user.is_authenticated:
        return {'user_projects': Project.objects.filter(user=request.user)}
    return {}
