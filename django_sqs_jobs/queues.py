from django.conf import settings
from abc import abstractmethod, ABCMeta
from six import add_metaclass
import boto3
import json


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
    queue_name = settings.SQS_JOBS.get('queue_name')

    def __init__(self, **kwargs):
        self.access_key = kwargs.get('access_key', self.access_key)
        self.secret_key = kwargs.get('secret_key', self.secret_key)
        self.region_name = kwargs.get('region_name', self.region_name)
        self.queue_name = kwargs.get('queue_name', self.queue_name)
        self.queue = self._connect()

    def _queue(self, job):
        response = self.queue.send_message(MessageBody=self._parse_job(job))
        return True if response.get('MessageId') else False

    def __next__(self):
        """In an Elastic Beanstalk Worker environment this is not used."""
        self.queue.receive_messages(MaxNumberOfMessages=1)

    def extend(self, jobs):
        self.queue.send_messages(Entries=[self._parse_job(j) for j in jobs])

    def _parse_job(self, job):
        return json.dumps({
            'ARGS': job.ARGS, 'KWARGS': job.KWARGS, 'JOB': job.__class__.__name__
        })

    def _connect(self):
        config = {
            'service_name': 'sqs',
            'region_name': self.region_name,
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key,
        }
        if self.endpoint_url:
            config['endpoint_url'] = self.endpoint_url
        return boto3.resource(**config).get_queue_by_name(QueueName=self.queue_name)


class LocalQueue(Queue):
    """An in-memory queue useful for testing and local reuse of jobs."""
    queue_name = 'local'

    def __init__(self, **kwargs):
        self.queue = []
        self.queue_name = kwargs.get('queue_name', self.queue_name)

    def _queue(self, job):
        self.queue.append(job)

    def append(self, job):
        self.queue.append(job)

    def extend(self, jobs):
        self.queue.extend(jobs)

    def __iter__(self):
        return self.queue

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
