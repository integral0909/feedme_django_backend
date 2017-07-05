import os
from django.shortcuts import render
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from main.models import Dish, Recipe
from common.utils.async import run_chunked_iter


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
    dishes = Dish.objects.all()

    def func(items):
        [d.randomise() for d in items]
    run_chunked_iter(dishes, func, num_threads=24)
    return HttpResponse('OK')


@csrf_exempt
@worker
def randomise_recipes(request):
    recipes = Recipe.objects.all()

    def func(items):
        [d.randomise() for d in items]
    run_chunked_iter(recipes, func, num_threads=24)
    return HttpResponse('OK')


@csrf_exempt
@worker
def validate_dish_integrity(request):
    dishes = Dish.objects.all()

    def func(items):
        [d.check_integrity() for d in items]
    run_chunked_iter(dishes, func, num_threads=24)
    return HttpResponse('OK')


@csrf_exempt
@worker
def validate_recipe_integrity(request):
    recipes = Recipe.objects.all()

    def func(items):
        [d.check_integrity() for d in items]
    run_chunked_iter(recipes, func, num_threads=24)
    return HttpResponse('OK')
