from django.conf import settings


def project_config(request):
    return {
        'project_title': settings.PROJECT_TITLE,
        'project_title_abbr': settings.PROJECT_TITLE_ABBR
    }
