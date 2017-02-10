from django.apps import AppConfig


class CronConfig(AppConfig):
    """
    For use in Elastic Beanstalk worker environments.

    Cron tasks are mapped to a url, and when that url
    receives a request the task is executed.
    """
    name = 'cron'
