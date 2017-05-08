from django.shortcuts import render
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from main.models import Dish


@csrf_exempt
def backup_db(request):
    call_command('dbbackup')
    return HttpResponse('OK')


@csrf_exempt
def randomise_dishes(request):
    for dish in Dish.objects.all():
        dish.randomise()
    return HttpResponse('OK')
