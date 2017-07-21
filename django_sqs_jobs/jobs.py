from abc import abstractmethod, ABCMeta
from six import add_metaclass
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

    def __init__(self, *args, **kwargs):
        self.ARGS = args
        self.KWARGS = kwargs

    def setup(self, *args, **kwargs):
        pass

    def teardown(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        self.setup(*self.ARGS, **self.KWARGS)
        self.result = self.exec(*self.ARGS, **self.KWARGS)
        self.teardown(*self.ARGS, **self.KWARGS)
        return self.result

    @abstractmethod
    def exec(self, *args, **kwargs):
        raise JobImplementationMissing("Job must implement 'execution' method")

    def encode(self):
        return json.dumps({
            'ARGS': self.ARGS, 'KWARGS': self.KWARGS, 'JOB': self.__class__.__name__
        })

    @classmethod
    def decode(cls, json_string, **kwargs):
        """
        Turns json into a Job subclass.

        Requires that potential subclasses are passed as key word arguments.
        This prevents execution of unspecified classes through json injection
        """
        job_data = json.loads(json_string)
        if cls.__name__ == job_data['JOB']:
            return cls(*job_data['ARGS'], **job_data['KWARGS'])
        JobClass = kwargs[job_data['JOB']]
        if issubclass(JobClass, Job):
            return JobClass(*job_data['ARGS'], **job_data['KWARGS'])

