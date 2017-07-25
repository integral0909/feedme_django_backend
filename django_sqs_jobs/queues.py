from django.conf import settings
from django_sqs_jobs import jobs
from abc import abstractmethod, ABCMeta
from six import add_metaclass
from common.utils import merge_dicts
from .daemons import SQSDaemon
import boto3


@add_metaclass(ABCMeta)
class Queue(object):
    """
    Queues are a way of storing and retrieving jobs.

    The queue metaclass does not care about implementation details,
    simply retrieving/queuing jobs.

    Subclasses should implement as many list-like methods as possible
    i.e. __contains__, __len__, __reversed__, __iter__
    """
    def append(self, value):
        """Only method for consumers to add a job to the queue"""
        self._queue(value)

    def extend(self, value):
        """Add many jobs to the queue"""
        for item in value:
            self.append(item)

    @abstractmethod
    def _queue(self, job):
        """Adds job to the queue. Required."""


    @abstractmethod
    def __next__(self):
        """Get a job from the queue"""
        pass

    def __iter__(self):
        return self


class SQSQueue(Queue):
    access_key = settings.SQS_JOBS.get('access_key')
    secret_key = settings.SQS_JOBS.get('secret_key')
    region_name = settings.SQS_JOBS.get('region_name')
    name = settings.SQS_JOBS.get('queue_name')
    endpoint_url = None

    def __init__(self, allowed_jobs=None, **kwargs):
        self.allowed_jobs = allowed_jobs or {}
        self.access_key = kwargs.get('access_key', self.access_key)
        self.secret_key = kwargs.get('secret_key', self.secret_key)
        self.region_name = kwargs.get('region_name', self.region_name)
        self.name = kwargs.get('name', self.name)
        self.queue = self._connect()
        self.daemon = SQSDaemon(sqs=self.queue, owner=self)
        self.daemon.start()

    def add_allowed_jobs(self, allowed_jobs):
        """Allows apps to register their allowed jobs."""
        self.allowed_jobs = merge_dicts(self.allowed_jobs, allowed_jobs)

    def _queue(self, job):
        """Asynchronously send job to SQS."""
        self.daemon.queue.put(job)

    def __next__(self):
        """Elastic Beanstalk Worker environments use JobMessageView instead."""
        response = self.queue.receive_messages(MaxNumberOfMessages=1)
        message = response['Messages'][0]
        receipt_handle = message['ReceiptHandle']
        job = jobs.Job.decode(message['Body'], allowed_jobs=self.allowed_jobs)
        self.queue.delete_message(
            ReceiptHandle=receipt_handle
        )
        return job

    def extend(self, jobs):
        self.daemon.queue.put(jobs)

    def _connect(self):
        config = {
            'service_name': 'sqs',
            'region_name': self.region_name,
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key,
        }
        if self.endpoint_url:
            config['endpoint_url'] = self.endpoint_url
        return boto3.resource(**config).get_queue_by_name(QueueName=self.name)


class LocalQueue(Queue):
    """An in-memory queue useful for testing and local reuse of jobs."""
    name = 'local'

    def __init__(self, **kwargs):
        self.queue = []
        self.name = kwargs.get('name', self.name)

    def _queue(self, job):
        self.queue.append(job)

    def append(self, job):
        self.queue.append(job)

    def extend(self, jobs):
        self.queue.extend(jobs)

    def __iter__(self):
        return iter(self.queue)

    def __contains__(self, job):
        return job in self.queue

    def __len__(self):
        return len(self.queue)

    def __reversed__(self):
        return reversed(self.queue)

    def __setitem__(self, key, value):
        self.queue[key] = value

    def __getitem__(self, key):
        return self.queue[key]

    def __next__(self):
        if len(self.queue):
            raise StopIteration
        return self.queue.pop()
