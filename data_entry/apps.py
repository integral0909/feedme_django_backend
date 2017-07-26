from django.apps import AppConfig
from django.db.models.signals import post_save
from data_entry.signals import enqueue_prepopulation


class DataEntryConfig(AppConfig):
    name = 'data_entry'

    def ready(self):
        post_save.connect(enqueue_prepopulation, sender='data_entry.RecipeDraft')
