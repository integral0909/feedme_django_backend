from django.test import TestCase, SimpleTestCase
from django_sqs_jobs import jobs, queues


class JobExample(jobs.Job):
    def exec(self, val):
        return val * 2


class JobExampleDivision(jobs.Job):
    def exec(self, numerator, denominator):
        return numerator / denominator


class CompositeJobExample(jobs.Job):
    def exec(self, *args, **kwargs):
        results = []
        for job_data_str in kwargs['jobs']:
            job = jobs.Job.decode(job_data_str, JobExample=JobExample,
                                  JobExampleDivision=JobExampleDivision)
            results.append(job())
        return results


class TestLocalQueue(SimpleTestCase):
    def setUp(self):
        self.queue = queues.LocalQueue()

    def tearDown(self):
        self.queue = None

    def test_local_queue(self):
        self.assertEqual(self.queue.name, 'local')
        self.queue.append(JobExample(5))
        for job in self.queue:
            self.assertEqual(job(), 10)

    def test_local_queue_extends(self):
        self.queue.extend([JobExample(2), JobExample(3), JobExample(4)])
        for idx, job in enumerate(self.queue):
            self.assertEqual(job(), (idx+2)*2)

    def test_multiple_jobs(self):
        self.queue.extend([JobExample(2), JobExampleDivision(8, 2), JobExample(4)])
        self.assertEqual(self.queue[0](), 4)
        self.assertEqual(self.queue[1](), 4)
        self.assertEqual(self.queue[2](), 8)

    def test_composite_jobs(self):
        cjob = CompositeJobExample(jobs=[
            JobExample(3).encode(),
            JobExampleDivision(9, 3).encode(),
        ])
        self.queue.append(cjob)
        results = self.queue[0]()
        self.assertEqual(results[0], 6)
        self.assertEqual(results[1], 3)

