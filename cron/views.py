import os
from django.shortcuts import render
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from main.models import Dish
from common.utils.async import run_chunked_iter


def worker(func):
    def wrapper(request):
        if os.environ.get('ROLE', '') == 'WORKER':
            return func(request)
        return HttpResponseBadRequest('BAD REQUEST')
    return wrapper


def func(dishes):
    for dish in dishes:
        dish.randomise()


@csrf_exempt
@worker
def backup_db(request):
    call_command('dbbackup')
    return HttpResponse('OK')


@csrf_exempt
@worker
def randomise_dishes(request):
    dishes = Dish.objects.all()
    run_chunked_iter(dishes, func, num_threads=24)
    return HttpResponse('OK')
