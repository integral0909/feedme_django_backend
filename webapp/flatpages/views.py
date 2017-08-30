from django.shortcuts import render
from main.models import Recipe


def load_flatpage(request, page='home'):
    context = {'title': page.title(), 'num_recipes': '{:0,}'.format(Recipe.objects.count())}
    return render(request, 'flatpages/%s.html' % page, context)
