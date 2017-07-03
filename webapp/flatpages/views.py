from django.shortcuts import render


def load_flatpage(request, page):
    return render(request, 'flatpages/%s.html' % page, {'title': page.title()})
