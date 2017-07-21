from django.conf import settings
from abc import abstractmethod, ABCMeta
from six import add_metaclass
import boto3
import json


class JobException(Exception):
    pass


class JobImplementationMissing(JobException):
    """Job is missing a callable implementation"""


@add_metaclass(ABCMeta)
class Job(object):
    """
    A job defines a way of performing a task when required.

    A job is a callable that will be called by an SQS message and given arguments.
    Another way to put it is that it's a fancy function for SQS, but could be called by anyone.

    SQS Jobs view relies on __subclasses__ to find and execute the relevant job.
    Therefore if you want your job to be executed, it MUST be a subclass of Job
    """
    ARGS = []
    KWARGS = {}
    queue_name = ''

    def __init__(self, *args, **kwargs):
        self.ARGS = self.ARGS + args
        self.KWARGS.update(kwargs)

    def setup(self, *args, **kwargs):
        pass

    def teardown(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        self.setup(*args, **kwargs)
        self.result = self.exec(*args, **kwargs)
        self.teardown(*args, **kwargs)
        return self.result

    @abstractmethod
    def exec(self, *args, **kwargs):
        raise JobImplementationMissing("Job must implement 'execution' method")

