from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import *
from main.management.commands.load_firebase_dump import chunkify, run_chunked_iter


def worker_func(rests):
    for res in rests:
        ots = res.opening_times.all()
        for ot in ots:
            dupes = OpeningTime.objects.filter(
                restaurant=res, opens=ot.opens, closes=ot.closes,
                day_of_week=ot.day_of_week, valid_from=ot.valid_from,
                valid_through=ot.valid_through
            )
            dupecount = dupes.count()
            for idx, dupe in enumerate(dupes):
                if dupecount - idx == 1:
                    break
                else:
                    dupe.delete()


class Command(BaseCommand):
    def handle(self, *args, **options):
        rests = Restaurant.objects.all()
        run_chunked_iter(rests, worker_func)
