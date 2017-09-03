from django.shortcuts import render
from django.http import Http404
from django.template import TemplateDoesNotExist
from main.models import Recipe



def load_flatpage(request, page='home'):
    context = {'title': page.title(), 'num_recipes': '{:0,}'.format(Recipe.objects.count())}
    try:
        return render(request, 'flatpages/%s.html' % page, context)
    except TemplateDoesNotExist:
        raise Http404('Page {} not found'.format(page))
