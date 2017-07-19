import os
from django.shortcuts import render
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from main.models import Dish, Recipe
from data_entry.models import RecipeDraft
from common.utils.async import run_chunked_iter
import boto3


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
    dsh = Dish.objects.all()
    run_chunked_iter(dsh, lambda items: [d.randomise() for d in items], num_threads=24)
    return HttpResponse('OK')


@csrf_exempt
@worker
def randomise_recipes(request):
    rec = Recipe.objects.all()
    run_chunked_iter(rec, lambda items: [d.randomise() for d in items], num_threads=24)
    return HttpResponse('OK')


@csrf_exempt
@worker
def validate_dish_integrity(request):
    dsh = Dish.objects.all()
    run_chunked_iter(dsh, lambda items: [d.check_integrity() for d in items], num_threads=24)
    return HttpResponse('OK')


@csrf_exempt
@worker
def validate_recipe_integrity(request):
    rec = Recipe.objects.all()
    run_chunked_iter(rec, lambda items: [d.check_integrity() for d in items], num_threads=24)
    return HttpResponse('OK')


@csrf_exempt
@worker
def process_draft_recipes(request):
    rcpds = RecipeDraft.objects.exclude(image_url_raw__isnull=True).filter(image_url='')
    s3 = boto3.resource('s3')
    run_chunked_iter(rcpds[:84], lambda itms: [r.prepopulate_image(s3) for r in itms], num_threads=12)