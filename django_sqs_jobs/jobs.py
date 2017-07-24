from abc import abstractmethod, ABCMeta
from six import add_metaclass
from importlib import import_module
import json


class JobException(Exception):
    pass


class JobImplementationMissing(JobException):
    """Job is missing a callable implementation."""


class JobExecutionError(JobException):
    """An exception occurred during execution."""


class JobSetupError(JobException):
    """An exception occurred during setup."""


class JobTeardownError(JobException):
    """An exception occurred during teardown."""


@add_metaclass(ABCMeta)
class Job(object):
    """
    A job defines a way of performing a task when required.

    A job is a callable that will be called (usually via an SQS message) and given
    arguments. Another way to put it is that it's a fancy function for SQS, but
    could be called by anyone.

    Queues check that a job is a subclass of Job before calling, and will not call a
    non-job object for security reasons.
    """

    def __init__(self, *args, **kwargs):
        self.ARGS = args
        self.KWARGS = kwargs

    def args_parser(self):
        """
        Override this function to perform filters/transforms on args.

        Only applied during encoding or when called manually.
        """
        return self.ARGS

    def kwargs_parser(self):
        """
        Override this function to perform filters/transforms on kwargs.

        Only applied during encoding or when called manually.
        """
        return self.KWARGS

    def setup(self, *args, **kwargs):
        pass

    def teardown(self, *args, **kwargs):
        pass

    def __call__(self):
        cls = self.__class__.__name__
        try:
            self.setup(*self.ARGS, **self.KWARGS)
        except Exception as e:
            raise JobSetupError("Error during setup of %s" % cls) from e
        try:
            self.result = self.exec(*self.ARGS, **self.KWARGS)
        except Exception as e:
            raise JobExecutionError("Error during execution of %s" % cls) from e
        try:
            self.teardown(*self.ARGS, **self.KWARGS)
        except Exception as e:
            raise JobTeardownError("Error during teardown of %s" % cls) from e
        return self.result

    @abstractmethod
    def exec(self, *args, **kwargs):
        raise JobImplementationMissing("Job must implement 'exec' method")

    def encode(self):
        """Encode this Job as a JSON job string."""
        return json.dumps({
            'JOB': self.__class__.__name__, 'ARGS': self.args_parser(),
            'KWARGS': self.kwargs_parser()
        })

    @classmethod
    def decode(cls, json_string, allowed_jobs=None):
        """
        Turns json into a Job subclass.

        REQUIRED: Potential subclasses must be passed as a list of
        absolute package.module.Class path strings or a dict of {ClassName: Class} pairs.
        This prevents execution of unspecified classes through json injection
        """
        job_data = json.loads(json_string)
        if isinstance(allowed_jobs, (list, tuple)):
            allowed_jobs = cls.resolve_allowed_jobs(allowed_jobs)
        if cls.__name__ == job_data['JOB']:
            return cls(*job_data['ARGS'], **job_data['KWARGS'])
        JobClass = allowed_jobs.get(job_data['JOB'])
        if issubclass(JobClass, Job):
            return JobClass(*job_data['ARGS'], **job_data['KWARGS'])

    @classmethod
    def resolve_allowed_jobs(cls, allowed_jobs):
        """
        Turns a list of absolute package.module.Class paths into a dict of
        {ClassName: Class} pairs
        """
        job_classes = {}
        for raw_path in allowed_jobs:
            path, class_name = raw_path.rsplit('.', 1)
            mod = import_module(path)
            job_classes[class_name] = getattr(mod, class_name)
        return job_classes



class CompositeJob(Job):
    """
    Provide a list of jobs to execute and a list of allowed_jobs with full absolute path.
    """
    def exec(self, *args, **kwargs):
        results = []
        for job_raw in args:
            if isinstance(job_raw, str):
                job = Job.decode(job_raw, allowed_jobs=kwargs['allowed_jobs'])
            else:
                job = job_raw
            results.append(job())
        return results

    def args_parser(self):
        """Permanently encode args on instance and return."""
        self.ARGS = [j.encode()
                     if not isinstance(j, str) and
                     (issubclass(j, Job) or isinstance(j, Job)) else j
                     for j in self.ARGS]
        return self.ARGS
