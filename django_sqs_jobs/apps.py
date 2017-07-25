from django.apps import AppConfig
from .queues import SQSQueue

WORKER_QUEUE = SQSQueue()


class DjangoSqsJobsConfig(AppConfig):
    name = 'django_sqs_jobs'
