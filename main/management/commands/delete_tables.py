from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import *


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('tables', nargs='+', type=str)

    def handle(self, *args, **options):
        for table in options['tables']:
            if table == 'User':
                User.objects.filter(is_staff=False).delete()
                continue
            ModelObj = globals()[table]
            ModelObj.objects.all().delete()
