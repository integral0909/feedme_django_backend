from django.dispatch import Signal
from django_sqs_jobs.queues import SQSQueue
from .jobs import PrepopulateImage

pre_publish = Signal(providing_args=['draft', 'final'])
post_publish = Signal(providing_args=['draft', 'final', 'commit'])