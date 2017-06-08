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
    return render(request, 'report.html')
