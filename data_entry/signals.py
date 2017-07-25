from django.dispatch import Signal
from django_sqs_jobs.apps import WORKER_QUEUE
from .jobs import PrepopulateDraft

pre_publish = Signal(providing_args=['draft', 'final'])
post_publish = Signal(providing_args=['draft', 'final', 'commit'])


def enqueue_prepopulation(sender, instance, created, **kwargs):
    if created:
        WORKER_QUEUE.append(PrepopulateDraft(instance, sender.__name__))