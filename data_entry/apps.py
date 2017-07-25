from django.apps import AppConfig
from django.db.models.signals import post_save
from data_entry.signals import enqueue_prepopulation
from data_entry.jobs import PrepopulateDraft
from django_sqs_jobs.apps import WORKER_QUEUE


class DataEntryConfig(AppConfig):
    name = 'data_entry'

    def ready(self):
        WORKER_QUEUE.add_allowed_jobs({'PrepopulateDraft': PrepopulateDraft})
        post_save.connect(enqueue_prepopulation, sender='data_entry.RecipeDraft')
