import os
from django.shortcuts import render
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from main.models import Dish


def worker(func):
    def wrapper(request):
        if os.environ.get('ROLE', '') == 'WORKER':
            return func(request)
        return HttpResponseBadRequest('BAD REQUEST')
    return wrapper


@csrf_exempt
@worker
def backup_db(request):
    call_command('dbbackup')
    return HttpResponse('OK')


@csrf_exempt
@worker
def randomise_dishes(request):
    for dish in Dish.objects.all():
        dish.randomise()
    return HttpResponse('OK')
