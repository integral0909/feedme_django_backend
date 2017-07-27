from django.apps import AppConfig
from django.db.models.signals import post_save
from main.signals import enqueue_onboarding


class MainConfig(AppConfig):
    name = 'main'

    def ready(self):
        post_save.connect(enqueue_onboarding, sender='main.Profile')
        # This post save is connected to profile because users are saved before profiles.
