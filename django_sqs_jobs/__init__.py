from .apps import WORKER_QUEUE
from .jobs import Job, CompositeJob, JobException, JobExecutionError

default_app_config = 'django_sqs_jobs.apps.DjangoSqsJobsConfig'