from django.apps import AppConfig, apps
from .queues import SQSQueue
from .jobs import Job
from common.utils import merge_dicts

WORKER_QUEUE = SQSQueue()


class DjangoSqsJobsConfig(AppConfig):
    name = 'django_sqs_jobs'
    verbose_name = 'Django SQS Jobs'

    def ready(self):
        allowed_jobs = {}
        for app in apps.get_app_configs():
            try:
                jobs_mod = getattr(app.module, 'jobs')
            except AttributeError as e:
                pass
            else:
                x = [(name, cls) for name, cls in jobs_mod.__dict__.items()
                      if isinstance(cls, type) and issubclass(cls, (Job,))]

                allowed_jobs = merge_dicts(allowed_jobs, dict(x))
        WORKER_QUEUE.add_allowed_jobs(allowed_jobs)

