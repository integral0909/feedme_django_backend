from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.contrib.admin.views.decorators import staff_member_required


@login_required
def home(request):
    return render(request, 'home.html')


@staff_member_required
def report(request):
    qs = User.objects.annotate(likes_count=Count('likes'))
    users_count = User.objects.count()
    context = {
        's100': qs.filter(likes_count__gte=100).count(),
        's50': qs.filter(likes_count__gte=50, likes_count__lte=99).count(),
        's20': qs.filter(likes_count__gte=20, likes_count__lte=49).count(),
        's1': qs.filter(likes_count__gte=1, likes_count__lte=19).count(),
        's0': qs.filter(likes_count=0).count(),
    }
    context['p100'] = '{:.2f}'.format((context['s100'] / users_count) * 100)
    context['p50'] = '{:.2f}'.format((context['s50'] / users_count) * 100)
    context['p20'] = '{:.2f}'.format((context['s20'] / users_count) * 100)
    context['p1'] = '{:.2f}'.format((context['s1'] / users_count) * 100)
    context['p0'] = '{:.2f}'.format((context['s0'] / users_count) * 100)
    return render(request, 'report.html', context)
